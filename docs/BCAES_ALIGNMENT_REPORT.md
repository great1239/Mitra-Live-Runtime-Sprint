# BCAES Alignment Report

MITRA exposes each ecosystem participant as an independently deployable
contract boundary. Attachments declare capability, input, response, transport,
health, version, and secret references. Runtime code does not infer platform
authority.

## Execution Compliance

- Signal: versioned companion or workflow request.
- Intelligence: manifest-driven deterministic analysis with optional external
  AI hints.
- Decision: capability selection from attached contracts.
- Contract: immutable selected-capability envelope.
- Execution: Raj and the selected product runtime.
- Truth: Ashmit and Bucket owner responses.
- Observability: InsightFlow/Pravah telemetry.
- Replay: network-free immutable reconstruction.
- Handover: Central Depository export and TANTRA outbox.

## Operational Compliance

- Versioned APIs and OpenAPI are available.
- Health, readiness, metrics, telemetry, lifecycle, dependency, recovery, and
  instance APIs are available.
- Persistent state supports SQLite for local operation and PostgreSQL for
  multi-instance production.
- Resource-scoped PostgreSQL advisory locks prevent unrelated execution paths
  from blocking one another.
- Runtime schema initialization is versioned and skips repeated DDL on cold
  instances.

## Open Compliance Items

Live Kanishk Runtime and Gurukul validation require published owner contracts.
The production domain requirement requires DNS authority outside this
repository. These are tracked as external blockers, not simulated.

