"""Paper 1 S4 sequential driver: for each (arm, batch) given, freeze -> start ONCE -> wait terminal -> verify -> settle ONCE -> commit+push.

Usage: python drive_paper1_s4.py FA:1 FA:2 FA:3 GR:1 ...
Stops at the first anomaly (non-zero exit, missing completion, worker failure, non-TERMINAL supervisor status,
incomplete calls, study not IDLE). It never retries, never restarts a launched job and never settles twice.
Fallback counts are pipeline outcomes, not failures. Resuming after an interruption: if a batch has launch.json
but no settlement.json, observe it with native_control.py and settle it by hand; then rerun with the remaining batches.
"""
import json, subprocess, sys, time
from pathlib import Path
R = Path('C:/Users/User/Desktop/myProject/patent-to-pilot')
A = R/'docs/healthtech/audits/ptp-automatic-preparation-20261112/takeover-20261112'
METER = ['python', str(R/'scripts/healthtech/meter_local_cpu.py'), str(A/'local-cpu-measurements.jsonl'), '--']
LOG = A/'paper1-s4-progress.jsonl'


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
    run(['git', 'commit', '-q', '-m', message + '\n\nCo-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>'], metered=False)
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
    arm, batch = item.split(':'); low = arm.lower(); sub = 'paper1-s4-%s-b%s' % (low, batch)
    name = 'ptp-auto-paper1-%s-fulldev-b%s-20261113-v1' % (low, batch)
    assert not (A/sub).exists(), sub + ' already frozen; resume by hand'
    summary = json.loads(run(['python', str(A/'freeze_paper1_s4.py'), arm, batch]).splitlines()[0])
    assert summary['status'] == 'STAGED_QUALIFIED_NOT_LAUNCHED' and summary['job'] == name
    log(event='FROZEN', job=name, generation=summary['journal_generation'])
    git_checkpoint('Paper 1 S4 %s b%s frozen (gen %d), launching' % (arm, batch, summary['journal_generation']))
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
          and 'worker_failure' not in v and c and c['status'] == 'PIPELINE_TERMINAL' and c['queries'] == 158
          and c['rewrites_used'] + c['fallbacks'] == 158 and len(v['call_markers']) == c['call_slots_consumed'])
    log(event='TERMINAL', job=name, ok=bool(ok), exit=state.get('ExitCode') if state != 'NOT_CREATED' else None,
        wall=v['terminal'].get('whole_wall_seconds'), completion=c, worker_failure=v.get('worker_failure'))
    settled = json.loads(run(['python', str(A/'settle_synthetic.py'), name, sub]).splitlines()[0])
    cost = settled['study']['stage_costs'][name]
    log(event='SETTLED', job=name, generation=settled['generation'], study=settled['study']['status'], cost=cost,
        gpu_charged=settled['gpu_charged'], model_calls=settled['model_calls'])
    git_checkpoint('Paper 1 S4 %s b%s settled (gen %d): %s' % (arm, batch, settled['generation'],
                   'used %d, fallback %d, %d s' % (c['rewrites_used'], c['fallbacks'], cost['seconds']) if ok else 'ANOMALY - stopped'))
    if not ok or settled['study']['status'] != 'IDLE' or cost['calls_complete'] is not True or settled['approved_gpu_occupied']:
        log(event='STOPPED_OWNER_DECISION_REQUIRED', job=name); sys.exit(2)
log(event='DRIVER_COMPLETE', items=sys.argv[1:])
