# Validation — Circular Intelligence

Updated: 2026-10-05.

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

## Recorded Databricks validation — 2026-10-05

A workspace recording confirms a completed Circular Intelligence notebook run on Databricks Serverless. The final cell passed its assertions and printed `CIRCULAR FIXTURE VALIDATED IN DATABRICKS` with expected contribution `33861.40` and gain `9066.40`.

Passed assertions: Bronze = 252; quarantine = 7; Silver = 243; expected contribution = BRL 33,861.40; gain = BRL 9,066.40. The recording also shows the Gold model summary and successful notebook cells.

Evidence: [edited recording](docs/evidence/Circular_Intelligence_Demo.mp4), [final validation screenshot](docs/evidence/Circular_Validacao_Databricks.png), [Gold summary screenshot](docs/evidence/Circular_Resultados_Databricks.png).

The Serverless execution used `append` only for table creation guarded by `not spark.catalog.tableExists(...)`. Existing tables retain MERGE processing.

**Still unverified:** a second execution to check replay idempotency, separate SQL dashboard queries, scheduled production jobs and deployment at production scale. Local tests and CI continue to exercise the Python reference model. The evidence does not validate the separate CrowdCanvas project.

See [generated evidence](data/reference_results.json), [setup](docs/SETUP.md) and [architecture decisions](docs/ARCHITECTURE.md).

## GitHub preparation checks

The repository validator completed without errors: five Python files, one JSON file and 35 local links checked. The standalone demo passed desktop/mobile case selection, source-link resolution and overflow checks without browser runtime errors. GitHub Actions is prepared but has not run on GitHub yet.

