# Trade Bot Operational Recovery

## File: `product_recovery/trade_bot/api/index.py`

**Sprint change:** Added.

**Purpose:** Exposes Trade Bot health, prediction, and analysis contracts using
live symbol-specific market candles.

**Why modified:** The owner Render service is suspended and its repository is
not writable.

**Key implementation areas:** Symbol normalization, Yahoo chart retrieval,
transparent momentum analysis, and typed upstream failures.

**Review focus:** No ticker substitution, cached AAPL default, or simulated
market response.

**Related tests:** `pratham/tests/test_product_recovery_services.py`.

## File: `product_recovery/trade_bot/requirements.txt`

**Sprint change:** Added.

**Purpose:** Declares the bounded production dependencies for Trade Bot
recovery.

**Why modified:** The service must rebuild from a clean serverless environment.

**Key implementation areas:** FastAPI and Pydantic version bounds.

**Review focus:** Market retrieval uses the Python standard library.

**Related tests:** Public deployment build and focused recovery tests.

## File: `product_recovery/trade_bot/vercel.json`

**Sprint change:** Added.

**Purpose:** Routes the published Trade Bot paths to the FastAPI function.

**Why modified:** The initial rewrite form produced platform 404 responses.

**Key implementation areas:** Explicit Python build and catch-all route.

**Review focus:** Both `/tools/predict` and `/tools/analyze` remain reachable.

**Related tests:** Public health and NVDA prediction validation.
