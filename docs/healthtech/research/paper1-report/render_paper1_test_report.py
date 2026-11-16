#!/usr/bin/env python3
"""Render the Paper 1 report tables (Markdown) from an evaluator summary.json. Standard library only.

Input: the summary.json written by scripts/healthtech/run_paper1_dev_eval.py
  - kind paper1-test-eval  -> status PAPER1_TEST_EVALUATED_ONCE, split 'test', results.confirmatory present;
  - kind paper1-dev-eval   -> status PAPER1_DEV_EVALUATED_DESCRIPTIVE (dev, descriptive, no verdicts).
A terminal-observation.json that embeds the summary under the key 'summary.json' is accepted too.

Optional:
  --dev PATH        the S5 dev summary, shown side by side with a test summary (Recall@200 and paired deltas);
  --receipts DIR    the takeover audit folder; the efficiency table is built from the settlement receipts found
                    there (missing receipts are shown as PENDING, never estimated).

The renderer only formats numbers that are already in the inputs. It does not recompute metrics or intervals.
It does re-apply the frozen interpretation rule (paper1_analysis.interpret / gatekeep / noninferior, copied below)
to the CIs in the summary and reports MATCH or MISMATCH, as a consistency check on the summary.

Usage:
  python render_paper1_test_report.py SUMMARY [--dev DEV_SUMMARY] [--receipts DIR] [--out REPORT.md]
"""
import argparse
import json
import math
import sys
from pathlib import Path

DEFAULT_DEV = ('docs/healthtech/audits/ptp-automatic-preparation-20261112/takeover-20261112/'
               'paper1-s5-eval/terminal-observation.json')
DEFAULT_RECEIPTS = 'docs/healthtech/audits/ptp-automatic-preparation-20261112/takeover-20261112'

PARTITIONS = ('OUT', 'IN', 'ALL')
SYSTEMS = ('B0', 'FA', 'GR', 'SACR', 'F-FA', 'F-GR', 'F-SACR', 'F-shuffle')
METRICS = ('Recall@10', 'Recall@100', 'Recall@200', 'NDCG@10', 'NDCG@100', 'NDCG@200')
PRIMARY = 'Recall@200'
COMPARISON_ORDER = ('H1', 'H2', 'H3', 'C2', 'F-GR_vs_B0', 'F-SACR_vs_B0', 'F-shuffle_vs_B0',
                    'FA_standalone', 'GR_standalone', 'SACR_standalone')
GATEKEEPING = (('H1', 'F-FA', 'B0'), ('H2', 'F-FA', 'F-GR'), ('H3', 'F-FA', 'F-SACR'))
# Frozen constants (paper1_analysis.py, frozen 13 Nov 2026). Used only for the consistency re-check.
EQUIVALENCE_MARGIN = 0.010
NONINFERIORITY_MARGIN = 0.020
LABEL_WORDS = {
    'SUPERIOR': 'superior (95% CI entirely above 0)',
    'INFERIOR': 'inferior (95% CI entirely below 0)',
    'PRACTICALLY_EQUIVALENT': 'practically equivalent (95% CI inside -delta..+delta)',
    'INCONCLUSIVE': 'inconclusive (CI includes 0 and reaches beyond delta)',
    'NOT_TESTED_GATE_CLOSED': 'not tested (an earlier step did not conclude superior)',
}
RANK_BINS = ('1-10', '11-50', '51-100', '101-200', 'none')
STRATA = ('both', 'arm_only', 'reference_only', 'neither')

# Generation jobs per split and arm (audit sub-folders under --receipts). The lists are the actual batch layout:
# dev from S4 (including continuation jobs after a held query), test from the S8 driver plan.
GENERATION_JOBS = {
    'dev': {
        'FA': ['paper1-s4-fa-b1', 'paper1-s4-fa-b2', 'paper1-s4-fa-b2c', 'paper1-s4-fa-b3'],
        'GR': ['paper1-s4-gr-b1', 'paper1-s4-gr-b2', 'paper1-s4-gr-b3'],
        'SACR': ['sacr-fulldev-b1', 'sacr-fulldev-b2', 'sacr-fulldev-b3', 'sacr-fulldev-b4', 'sacr-fulldev-b4c',
                 'sacr-fulldev-b4d', 'sacr-fulldev-b5', 'sacr-fulldev-b6'],
    },
    'test': {
        'FA': ['paper1-s8-fa-b%d' % i for i in range(1, 6)],
        'GR': ['paper1-s8-gr-b%d' % i for i in range(1, 6)],
        'SACR': ['paper1-s8-sacr-b%d' % i for i in range(1, 11)],
    },
}
RETRIEVAL_JOB = {'dev': 'paper1-s5-retrieval', 'test': 'paper1-s8-retrieval'}
EVAL_JOB = {'dev': 'paper1-s5-eval', 'test': 'paper1-s8-eval'}
SPLIT_QUERIES = {'dev': 474, 'test': 773}
MAX_CALLS_PER_QUERY = {'FA': 1, 'GR': 1, 'SACR': 2}
PENDING = '_PENDING_'


# ---------------------------------------------------------------- loading

def load_summary(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if 'summary.json' in data and isinstance(data['summary.json'], dict):
        data = data['summary.json']
    if 'results' not in data or 'main' not in data['results']:
        raise ValueError('%s: not a Paper 1 evaluator summary (no results.main)' % path)
    return data


def split_of(summary):
    if summary.get('split') in ('dev', 'test'):
        return summary['split']
    return 'test' if summary.get('status') == 'PAPER1_TEST_EVALUATED_ONCE' else 'dev'


def query_count(summary):
    return summary.get('queries', summary.get('dev_queries'))


# ---------------------------------------------------------------- formatting

def f4(x):
    return '—' if x is None else '%.4f' % x


def sd4(x):
    return '—' if x is None else '%+.4f' % x


def ci(c):
    return '—' if not c else '[%+.4f, %+.4f]' % (c['ci_low'], c['ci_high'])


def pct(x):
    return '—' if x is None else '%.1f%%' % (100 * x)


def table(header, rows):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '|'.join('---' for _ in header) + '|']
    out += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]
    return '\n'.join(out)


def systems_in(part):
    present = part.get('metrics', {})
    return [s for s in SYSTEMS if s in present] + sorted(s for s in present if s not in SYSTEMS)


# ---------------------------------------------------------------- frozen rule (copy, for the re-check only)

def interpret(c, margin=EQUIVALENCE_MARGIN):
    if c['ci_low'] > 0:
        return 'SUPERIOR'
    if c['ci_high'] < 0:
        return 'INFERIOR'
    if -margin < c['ci_low'] and c['ci_high'] < margin:
        return 'PRACTICALLY_EQUIVALENT'
    return 'INCONCLUSIVE'


def gatekeep(cis):
    out, open_gate = {}, True
    for step, _, _ in GATEKEEPING:
        if not open_gate:
            out[step] = 'NOT_TESTED_GATE_CLOSED'
            continue
        out[step] = interpret(cis[step])
        open_gate = out[step] == 'SUPERIOR'
    return out


def noninferior(c, margin=NONINFERIORITY_MARGIN):
    return c['ci_low'] > -margin


# ---------------------------------------------------------------- sections

def section_header(s, dev):
    split = split_of(s)
    lines = ['## Report header', '',
             table(['Field', 'Value'], [
                 ['Split', split],
                 ['Status', s.get('status', '—')],
                 ['Queries', query_count(s)],
                 ['Protected test access', s.get('protected_test_access', '—')],
                 ['Gatekeeping applied', s.get('gatekeeping_applied', '—')],
                 ['Significance claim', s.get('significance_claim', '—')],
                 ['Retrieval reference', s.get('retrieval_reference', '—')],
                 ['Evaluator process CPU s', f4(s.get('process_cpu_seconds'))],
             ])]
    if s.get('_synthetic'):
        lines += ['', '**SYNTHETIC INPUT: %s**' % s['_synthetic']]
    if dev is not None:
        lines += ['', 'Side-by-side dev summary: status %s, %s queries.' % (dev.get('status', '—'), query_count(dev))]
    if split == 'dev':
        lines += ['', 'Dev results are descriptive (protocol section 6). Intervals are reported for readiness and '
                      'planning only; no verdicts or significance labels are produced for dev.']
    return '\n'.join(lines)


def section_metrics(s, dev):
    lines = ['## Table R1. Retrieval metrics per system (macro over eligible queries)']
    with_dev = dev is not None and split_of(s) == 'test'
    for p in PARTITIONS:
        part = s['results']['main'][p]
        if not part.get('eligible_queries'):
            lines += ['', '### %s: no eligible queries' % p]
            continue
        header = ['System'] + list(METRICS)
        if with_dev:
            header.append('dev %s' % PRIMARY)
        rows = []
        for name in systems_in(part):
            m = part['metrics'][name]
            row = [name] + [f4(m.get(k)) for k in METRICS]
            if with_dev:
                row.append(f4(dev['results']['main'][p]['metrics'].get(name, {}).get(PRIMARY)))
            rows.append(row)
        lines += ['', '### R1-%s (eligible queries: %s; target components: %s; largest component share: %s)'
                  % (p, part['eligible_queries'], part.get('components', '—'), pct(part.get('largest_component_share'))),
                  '', table(header, rows)]
    return '\n'.join(lines)


def section_paired(s, dev):
    lines = ['## Table R2. Paired differences in %s (system minus reference, same queries)' % PRIMARY,
             '', 'CI = cluster bootstrap over connected components of the query-to-positive graph '
                 '(10,000 resamples, seed 20261113, percentile 95%). W/L/T = queries where the system is better / '
                 'worse / equal.']
    with_dev = dev is not None and split_of(s) == 'test'
    for p in PARTITIONS:
        part = s['results']['main'][p]
        pp = part.get('paired_primary')
        if not pp:
            continue
        header = ['Label', 'System − reference', 'n', 'Mean Δ', '95% CI', 'W/L/T', 'Paired SD', 'MDE (80%, n=556)']
        if with_dev:
            header += ['dev mean Δ', 'dev 95% CI']
        rows, sens = [], []
        for label in [l for l in COMPARISON_ORDER if l in pp] + sorted(l for l in pp if l not in COMPARISON_ORDER):
            r = pp[label]
            row = [label, '%s − %s' % (r['system'], r['reference']), r['queries'], sd4(r['mean_delta']),
                   ci(r['cluster_bootstrap_descriptive']), '%d/%d/%d' % (r['wins'], r['losses'], r['ties']),
                   f4(r.get('paired_sd')), f4(r.get('mde_80_power'))]
            if with_dev:
                d = dev['results']['main'][p]['paired_primary'].get(label)
                row += [sd4(d['mean_delta']) if d else '—', ci(d['cluster_bootstrap_descriptive']) if d else '—']
            rows.append(row)
            if 'query_bootstrap_sensitivity' in r:
                sens.append([label, ci(r['query_bootstrap_sensitivity']), f4(r.get('sign_flip_p_sensitivity'))])
        lines += ['', '### R2-%s' % p, '', table(header, rows)]
        if sens:
            lines += ['', 'Sensitivity (largest component > 50% of queries; the primary decision does not change):',
                      '', table(['Label', 'Query-level bootstrap 95% CI', 'Sign-flip p'], sens)]
    return '\n'.join(lines)


def section_gatekeeping(s):
    lines = ['## Table R3. Confirmatory gatekeeping H1 → H2 → H3 (OUT %s)' % PRIMARY]
    conf = s['results'].get('confirmatory')
    if split_of(s) != 'test' or conf is None:
        lines += ['', 'Not applicable: this is a dev summary (descriptive, protocol section 6). '
                      'No gatekeeping verdicts are computed or shown.']
        return '\n'.join(lines), None
    margin = conf.get('equivalence_margin')
    out_pp = s['results']['main']['OUT']['paired_primary']
    recheck = gatekeep(conf['cis'])
    rows, problems = [], []
    for step, system, reference in GATEKEEPING:
        c = conf['cis'][step]
        verdict = conf['gatekeeping'][step]
        if (out_pp[step]['system'], out_pp[step]['reference']) != (system, reference):
            problems.append('%s compares %s − %s, expected %s − %s' % (step, out_pp[step]['system'],
                            out_pp[step]['reference'], system, reference))
        if c != out_pp[step]['cluster_bootstrap_descriptive']:
            problems.append('%s: confirmatory CI differs from the OUT paired CI' % step)
        check = 'MATCH' if recheck[step] == verdict else 'MISMATCH (re-check gives %s)' % recheck[step]
        if check != 'MATCH':
            problems.append('%s verdict %s, frozen rule gives %s' % (step, verdict, recheck[step]))
        rows.append([step, '%s − %s' % (system, reference), sd4(c['mean']), ci(c), '`%s`' % verdict,
                     LABEL_WORDS.get(verdict, verdict), check])
    lines += ['', 'Two-sided alpha 0.05; each step is tested only if the previous one concluded SUPERIOR. '
                  'Equivalence margin delta = %s (absolute OUT %s).' % (margin, PRIMARY), '',
              table(['Step', 'Comparison', 'Mean Δ', '95% CI', 'Verdict (as returned)', 'Meaning', 'Re-check'], rows)]
    per = conf.get('per_step_interpretation_if_tested', {})
    closed = [st for st, _, _ in GATEKEEPING if conf['gatekeeping'][st] == 'NOT_TESTED_GATE_CLOSED']
    if closed:
        lines += ['', 'Descriptive only, not a confirmatory result: the interpretation each closed step would have '
                      'received if tested: ' + '; '.join('%s `%s`' % (st, per.get(st, '—')) for st in closed) + '.']
    harm_rows = []
    for p in ('IN', 'ALL'):
        h = conf['harm_check_F-FA_vs_B0'][p]
        mine = noninferior(h['ci'], conf.get('harm_noninferiority_margin', NONINFERIORITY_MARGIN))
        if mine != h['noninferior']:
            problems.append('harm %s: summary says %s, frozen rule gives %s' % (p, h['noninferior'], mine))
        harm_rows.append([p, 'F-FA − B0', sd4(h['ci']['mean']), ci(h['ci']), '-%s' % conf.get('harm_noninferiority_margin'),
                          'non-inferior' if h['noninferior'] else 'non-inferiority NOT shown',
                          'MATCH' if mine == h['noninferior'] else 'MISMATCH'])
    lines += ['', '### R3b. Harm check (secondary, non-inferiority of F-FA vs B0 on %s)' % PRIMARY, '',
              table(['Partition', 'Comparison', 'Mean Δ', '95% CI', 'Margin', 'Result', 'Re-check'], harm_rows)]
    c2 = conf.get('c2_descriptive')
    if c2:
        lines += ['', 'C2 (F-FA − F-shuffle, OUT), descriptive and outside the gatekeeping: mean %s, 95%% CI %s.'
                  % (sd4(c2['mean']), ci(c2))]
    lines += ['', 'Consistency re-check: ' + ('all verdicts MATCH the frozen rule applied to the reported CIs.'
                                              if not problems else 'PROBLEMS: ' + '; '.join(problems))]
    return '\n'.join(lines), problems


def section_controls(s, dev):
    lines = ['## Table R4. Controls (amendment A1)', '', '### R4-C1. Manipulation check (label-free)', '']
    c1 = s.get('c1') or {}
    rows = []
    for arm in ('FA', 'GR', 'SACR', 'shuffle'):
        r = c1.get(arm)
        if not r:
            continue
        tr = r.get('truncation') or {}
        rows.append([arm, r.get('used_queries', '—'), pct(r.get('identical_top_k_share')),
                     f4(r.get('mean_top_k_jaccard')), '%s/%s' % (tr.get('truncated', '—'), tr.get('texts', '—')),
                     r.get('verdict', '—')])
    at = c1.get('anchor_truncation')
    if at:
        rows.append(['anchors (original query)', at.get('texts', '—'), '—', '—',
                     '%s/%s' % (at.get('truncated', '—'), at.get('texts', '—')), '—'])
    lines.append(table(['Arm', 'Non-fallback queries', 'Top-200 identical to reference', 'Mean top-200 Jaccard',
                        'Texts truncated', 'Verdict'], rows) if rows else '_No C1 block in this summary._')
    lines += ['', 'Rule: more than 95% identical top-200 lists = ENGINEERING_FAULT; the arm is not evaluated.']

    lines += ['', '### R4-C2. F-shuffle control (B0 fused with a word-shuffled copy of the query; no LLM)', '']
    rows = []
    for p in PARTITIONS:
        pp = s['results']['main'][p].get('paired_primary', {})
        for label in ('C2', 'F-shuffle_vs_B0'):
            if label in pp:
                r = pp[label]
                rows.append([p, '%s − %s' % (r['system'], r['reference']), r['queries'], sd4(r['mean_delta']),
                             ci(r['cluster_bootstrap_descriptive']), '%d/%d/%d' % (r['wins'], r['losses'], r['ties'])])
    lines.append(table(['Partition', 'Comparison', 'n', 'Mean Δ', '95% CI', 'W/L/T'], rows))

    lines += ['', '### R4-C3. Family-overlap sensitivity (queries whose family is in the corpus excluded)', '']
    audit = s['results'].get('c3_audit', {})
    lines.append('Audit: %s queries; %s query families occur in the corpus; %s are their own positives; '
                 '%s queries excluded in the sensitivity run.' % (audit.get('queries', '—'),
                 audit.get('query_families_in_corpus', '—'), audit.get('self_positive_queries', '—'),
                 audit.get('excluded_queries', '—')))
    c3 = s['results'].get('c3_family_overlap_sensitivity', {})
    rows = []
    for p in PARTITIONS:
        main, sens = s['results']['main'][p], c3.get(p, {})
        if not sens.get('eligible_queries'):
            continue
        row = [p, '%s → %s' % (main.get('eligible_queries'), sens.get('eligible_queries'))]
        for name in ('B0', 'F-FA', 'F-GR', 'F-SACR'):
            row.append('%s → %s' % (f4(main['metrics'][name][PRIMARY]), f4(sens['metrics'][name][PRIMARY])))
        for label in ('H1', 'H2', 'H3'):
            a, b = main['paired_primary'][label], sens['paired_primary'][label]
            row.append('%s → %s %s' % (sd4(a['mean_delta']), sd4(b['mean_delta']), ci(b['cluster_bootstrap_descriptive'])))
        rows.append(row)
    lines += ['', table(['Partition', 'Eligible (main → C3)', 'B0 R@200', 'F-FA R@200', 'F-GR R@200', 'F-SACR R@200',
                         'H1 Δ (main → C3, C3 CI)', 'H2 Δ', 'H3 Δ'], rows)]
    return '\n'.join(lines)


def section_exposure(s):
    lines = ['## Table R5. Exposure: queries with at least one known positive in the top 200']
    for p in PARTITIONS:
        part = s['results']['main'][p]
        n = part.get('eligible_queries')
        if not n:
            continue
        names = systems_in(part)
        exp = part.get('exposure_at_200', {})
        strata = part.get('exposure_strata_vs_B0', {})
        rows = []
        for name in names:
            st = strata.get(name)
            rows.append([name, '%s/%s' % (exp.get(name, '—'), n), pct(exp[name] / n) if name in exp else '—']
                        + ([st[k] for k in STRATA] if st else ['—'] * 4))
        lines += ['', '### R5-%s (n = %s)' % (p, n), '',
                  table(['System', 'Exposed', 'Share', 'Both', 'System only (rescued)', 'B0 only (displaced)',
                         'Neither'], rows)]
        bins = part.get('first_positive_rank_bins', {})
        unj = part.get('unjudged_share_top10', {})
        rows = [[name] + [bins.get(name, {}).get(b, 0) for b in RANK_BINS] + [pct(unj.get(name))] for name in names]
        lines += ['', 'First known positive by rank bin, and share of top-10 results with no judgment '
                      '(unjudged is not negative):', '',
                  table(['System'] + ['rank %s' % b if b != 'none' else 'none in top 200' for b in RANK_BINS]
                        + ['Unjudged top-10 share'], rows)]
    return '\n'.join(lines)


def section_panels(s):
    pc = s.get('panel_counts') or {}
    rows = [[arm, pc[arm].get('used', '—'), pc[arm].get('fallback', '—'),
             pct(pc[arm]['fallback'] / (pc[arm]['used'] + pc[arm]['fallback']))
             if isinstance(pc[arm].get('fallback'), int) and isinstance(pc[arm].get('used'), int) else '—']
            for arm in ('FA', 'GR', 'SACR') if arm in pc]
    return '\n'.join(['## Table R6. Arm output used vs original-query fallback', '',
                      table(['Arm', 'LLM output used', 'Fallback to original query', 'Fallback share'], rows)
                      if rows else '_No panel counts in this summary._',
                      '', 'Every fallback query stays in the denominator.'])


def _read(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def collect_efficiency(receipts, split):
    """-> (rows by arm, shared rows, list of receipt paths used). Only receipts that exist are read."""
    root = Path(receipts)
    arms, used = {}, []
    for arm, jobs in GENERATION_JOBS[split].items():
        settled, seconds, calls, complete, cpu = 0, 0.0, 0, True, 0.0
        for job in jobs:
            p = root / job / 'settlement-terminal.json'
            r = _read(p)
            if r is None:
                continue
            settled += 1
            used.append(str(p))
            seconds += math.ceil(r['whole_wall_seconds'])
            calls += r['known_model_calls']
            complete = complete and bool(r.get('calls_complete'))
            cpu += r.get('aggregate_cpu_seconds') or 0.0
        arms[arm] = dict(batches=len(jobs), settled=settled, gpu_seconds=seconds, calls=calls,
                         calls_complete=complete, cpu=cpu)
    shared = {}
    for label, job in (('retrieval', RETRIEVAL_JOB[split]), ('evaluation', EVAL_JOB[split])):
        p = root / job / ('settlement-terminal.json' if label == 'retrieval' else 'terminal-observation.json')
        r = _read(p)
        if r is not None:
            used.append(str(p))
            wall = r.get('whole_wall_seconds', (r.get('terminal') or {}).get('whole_wall_seconds'))
            shared[label] = dict(wall=wall, calls=r.get('known_model_calls', (r.get('terminal') or {}).get('model_calls')))
    return arms, shared, used


def section_efficiency(s, receipts):
    split = split_of(s)
    lines = ['## Table R7. Efficiency (generation cost per arm, from settlement receipts)', '']
    if receipts is None:
        lines.append('_No receipts folder given; run with --receipts._')
        return '\n'.join(lines), []
    arms, shared, used = collect_efficiency(receipts, split)
    nq = SPLIT_QUERIES[split]
    rows = []
    for arm in ('FA', 'GR', 'SACR'):
        a = arms[arm]
        done = a['settled'] == a['batches']
        per_q = f4(a['gpu_seconds'] / nq) if done else '%s (%d/%d batches settled)' % (PENDING, a['settled'], a['batches'])
        rows.append([arm, '%d/%d' % (a['settled'], a['batches']), '%.0f' % a['gpu_seconds'], per_q,
                     '%d%s' % (a['calls'], '' if a['calls_complete'] else ' (lower bound)'),
                     f4(a['calls'] / nq) if done else PENDING, MAX_CALLS_PER_QUERY[arm],
                     '_NOT IN PUBLIC RECEIPTS_'])
    rows.append(['B0', '—', '0', '0', '0', '0', 0, '0'])
    lines += ['Split: %s, %d queries per arm. GPU seconds = wall time of each generation job, rounded up as charged '
              '(includes model load). Calls = known model calls from the settlement receipts.' % (split, nq), '',
              table(['Arm', 'Batches settled', 'GPU s (generation)', 'GPU s / query', 'Model calls', 'Calls / query',
                     'Max calls / query', 'Tokens in/out'], rows)]
    srows = []
    for label in ('retrieval', 'evaluation'):
        r = shared.get(label)
        srows.append([label, ('%.1f' % r['wall']) if r and r.get('wall') is not None else PENDING,
                      r.get('calls', '—') if r else PENDING,
                      'GPU, all arms + B0 + F-shuffle encodes' if label == 'retrieval' else 'CPU only'])
    lines += ['', 'Shared jobs (not attributed to one arm):', '',
              table(['Job', 'Wall s', 'Model calls', 'Resource'], srows),
              '', 'Token counts per call are kept only in the private call records on the remote host; '
                  'they are not in the public receipts and are left as a placeholder.',
              '', 'Receipts read (%d):' % len(used), ''] + ['- `%s`' % p.replace('\\', '/') for p in used]
    return '\n'.join(lines), used


def render(summary, dev=None, receipts=None):
    gate_text, problems = section_gatekeeping(summary)
    eff_text, _ = section_efficiency(summary, receipts)
    parts = ['# Paper 1 results tables (%s)' % split_of(summary),
             '_Generated by render_paper1_test_report.py from the evaluator summary. Do not edit numbers by hand._',
             section_header(summary, dev), section_metrics(summary, dev), section_paired(summary, dev), gate_text,
             section_controls(summary, dev), section_exposure(summary), section_panels(summary), eff_text]
    return '\n\n'.join(parts) + '\n', problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('summary')
    ap.add_argument('--dev', help='S5 dev summary for side-by-side (test mode)')
    ap.add_argument('--receipts', help='takeover audit folder with the settlement receipts')
    ap.add_argument('--out', help='write Markdown here (default: stdout)')
    a = ap.parse_args(argv)
    summary = load_summary(a.summary)
    dev = load_summary(a.dev) if a.dev else None
    text, problems = render(summary, dev, a.receipts)
    if a.out:
        Path(a.out).write_text(text, encoding='utf-8')
    else:
        sys.stdout.write(text)
    if problems:
        sys.stderr.write('CONSISTENCY PROBLEMS: %s\n' % '; '.join(problems))
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
