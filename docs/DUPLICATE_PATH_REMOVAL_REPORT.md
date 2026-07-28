# Duplicate Execution Path Removal Report

## Removed

The companion auto-dispatch branch previously called product transport
directly and could fall back to a second product after a transport failure.
That bypassed Raj, TANTRA participation, Bucket, integrity, observability,
replay, and Central Depository.

It now calls `execute_ecosystem` with:

- the selected manifest product and capability;
- the resolved product payload;
- a generic Raj task envelope derived from the selected contract;
- the existing session, actor, workspace, and client identity;
- a canonical-entrypoint marker.

No second-product fallback occurs after execution begins. A failed dependency
or product remains a typed, checkpointed failure recoverable through the
ecosystem recovery endpoint.

## Retained

`dispatch` remains an internal product transport primitive. It is required for
contract-level tests and immutable dispatch reconstruction, but public
companion and frontend workflow requests do not use it as an orchestration
entry point.

