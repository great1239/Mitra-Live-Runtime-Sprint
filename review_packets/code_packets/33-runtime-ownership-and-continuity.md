# Runtime Ownership And Companion Continuity

## Execution Boundary

### `integration_services/universal_capability_runtime.py`

- Purpose: product-neutral capability registry, lifecycle, health, version
  negotiation, and manifest dispatch service.
- Why modified: Kanishk's runtime was not available as a callable owner
  service, but MITRA still needed a real, replaceable execution boundary.
- Key implementation areas: contract negotiation, schema validation, manifest
  transport, typed failures, runtime receipts.
- Review focus: no product-specific branches and no claim of owner
  certification.
- Related tests: `integration_services/tests/test_contract_services.py`.

### `integration_services/tantra_execution_gateway.py`

- Purpose: trace-preserving TANTRA execution boundary between Raj and the
  capability runtime.
- Why modified: TANTRA previously appeared only as documentation or as a
  misleading name for post-product integrations.
- Key implementation areas: canonical-byte forwarding, authentication, trace
  mutation rejection, boundary receipts.
- Review focus: no governance, product, or downstream owner logic.
- Related tests: `integration_services/tests/test_contract_services.py`.

### `integration_services/raj.py`

- Purpose: orchestrate the selected capability through TANTRA.
- Why modified: Raj previously dispatched directly to a product endpoint.
- Key implementation areas: execution-mode health, TANTRA handoff, compatibility
  fallback when the new gateway is not configured.
- Review focus: production configuration uses TANTRA; the direct path is
  labeled compatibility behavior.
- Related tests: `integration_services/tests/test_contract_services.py`.

## Companion Continuity

### `pratham/companion-runtime/mitra_companion/runtime.py`

- Purpose: preserve actor continuity across sessions, products, workspaces,
  devices, and clients.
- Why modified: Ashwini-owned companion behavior needs stable runtime hooks.
- Key implementation areas: profile hydration, persistence, factual interaction
  observations, explicit external relationship/trust boundary.
- Review focus: no inferred trust or relationship decision.
- Related tests: `pratham/tests/test_companion_interaction.py`.

### `pratham/companion-runtime/mitra_companion/store.py`

- Purpose: durable companion identity storage.
- Why modified: session summaries alone cannot provide cross-session identity.
- Key implementation areas: schema migration, actor lookup, atomic upsert,
  stable profile version.
- Review focus: SQLite/PostgreSQL parity and deterministic companion ID use.
- Related tests: `pratham/tests/test_companion_interaction.py`.

### `pratham/companion-runtime/mitra_companion/api.py`

- Purpose: expose versioned identity read/update hooks.
- Why modified: external companion clients need a published integration
  surface.
- Key implementation areas: `GET` and `PUT`
  `/api/v1/companion/identities/{actor_id}`.
- Review focus: validation and standard response envelope.
- Related tests: `pratham/tests/test_companion_interaction.py`.

## Deployment And Ownership

### `render.yaml`

- Purpose: deploy Universal Capability Runtime and TANTRA independently and
  wire Raj through both services.
- Why modified: local architecture alone does not provide interoperability.
- Key implementation areas: generated service keys, `fromService` secret
  references, public service URLs.
- Review focus: no committed secrets or localhost endpoints.
- Related tests: `pratham/tests/test_production_readiness_gate.py`.

### `docker-compose.ecosystem.yml`

- Purpose: reproduce the same service boundaries locally.
- Why modified: clean rebuilds must not collapse TANTRA and capability runtime
  into Raj's process.
- Key implementation areas: independent containers, dependency ordering,
  endpoint overrides.
- Review focus: topology parity with Render.
- Related validation: `docker compose config --quiet`.

### `pratham/companion-runtime/mitra_companion/bhiv_downstream.py`

- Purpose: own ordered post-capability BHIV contract transport.
- Why modified: the former `tantra_runtime.py` name conflated TANTRA with
  KESHAV/Ashmit/Bucket/Karma/PRANA/InsightFlow/Depository transport.
- Key implementation areas: immutable handoff, stage ordering, failure
  checkpoints.
- Review focus: transport ownership only; downstream systems retain authority.
- Related tests: `pratham/tests/test_mitra_tantra_separation.py`.
