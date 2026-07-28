# SETU Product Integration

Owner-service implementation is published separately at
`blackholeinfiverse51/ai-crm@38e9176c07776778b3cdcf7907917a3a998ac2eb`.

## File: `contracts/production/product-setu-ai-crm.json`

**Sprint change:** Added

**Purpose:** Publishes SETU's health, capability, intent, dispatch, response,
credential, and source-revision contracts to Mitra.

**Why modified:** SETU must attach through the production manifest directory
without a product branch in runtime code.

**Key implementation areas:** Read-only CRM intents; authenticated Mitra
envelope dispatch; MongoDB-aware health requirements; response schemas.

**Review focus:** Contract fidelity, secret-name parity, source revision, and
absence of product-specific runtime routing.

**Related tests:** `pratham/tests/test_bhiv_product_integration.py`;
`pratham/tests/test_operational_validators.py`.
