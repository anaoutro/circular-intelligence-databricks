"""Deterministic synthetic data and local reference outputs. Run from any directory."""
import csv
import json
import random
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from circular_model import REQUIRED, process

def generate():
    rng = random.Random(73)
    rows = []
    models = [("Atlas 14",1000,1400,100),("Orion 15",900,1400,150),("Lumen 13",700,1100,120)]
    suppliers = ["Northstar IT", "Harbor Devices", "Meridian Systems"]
    for i in range(240):
        model,resale,refurb,salvage = models[i%3]
        rows.append(dict(equipment_id=f"EQ-{i+1:04d}",model=model,supplier=suppliers[(i//3)%3],
            updated_at=f"2026-09-{1+i%28:02d}T12:00:00Z",condition_score=str(rng.randint(10,100)),
            resale_price=str(resale+rng.randrange(-100,101,10)),refurbished_price=str(refurb+rng.randrange(-100,101,10)),
            repair_cost=str(rng.randrange(80,851,10)),failure_probability=f"{rng.randrange(2,61)/100:.2f}",
            salvage_value=str(salvage),acquisition_credit=str(rng.randrange(40,651,10)),logistics_cost=str(rng.randrange(30,91,10))))
    for key,model,supplier,condition,resale,refurb,repair,failure,salvage,credit,logistics in [
        ("DEMO-001","Atlas 14","Northstar IT",85,1000,1400,200,.1,100,400,50),
        ("DEMO-002","Orion 15","Harbor Devices",65,900,1400,850,.55,150,600,70),
        ("DEMO-003","Lumen 13","Northstar IT",20,700,1100,250,.3,120,40,30)]:
        rows.append(dict(zip(REQUIRED,[key,model,supplier,"2026-09-30T12:00:00Z",str(condition),str(failure),str(resale),str(refurb),str(repair),str(salvage),str(credit),str(logistics)])))
    rows.extend([dict(rows[i]) for i in range(8)])
    # A legitimate correction and an older out-of-order event for the same asset.
    rows.append(dict(rows[0],updated_at="2026-09-30T12:00:00Z",repair_cost="800"))
    rows.append(dict(rows[0],updated_at="2026-08-01T12:00:00Z",repair_cost="50"))
    for key,changes in [("BAD-001",{"failure_probability":"1.2"}), ("BAD-002",{"repair_cost":"-10"}),
        ("BAD-003",{"condition_score":"101"}), ("BAD-004",{"model":""}),
        ("BAD-005",{"updated_at":"not-a-date"}), ("BAD-006",{"resale_price":"unknown"}),
        ("BAD-007",{"condition_score":"69.5"})]:
        rows.append(dict(rows[0],equipment_id=key,**changes))
    return rows

if __name__ == "__main__":
    data = ROOT / "data"; data.mkdir(exist_ok=True)
    rows = generate()
    with (data / "equipment_events.csv").open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=REQUIRED); writer.writeheader(); writer.writerows(rows)
    results = process(rows)
    (data / "reference_results.json").write_text(json.dumps(results,indent=2)+"\n",encoding="utf-8",newline="\n")
    for portfolio in (ROOT / "docs/demo", ROOT.parent / "portfolio"):
        if (portfolio / "index.html").exists():
            (portfolio / "data.js").write_text("window.CIRCULAR_DATA = " + json.dumps(results) + ";\n",encoding="utf-8",newline="\n")
    print(json.dumps(results["summary"],indent=2))
