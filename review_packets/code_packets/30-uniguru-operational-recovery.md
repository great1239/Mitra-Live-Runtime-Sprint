# UniGuru Operational Recovery

## File: `product_recovery/uniguru/api/index.py`

**Sprint change:** Added.

**Purpose:** Exposes the published UniGuru health, ask, and RAG contracts.

**Why modified:** The owner host was unavailable and its repository is
read-only to the current operator.

**Key implementation areas:** Deterministic token retrieval, Kosha signal
projection, stable trace IDs, and explicit recovery-runtime provenance.

**Review focus:** Unknown queries reject instead of inventing an answer.

**Related tests:** `pratham/tests/test_product_recovery_services.py`.

## File: `product_recovery/uniguru/requirements.txt`

**Sprint change:** Added.

**Purpose:** Declares the bounded production dependencies for the recovery
service.

**Why modified:** The service must rebuild independently from a clean Vercel
environment.

**Key implementation areas:** FastAPI and Pydantic version bounds.

**Review focus:** No undeclared owner-repository or local-only dependency.

**Related tests:** Public deployment build and focused recovery tests.

## File: `product_recovery/uniguru/vercel.json`

**Sprint change:** Added.

**Purpose:** Routes every public request to the independent FastAPI function.

**Why modified:** The initial rewrite form produced platform 404 responses.

**Key implementation areas:** Explicit Python build and catch-all route.

**Review focus:** `/health`, `/ask`, and `/new_rag` reach the same application.

**Related tests:** Public HTTP health and drip-irrigation validation.
