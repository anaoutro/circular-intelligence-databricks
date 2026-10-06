# Databricks notebook source
# MAGIC %md
# MAGIC # Circular Intelligence · a risk-aware recovery lakehouse
# MAGIC All values are synthetic BRL assumptions. No actual environmental impact is claimed.
# MAGIC Upload data/equipment_events.csv to a Unity Catalog volume. Supply its full /Volumes/... path.
# MAGIC The execution principal needs USE CATALOG, USE/CREATE SCHEMA, CREATE TABLE,
# MAGIC SELECT/MODIFY on output tables, and READ VOLUME on the source.

# COMMAND ----------
from pyspark.sql import functions as F, Window
from pyspark.sql.types import StructType, StructField, StringType
from delta.tables import DeltaTable
import re

dbutils.widgets.text("catalog", "main")
dbutils.widgets.text("schema", "circular_portfolio")
dbutils.widgets.text("input_path", "/Volumes/main/circular_portfolio/input/equipment_events.csv")
catalog = dbutils.widgets.get("catalog")
schema_name = dbutils.widgets.get("schema")
input_path = dbutils.widgets.get("input_path")
assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", catalog), "Use a simple catalog identifier"
assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema_name), "Use a simple schema identifier"
assert input_path.startswith("/Volumes/") and input_path.endswith(".csv"), "Expected a UC volume CSV path"
spark.conf.set("spark.sql.session.timeZone", "UTC")
prefix = f"{catalog}.{schema_name}"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {prefix}")
columns = ["equipment_id","model","supplier","updated_at","condition_score","failure_probability",
           "resale_price","refurbished_price","repair_cost","salvage_value","acquisition_credit","logistics_cost"]
money_columns = columns[6:]

def upsert_events(frame, table):
    if not spark.catalog.tableExists(table):
        frame.write.format("delta").mode("append").saveAsTable(table)
    else:
        (DeltaTable.forName(spark, table).alias("t").merge(frame.alias("s"), "t.event_hash = s.event_hash")
         .whenNotMatchedInsertAll().execute())

# COMMAND ----------
# Bronze preserves raw values. A hash of the ordered source fields makes replays idempotent.
raw_schema = StructType([StructField(c, StringType(), True) for c in columns])
source = (spark.read.option("header", True).option("mode", "FAILFAST").schema(raw_schema).csv(input_path))
bronze_input = (source.withColumn("event_hash", F.sha2(F.to_json(F.struct(*[F.col(c) for c in columns])),256))
               .withColumn("source_file", F.lit(input_path)).withColumn("ingested_at", F.current_timestamp())
               .dropDuplicates(["event_hash"]))
upsert_events(bronze_input, f"{prefix}.bronze_equipment_events")

# COMMAND ----------
# Silver normalization scans the demo Bronze table on each run.
# Ingestion is incremental; this is deliberately not advertised as incremental Silver processing.
bronze = spark.table(f"{prefix}.bronze_equipment_events")
typed = bronze
for c in money_columns:
    typed = typed.withColumn(c + "_value", F.expr(f"try_cast({c} AS DECIMAL(20,6))"))
typed = (typed.withColumn("condition_value", F.expr("try_cast(condition_score AS DECIMAL(10,4))"))
         .withColumn("probability_value", F.expr("try_cast(failure_probability AS DECIMAL(10,6))"))
         .withColumn("event_time", F.expr("try_cast(updated_at AS TIMESTAMP)")))
missing = F.lit(False)
for c in columns:
    missing = missing | F.col(c).isNull() | (F.trim(F.col(c)) == "")
invalid_money = F.lit(False)
for c in money_columns:
    v = F.col(c + "_value")
    invalid_money = invalid_money | v.isNull() | (v < 0) | (v != F.round(v,2)) | ~F.trim(F.col(c)).rlike(r"^\d{1,14}(\.\d{1,2})?$")
condition = F.col("condition_value")
probability = F.col("probability_value")
invalid_condition = condition.isNull() | (condition < 0) | (condition > 100) | (condition != F.floor(condition)) | ~F.trim(F.col("condition_score")).rlike(r"^\d{1,3}$")
invalid_probability = probability.isNull() | (probability < 0) | (probability > 1) | (probability != F.round(probability,4)) | ~F.trim(F.col("failure_probability")).rlike(r"^\d(\.\d{1,4})?$")
invalid_timestamp = F.col("event_time").isNull() | ~F.col("updated_at").rlike(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|\+00:00)$")
typed = typed.withColumn("quality_reason", F.when(missing,"missing_fields")
    .when(invalid_money,"invalid_money").when(invalid_condition,"invalid_condition")
    .when(invalid_probability,"invalid_probability").when(invalid_timestamp,"invalid_timestamp"))
quarantine = typed.filter(F.col("quality_reason").isNotNull())
upsert_events(quarantine, f"{prefix}.quarantine_equipment_events")
valid = typed.filter(F.col("quality_reason").isNull())
for c in ("equipment_id","model","supplier"):
    valid = valid.withColumn(c,F.trim(F.col(c)))
window = Window.partitionBy("equipment_id").orderBy(F.col("event_time").desc(),F.col("event_hash").desc())
latest = valid.withColumn("_rank",F.row_number().over(window)).filter("_rank = 1")
silver = latest.select("equipment_id","model","supplier","updated_at","event_time","event_hash",
    F.col("condition_value").cast("int").alias("condition_score"),
    F.col("probability_value").cast("decimal(5,4)").alias("failure_probability"),
    *[F.col(c+"_value").cast("decimal(16,2)").alias(c) for c in money_columns])
if not spark.catalog.tableExists(f"{prefix}.silver_equipment"):
    silver.write.format("delta").mode("append").saveAsTable(f"{prefix}.silver_equipment")
else:
    (DeltaTable.forName(spark,f"{prefix}.silver_equipment").alias("t")
     .merge(silver.alias("s"),"t.equipment_id = s.equipment_id")
     .whenMatchedUpdateAll(condition="s.event_time > t.event_time OR (s.event_time = t.event_time AND s.event_hash > t.event_hash)")
     .whenNotMatchedInsertAll().execute())

# COMMAND ----------
# Compare unrounded candidate values before rounding currency for presentation.
s = spark.table(f"{prefix}.silver_equipment")
base = F.col("acquisition_credit") + F.col("logistics_cost")
scored = (s.withColumn("resale_raw",F.col("resale_price")-base)
    .withColumn("repair_raw",(1-F.col("failure_probability"))*F.col("refurbished_price") +
        F.col("failure_probability")*F.col("salvage_value")-F.col("repair_cost")-base)
    .withColumn("recycle_raw",F.col("salvage_value")-base)
    .withColumn("naive_repair_raw",F.col("refurbished_price")-F.col("repair_cost")-base))

def choose_route(repair_column):
    resale = F.col("resale_raw")
    repair = F.col(repair_column)
    recycle = F.col("recycle_raw")
    condition = F.col("condition_score")
    return (F.when((condition>=70)&(resale>=repair)&(resale>=recycle),"Resale")
        .when((condition>=30)&(repair>=recycle)&((condition<70)|(repair>resale)),"Repair")
        .when((condition>=70)&(resale>=recycle),"Resale").otherwise("Recycle"))

def selected_value(route_column):
    return (F.when(F.col(route_column)=="Resale",F.col("resale_raw"))
        .when(F.col(route_column)=="Repair",F.col("repair_raw")).otherwise(F.col("recycle_raw")))

decisions = scored.withColumn("route",choose_route("repair_raw")).withColumn("naive_route",choose_route("naive_repair_raw"))
decisions = (decisions.withColumn("expected_net",F.round(selected_value("route"),2))
    .withColumn("baseline_expected_net",F.round(selected_value("naive_route"),2))
    .withColumn("decision_gain",F.round(selected_value("route")-selected_value("naive_route"),2))
    .withColumn("needs_review",selected_value("route")<0)
    .withColumn("policy_version",F.lit("circular-v1")))
gold = decisions.select("equipment_id","model","supplier","condition_score","route","naive_route",
    "expected_net","baseline_expected_net","decision_gain","needs_review","policy_version","event_time",
    F.round("resale_raw",2).alias("resale_net"),F.round("repair_raw",2).alias("repair_net"),
    F.round("recycle_raw",2).alias("recycle_net"))
gold.write.format("delta").mode("overwrite").option("overwriteSchema",True).saveAsTable(f"{prefix}.gold_asset_decisions")
model_summary = gold.groupBy("model").agg(F.count("*").alias("assets"),F.sum("expected_net").alias("expected_net"),
    F.sum(F.col("needs_review").cast("int")).alias("review_assets"),F.sum("decision_gain").alias("decision_gain"))
model_summary.write.format("delta").mode("overwrite").option("overwriteSchema",True).saveAsTable(f"{prefix}.gold_model_summary")

# COMMAND ----------
# Fail the run if key integrity or policy invariants break. Replays should keep these stable.
assert silver.count() == silver.select("equipment_id").distinct().count(), "Duplicate Silver equipment IDs"
assert gold.filter("decision_gain < 0").count() == 0, "Policy underperforms its own eligible baseline"
assert gold.filter("route = 'Resale' AND condition_score < 70").count() == 0, "Ineligible resale"
assert gold.filter("route = 'Repair' AND condition_score < 30").count() == 0, "Ineligible repair"
display(model_summary.orderBy(F.col("expected_net").desc()))
display(gold.filter("needs_review").orderBy("expected_net"))
display(quarantine.select("equipment_id","quality_reason"))

