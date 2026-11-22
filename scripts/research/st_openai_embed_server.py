"""Minimal OpenAI-compatible embedding server around sentence-transformers (research/QA tool, G02).

Serves GET /v1/models and POST /v1/embeddings for ONE local model directory, bound to 127.0.0.1 only.
It exists so the Workbench's ``openai_compatible`` adapter can be checked against a real model without
installing vLLM/TEI. It is not part of the product and downloads nothing (``local_files_only``).

    CUDA_VISIBLE_DEVICES= python st_openai_embed_server.py --model-dir /data/ptp-paper2/models/qwen3-embedding-0.6b \
        --served-name Qwen/Qwen3-Embedding-0.6B --port 18000
"""
from __future__ import annotations

import argparse
import hashlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", required=True)
    ap.add_argument("--served-name", required=True)
    ap.add_argument("--port", type=int, default=18000)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--max-batch", type=int, default=32)
    args = ap.parse_args()

    from sentence_transformers import SentenceTransformer  # imported late: --help works without it

    model = SentenceTransformer(args.model_dir, device=args.device, local_files_only=True)
    files = sorted(p for p in Path(args.model_dir).rglob("*") if p.is_file() and p.suffix in (".safetensors", ".bin"))
    h = hashlib.sha256()
    for p in files:
        h.update(p.name.encode())
        h.update(str(p.stat().st_size).encode())
    weights_id = "files-sha256:" + h.hexdigest()[:16]
    lock = threading.Lock()
    print(f"loaded {args.served_name} from {args.model_dir} ({weights_id}) on {args.device}", flush=True)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *a):
            print("[srv]", fmt % a, flush=True)

        def _out(self, code, obj):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802
            if self.path == "/v1/models":
                return self._out(200, {"object": "list", "data": [{"id": args.served_name, "object": "model",
                                                                    "owned_by": "local", "weights_id": weights_id}]})
            return self._out(404, {"error": {"message": "not found"}})

        def do_POST(self):  # noqa: N802
            if self.path != "/v1/embeddings":
                return self._out(404, {"error": {"message": "not found"}})
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
                texts = body["input"] if isinstance(body["input"], list) else [body["input"]]
                if body.get("model") != args.served_name:
                    return self._out(404, {"error": {"message": f"model {body.get('model')} not served"}})
                if len(texts) > args.max_batch or not all(isinstance(t, str) for t in texts):
                    return self._out(400, {"error": {"message": "bad input"}})
            except (ValueError, KeyError):
                return self._out(400, {"error": {"message": "bad request"}})
            with lock:
                vecs = model.encode(texts, normalize_embeddings=False, convert_to_numpy=True)
            n_tok = sum(len(model.tokenizer(t)["input_ids"]) for t in texts)
            return self._out(200, {"object": "list", "model": args.served_name,
                                   "data": [{"object": "embedding", "index": i, "embedding": v.astype(float).tolist()}
                                            for i, v in enumerate(vecs)],
                                   "usage": {"prompt_tokens": n_tok, "total_tokens": n_tok}})

    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"serving on http://127.0.0.1:{args.port}/v1", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
