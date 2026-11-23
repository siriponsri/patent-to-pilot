"""A3r1 RunPod rebuild: fetch (if absent) and verify the previously approved encoder files at their recorded revisions.

Amendment: docs/healthtech/research/g03-dev/A3R1-AMENDMENT-RUNPOD-REBUILD.md (owner D23: "the PatEmbed and Qwen3 weights are
the previously approved items at their recorded revisions"; Arctic is the D20 item, needed only to rebuild ser-arctic-v1).
Every pinned file must match its recorded sha256, or the script exits 1 and nothing may be encoded.

Pins come from the repository records, never from the download:
  qwen3     Qwen/Qwen3-Embedding-0.6B @97b0c614...  docs/healthtech/research/paper1-bridgeret/models.sha256
  patembed  datalyes/patembed-large   @2d5c0f92...  dr-train org-adaptive-20261105/code/dl_patembed_large.py (archived 21 Nov)
                                                    = scripts/healthtech/run_dapfam_native_baseline.py MODEL_PINS
  arctic    Snowflake/snowflake-arctic-embed-m-v2.0 @95c27414...  paper1-bridgeret/models.sha256

Usage: python3 -I g03_a3r1_runpod_models.py <qwen3|patembed|arctic> <dest_dir> [--verify-only]
"""
import hashlib
import json
import sys
from pathlib import Path

PINS = {
    'qwen3': ('Qwen/Qwen3-Embedding-0.6B', '97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3', {
        '1_Pooling/config.json': '37bf193fa101f19101bfad9c31d3eb0f786e247b7b1e5cb7f007d730eed1ddbd',
        'config.json': 'b5bf1f51fc45be473a54718cef92448d90a1be001bf9b9a44b8c7f10a19feaa9',
        'config_sentence_transformers.json': '10667c72ddb772627bf1780cb7f86af8e2ae0032b8c243c731172064105c6961',
        'generation_config.json': '28396d421a2108acce96383f6a7de78008f7f1b17f807958f3c14c51dbfb65fb',
        'merges.txt': '8831e4f1a044471340f7c0a83d7bd71306a5b867e95fd870f74d0c5308a904d5',
        'model.safetensors': '0437e45c94563b09e13cb7a64478fc406947a93cb34a7e05870fc8dcd48e23fd',
        'modules.json': '84e40c8e006c9b1d6c122e02cba9b02458120b5fb0c87b746c41e0207cf642cf',
        'README.md': 'c34d9b7e5a267ad3fdd13227a253686bc90844ff4744a2a6a86c7c905e3d06f3',
        'tokenizer_config.json': '253153d0738ceb4c668d2eff957714dd2bea0b56de772a9fdccd96cbf517e6a0',
        'tokenizer.json': 'def76fb086971c7867b829c23a26261e38d9d74e02139253b38aeb9df8b4b50a',
        'vocab.json': 'ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910',
    }),
    'patembed': ('datalyes/patembed-large', '2d5c0f92a3e5dc3d5415c08e612c57543c0e03ad', {
        'model.safetensors': '234ea36a876fe5d5c416c1cbaad6f7221e17861fadd6481f0b96588fdc1ca482',
        'vocab.txt': 'a123c19b8d4677efb40940208592207ef800cf302149a85ba073b430d050f591',
        'tokenizer_config.json': '0088a6f8bcdd4014184fb068b83ebb12896a9db2bb269a71f73de83fef24bceb',
        'special_tokens_map.json': 'b6d346be366a7d1d48332dbc9fdf3bf8960b5d879522b7799ddba59e76237ee3',
        'modules.json': '8f4b264b80206c830bebbdcae377e137925650a433b689343a63bdc9b3145460',
        'tokenizer.json': 'd5496fadd2d7fda4e958da4285f7cd97c41177bbfc500580addc9c08896fb773',
        'config_sentence_transformers.json': '187f2d0a140e537a751e283983ddacc129614333726dfb78b986b6c723dd8d2d',
        'config.json': 'bfa5f86c1416b6df6e51ef0b8a6d0d4cc8f34c083d0435c57856b95f8ed47854',
        'sentence_bert_config.json': '948201d8329907aae938fa62f9ceeed53f5694dacc2b87b9f3b78b37ee986529',
        '1_Pooling/config.json': 'a30548e8bc4255aafe5e5c638f6b15712eebbc8e84ea5988a5835f976c412907',
    }),
    'arctic': ('Snowflake/snowflake-arctic-embed-m-v2.0', '95c2741480856aa9666782eb4afe11959938017f', {
        '1_Pooling/config.json': '2b1d283d4e7e9a64eef827933051d26478d271766eb234c76012f9012cd97907',
        'config.json': '2e0b386e7a826903b06c301f8d4dde2ac6279f7ccd3ea11f3911019a1ee0bc05',
        'config_sentence_transformers.json': 'e4037d7ad09d5c33b4c8b132e485f2fc0866707688ce46d2c642f066be1d3bd4',
        'configuration_hf_alibaba_nlp_gte.py': 'd31622918ecf738d1bb082bb27fe8141c3189238cef51d464c7f68e32bbe3d54',
        'modeling_hf_alibaba_nlp_gte.py': 'f8dff057e7c91790771f24ac8b8c172ab5c863835194872539c74fa5f538ed4c',
        'model.safetensors': '3d80d4727ac8759fb8624b690697c053a3d1992120111dc4a71178e608c26604',
        'modules.json': 'c6e29747481e8b5dd2b58401966aeac910de39092f90cda9a704b1545f902b04',
        'README.md': '049aaf65db2b2e3713faf49b34a92728bd39eb7b16fb6987f93faaf62ba4531c',
        'special_tokens_map.json': '8c785abebea9ae3257b61681b4e6fd8365ceafde980c21970d001e834cf10835',
        'tokenizer_config.json': '6f00514620aff01ba8b7291b2394e98daca5be264cb743805232d9ae27494b2a',
        'tokenizer.json': 'f1cc44ad7faaeec47241864835473fd5403f2da94673f3f764a77ebcb0a803ec',
    }),
}


def fsha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def main(argv):
    if len(argv) < 2 or argv[0] not in PINS:
        raise SystemExit(__doc__)
    which, dest, verify_only = argv[0], Path(argv[1]), '--verify-only' in argv[2:]
    repo, rev, pins = PINS[which]
    missing = [k for k in pins if not (dest / k).is_file()]
    if missing and not verify_only:
        from huggingface_hub import hf_hub_download
        dest.mkdir(parents=True, exist_ok=True)
        for k in missing:
            hf_hub_download(repo, k, revision=rev, local_dir=str(dest))
    got = {k: fsha(dest / k) if (dest / k).is_file() else None for k in pins}
    bad = {k: v for k, v in got.items() if v != pins[k]}
    res = {'model': which, 'repo': repo, 'revision': rev, 'dest': str(dest), 'files': len(pins),
           'status': 'PASS' if not bad else 'FAIL', 'mismatch_or_missing': sorted(bad)}
    (dest / f'pins-verified-{which}.json').write_text(json.dumps({**res, 'sha256': got}, indent=1)) if dest.is_dir() else None
    print(json.dumps(res), flush=True)
    sys.exit(0 if not bad else 1)


if __name__ == '__main__':
    main(sys.argv[1:])
