# SETU Product Integration Code Packet

This packet contains only sprint changes needed to attach SETU AI CRM as a
real, product-owned Mitra capability. Generated validation output and copied
product source are excluded.

## Implementation Area: Product Contract

### File: `contracts/production/product-setu-ai-crm.json`

- Purpose: Publishes SETU's health, capability, intent, dispatch, response,
  credential, and source-revision contracts to Mitra.
- Why modified: SETU must attach through the production manifest directory
  without a product branch in runtime code.
- Key implementation areas: read-only CRM intents, authenticated Mitra
  envelope dispatch, MongoDB-aware health requirements, response schemas.
- Review focus: contract fidelity, secret-name parity, source revision, and
  absence of product-specific runtime routing.
- Related tests:
  `pratham/tests/test_bhiv_product_integration.py`,
  `pratham/tests/test_operational_validators.py`.

### File: `pratham/companion-runtime/mitra_companion/transport.py`

- Purpose: Validates nested product dependency facts declared by any manifest
  health contract.
- Why modified: A top-level `healthy` string is insufficient when the product
  reports a disconnected database or unconfigured machine integration.
- Key implementation areas: generic dot-path lookup and exact required-value
  validation.
- Review focus: fail-closed behavior and product neutrality.
- Related tests: `pratham/tests/test_bhiv_product_integration.py`.

### File: `contracts/operational-acceptance.json`

- Purpose: Adds the reproducible SETU low-stock inventory execution case.
- Why modified: Attachment presence is not interoperability; acceptance must
  submit product data and verify response-bearing output.
- Key implementation areas: natural request, selected capability and intent,
  response path and value assertions.
- Review focus: real product selection and read-only output validation.
- Related tests: `pratham/tests/test_operational_validators.py`.

## Implementation Area: SETU Owner Service

The following critical files are in
`blackholeinfiverse51/ai-crm@38e9176c07776778b3cdcf7907917a3a998ac2eb`.

### File: `backend-nodejs/src/routes/mitra.js`

- Purpose: Exposes SETU's authenticated product execution endpoint.
- Why modified: Existing human JWT routes were not a suitable machine
  attachment contract.
- Key implementation areas: timing-safe API-key validation, Mongo readiness,
  typed client errors, and `POST /api/mitra/execute`.
- Review focus: authentication, status codes, and no bypass of product logic.
- Related tests: `backend-nodejs/test/mitraProductService.test.js`.

### File: `backend-nodejs/src/services/mitraProductService.js`

- Purpose: Executes Mitra intents through SETU's real Product and Order models.
- Why modified: SETU needed a narrow product-native adapter rather than
  orchestration-side schema branches.
- Key implementation areas: inventory lookup, operational aggregates, non-PII
  order lookup, trace continuity, and read-only response metadata.
- Review focus: data minimization, query bounds, and model-backed execution.
- Related tests: `backend-nodejs/test/mitraProductService.test.js`.

### File: `render.yaml`

- Purpose: Defines the public SETU owner-service deployment.
- Why modified: Hosted Mitra cannot call a local-only product.
- Key implementation areas: Node root directory, build/start commands, health
  route, generated machine secret, and external MongoDB configuration.
- Review focus: environment parity and secret handling.
- Related tests: Node syntax checks, `npm test`, and hosted health/dispatch
  validation after deployment.
