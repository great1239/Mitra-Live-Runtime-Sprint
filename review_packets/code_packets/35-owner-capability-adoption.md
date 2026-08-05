# Owner Capability Adoption

## Implementation area

Canonical owner capability execution through Raj and Kanishk UCR.

## Critical files

### `integration_services/raj.py`

- **Purpose:** Raj-to-UCR transport.
- **Why modified:** The transport previously hardcoded the locally invented
  `mitra-remote-product-v1` capability.
- **Key implementation:** Reads `capability.capability_id` from the selected
  manifest contract and uses it in Kanishk's published execution route.
- **Review focus:** Missing IDs fail with 422; no generic fallback exists.
- **Related tests:**
  `test_raj_embeds_tantra_boundary_and_calls_capability_runtime`.

### `integration_services/kanishk_runtime_adapter.py`

- **Purpose:** Thin binding into Kanishk's pinned execution fabric.
- **Why modified:** Remove the generic descriptor and attach product-owned
  capability descriptors through the owner registry and engine.
- **Key implementation:** Manifest-ID equality, source/product provenance,
  lock-protected attachment, and owner-collision rejection.
- **Review focus:** The adapter owns only contract validation and transport;
  Kanishk's engine owns execution lifecycle, retries, events, and health.
- **Related tests:** `test_kanishk_owner_capabilities.py`.

### `integration_services/tests/test_kanishk_owner_capabilities.py`

- **Purpose:** Execute the adapter against the pinned owner repository.
- **Why modified:** Demonstrate actual owner registry and engine use.
- **Key implementation:** Established capability execution, manifest mismatch
  rejection, and conflicting owner rejection.
- **Review focus:** Tests require `KANISHK_OWNER_RUNTIME_PATH`; they skip when
  the owner source is not present instead of substituting a fake runtime.

## Validation

The owner-capability, contract-service, ecosystem-convergence, and continuity
suites completed with 34 passing tests against Kanishk commit
`74a5efdd4d3c079d415903c4e151250bf4642f57`.
