# OSF registration update sheet (update 1)

**AUDITED: YES** (main planner, 28 November 2026). This sheet tells the owner's browser agent (GPT-6.2 Sol high with the Chrome extension) how to file one update to registration [p2smd](https://osf.io/p2smd) (doi:10.17605/OSF.IO/P2SMD) **before** the C′ gate runs.

**Why.** The original registration (28 November 2026, 03:59 UTC) asks for the digest of an "OSF-issued registered PDF", but OSF issued no PDF, and the ten supporting files were not attached. The study therefore locks the canonical original registration record instead. The co-planner audit found this the only blocker. The statistical plan is unchanged. Filing before the gate shows that the correction preceded any knowledge of its verdict.

## Rules for the agent

1. Use only the owner's signed-in session. Never enter credentials.
2. Open https://osf.io/p2smd and choose **Update** (OSF registration update). Do not withdraw, re-register or create a new registration.
3. Paste text **verbatim** from this sheet. Do not reword, shorten or translate.
4. Change only the two fields below, using exact find-and-replace. Leave every other field untouched.
5. **Stop before submitting the update.** Show the owner the justification, the two edited fields and a count of changed sentences (expected: 2 in the first field, 7 in the second). Submit only after the owner types `submit`.
6. After submission, report the update's timestamp and the version shown on the registration page.

## 1. Justification (paste into the update's justification box)

> The original registration was submitted on 28 November 2026 at 03:59 UTC. Some responses were reworded during entry, and none of the ten intended supporting files was attached. The repository release lock was subsequently calculated from the canonical public OSF registration record. The original text requires a registered-PDF digest, but no OSF-issued registration PDF was available for that lock. We are documenting the artifact substitution before running the C′ gate or inspecting any new protected labels, counts or scores. The original registration and the prior-exposure disclosures remain part of the study record. The exploratory C9 training window is widened from January 2027 to December 2026 or January 2027, still before the core Track A freeze, so that the study can finish earlier; C9 data, roster, budget and failure rules are unchanged. The statistical plan, hypotheses, thresholds, retry rules and prospective-freeze rules are unchanged.

## 2. Field containing "The preregistration PDF records the exact checksums." (data access and availability)

Find this exact text:

> The preregistration PDF records the exact checksums. The OSF hash manifest records the canonical attachment checksum.

Replace it with:

> The audited supporting package, including the preregistration PDF and the hash manifest, is available at Git revision 52908944 (https://github.com/siriponsri/patent-to-pilot/tree/52908944f8d659a955e3fdc4316a4b6080691ce6/docs/loe-bench). The seven linked JSON specifications and manifests match the audited LF SHA-256 values listed in that manifest. "Set of active ingredients" uses the frozen FIX2c active-moiety key for eligibility, outcomes, clustering and C3 linkage. The +10 percentage-point threshold describes practical usefulness and is reported separately from the superiority decision.

## 3. Field containing "Secondary measures of forecasting performance" (the long exploratory and release field)

Make these seven find-and-replace edits. Each "find" text occurs exactly once.

**3a.** Find:

> The OSF hash manifest records the LF checksums of the frozen configurations and specifications.

Replace with:

> The hash manifest at Git revision 52908944 (https://github.com/siriponsri/patent-to-pilot/blob/52908944f8d659a955e3fdc4316a4b6080691ce6/docs/loe-bench/OSF-HASH-MANIFEST.txt) records the LF checksums of the frozen configurations and specifications.

**3b.** Find:

> The preregistration PDF records the exact checksum for the C9 prompt renderer.

Replace with:

> The C9 prompt renderer's LF SHA-256 is 07e43988f7aeecacf9a8078b2cf1f519608eaf5828666110def92fd380f9f1e9.

**3c.** Find:

> The OSF hash manifest records the LF SHA-256 checksum for the C9 v2 specification.

Replace with:

> The C9 v2 specification's LF SHA-256 is e865e719e7fcbd8fa636164270c4c3959d007cb9357cbedb59d7802b8951f28f.

**3d.** Find:

> After registration, the first author downloads the registered PDF, and the analysis lead records the SHA-256 of those exact bytes in loe-bench/data/PREREG_LOCK.json under sha256. Follow the post-registration sequence above. Before C′ scoring, require the first author's authorization, the gate's PASS, pinned source and code identities and the same lowercase registered PDF digest in LOE_PREREG_SHA256.

Replace with:

> For C′ release, use the SHA-256 of the original registration's canonical UTF-8 JSON archived at https://github.com/siriponsri/patent-to-pilot/blob/f0bdb0c5/loe-bench/data/OSF_REGISTRATION_P2SMD.json and rebuilt from the original OSF schema response by loe-bench/scripts/osf_lock.py. Its digest is 3f91145251465b0ed9c89233337748e1b9fd84db8c4c2a6158860374670e1c77. Preserve these original bytes across registration updates. Follow the post-registration sequence above. Before C′ scoring, require this exact lowercase digest in PREREG_LOCK.json and LOE_PREREG_SHA256, the first author's authorization, a PASS gate verdict and verified source and code identities. A failed release check stops scoring. All statistical, retry and prospective-freeze rules continue to apply.

**3e.** Find:

> Verify fit and throughput in January before proceeding.

Replace with:

> Verify fit and throughput before training.

**3f.** Find:

> January 2027 training.

Replace with:

> Training in December 2026 or January 2027, after the C′ gate and before the core Track A freeze.

**3g.** Find:

> Re-quote all line items live in January and obtain the first author's recorded approval before creating a pod.

Replace with:

> Re-quote all line items live before training and obtain the first author's recorded approval before creating a pod.

## Hand-back

The owner tells the main planner that the update is submitted. The main planner confirms on the OSF API that a second schema response exists with this justification, and that the lock still reproduces from the original response.
