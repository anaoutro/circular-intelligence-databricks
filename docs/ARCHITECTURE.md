# Architecture decisions — Circular Intelligence

## Raw events before typing

Bronze preserves source strings and deduplicates exact payloads using a stable event hash. Validation happens before Silver accepts device state. Quarantine preserves invalid events for inspection.

## Latest valid state

Silver selects the newest valid event per equipment ID, with hash ordering as a deterministic equal-timestamp tie-breaker. Invalid corrections retain the last valid state. Equal timestamps need a source sequence in production; hash order is not business recency.

## Fair comparison

The risk-aware policy chooses the best eligible expected contribution. The baseline chooses routes ignoring repair failure, then evaluates those choices under the same risk-adjusted economics. This compares policy decisions, not two incompatible definitions of profit.

## Incremental boundaries

Bronze uses MERGE. Silver validation scans full demo Bronze history; Gold is rebuilt. Source deduplication occurs before MERGE. Multiple table writes are not an atomic pipeline transaction. Concurrent pipeline runs are out of scope.

## Portable evidence

The Python Decimal model runs without Spark and enables local testing. It is not a Spark substitute. The notebook uses PySpark expressions and Delta tables; workspace execution remains required. The demo reads reference-model results.

See [the input contract](DATA-CONTRACT.md).
