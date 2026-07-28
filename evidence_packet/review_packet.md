# Evidence Review Packet

## Canonical Validation

Run:

```powershell
$env:PYTHONPATH='C:\tmp\mitra-test-deps;pratham\companion-runtime;pratham\attachment-runtime;pratham\context-runtime;pratham\intent-router;pratham\session-runtime'
python -m pytest pratham\tests -q
```

The canonical companion test verifies that one natural request reaches Raj,
Bucket, Karma, PRANA, InsightFlow, replay, and Central Depository in contract
order.

## Production Validation

Use `scripts/validate_ecosystem_runtime.py` against the hosted runtime and an
operational acceptance case. The command is successful only when owner
responses satisfy their real contracts. It never generates a pass artifact for
an unavailable dependency.

## Evidence Locations

- Runtime logs: `evidence_packet/runtime_logs`
- API samples: `evidence_packet/api_samples`
- Deployment proof: `evidence_packet/deployment_proof`
- Screenshots: `review_packets/SCREENSHOTS`
- Test evidence: `review_packets/testing`

