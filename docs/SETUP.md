# Circular Intelligence — Databricks Recovery Lakehouse

**PySpark + Delta Lake + SQL + Python reference model.** Explain when high resale prices conceal poor expected recovery economics.

## Implemented
- Deterministic synthetic dataset: 243 devices, repeated events, corrections, out-of-order delivery, and seven invalid events.
- Bronze raw-string ingestion, event hashing, replay-safe Delta MERGE.
- Quarantine for missing values, invalid types/ranges, timestamp problems, and invalid precision.
- Silver latest-valid-event selection per equipment ID. Source is deduplicated before MERGE; older events cannot overwrite newer ones.
- Gold risk-adjusted route decisions and model summaries, plus SQL dashboard queries.
- An executable local Decimal reference model and business-rule tests without Spark or cloud dependencies.

## Local demo
Requires Python 3.10+; standard library only.
~~~powershell
python scripts/generate_data.py
python -m unittest discover -s tests -v
~~~
Generation rewrites the synthetic CSV, the reference JSON, and docs/demo/data.js. In the combined portfolio package it also refreshes the adjacent portfolio data.js. The interactive browser dashboard shows reference-model results, not a screenshot or live connection to Databricks.

## Databricks execution
1. Use a workspace with Unity Catalog and compute supporting PySpark and Delta. The notebook assumes Databricks Runtime 15.4 LTS or newer compatible compute; this baseline still needs execution verification in your workspace.
2. Upload data/equipment_events.csv to a UC volume. Import notebooks/01_circular_pipeline.py as a notebook.
3. Set catalog, schema, and input_path widgets. The principal must be allowed to read the volume and create/write the tables.
4. Run all cells. Inspect quarantine and the two Gold outputs. Run again: the same input must preserve Bronze and Silver counts and Gold financial totals.
5. Run sql/portfolio_dashboard.sql in a SQL editor and add the result queries to dashboard tiles.

## Data-quality semantics
Rows are events, not devices. Repeated exact payloads count once in Bronze. The newest **valid** event wins; an invalid correction is quarantined and leaves the last valid state intact. Equal timestamps use a stable hash as a deterministic technical tie-breaker, not business recency. The Python model and Spark hash different serializations; conflicting equal-time payloads are excluded from the shared fixture. A production source should supply an authoritative event sequence.

Financial amounts require nonnegative values with at most two decimals and below 10^14; probability requires at most four decimals in [0,1]; condition is an integer in [0,100]. The fixture uses ISO UTC timestamps to seconds. The notebook also validates raw numeric text before accepting cast values, avoiding acceptance of excess decimal precision after a cast rounds it. The reference model accepts broader valid Decimal text; the shared fixture uses plain decimal notation. The notebook and portable model are not asserted equivalent for arbitrary input.

## Metric definitions
Expected contribution is a modeled amount, not realized profit. Repair failure probability is an input assumption, not a trained ML prediction. The baseline chooses eligible routes while ignoring repair failure, then is evaluated under the same risk-aware economics. Policy gain compares those two choices on the same devices. Negative recommended contributions remain visible. No avoided-CO2 claim is made.

## Architecture
~~~mermaid
flowchart LR
  CSV[Synthetic event CSV] --> Bronze[Bronze / immutable payload hash]
  Bronze --> Quality[Validate and normalize]
  Quality --> Quarantine[Quarantine / rejected events]
  Quality --> Silver[Silver / latest valid device state]
  Silver --> Policy[Risk-aware route scoring]
  Policy --> Gold[Gold decisions and model summary]
  Gold --> SQL[SQL dashboard queries]
~~~

## Scope and next steps
Bronze ingestion uses incremental MERGE; Silver validation scans all demo Bronze history, and Gold is rebuilt. This is a transparent small-data implementation, not a streaming or terabyte-scale claim. Run one pipeline at a time; multi-table writes are not one atomic transaction. No hard-delete events, orchestration deployment, live Salesforce connector, or trained model are included. Production extensions: source event sequencing, partition-aware incremental transformation, job orchestration, observed repair outcomes, and audit snapshots.

## Official references
- [Delta MERGE and source deduplication](https://docs.databricks.com/aws/en/delta/merge)
- [Delta streaming semantics](https://docs.databricks.com/aws/en/structured-streaming/delta-lake)
- [foreachBatch considerations](https://docs.databricks.com/aws/en/structured-streaming/foreach)
