# Full profile schema: CPU compatibility gate FAILED
The inline quote-profile schema binds input identity and all nested field types,
required fields, enums, optional nullable roles and eight-block/eight-condition caps.
It does not enforce exact source quotes, unique IDs, source order, whitespace-only
text, conditional status consistency or semantic correctness; downstream validation
remains mandatory. Existing profile/quote checks plus new schema tests: 46 passed.
Ruff passed for all three new Python files.

Eight authored fixtures were independently checked with jsonschema4.26.0:
all eight matched expectations. The actual Qwen tokenizer with installed
lm-format-enforcer0.11.3 matched seven; the Unicode/optional-null fixture failed.
The original result.json is preserved with all_expected=false. No model weights,
model calls, GPU generation or benchmark data. SSH stdin execution, not a model
experiment or archive deployment. All probe processes completed.

The diagnostic consumes the same authored fixture character by character:
the parser refuses the first Thai character at character260, while can_end is false.
At token109 the token filter instead allows EOS151645. This is evidence of a
parser/token-filter dead-end path that can terminate before a complete object.
The combined fixture's failure is localized to Thai text, not evidence that all
optional-null/escape behavior is broken or verified. Nested English and two-block
fixtures passed; duplicate IDs remain intentionally grammar-valid and require the
post-check. Successful complete examples allowed EOS151645, not151643.

Do not connect this default configuration to model generation or declare SYN-SACR-003.
Next inspect the installed parser alphabet and dead-end behavior, design a documented
Unicode-capable configuration and fail-closed integration, then run a distinct
versioned CPU check. Preserve this failed receipt. Do not silently narrow source
text to ASCII, normalize quotations, or add a completion salvage path. The bounded
one-third-model-attempt rule remains; no fourth automatic attempt if that fails.
Curator/environment, actual A03/parity and semantic acceptance gates remain open.

Artifacts: authored-fixtures.json contains only developer-authored text/schema;
result.json is the actual token probe; independent-validation.json is the independent
schema check; diagnostic.json localizes the rejected character. None is model output.
