"""RunPod pilot for P1-BridgeRet (owner-approved, cap USD 10). Engineering timing only, no quality.
Inputs are random token ids whose lengths follow the measured TRAIN token-length histogram of the Arctic tokenizer
(2,000 TRAIN queries with 'query: ', 16,000 passages; bin = upper edge, width 16, cap 512). Speed depends on length,
not content. Measures encode passages/s (fp16, fp32) and full-FT step time/peak memory (1 pos + in-batch + 7 negs).
"""
import json, random, time, torch, torch.nn.functional as F
from transformers import AutoModel

Q = [[80,1],[96,6],[112,10],[128,14],[144,37],[160,38],[176,53],[192,63],[208,75],[224,78],[240,86],[256,105],[272,106],[288,104],[304,122],[320,100],[336,113],[352,94],[368,115],[384,73],[400,98],[416,79],[432,42],[448,55],[464,45],[480,33],[496,37],[512,218]]
P = [[32,5],[48,2],[64,3],[80,12],[96,22],[112,61],[128,87],[144,148],[160,229],[176,251],[192,363],[208,473],[224,512],[240,540],[256,624],[272,696],[288,767],[304,789],[320,795],[336,766],[352,753],[368,732],[384,619],[400,688],[416,556],[432,565],[448,518],[464,435],[480,456],[496,371],[512,3162]]
TRAIN_PAIRS, CORPUS, rnd = 409866, 1000000, random.Random(20261119)


def lens(h, n):
    return rnd.choices([e for e, _ in h], weights=[c for _, c in h], k=n)


def batch(ls):
    m = max(ls); ids = torch.randint(1000, 200000, (len(ls), m)); att = torch.zeros(len(ls), m, dtype=torch.long)
    for i, l in enumerate(ls):
        att[i, :l] = 1; ids[i, l:] = 1
    return {'input_ids': ids.cuda(), 'attention_mask': att.cuda()}


def model(dtype):
    return AutoModel.from_pretrained('/workspace/arctic', trust_remote_code=True, use_memory_efficient_attention=False,
                                     unpad_inputs=False, torch_dtype=dtype).cuda()


def emb(m, b):
    return F.normalize(m(**b).last_hidden_state[:, 0], dim=-1)


R = {'gpu': torch.cuda.get_device_name(0), 'torch': torch.__version__, 'bf16': torch.cuda.is_bf16_supported(),
     'method': 'random token ids, TRAIN length histogram', 'encode': [], 'train': []}
plen = lens(P, 4096)
for dt, nm in ((torch.float16, 'fp16'), (torch.float32, 'fp32')):
    m = model(dt).eval()
    for bs in (64, 128, 256):
        torch.cuda.reset_peak_memory_stats(); torch.cuda.synchronize(); t = time.time()
        try:
            with torch.inference_mode():
                for i in range(0, len(plen), bs):
                    emb(m, batch(plen[i:i + bs]))
            torch.cuda.synchronize(); r = len(plen) / (time.time() - t)
            R['encode'].append({'dtype': nm, 'batch': bs, 'p_per_s': round(r, 1), 'peak_gb': round(torch.cuda.max_memory_allocated() / 2**30, 2), 'h_1M': round(CORPUS / r / 3600, 3)})
        except torch.cuda.OutOfMemoryError:
            R['encode'].append({'dtype': nm, 'batch': bs, 'oom': True}); torch.cuda.empty_cache()
        print(R['encode'][-1], flush=True)
    del m; torch.cuda.empty_cache()
amp = torch.bfloat16 if R['bf16'] else torch.float16
for gc in (False, True):
    for bs in (16, 32, 64, 128):
        m = model(torch.float32).train()
        if gc: m.gradient_checkpointing_enable()
        opt = torch.optim.AdamW(m.parameters(), lr=2e-5); sc = torch.amp.GradScaler(enabled=amp == torch.float16)
        torch.cuda.reset_peak_memory_stats(); ts = []
        try:
            for step in range(10):
                qb, db = batch(lens(Q, bs)), batch(lens(P, bs * 8)); torch.cuda.synchronize(); t = time.time()
                with torch.autocast('cuda', dtype=amp):
                    loss = F.cross_entropy(emb(m, qb) @ emb(m, db).T / 0.02, torch.arange(bs, device='cuda') * 8)
                opt.zero_grad(); sc.scale(loss).backward(); sc.step(opt); sc.update(); torch.cuda.synchronize()
                if step >= 2: ts.append(time.time() - t)
            s = sum(ts) / len(ts)
            R['train'].append({'grad_ckpt': gc, 'bq': bs, 'docs': bs * 8, 'amp': str(amp), 'step_s': round(s, 3), 'peak_gb': round(torch.cuda.max_memory_allocated() / 2**30, 2), 'h_epoch': round(TRAIN_PAIRS / bs * s / 3600, 2)})
        except torch.cuda.OutOfMemoryError:
            R['train'].append({'grad_ckpt': gc, 'bq': bs, 'oom': True})
        print(R['train'][-1], flush=True)
        del m, opt; torch.cuda.empty_cache()
json.dump(R, open('/workspace/pilot-result.json', 'w'), indent=1); print('PILOT_DONE', flush=True)
