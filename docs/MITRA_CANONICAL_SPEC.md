# MITRA Canonical Product Specification

## Product Position

MITRA is the BHIV companion product. It owns interaction, sessions, context,
capability discovery, routing, transport coordination, replay presentation, and
operator observability. It consumes platform services through published
contracts and does not embed their authority or business logic.

## Canonical User Execution

`POST /api/v1/companion/messages` and the frontend workflow connector both
enter `CompanionRuntime.execute_ecosystem`.

The only user execution sequence is:

1. MITRA preserves the user, workspace, session, and request.
2. Manifest metadata selects one published capability.
3. MITRA creates Raj's generic task envelope from that selected contract.
4. Raj executes the selected product contract.
5. The product-owned runtime returns its native response.
6. KESHAV is called only for a typed product failure.
7. Ashmit records governance/provenance acceptance.
8. Bucket persists the immutable execution artifact.
9. Karma accepts the canonical hash-chain append.
10. PRANA forwards the exact accepted bytes and verifies trace continuity.
11. InsightFlow consumes the canonical telemetry envelope.
12. MITRA reconstructs execution from immutable artifacts.
13. Central Depository receives the immutable export.

Karma precedes PRANA because that ordering is required by their published
contract, even where an assignment diagram lists the names differently.

## Internal Primitive

`CompanionRuntime.dispatch` is a product-transport primitive used by the
canonical coordinator and deterministic transport tests. It is not a public
user orchestration path. Product-specific branches and automatic substitution
of a different product after execution begins are prohibited.

## Product Attachments

Production manifests currently cover:

- UniGuru learning and reasoning
- Samruddhi market prediction
- SETU AI CRM read-only operations

Future products attach by manifest, schema, health contract, and secret
reference. No runtime source branch is required.

## Identity And Replay

Every stage preserves one trace ID and records immutable request bytes,
response bytes, contract identity, hashes, timestamps, and lineage links.
Replay reads only those artifacts and never calls a live owner service.

## Authority Boundaries

- Raj owns workflow execution.
- TANTRA owns cross-system constitutional coordination.
- Capability runtimes own product execution.
- Ashmit and Bucket own their governance and truth contracts.
- Karma owns integrity acceptance.
- PRANA owns strict forwarding.
- InsightFlow/Pravah owns observability consumption.
- MITRA owns orchestration and companion presentation only.

