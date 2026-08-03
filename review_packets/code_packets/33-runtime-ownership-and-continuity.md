# Runtime Ownership And Companion Continuity

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
