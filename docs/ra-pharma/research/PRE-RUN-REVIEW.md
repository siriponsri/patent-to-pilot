# Independent fixture release

A read-only reviewer independently checked the R1 source identities and the prospective R3 implementation. The [published prospective checkpoint] records the fixture design before scoring. The reviewer matched all eight declared asset hashes to the [machine freeze](fixtures/freeze.json), SHA-256 `5aacb45c351c85ff292fce141da99b0dbea4ee6ff01470ea07baa490f93b867f`, and confirmed the canonical output path was absent.

Review confirmed five named arms, common source bytes, equal action sequences for single versus fixed and for both learned ablations, two-read caps, provenance checking, and a separate scorer that reads the diagnostic key only after capture sealing. It identified the four template echoes, sought a role-only mismatch, and checked the resulting eleven-case inventory and the distinction between role-off and all-scope-off. This was a static check. The reviewer did not run the policy or score any case.

**Released for one local R3 engineering capture on the exact freeze.** The original goes to `docs/ra-pharma/research/fixtures/original/`. The depth matrix and R4 reserved DEV have no execution release.

[published prospective checkpoint]: https://github.com/siriponsri/patent-to-pilot/commit/b5584589e32bc90b2b38cc43a97240b388342eff
