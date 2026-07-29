# Runtime Ownership And Companion Continuity

## File: `integration_services/universal_capability_runtime.py`

**Sprint change:** Added.

**Purpose:** Provides product-neutral capability registration, lifecycle,
health, version negotiation, and manifest dispatch.

**Why modified:** MITRA needed a runnable, replaceable execution boundary while
Kanishk's owner-certified runtime remains unavailable.

**Key implementation areas:** Contract negotiation, schema validation,
manifest transport, typed failures, and runtime receipts.

**Review focus:** Verify there are no product-specific branches and that the
compatibility runtime does not claim owner certification.

**Related tests:** `integration_services/tests/test_contract_services.py`.

## File: `integration_services/tantra_execution_gateway.py`

**Sprint change:** Added.

**Purpose:** Implements the trace-preserving TANTRA execution boundary between
Raj and the capability runtime.

**Why modified:** TANTRA previously appeared as documentation or as a
misleading name for post-product integrations.

**Key implementation areas:** Canonical-byte forwarding, authentication, trace
mutation rejection, and boundary receipts.

**Review focus:** Confirm the service contains no governance, product, or
downstream owner logic.

**Related tests:** `integration_services/tests/test_contract_services.py`.

## File: `pratham/companion-runtime/mitra_companion/bhiv_downstream.py`

**Sprint change:** Renamed from `tantra_runtime.py` and corrected ownership
metadata.

**Purpose:** Owns ordered post-capability BHIV contract transport.

**Why modified:** The prior name conflated TANTRA with KESHAV, Ashmit, Bucket,
Karma, PRANA, InsightFlow, and Central Depository transport.

**Key implementation areas:** Immutable handoff, stage ordering, failure
checkpoints, and explicit post-capability boundary metadata.

**Review focus:** Confirm this layer owns transport only and downstream systems
retain their authority.

**Related tests:** `pratham/tests/test_mitra_tantra_separation.py`.
