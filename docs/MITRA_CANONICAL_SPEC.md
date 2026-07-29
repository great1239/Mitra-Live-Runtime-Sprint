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
4. Raj submits the selected contract to the TANTRA execution gateway.
5. TANTRA preserves the boundary contract and invokes the Universal Capability
   Runtime.
6. The Universal Capability Runtime negotiates versions, registers lifecycle
   observations, and dispatches through the manifest transport contract.
7. The product-owned runtime returns its native response.
8. The BHIV downstream runtime calls KESHAV only for a typed product failure.
9. Ashmit records governance/provenance acceptance.
10. Bucket persists the immutable execution artifact.
11. Karma accepts the canonical hash-chain append.
12. PRANA forwards the exact accepted bytes and verifies trace continuity.
13. InsightFlow consumes the canonical telemetry envelope.
14. MITRA reconstructs execution from immutable artifacts.
15. Central Depository receives the immutable export.

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

MITRA also exposes durable companion identity hooks by actor ID. They preserve
preferences, explicit consent scopes, device/client history, and continuity
across sessions, workspaces, and products. MITRA does not infer relationship
or trust semantics and does not claim ownership of the companion UI; those
remain external owner capabilities.

## Authority Boundaries

- MITRA owns companion coordination, capability selection, and presentation.
- Raj owns workflow orchestration.
- TANTRA owns the Raj-to-execution boundary, not governance or product logic.
- The Universal Capability Runtime owns product-neutral loading, lifecycle,
  health, version negotiation, and manifest dispatch.
- Product runtimes own capability behavior.
- The BHIV downstream runtime owns ordered contract transport after execution,
  not the authority decisions made by those systems.
- Ashmit and Bucket own their governance and truth contracts.
- Karma owns integrity acceptance.
- PRANA owns strict forwarding.
- InsightFlow/Pravah owns observability consumption.

The in-repository Universal Capability Runtime is a compatibility
implementation that makes this boundary runnable now. It is not presented as
Kanishk's owner-certified runtime; its published contract is the replacement
point for that service.
