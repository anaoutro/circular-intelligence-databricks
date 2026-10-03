"""Portable reference policy; no Spark dependency. All input/output data is synthetic."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime
from collections import Counter, defaultdict
import hashlib
import json

POLICY = "circular-v1"
MONEY = ("resale_price", "refurbished_price", "repair_cost", "salvage_value", "acquisition_credit", "logistics_cost")
REQUIRED = ("equipment_id", "model", "supplier", "updated_at", "condition_score", "failure_probability") + MONEY

def money(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def validate(row):
    missing = [k for k in REQUIRED if str(row.get(k, "") or "").strip() == ""]
    if missing:
        return None, "missing_fields:" + ",".join(missing)
    parsed = dict(row)
    try:
        for key in MONEY + ("condition_score", "failure_probability"):
            parsed[key] = Decimal(str(row[key]).strip())
            if not parsed[key].is_finite():
                return None, "invalid_number:" + key
        if any(parsed[k] < 0 for k in MONEY):
            return None, "negative_amount"
        if any(parsed[k] != money(parsed[k]) or parsed[k] >= Decimal("100000000000000") for k in MONEY):
            return None, "money_precision"
        condition = parsed["condition_score"]
        if condition < 0 or condition > 100 or condition != condition.to_integral_value():
            return None, "invalid_condition"
        probability = parsed["failure_probability"]
        if probability < 0 or probability > 1 or probability != probability.quantize(Decimal("0.0001")):
            return None, "invalid_probability"
        stamp = datetime.fromisoformat(str(row["updated_at"]).replace("Z", "+00:00"))
        if stamp.tzinfo is None or stamp.utcoffset().total_seconds() != 0:
            return None, "timestamp_must_be_utc"
        parsed["timestamp"] = stamp
        for key in ("equipment_id", "model", "supplier"):
            parsed[key] = str(parsed[key]).strip()
        parsed["source_hash"] = hashlib.sha256(json.dumps({k:row.get(k, "") for k in REQUIRED},sort_keys=True).encode()).hexdigest()
    except (InvalidOperation, ValueError, TypeError):
        return None, "invalid_type"
    return parsed, None

def decide(a):
    base = a["acquisition_credit"] + a["logistics_cost"]
    values = {
        "Resale": a["resale_price"] - base,
        "Repair": (1-a["failure_probability"])*a["refurbished_price"] + a["failure_probability"]*a["salvage_value"] - a["repair_cost"] - base,
        "Recycle": a["salvage_value"] - base,
    }
    eligible = (["Resale"] if a["condition_score"] >= 70 else []) + (["Repair"] if a["condition_score"] >= 30 else []) + ["Recycle"]
    route = max(eligible, key=lambda r: values[r])
    naive = dict(values, Repair=a["refurbished_price"]-a["repair_cost"]-base)
    naive_route = max(eligible, key=lambda r: naive[r])
    return {"equipment_id": a["equipment_id"], "model": a["model"], "supplier": a["supplier"],
        "condition_score": int(a["condition_score"]), "route": route, "expected_net": float(money(values[route])),
        "resale_net": float(money(values["Resale"])), "repair_net": float(money(values["Repair"])),
        "recycle_net": float(money(values["Recycle"])), "needs_review": values[route] < 0,
        "naive_route": naive_route, "baseline_expected_net": float(money(values[naive_route])),
        "decision_gain": float(money(values[route]-values[naive_route])), "policy_version": POLICY,
        "updated_at": a["updated_at"],
        "inputs": {k:float(a[k]) for k in MONEY + ("failure_probability",)}}

def process(rows):
    latest = {}
    quarantine = []
    seen = set()
    duplicates = 0
    valid_events = 0
    for row in rows:
        identity = json.dumps({k:row.get(k, "") for k in REQUIRED}, sort_keys=True)
        if identity in seen:
            duplicates += 1
            continue
        seen.add(identity)
        a, reason = validate(row)
        if reason:
            quarantine.append({"equipment_id": row.get("equipment_id", ""), "reason": reason})
            continue
        valid_events += 1
        key = a["equipment_id"]
        prior = latest.get(key)
        if prior is None or (a["timestamp"], a["source_hash"]) > (prior["timestamp"], prior["source_hash"]):
            latest[key] = a
    decisions = [decide(latest[k]) for k in sorted(latest)]
    groups = defaultdict(list)
    for a in decisions:
        groups[a["model"]].append(a)
    by_model = [{"model": model, "assets": len(items),
        "expected_net": float(sum((Decimal(str(x["expected_net"])) for x in items), Decimal(0))),
        "review_assets": sum(x["needs_review"] for x in items)} for model, items in sorted(groups.items())]
    summary = {"raw_rows": len(rows), "duplicate_rows": duplicates, "unique_events": len(seen),
        "quarantined_events": len(quarantine), "valid_events": valid_events, "superseded_events": valid_events-len(latest),
        "assets": len(decisions), "review_assets": sum(a["needs_review"] for a in decisions),
        "expected_net": float(sum((Decimal(str(a["expected_net"])) for a in decisions),Decimal(0))),
        "baseline_expected_net": float(sum((Decimal(str(a["baseline_expected_net"])) for a in decisions),Decimal(0))),
        "decision_gain": float(sum((Decimal(str(a["decision_gain"])) for a in decisions),Decimal(0))),
        "route_counts": dict(Counter(a["route"] for a in decisions)),
        "changed_routes": sum(a["route"] != a["naive_route"] for a in decisions)}
    return {"policy_version": POLICY, "summary": summary, "by_model": by_model, "assets": decisions, "quarantine": quarantine}
