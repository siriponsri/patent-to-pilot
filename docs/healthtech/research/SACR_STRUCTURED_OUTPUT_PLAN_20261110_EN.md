# SACR structured-output feasibility and stopping plan

Status: preparatory engineering only. SYN-SACR-001 and SYN-SACR-002 remain failed,
immutable attempts. No benchmark or additional model call is declared here.

## Motivation and bounded work

The first profile attempt failed exact source offsets. The prospective quote-only
attempt then failed JSON syntax before alignment. More unconstrained prompt retries
would mix format debugging with method selection. Assess token-level grammar
constraints on authored fixtures before considering one separately declared smoke.

The installed lm-format-enforcer 0.11.3 offers JsonSchemaParser and a Transformers
prefix_allowed_tokens_fn integration. Its primary [repository documentation](https://github.com/noamgat/lm-format-enforcer)
describes filtering the tokens available during decoding. This changes the decoding
distribution and must be versioned as a new intervention; it does not repair an old
response or establish factual correctness.

## CPU gate

The initial probe loads only the existing Qwen tokenizer and exercises a small
quote-object schema. It checks a literal quote, an invented quote, missing comma,
wrong field enum and extra property. Expected behavior is acceptance of both
well-formed quotes and rejection of the three structural violations. Invented text
being accepted is a limitation demonstration, not a successful extraction.

This probe is NOT full-profile schema validation, exhaustive tokenizer compatibility,
model generation, GPU timing, retrieval evaluation or semantic review. Preserve its
result even if expectations fail. No installation or model weights are needed.

## Required before any third model attempt

1. Implement a versioned full quote-profile schema matching the existing validator,
   including required/optional fields, array caps and per-input identity enums.
   Document rules that remain post-generation only: unique IDs, exact quotations,
   source order, conditional consistency and semantic attachments.
2. Exercise the full schema against authored valid/invalid fixtures with both an
   independent JSON Schema validator and the actual tokenizer filter. Check multiple
   blocks, nested conditions, Unicode/escapes, empty lists, optional null roles,
   completion/EOS and truncated output. Do not claim unsupported keywords enforce
   constraints without evidence. Preserve schema and integration hashes.
3. Integrate filtering as an explicit optional, versioned generation path. Keep
   strict finish/byte/token checks, exclusive attempt reservation, unchanged raw
   output and the existing quote-alignment/semantic gates. Record decoder settings
   and actual EOS behavior; do not silently fall back to unconstrained decoding.
4. Predeclare at most ONE new synthetic engineering attempt with fixed authored
   inputs, exact schema/prompt/code/model hashes and the existing resource caps.
   Bound profile and selective calls in advance. Record every call, failure, time
   and token count. Do not execute based on this plan alone.

## Decision rule

If that separately declared attempt fails, stop the generation branch and report
the failure; do not initiate a fourth prompt/schema attempt automatically. If it
passes structure/alignment, report engineering acceptance only and move to the
predeclared fidelity review. No benchmark pilot until R1 isolation/A03/parity and
the semantic acceptance policy are resolved. No automatic alternate method.

Full SACR remains untested. An anchor fallback is a recorded failure outcome, not
evidence for SACR effectiveness. Grammar constraints cannot establish preservation
of relations, necessity of conditions, correct abstraction or retrieval benefit.
