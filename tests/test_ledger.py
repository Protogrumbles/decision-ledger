"""Tests for decision-ledger — fictional data only."""
import json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ledger as lg

class TestLedger(unittest.TestCase):
    def _seeded(self, td):
        store = str(Path(td) / "ledger-data")
        self.assertEqual(lg.main(["seed", "--store", store]), 0)
        return store

    def test_seed_examples(self):
        with tempfile.TemporaryDirectory() as td:
            store = self._seeded(td)
            data = lg.load(store)
            self.assertEqual(len(data), 4)
            self.assertEqual([d["id"] for d in data], ["ADR-0001", "ADR-0002", "ADR-0003", "ADR-0004"])
            self.assertTrue(all(d["status"] == "active" for d in data))

    def test_full_flow(self):
        with tempfile.TemporaryDirectory() as td:
            store = self._seeded(td)
            # add a 5th decision
            self.assertEqual(lg.main(["add", "--store", store,
                "--title", "Buy a vendor spend tool", "--context", "Manual dashboard is slow.",
                "--decision", "Buy the vendor tool.", "--alternatives", "Keep the shared dashboard.",
                "--owner", "sean", "--date", "2026-12-01", "--review-date", "2027-06-01",
                "--tags", "spend"]), 0)
            data = lg.load(store)
            self.assertEqual(data[-1]["id"], "ADR-0005")
            # supersede ADR-0001 with ADR-0005
            self.assertEqual(lg.main(["supersede", "--store", store, "--id", "ADR-0001",
                "--superseded-by", "ADR-0005", "--reason", "Vendor tool replaces the dashboard."]), 0)
            data = lg.load(store)
            adr1 = [d for d in data if d["id"] == "ADR-0001"][0]
            self.assertEqual(adr1["status"], "superseded")
            self.assertEqual(adr1["superseded_by"], "ADR-0005")
            # list / search / review-due
            self.assertEqual(lg.main(["list", "--store", store]), 0)
            self.assertEqual(lg.main(["search", "--store", store, "--tag", "spend"]), 0)
            self.assertEqual(lg.main(["review-due", "--store", store, "--as-of", "2026-12-15"]), 0)
            # report
            report = Path(td) / "DECISIONS.md"
            self.assertEqual(lg.main(["report", "--store", store, "--out", str(report)]), 0)
            text = report.read_text()
            self.assertIn("ADR-0001", text); self.assertIn("superseded by ADR-0005", text)
            self.assertIn("ADR-0005", text)

    def test_supersede_nonexistent_fails_cleanly(self):
        """Negative path: superseding a nonexistent decision fails, nothing written."""
        with tempfile.TemporaryDirectory() as td:
            store = self._seeded(td)
            before = lg.load(store)
            # superseding decision does not exist
            self.assertEqual(lg.main(["supersede", "--store", store, "--id", "ADR-0001",
                "--superseded-by", "ADR-9999"]), 2)
            # target decision does not exist
            self.assertEqual(lg.main(["supersede", "--store", store, "--id", "ADR-9999",
                "--superseded-by", "ADR-0002"]), 2)
            # self-supersede rejected
            self.assertEqual(lg.main(["supersede", "--store", store, "--id", "ADR-0001",
                "--superseded-by", "ADR-0001"]), 2)
            self.assertEqual(lg.load(store), before)

    def test_invalid_date_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            store = str(Path(td) / "ledger-data")
            self.assertEqual(lg.main(["add", "--store", store, "--title", "t",
                "--context", "c", "--decision", "d", "--alternatives", "a",
                "--owner", "sean", "--date", "2026-13-01", "--review-date", "2027-01-01"]), 2)

if __name__ == "__main__":
    unittest.main()
