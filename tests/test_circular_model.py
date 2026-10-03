import unittest
import sys
from pathlib import Path
from decimal import Decimal
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from circular_model import validate, decide, process
from generate_data import generate

class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.row = next(r for r in generate() if r["equipment_id"] == "DEMO-001")
    def evaluate(self, **changes):
        parsed,error=validate(dict(self.row,**changes)); self.assertIsNone(error); return decide(parsed)
    def test_risk_adjusted_margin(self):
        a=self.evaluate(); self.assertEqual((a["route"],a["expected_net"]),("Repair",620))
    def test_condition_gates(self):
        self.assertEqual(self.evaluate(condition_score="29")["route"],"Recycle")
        self.assertEqual(self.evaluate(condition_score="30")["route"],"Repair")
    def test_tie_preference(self):
        self.assertEqual(self.evaluate(refurbished_price="1000",repair_cost="0",failure_probability="0")["route"],"Resale")
    def test_failure_probability_one(self):
        self.assertEqual(self.evaluate(failure_probability="1")["route"],"Resale")
    def test_negative_best_route_is_reviewed(self):
        self.assertTrue(self.evaluate(condition_score="20")["needs_review"])
    def test_invalid_values(self):
        for changes in [dict(failure_probability="1.01"),dict(repair_cost="-1"),dict(condition_score="69.5"),
            dict(model=""),dict(updated_at="bad"),dict(resale_price="NaN"),dict(resale_price="Infinity"),dict(resale_price="1.001")]:
            with self.subTest(changes=changes): self.assertIsNotNone(validate(dict(self.row,**changes))[1])
    def test_utc_required(self):
        self.assertIsNotNone(validate(dict(self.row,updated_at="2026-09-01T12:00:00"))[1])
    def test_latest_event_wins_even_out_of_order(self):
        old=dict(self.row,updated_at="2026-08-01T12:00:00Z",repair_cost="50")
        new=dict(self.row,updated_at="2026-10-01T12:00:00Z",repair_cost="900")
        self.assertEqual(process([new,old])["assets"][0]["route"],"Resale")
    def test_invalid_correction_retains_last_valid(self):
        bad=dict(self.row,updated_at="2026-10-01T12:00:00Z",repair_cost="-1")
        r=process([self.row,bad]); self.assertEqual(r["assets"][0]["expected_net"],620); self.assertEqual(len(r["quarantine"]),1)
    def test_replay_is_idempotent(self):
        rows=generate(); self.assertEqual(process(rows)["assets"],process(rows+rows)["assets"])
    def test_dataset_reconciliation(self):
        s=process(generate())["summary"]
        self.assertEqual(s["raw_rows"],260); self.assertEqual(s["assets"],243); self.assertEqual(s["duplicate_rows"],8)
        self.assertEqual(s["quarantined_events"],7); self.assertEqual(s["superseded_events"],2)
        self.assertEqual(s["raw_rows"],s["duplicate_rows"]+s["quarantined_events"]+s["superseded_events"]+s["assets"])
    def test_gain_is_nonnegative_for_every_asset(self):
        self.assertTrue(all(a["decision_gain"]>=0 for a in process(generate())["assets"]))
    def test_hash_tie_is_deterministic(self):
        other=dict(self.row,repair_cost="900")
        self.assertEqual(process([self.row,other])["assets"],process([other,self.row])["assets"])

if __name__ == "__main__": unittest.main()
