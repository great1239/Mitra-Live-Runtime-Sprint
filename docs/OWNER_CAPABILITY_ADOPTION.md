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
| Ashmit | Healthy public deployment built from `blackholeinfiverse54-creator/Mitra_T42`; MongoDB-backed Bucket and execution modules are active | MITRA contract client and trace validation | Owner code active; owner signoff pending |
| Bucket | Accessible BHIV Bucket deployment and its append-only APIs | MITRA artifact envelope | Owner capability active |
| SETU | Product-owned `/api/mitra/execute` route from `blackholeinfiverse51/ai-crm`; public health confirms MongoDB and MITRA integration | Manifest envelope mapping | Owner capability active |
| UniGuru | Owner Dockerfile and `/ask`, `/new_rag`, and `/health` implementation from `VJY123VJY/uniguru_ai` | Blueprint service consumes the owner repository directly | Owner code active |
| Samruddhi Trade Bot | Owner `/tools/fetch_data`, `/tools/predict`, `/tools/analyze`, and `/tools/health` implementation | Blueprint consumes a private, unchanged deployment mirror because Render cannot read the private owner repository directly | Owner market-data capability active; prediction remains unavailable until the owner supplies trained models |
| SL Validator | Owner `/validate` deterministic decision-validation API from `BHIV-Engineering-Exchange/sl_validator_parity` | Blueprint consumes a private, unchanged deployment mirror | Owner endpoint active; not misrepresented as artifact storage |
| KESHAV | Public owner API and published integration guide | Conditional error envelope | Owner endpoint active |
| Karma / PRANA | Only published API contracts were supplied | Contract-compatible services implement those exact APIs | Owner repositories unavailable |

## Removed duplication

`mitra-remote-product-v1` was a locally invented generic UCR capability. It has
been removed. UCR now records and executes the established capability IDs from
the selected product manifest, such as `market-data`,
`learning-reasoning`, and `crm-operations`.

## Remaining exceptions

UniGuru and Samruddhi now use their owner-code Render services. UniGuru passed
`GET /health` and `POST /ask`. Samruddhi passed `GET /tools/health` and
`POST /tools/fetch_data` with live AAPL data. Samruddhi's existing
`POST /tools/predict` returned `Model training failed`, so MITRA does not hide
that owner limitation: stock display uses the established market-data
capability, while prediction remains unavailable pending owner-trained models.

The accessible `sl_validator_parity` repository is a deterministic constraint
validator, not a Central Depository storage service. MITRA therefore deploys
its real `/validate` capability separately and does not substitute it for the
Central Depository artifact contract. The Central Depository remains an export
and handover boundary until its storage owner supplies a matching API.
