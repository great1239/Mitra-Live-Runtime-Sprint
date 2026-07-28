# Code Packet

## Entry Points

- Companion: `POST /api/v1/companion/messages`
- Frontend: `POST /api/workflow/run`
- Explicit canonical API: `POST /api/v1/ecosystem/execute`
- Coordinator: `CompanionRuntime.execute_ecosystem`
- Owner orchestration: `EcosystemRuntime.execute`

## Sprint Changes

See `code_packets/29-canonical-product-convergence.md`.

## Integration Points

Raj, product manifest transport, conditional KESHAV, Ashmit, Bucket, Karma,
PRANA, InsightFlow/Pravah, replay, Central Depository, and TANTRA handover.

## Untouched Components

No Raj workflow logic, product business logic, governance decisions, integrity
decisions, PRANA forwarding logic, InsightFlow analytics, or downstream TANTRA
authority logic was imported.

## Validation

Run the full test suite documented in `evidence_packet/review_packet.md`.

