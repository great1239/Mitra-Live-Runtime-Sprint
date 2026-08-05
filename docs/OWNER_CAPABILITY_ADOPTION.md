# Owner Capability Adoption

MITRA integrates owner systems by invoking capabilities already defined by
their repositories or published contracts. A local adapter may translate
transport or schema shape, but it must not replace owner business behavior.

## Enforcement rules

1. A production capability must identify its source repository and pinned
   source commit in the product manifest or service image.
2. Raj sends the manifest's `capability.capability_id` to UCR. It does not use a
   generic MITRA capability ID.
3. UCR attaches that descriptor through Kanishk's `CapabilityRegistry` and
   executes it through Kanishk's `ExecutionEngine`.
4. The capability ID in the UCR URL must equal the capability ID in the signed
   manifest contract. A mismatch fails with HTTP 409.
5. Product execution uses the endpoint and request schema declared by the
   product-owned manifest. MITRA does not implement product business logic.
6. Compatibility services are allowed only when no owner repository or owner
   deployment is available. They must be labelled as compatibility or recovery
   deployments and cannot receive owner-production certification.

## Current owner-code matrix

| System | Owner implementation used | Integration-only code | Status |
| --- | --- | --- | --- |
| Kanishk UCR | Pinned `Mitra-runtime_execution_fabric` engine, registry, lifecycle, events, health, and BucketStore | API-key boundary and manifest capability attachment | Owner code active |
| InsightFlow | Pinned `VJY123VJY/bhiv` application and migrations | Contract bridge translates MITRA telemetry into owner dataset/provenance APIs | Owner code active |
| Ashmit | Public deployment built from the accessible Ashmit repository/fork | MITRA contract client and trace validation | Owner deployment acceptance pending |
| Bucket | Accessible BHIV Bucket deployment and its append-only APIs | MITRA artifact envelope | Owner capability active |
| SETU | Product-owned `/api/mitra/execute` route | Manifest envelope mapping | Owner capability active |
| UniGuru | Product-owned `/ask` and `/new_rag` contracts are declared | Current public target is a labelled recovery deployment | Owner production deployment pending |
| Samruddhi Trade Bot | Product-owned `/tools/predict` and `/tools/analyze` contracts are declared | Current public target is a labelled recovery deployment | Owner production deployment pending |
| KESHAV | Public owner API and published integration guide | Conditional error envelope | Owner endpoint active |
| Karma / PRANA | Only published API contracts were supplied | Contract-compatible services implement those exact APIs | Owner repositories unavailable |

## Removed duplication

`mitra-remote-product-v1` was a locally invented generic UCR capability. It has
been removed. UCR now records and executes the established capability IDs from
the selected product manifest, such as `market-prediction`,
`learning-reasoning`, and `crm-operations`.

## Remaining exceptions

UniGuru and Samruddhi still use explicitly labelled recovery deployments.
Their manifests point to the owner routes and schemas, but the deployments are
not owner-operated production services. They must be replaced with healthy
owner-code deployments before final owner certification; until then MITRA must
continue to disclose the recovery status rather than treating them as canonical
owner runtimes.
