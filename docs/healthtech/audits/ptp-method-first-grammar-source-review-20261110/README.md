# Static source review of preserved escape-token failure

Status: SOURCE_SUPPORTED_REPAIR_HYPOTHESIS; NOT_RUNTIME_VERIFIED. No tokenizer,
grammar callback, model, remote job or retry executed. Historical failures remain.

## Evidence and inference

The stored diagnostic reports two strings accepted by complete character parsing
but refused at token111, whose decoded characters are backslash, quote, backslash.
Installed version was recorded as0.11.3; installed source equality to the reviewed
tagged upstream files is NOT_VERIFIED.

In upstream [v0.11.3 tokenizer cache](https://github.com/noamgat/lm-format-enforcer/blob/v0.11.3/lmformatenforcer/tokenizerprefixtree.py),
`add_token` checks some escaped strings by surrounding them with quotes and requiring
the standalone JSON string to parse. The recorded token's trailing backslash escapes
the appended closing quote, leaving that wrapper incomplete. It can therefore be
omitted from the free-text cache even though subsequent characters could complete
the escape. This is source reasoning, not a new execution of the cache predicate.

Upstream [token traversal](https://github.com/noamgat/lm-format-enforcer/blob/v0.11.3/lmformatenforcer/tokenenforcer.py)
combines cached free-text tokens with dynamic exploration restricted to quote-starting
children. An omitted backslash-starting token is not recovered when that shortcut
applies. A candidate repair retains the cache and explores the legal backslash
subtree through the exact character parser. This is narrower than disabling all
shortcuts, which previously timed out. Other token shapes, length accounting,
pending escapes and decoding remain untested; completeness is not established.

## Separate effective-configuration issue

That TokenEnforcer constructor also creates a new config and assigns it to the
supplied parser. The [base setter](https://github.com/noamgat/lm-format-enforcer/blob/v0.11.3/lmformatenforcer/characterlevelparser.py)
replaces stored config; other settings use environment/default factories.
The [Transformers builder](https://github.com/noamgat/lm-format-enforcer/blob/v0.11.3/lmformatenforcer/integrations/transformers.py)
constructs TokenEnforcer directly. The [JSON parser](https://github.com/noamgat/lm-format-enforcer/blob/v0.11.3/lmformatenforcer/jsonschemaparser.py)
has already snapshotted alphabet-derived context. Historical config fields therefore
describe requested settings, not verified effective settings after construction.
Do not infer actual values from defaults or version alone. Context/config agreement
also requires observation. Raw receipts stay unchanged; clarification is appended.

## Bounded next design, not a launch declaration

1. Compare installed source hashes to reviewed tagged files before relying on this
   mechanism; stop on mismatch, without changing installed packages.
2. Design a version-pinned project-local adapter preserving explicit effective config
   and exploring only the legal backslash subtree alongside cache/quote traversal.
   Keep the independent complete-JSON EOS guard and unchanged source quotations.
3. Snapshot config before/after construction and parser transitions; check context
   consistency instead of merely editing the reported settings dictionary.
4. Separately declare a time-bounded CPU check with unchanged full fixtures plus
   escape-boundary/length negatives. Preserve failure/time receipts and inspect the
   same process handle on timeout; do not automatically restart.
5. No SYN-SACR-003, model integration, global package monkeypatch, character removal,
   output salvage or automatic retry follows. CPU PASS would not authorize R3.

Owner protocol and curator questions remain pending. Actual R1/generation/fidelity/
resource gates and R3-R6 remain incomplete. No scientific advantage is claimed.
An initial documentation patch failed because a methods-log context marker did not
exist; it applied no changes, and the corrected append uses inspected context.
