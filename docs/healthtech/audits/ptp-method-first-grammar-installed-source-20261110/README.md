# Installed-source verification and candidate adapter

Five installed LMFE0.11.3 source files on the configured research venv match the
reviewed tagged upstream bytes exactly; see `source-comparison.json`. Verification
used Python standard-library distribution metadata, exact file reads and SHA256
over SSH. No LMFE import, tokenizer/model load, parser callback, GPU or benchmark
data access. Command exited0. This does not attest the whole dependency environment
or prove runtime causality. Remote model/job state was not surveyed.

The new `sacr_escape_callback.py` is an explicitly unused candidate adapter. It
checks the five supplied source pins and version before LMFE imports, preserves
the existing free-text cache/quote traversal, and adds exact-parser traversal of
the legal backslash subtree. It restores the explicitly requested root config
after the upstream constructor overwrites it, before consuming tokens, and exposes
requested/overwritten/effective root-config receipts with alphabet hashes. The
parser context is initially constructed from that same requested config. The
callback deduplicates overlapping token IDs. Installed library files are untouched.

No existing generation path imports or dispatches this adapter. No claim that it
passes the tokenizer gate: token-state/context consistency, string-length handling,
escape boundary negatives, all previous fixtures, EOS and cost bounds remain to
be checked in a separately declared CPU-only run. Keep the independent EOS guard;
do not infer valid complete output merely from this callback's allowed token list.

Local validation is limited to Python syntax compilation and Ruff. No new grammar
or model attempt was executed and no SYN-SACR-003 was declared. Prior429 related
tests remain historical; they do not test this new adapter.

Next: fix the unchanged full fixture payload, precise augmented escape cases,
source/schema/tokenizer/code pins, wall-time cap and terminal handling in one CPU
declaration before execution. Source match supports this bounded design, not
automatic repeated variants. A CPU PASS would still not establish model generation,
fidelity, R1 isolation/parity or R3 acceptance. Owner protocol/curator questions
remain pending; protected evaluation remains unauthorized.
