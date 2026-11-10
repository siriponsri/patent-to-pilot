# SYN-SACR-004 prospective source-order prompt correction

Status: DECLARED_NOT_RUN. Uses the owner's one additional synthetic smoke authorization after diagnosed repair. No further generation attempt is authorized by this document.

SYN003 failed canonical source-order validation despite completed/schema-valid exact quotations. `sacr_profile.validate_profile` compares the minimum block-span start to the previous block's minimum, permitting equal starts. Old prompt said source order without this operational definition. New prompt `sacr_profile_quotes_order_v2.txt` explicitly specifies that same rule, distinguishes block evidence from condition evidence, and prohibits output sorting/repair. This is a prospective prompt hypothesis, not proof that it cures the failure.

The old prompt/default assembly and v3 smoke remain unchanged. `build_messages` accepts an explicit source_order_v2 variant only for profile_quotes; schema identity remains sacr-profile-quotes-v1. New v4 smoke pins prompt bytes before loading the model and again before the single call. Authored source, model, decoder, grammar and validation are unchanged. No benchmark text, labels, targets or prior generated answer embedded in the prompt.

25 prompt/profile tests PASS, including unchanged legacy default, identical source/identity across variants, different prompt/message hashes, invalid variant rejection and existing source-order rejection. New smoke syntax PASS. A local file-generation command failed quoting before execution, then explicit copy/patch succeeded; zero model calls.

Configuration digest `9127a6a42c0ccaa9cdee9b5bcfb253b41aebd8fd149c36bd3e934599804bbda6` binds declaration fields before adding the digest field itself. Prompt/script byte hashes are in declaration.json. Acceptance is EOS plus unchanged exact quote/canonical profile checks, not semantic fidelity. Maximum one call,1800s plus declared supervisor handling,8CPU,total32GiB,one approved GPU; cumulative ledger retained. Next bind final isolated supervisor/image/model/grammar inputs and resource reservation, then dispatch once. Preserve unsuccessful output and costs; no automatic additional smoke.
