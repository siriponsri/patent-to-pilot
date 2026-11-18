"""Serialise BridgeRet texts to the 512-token cap of one tokenizer (pre-declaration section 3).

passages.jsonl : unit, text, ntok, truncated(dict)     (no prompt for documents)
queries.jsonl  : app_id, block, text, ntok, truncated  (non-TEST tasks; cap counts the query prompt)
Usage: python3 -I serialise_bridgeret_texts.py <texts_dir> <tokenizer_dir> <query_prompt> <out_dir> [workers]
"""
import json, multiprocessing as mp, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from patent_to_pilot.research import bridgeret_query as q
except ImportError:
    import bridgeret_query as q

TOK = None
PROMPT = ''


def init(tok_dir, prompt):
    global TOK, PROMPT
    from transformers import AutoTokenizer
    TOK = AutoTokenizer.from_pretrained(tok_dir)
    PROMPT = prompt


def ser(args):
    line, is_query = args
    r = json.loads(line)
    if is_query and not r.get('doc'):
        return None
    pre = PROMPT if is_query else ''
    count = lambda t: len(TOK(pre + t, add_special_tokens=True)['input_ids'])
    claims = [q.ClaimRow(1, r['claim'])] if r.get('claim') else []
    s = q.serialise(r.get('title') or '(no title)', r.get('abstract'), claims, count, 512)
    key = {'app_id': r['app_id'], 'block': r['block']} if is_query else {'unit': r['unit']}
    return json.dumps({**key, 'text': s.text, 'ntok': s.tokens, 'truncated': s.truncated, 'variant': s.variant},
                      ensure_ascii=False)


def main(argv):
    d, tok_dir, prompt, out = Path(argv[0]), argv[1], argv[2], Path(argv[3])
    workers = int(argv[4]) if len(argv) > 4 else 16
    out.mkdir(parents=True, exist_ok=False)
    with mp.get_context('fork').Pool(workers, initializer=init, initargs=(tok_dir, prompt)) as pool:
        for name, is_q in (('queries.jsonl', True), ('passages.jsonl', False)):
            src = 'queries.jsonl' if is_q else 'corpus.jsonl'
            with open(d / src, encoding='utf-8') as f, open(out / name, 'w', encoding='utf-8') as g:
                for res in pool.imap(ser, ((l, is_q) for l in f), chunksize=256):
                    if res:
                        g.write(res + '\n')
    print('done', out)


if __name__ == '__main__':
    main(sys.argv[1:])
