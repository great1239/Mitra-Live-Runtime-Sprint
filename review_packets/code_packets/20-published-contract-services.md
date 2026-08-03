# Published Contract Services

## File: `integration_services/raj.py`

**Sprint change:** Added a manifest-driven Raj workflow executor and later
updated its execution boundary to Kanishk's published capability route.

**Purpose:** Hands the selected capability contract to Kanishk's runtime
without product branches and preserves its execution receipt.

**Why modified:** Raj must orchestrate the selected contract through the
canonical capability runtime instead of dispatching products directly.

**Key implementation areas:** API-key ingress, capability parsing, canonical
runtime request envelope, owner state/output handling, trace validation, exact
request hashing, and runtime execution metadata.

**Review focus:** Raj must never invent an action or product response, bypass
the runtime, or confuse an owner runtime failure with a product result.

**Related tests:**
`test_raj_dispatches_selected_manifest_without_product_branch`,
`test_raj_returns_typed_product_error_for_owner_rejection`, and
`test_raj_embeds_tantra_boundary_and_calls_capability_runtime`.

## File: `integration_services/karma.py`

**Sprint change:** Added the supplied replay-safe integrity contract with
durable state.

**Purpose:** Implements append, bucket-artifact append, duplicate detection,
and parent-hash violation responses.

**Why modified:** Karma had an API contract but no reachable process.

**Key implementation areas:** Canonical JSON SHA-256, SQLite chain head,
unique replay keys, exact status values.

**Review focus:** Duplicate IDs cannot mutate the chain and a bad parent cannot
append.

**Related tests:** `test_karma_append_replay_and_violation`.

## File: `integration_services/prana.py`

**Sprint change:** Added strict-byte and trace-preserving forwarding contracts.

**Purpose:** Forwards accepted Karma bytes and core trace envelopes to
configured targets.

**Why modified:** PRANA had an API contract but no reachable process.

**Key implementation areas:** Raw request bytes, SHA-256 response headers,
trace mutation rejection, fail-closed targets.

**Review focus:** Strict bytes must never be parsed and reserialized before
forwarding.

**Related tests:** `test_prana_preserves_strict_bytes_and_trace`.
