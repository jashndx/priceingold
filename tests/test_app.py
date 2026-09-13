import unittest
from backend.stock_data import search_stocks, normalize_symbol, STOCKS_CATALOG
from backend.gold_service import compute_stock_in_gold

class TestSwarnaStock(unittest.TestCase):
    def test_stock_catalog_loaded(self):
        self.assertGreater(len(STOCKS_CATALOG), 10, "Stock directory should contain entries")

    def test_search_stocks(self):
        results = search_stocks("Tata")
        self.assertTrue(any("TATA" in r["ticker"] for r in results), "Should find Tata stocks")

    def test_normalize_symbol(self):
        self.assertEqual(normalize_symbol("RELIANCE"), "RELIANCE.NS")
        self.assertEqual(normalize_symbol("TCS.NS"), "TCS.NS")
        self.assertEqual(normalize_symbol("^NSEI"), "^NSEI")

    def test_gold_computation_reliance(self):
        data = compute_stock_in_gold("RELIANCE.NS", period="1m")
        self.assertIn("latest", data)
        self.assertIn("series", data)
        self.assertIn("verdict", data)
        self.assertGreater(data["latest"]["gold_inr_per_gram"], 0)
        self.assertGreater(data["latest"]["stock_in_gold_mg"], 0)
        self.assertGreater(data["latest"]["shares_per_10g"], 0)
        self.assertTrue(len(data["series"]) > 0)

if __name__ == "__main__":
    unittest.main()
