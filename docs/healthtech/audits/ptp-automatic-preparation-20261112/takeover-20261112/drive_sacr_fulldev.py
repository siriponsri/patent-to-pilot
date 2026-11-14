"""Paper 1 S4 SACR full-dev sequential driver (derived from drive_paper1_s4_v2.py): freeze_sacr_fulldev_v2 ->
start ONCE -> wait terminal -> verify -> settle ONCE -> commit+push, for each batch in order.

Usage: python drive_sacr_fulldev.py 1 2 3 4 5 6   (79 queries x <=2 calls per batch)
The SACR worker HOLDs on ANY backend exception (owner decision A covered only the FA/GR worker), so a grammar
refusal stops the batch and the driver; that needs the owner. Stops at the first anomaly; never retries, never
restarts a launched job, settles once. Resume: launch.json present but no settlement.json -> observe with
native_control.py and settle by hand, then rerun with the remaining batches.
"""
import json, subprocess, sys, time
from pathlib import Path
R = Path('C:/Users/User/Desktop/myProject/patent-to-pilot')
A = R/'docs/healthtech/audits/ptp-automatic-preparation-20261112/takeover-20261112'
METER = ['python', str(R/'scripts/healthtech/meter_local_cpu.py'), str(A/'local-cpu-measurements.jsonl'), '--']
LOG = A/'paper1-s4-progress.jsonl'  # shared S4 log


def log(**v):
    v['unix'] = time.time()
    with LOG.open('a', encoding='utf-8') as f: f.write(json.dumps(v) + '\n')
    print(json.dumps(v), flush=True)


def run(cmd, metered=True, timeout=900):
    r = subprocess.run((METER if metered else []) + cmd, cwd=R, capture_output=True, text=True, timeout=timeout)
    if r.returncode: raise RuntimeError('command failed: %s\n%s\n%s' % (cmd, r.stdout[-2000:], r.stderr[-2000:]))
    return r.stdout


def git_checkpoint(message):
    run(['git', 'add', '-A', str(A), 'docs/healthtech/audits/ptp-mtm-dapfam-resume-20261110/resource-ledger.json'], metered=False)
    run(['git', 'commit', '-q', '-m', message + '\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'], metered=False)
    try: run(['git', 'push', '-q', 'origin', 'main'], metered=False, timeout=180)
    except Exception as error: log(event='PUSH_FAILED_COMMIT_KEPT', error=str(error)[:300])


def observe(sub):
    for attempt in range(5):
        try:  # native_control prints a truncated line; the full observation is in the file it writes
            run(['python', str(A/'native_control.py'), 'observe', sub], metered=False, timeout=120)
            done = A/sub/'terminal-observation.json'
            return json.loads((done if done.exists() else A/sub/'latest-observation.json').read_bytes())
        except Exception as error:  # observation failure is not job failure: observe the same job again
            log(event='OBSERVATION_RETRY', sub=sub, error=str(error)[:200]); time.sleep(60)
    raise RuntimeError('observation unavailable; job state UNKNOWN (not failed)')


for item in sys.argv[1:]:
    sub = 'sacr-fulldev-b%s' % item
    assert not (A/sub).exists(), sub + ' already frozen; resume by hand'
    summary = json.loads(run(['python', str(A/'freeze_sacr_fulldev_v2.py'), item]).splitlines()[0])
    name, n = summary['job'], summary['queries']
    assert summary['status'] == 'STAGED_QUALIFIED_NOT_LAUNCHED'
    log(event='FROZEN', job=name, generation=summary['journal_generation'], queries=n, dev_rows=summary['dev_rows'])
    git_checkpoint('Paper 1 S4 SACR full-dev b%s frozen (gen %d), launching' % (item, summary['journal_generation']))
    launch = json.loads(run(['python', str(A/'native_control.py'), 'start', sub], metered=False, timeout=120).splitlines()[-1])
    log(event='LAUNCHED', job=name, pid=launch.get('pid'))
    deadline = time.time() + 10800 + 900
    while True:
        time.sleep(120)
        v = observe(sub)
        if 'terminal' in v: break
        if time.time() > deadline: raise RuntimeError('no terminal receipt after the declared window; state UNKNOWN, inspect by hand')
    state, c = v['container_state'], v.get('completion')
    ok = (v['terminal'].get('status') == 'TERMINAL' and state != 'NOT_CREATED' and state['Running'] is False and state['ExitCode'] == 0
          and 'worker_failure' not in v and c and c['status'] == 'PIPELINE_TERMINAL' and c['queries'] == n
          and c['screened_candidates'] + c['fallbacks'] == n and len(v['call_markers']) == c['call_slots_consumed'])
    log(event='TERMINAL', job=name, ok=bool(ok), exit=state.get('ExitCode') if state != 'NOT_CREATED' else None,
        wall=v['terminal'].get('whole_wall_seconds'), completion=c, worker_failure=v.get('worker_failure'))
    settled = json.loads(run(['python', str(A/'settle_synthetic.py'), name, sub]).splitlines()[0])
    cost = settled['study']['stage_costs'][name]
    calls_ok = bool(c) and cost['calls_complete'] is True and cost['known_calls'] == c['call_slots_consumed']
    log(event='SETTLED', job=name, generation=settled['generation'], study=settled['study']['status'], cost=cost, calls_accounting_ok=calls_ok,
        gpu_charged=settled['gpu_charged'], model_calls=settled['model_calls'])
    git_checkpoint('Paper 1 S4 SACR full-dev b%s settled (gen %d): %s' % (item, settled['generation'],
                   'screened %d, fallback %d, %d calls, %d s' % (c['screened_candidates'], c['fallbacks'], c['call_slots_consumed'], cost['seconds'])
                   if ok and calls_ok else 'ANOMALY - stopped'))
    if not ok or not calls_ok or settled['study']['status'] != 'IDLE' or settled['approved_gpu_occupied']:
        log(event='STOPPED_OWNER_DECISION_REQUIRED', job=name); sys.exit(2)
log(event='DRIVER_COMPLETE', items=['sacr-b' + i for i in sys.argv[1:]])
