# Reproduction scope and safe use

Use a fresh audit-owned scratch directory and the exact audited SHA. Do not run probes against production budget journals/history or write raw licensed data into this documentation folder. Probe scripts expecting a sibling snapshot/ must be copied beside a fresh exact Git checkout/archive. Local parquet/model file dependencies remain in existing permitted storage; manifests record their identity. No private key, .env, session or billing journal is required.

Commands actually used (paths abbreviated only for privacy):

    git archive --format=tar --output=<scratch>/snapshot.tar db0798276e3158b04131b4e910abc0a11511e94c
    rtk proxy python -B run_guarded.py
    git init --quiet <scratch>/git-snapshot
    git -c safe.directory=<project> -C <scratch>/git-snapshot fetch --depth=1 --no-tags <local-project> db0798276e3158b04131b4e910abc0a11511e94c
    git -c core.autocrlf=true -C <scratch>/git-snapshot checkout --quiet --detach FETCH_HEAD
    rtk proxy python -B run_checkout_subset.py
    rtk proxy python -B run_guarded.py git-snapshot clean-git-suite

Full clean checkout:455pass/3fail/1optional-tokenizer skip. Archive:454pass/4fail/1skip. Missing.git is an archive-only artifact. Cross-cohort missing ignored inputs and raw-byte newline fixture hashes remain genuine reproducibility dependencies. No implementation was repaired to make tests green.

Independent area probe scripts/results are in the neighboring integrity-budget/data-evaluator folders. They use authored inputs or targeted reads of existing pinned local files. The simulated14USD budget exposure never sent a provider call and is not an actual debit. Raw simulation DBs, actual corpora, qrels, per-queryjudgments, modelweights and private journals are deliberately excluded.
