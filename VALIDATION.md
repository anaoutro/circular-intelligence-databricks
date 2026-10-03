# Validation — Circular Intelligence

Date: 2026-10-03.

## Executed locally

- 13 Python reference-model business tests passed.
- Deterministic generator reconciles 260 source rows into 243 devices, eight duplicate payloads, seven rejected events and two superseded valid events.
- Python syntax, JSON files, local documentation links and demo asset links were checked.
- The included browser demo was checked at desktop and mobile sizes. It uses local reference-model results.

## Simulation results

| Metric | Value |
|---|---:|
| Repair / Resale / Recycle | 102 / 75 / 66 |
| Negative contribution devices | 104 |
| Expected contribution | BRL 33,861.40 |
| Baseline expected contribution | BRL 24,795.00 |
| Expected policy gain | BRL 9,066.40 |
| Routes changed vs baseline | 46 |

## Pending platform verification

No Databricks workspace or local PySpark/Delta runtime was connected. Notebook execution, Spark/Delta integration, privileges and SQL execution remain unverified. Local tests and CI exercise the Python reference model, not the Databricks runtime.

See [generated evidence](data/reference_results.json), [setup](docs/SETUP.md) and [architecture decisions](docs/ARCHITECTURE.md).

## GitHub preparation checks

The repository validator completed without errors: five Python files, one JSON file and 35 local links checked. The standalone demo passed desktop/mobile case selection, source-link resolution and overflow checks without browser runtime errors. GitHub Actions is prepared but has not run on GitHub yet.
