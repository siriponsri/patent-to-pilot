# Data inventory and reuse

The [RA Pharma master plan](../docs/ra-pharma/MASTER-PLAN.md) separates research inputs from material cleared for the local product. The [research brief](../docs/ra-pharma/research/BRIEF.md) calls for an eligibility and rights inventory before measurement. The [product brief](../docs/ra-pharma/product/BRIEF.md) uses cleared sources and fictional applicant records. Each addition needs a source, revision, intended use, rights and digest. Store restricted or large payloads outside Git. Keep evaluator labels outside the runtime.

## Inherited HealthTech records

The earlier HealthTech plan considered Bridge-MedDevKG subject to rights and cohort eligibility, SciFact for the evidence component, and official device or product records. The [data registry](../configs/healthtech/data_registry.json) records those roles. The migration downloaded no Bridge or SciFact payload and published no third-party raw data. The device example in `examples/healthtech/synthetic-device/` uses developer-authored text and identifiers.

The G03 manifests document historical acquisitions. Consult the [migration and recovery record](../docs/healthtech/HISTORY.md) before considering legacy local material. The old PLS and EnterpriseRAG downloads did not establish HealthTech benchmarks or scientific performance. Check source-code coverage in the [license](../LICENSE) and [notice](../NOTICE); dataset, paper and release-asset rights require separate verification.
