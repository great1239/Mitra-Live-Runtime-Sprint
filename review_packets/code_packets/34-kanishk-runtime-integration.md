# Kanishk Runtime Integration

## File: `integration_services/kanishk_runtime_adapter.py`

**Sprint change:** Added.

**Purpose:** Binds MITRA's selected capability contract to Kanishk's canonical
execution engine.

**Why modified:** The previous service reproduced runtime behaviour but did
not execute Kanishk's owner code.

**Key implementation areas:** Owner engine bootstrap, product-neutral remote
dispatch, lifecycle read-back, health, trace preservation, and BucketStore.

**Review focus:** Confirm there are no product branches and manifests remain
the product contract.

**Related tests:** Docker AAPL execution with lifecycle and Bucket read-back.

## File: `integration_services/kanishk-runtime.Dockerfile`

**Sprint change:** Added.

**Purpose:** Builds a reproducible image containing Kanishk's owner runtime.

**Why modified:** Deployment must run owner code, not a reimplementation.

**Key implementation areas:** Pinned repository and commit, dependency
isolation, non-root execution, and writable runtime data path.

**Review focus:** Verify source provenance and absence of copied owner logic.

**Related tests:** Image build, container health, capability listing, real
Samruddhi execution, lifecycle, and BucketStore read-back. The validation used
Kanishk execution `09b087bb-db09-4741-a1aa-66c3ae5d1d79`; focused regression
validation passed 20 tests.
