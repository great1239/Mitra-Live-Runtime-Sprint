# Deployment Proof

Deployment proof must identify the Git commit, provider deployment, public URL,
HTTPS response, readiness response, and validation timestamp. Provider or
runtime failure is retained as a failure record rather than rewritten as proof.

## Canonical Deployment

| Field | Observed value |
| --- | --- |
| Validation time | `2026-07-28T13:17:05+05:30` |
| Git release | `9a866bf8e1a3e68f5916b4ccd9099698e6205585` |
| Provider | Vercel team `team_ciZh4E8ZRzVl7Gxnwl5y5Wbq` |
| Public URL | `https://mitra-live-runtime-sprint.vercel.app` |
| HTTPS `/ready` | HTTP response received with `ready=true` |
| Storage | persistent PostgreSQL |
| Attached products | `samruddhi-trade-bot`, `samruddhi-uniguru`, `setu-ai-crm` |
| Endpoint configuration | Raj, Ashmit, Bucket, KESHAV, Karma, PRANA, InsightFlow, and Central Depository configured with portable public endpoints |

The public response identifies the deployed canonical release and reports no
configuration-parity blockers. It also reports runtime state `DEGRADED`.
SETU's latest health observation is healthy; the deployed UniGuru and Trade
Bot owners are unhealthy, with Trade Bot returning a suspended-service HTTP
503. Therefore this is valid deployment and configuration evidence, not a
claim of successful live interoperability across every owner.

Screenshots:

- `review_packets/SCREENSHOTS/33-canonical-deployment-parity.png`
- `review_packets/SCREENSHOTS/34-canonical-vercel-deployment.png`
