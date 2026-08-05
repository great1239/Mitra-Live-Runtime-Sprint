# Owner Repository Cutover

## Implementation area

Owner product and validation runtime adoption.

## Critical files

### `render.yaml`

- **Purpose:** Defines services built directly from accessible owner repositories.
- **Why modified:** UniGuru and Samruddhi were still routed to locally implemented recovery services.
- **Key implementation areas:** owner repository URLs, owner Docker entry points, semantic health routes.
- **Review focus:** MITRA contains no copied product business logic and private source is not published.
- **Related tests:** `pratham/tests/test_owner_repository_adoption.py`.

### `contracts/production/product-samruddhi-uniguru.json`

- **Purpose:** Declares UniGuru's active and intended owner runtime endpoints.
- **Why modified:** Records the current owner commit and safe cutover target without prematurely breaking traffic.
- **Key implementation areas:** source commit, `owner_runtime_target`, recovery disclosure.
- **Review focus:** activation must occur only after semantic health and dispatch validation.
- **Related tests:** `pratham/tests/test_owner_repository_adoption.py`.

### `contracts/production/product-samruddhi-trade-bot.json`

- **Purpose:** Declares Samruddhi's intended owner runtime endpoint.
- **Why modified:** Prepares replacement of the local recovery deployment with the private owner repository.
- **Key implementation areas:** owner target and recovery disclosure.
- **Review focus:** Render must have access to the private repository before cutover.
- **Related tests:** `pratham/tests/test_owner_repository_adoption.py`.
