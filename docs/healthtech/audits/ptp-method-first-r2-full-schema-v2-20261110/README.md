# Full-schema CPU integration v2: FAILED escape-token compatibility
Versioned CPU check using committed modules11d7a164f6c2a7217ddea2e13565c4c6121a1caf,
a Git ZIP archive imported from a remote temporary file, and authored v2 probe source.
No model weights, model calls, benchmark inputs or GPU generation. Original v1
result remains unchanged. Probe and follow-up diagnostic completed exit0.

The vocabulary/source alphabet has17,797 non-control scalar characters, SHA256
9ecba166f5fb315a848212e8428f54900bfb420b72095f5f49df48732d202635.
Parser settings are explicit: whitespace4096, field order false, uncapped-array
default4096 (schema block/condition caps still8). Token budget4096 in the proposed
generation contract is the separate overall bound. Independent complete-JSON/schema
EOS guard wraps the token callback. No premature EOS observed in these ten cases.

Independent JSON Schema:10/10 expected. Actual token callback:8/10 expected.
The original Unicode fixture and new ASCII-escape-only fixture fail at token111.
Null-only succeeds. Diagnostic character-by-character parsing now accepts both
complete failing strings and can_end is true. The rejected token decodes to a
backslash, double quote, backslash sequence. Thus the remaining discrepancy is
between character parsing and token filtering for combined escape tokens; this
does NOT establish broken Unicode parsing or a successful production decoder.

Installed JsonSchemaParser.shortcut_key source exposes a json_freetext token-cache
optimization. It is a candidate cause, not yet proven. Next bounded diagnostic:
compare default and no-shortcut character-parser wrappers at the rejected token
with the same prefix, and inspect token-tree handling. Do not modify the installed
library, silently restrict quotation characters, or salvage output. Preserve this
failed receipt. Any proposed fix must be explicitly versioned and pass the full
fixture set before generation integration or SYN-SACR-003 declaration.
R1 curator/isolation/A03/parity and semantic acceptance remain unresolved.
Ruff passed for the new probe. Prior39 component tests were not re-run because
their code was unchanged; this package adds actual tokenizer evidence.
