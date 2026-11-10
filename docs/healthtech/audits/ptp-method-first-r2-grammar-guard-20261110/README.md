# Grammar dead-end diagnosis and prospective guard
Installed lm-format-enforcer0.11.3 source was inspected read-only on dr-train.
CharacterLevelParserConfig defaults to a 92-character alphabet. TokenEnforcer
_apply_new_characters catches character-parser exceptions and substitutes
ForceStopParser; _compute_allowed_tokens also falls back to EOS on unexpected
exceptions. These paths explain why an EOS token is not a completion certificate.
No library files or environment settings were changed.

Read-only Qwen tokenizer inspection found 17,829 distinct characters in individually
decoded vocabulary tokens, including all three Thai letters and the emoji in the
previous failed fixture. This observation does not prove correct filtering with a
new alphabet or arbitrary Unicode support.

Added CompleteJsonEOSGuard: when the proposed tokens include either configured EOS,
independently decode the generated suffix and require a complete JSON object with
no duplicate keys/non-JSON constants, accepted by an independent schema validator.
If incomplete, remove EOS; if nothing remains, raise a generic boundary error without
the generated text. This closes EOS-only library fallbacks without salvaging output.
The guard is prospective and not yet connected to model.generate. It requires the
exact prompt-token boundary and one sequence. Final quote alignment/semantic checks
remain mandatory. Other library exceptions still fail the attempt, never retry.

Added deterministic alphabet builder: printable ASCII + individually decoded
tokenizer vocabulary + allowed source characters, sorted and hashed. Controls must
use JSON escapes; source text itself is unchanged. Lone surrogates are refused.
This is a finite vocabulary/source alphabet, NOT a promise of all Unicode output.
Tokenizer identity must be pinned. Config knobs must be explicitly fixed in the
next CPU check rather than inherited from environment variables.

39 targeted tests passed (alphabet4, guard10, schema17, generation8). Ruff passed
for four new files. These are local tests; actual configured-tokenizer integration
remains NOT_RUN. Prior full-schema failure remains immutable. No model calls or GPU
jobs. Next: a new versioned CPU probe with the pinned schema and explicit parser
settings, the alphabet builder, independent EOS guard, null-only/escape-only cases
and the original failed fixture. Record all results; do not overwrite the first
probe. Only after that gate and generation integration may one bounded third model
attempt be declared. R1 actual isolation/A03/parity and semantic acceptance still open.
