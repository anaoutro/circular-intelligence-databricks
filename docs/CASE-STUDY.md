# Circular Intelligence — Case Study

**Headline:** Finding the recovery margin hidden behind repair risk.

**Context.** A fictional recovery operation receives repeated and out-of-order equipment events. Resale prices alone do not reveal whether repair is worthwhile, and invalid inputs can corrupt the picture.

**My approach.** I implemented Bronze raw ingestion, a quarantine path, Silver latest-valid device state and Gold route economics. Delta MERGE prevents replayed payloads and older events from overwriting current device state. SQL queries compare a risk-aware policy with a baseline that ignores repair failure when selecting a route.

**Technical decisions.** I preserved raw strings until validation, deduplicated the merge source and compared unrounded financial candidates. I made the last-valid-state behavior explicit: an invalid correction is quarantined rather than replacing a valid device record. Incremental ingestion is implemented; full Silver scanning remains an explicit demo limitation.

**Evidence.** A deterministic CSV with 260 rows representing 243 devices, eight repeated payloads, two superseded valid events and seven rejected events; a Python Decimal reference model; local business tests; a Databricks notebook and SQL dashboard queries.

**Results.** Use the generated reference_results.json for reproducible simulation metrics. These values are expected outcomes under synthetic assumptions, not observed savings. Databricks execution has not been claimed without a workspace run.

**Next iteration.** Add authoritative event sequence numbers, jobs, incremental partition processing and observed repair outcomes to calibrate the input probabilities.


## Review the implementation

See the [repository README](../README.md), [setup guide](SETUP.md), [data contract](DATA-CONTRACT.md) and [validation report](../VALIDATION.md).
