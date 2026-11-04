# Prior remote vector artifact manifest reconciliation

Status: `PASS_PRIOR_REMOTE_ARTIFACT_HASH_MATCH_NO_RERUN`

This read-only checkpoint reconciles the existing `dr-train` PatEmbed and
multilingual-e5 vector bundle manifests with the private Windows copies used by
the current candidate. It does not start a GPU job, transfer files, or promote
the result to a new remote encode/retrieval run.

Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`

At `2026-11-03T06:55:22.0138419Z`, the four local manifest SHA-256 values
matched the four manifests at the prior remote job root:

| Bundle | Local/private and prior-remote manifest SHA-256 |
|---|---|
| PatEmbed corpus | `75348afa4fede2535c09970d70353ecf9477f306a48fa46c71a445677f2302f1` |
| PatEmbed queries | `45da46ee7dbd755f8ca8dd4c244ff6b9063f16253c27907e92ff0291c61c7e54` |
| multilingual-e5 corpus | `643ab8856a1bcd72d2c2e4745d02bdfe46bed0190f16ab8834c3870249fdcc7b` |
| multilingual-e5 queries | `8e0a933f34c26a7f1370809c5220911cf6ed1b318bd02e7b4b60cc25ce76494c` |

The reconciled artifacts remain a prior actual remote run and are bound to the
current source through the existing runtime-rebind and vector-integrity audits.
The current candidate still has no new remote encode, no new retrieval
evaluation from this check, and no allocation reference for launching another
remote batch. The existing HTTP service was not touched.

Evidence: `verification.json` and `remote-manifest-sha256.txt`.
