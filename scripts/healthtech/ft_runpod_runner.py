"""P1-BridgeRet fine-tuning grid runner for a RunPod pod (owner envelope USD 20; pre-declaration AM-1/AM-2).

Runs on the pod. For each config, in order: train with train_bridgeret.py, encode the 1M Challenge-1M passages and the
P1-DEV + VAL queries with the checkpoint, and write top-1000 runs (RPD mask, self-unit exclusion, the same rule as
dense_bridgeret.py) to results/<name>/run-<BLOCK>.tsv.gz. Then delete the weights and touch results/<name>/DONE.
The bundle holds no TEST block and no gold. Evaluation happens on dr-train (eval_bridgeret_dev.py).
A watchdog stops the work at --deadline-hours. After ALL_DONE, the pod waits up to 2 h for the PULLED marker that dr-train
writes after copying results, then asks runpodctl to stop the pod.
Usage: python3 ft_runpod_runner.py --bundle /workspace/bundle --model /workspace/models/qwen3 --configs configs.json
       --work /workspace/work --results /workspace/results --deadline-hours 30
"""
import argparse, csv, gzip, json, os, shutil, subprocess, sys, time
from pathlib import Path

QPROMPT = 'Instruct: Given a patent application, retrieve prior art cited against it\nQuery: '
TOPK = 1000
BLOCKS = ('P1-DEV', 'VAL')


def encode_and_retrieve(ck, bundle, outdir, bs=64):
    import numpy as np, torch, torch.nn.functional as F
    from transformers import AutoModel, AutoTokenizer
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(ck, padding_side='left')
    model = AutoModel.from_pretrained(ck, torch_dtype=torch.float16).cuda().eval()

    def enc(texts):
        b = tok(texts, padding=True, truncation=True, max_length=512, return_tensors='pt').to('cuda')
        with torch.inference_mode():
            return F.normalize(model(**b).last_hidden_state[:, -1].float(), dim=-1).half()

    units, texts = [], []
    with open(bundle / 'ser' / 'passages.jsonl', encoding='utf-8') as f:
        for l in f:
            r = json.loads(l); units.append(r['unit']); texts.append(r['text'])
    order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
    P = torch.zeros((len(texts), model.config.hidden_size), dtype=torch.float16, device='cuda')
    for s in range(0, len(order), bs):
        idx = order[s:s + bs]
        P[idx] = enc([texts[i] for i in idx])
    del texts
    enc_sec = time.time() - t0
    pub = {}
    with open(bundle / 'corpus-units.tsv', encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            pub[r['unit_id']] = int(r['first_pub'].replace('-', ''))
    pubs = torch.tensor([pub[u] for u in units], device='cuda'); uidx = {u: i for i, u in enumerate(units)}
    fd = {}
    with open(bundle / 'tasks-ft.tsv', encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            fd[r['app_id']] = int(r['filing_date'].replace('-', ''))
    qs = [json.loads(l) for l in open(bundle / 'ser' / 'queries.jsonl', encoding='utf-8')]
    for blk in BLOCKS:
        sel = [r for r in qs if r['block'] == blk]
        with gzip.open(outdir / f'run-{blk}.tsv.gz', 'wt', encoding='utf-8') as g:
            g.write('app_id\trank\tunit\tscore\n')
            for s in range(0, len(sel), 256):
                chunk = sel[s:s + 256]
                Q = torch.cat([enc([QPROMPT + r['text'] for r in chunk[i:i + bs]]) for i in range(0, len(chunk), bs)])
                S = (Q @ P.T).float()
                for i, r in enumerate(chunk):
                    S[i][pubs >= fd[r['app_id']]] = -float('inf')
                    own = uidx.get('A:' + r['app_id'])
                    if own is not None:
                        S[i][own] = -float('inf')
                vals, idx = torch.topk(S, TOPK, dim=1)
                vals, idx = vals.cpu().numpy(), idx.cpu().numpy()
                for i, r in enumerate(chunk):
                    rows = [(float(v), units[j]) for v, j in zip(vals[i], idx[i]) if v != -float('inf')]
                    rows.sort(key=lambda x: (-x[0], uidx[x[1]]))      # ties by corpus index, as dense_bridgeret
                    g.write(''.join(f"{r['app_id']}\t{k + 1}\t{u}\t{v:.5f}\n" for k, (v, u) in enumerate(rows)))
    return {'encode_seconds': round(enc_sec, 1), 'retrieve_seconds': round(time.time() - t0 - enc_sec, 1)}


def stop_pod(reason):
    print('STOP_POD', reason, flush=True)
    pid = os.environ.get('RUNPOD_POD_ID')
    if pid and shutil.which('runpodctl'):
        subprocess.run(['runpodctl', 'stop', 'pod', pid])


def main():
    ap = argparse.ArgumentParser()
    for a in ('--bundle', '--model', '--configs', '--work', '--results'):
        ap.add_argument(a, required=True)
    ap.add_argument('--deadline-hours', type=float, required=True)
    ap.add_argument('--encode-only', default='')
    a = ap.parse_args()
    t_start = time.time(); deadline = t_start + a.deadline_hours * 3600
    bundle, work, res = Path(a.bundle), Path(a.work), Path(a.results)
    work.mkdir(parents=True, exist_ok=True); res.mkdir(parents=True, exist_ok=True)
    configs = json.load(open(a.configs))
    for c in configs:
        name = c['name']; od = res / name
        if (od / 'DONE').exists():
            continue
        if time.time() > deadline:
            (res / 'DEADLINE').write_text(name); break
        od.mkdir(exist_ok=True)
        wd = work / name
        if wd.exists():
            shutil.rmtree(wd)                                    # an interrupted config restarts cleanly
        cmd = [sys.executable, str(bundle / 'code' / 'train_bridgeret.py'), '--device', 'cuda', '--model', a.model,
               '--mined', str(bundle / 'mined-TRAIN.jsonl'), '--ser', str(bundle / 'ser'), '--out', str(wd),
               '--recipe', c['recipe'], '--k', str(c.get('k', 3)), '--tau', str(c['tau']), '--w-out', str(c.get('w_out', 1.0)),
               '--denoise', c.get('denoise', 'rule'), '--subset', str(c.get('subset', 0)), '--bq', str(c.get('bq', 16)),
               '--seed', str(c.get('seed', 1)), '--pooling', 'last', '--query-prompt', QPROMPT]
        t0 = time.time()
        with open(od / 'train.log', 'w') as lg:
            rc = subprocess.run(cmd, stdout=lg, stderr=subprocess.STDOUT).returncode
        for f in ('train-log.jsonl', 'train-config.json'):
            if (wd / f).exists():
                shutil.copyfile(wd / f, od / f)
        if rc != 0:
            (od / 'FAILED').write_text(f'train rc={rc}'); continue
        info = {'train_seconds': round(time.time() - t0, 1)}
        info.update(encode_and_retrieve(wd / 'checkpoint', bundle, od))
        if c.get('keep_checkpoint'):
            shutil.move(str(wd / 'checkpoint'), str(od / 'checkpoint'))
        shutil.rmtree(wd)
        (od / 'timing.json').write_text(json.dumps(info))
        (od / 'DONE').write_text('ok')
        print('CONFIG_DONE', name, info, flush=True)
    (res / 'ALL_DONE').write_text(str(round(time.time() - t_start, 1)))
    t_wait = time.time()
    while not (res / 'PULLED').exists() and time.time() - t_wait < 7200:
        time.sleep(60)
    stop_pod('pulled' if (res / 'PULLED').exists() else 'pull wait timeout')


if __name__ == '__main__':
    main()
