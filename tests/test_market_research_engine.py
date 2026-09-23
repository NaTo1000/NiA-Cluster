import unittest

from market_research_engine import MarketResearchEngine


class MarketResearchEngineTests(unittest.TestCase):
    def test_public_records_generate_patterns(self):
        engine = MarketResearchEngine(vm_layers=3)
        result = engine.run([
            {
                "company": "Acme",
                "source_public": True,
                "company_sales": 80,
                "future_investment": 45,
                "merger_opportunity": 35,
                "tax_regulation_score": 0.8,
                "financing_regulation_score": 0.9,
            }
        ])

        self.assertEqual(result["vm_layers"], 3)
        self.assertEqual(len(result["patterns"]), 1)
        self.assertEqual(result["patterns"][0]["company"], "acme")
        self.assertEqual(result["patterns"][0]["pattern_type"], "high-opportunity")

    def test_non_public_records_are_excluded(self):
        engine = MarketResearchEngine()
        result = engine.run([
            {
                "company": "PrivateCo",
                "source_public": False,
                "company_sales": 999,
                "future_investment": 999,
                "merger_opportunity": 999,
                "tax_regulation_score": 1.0,
                "financing_regulation_score": 1.0,
            }
        ])

        self.assertEqual(result["patterns"], [])
        self.assertEqual(result["compliance"]["non_public_records_excluded"], 1)
        self.assertEqual(result["compliance"]["public_records"], 0)

    def test_vm_layers_change_layered_score(self):
        single_layer = MarketResearchEngine(vm_layers=1).run([
            {
                "company": "Layered",
                "source_public": True,
                "company_sales": 50,
                "future_investment": 25,
                "merger_opportunity": 25,
                "tax_regulation_score": 0.7,
                "financing_regulation_score": 0.7,
            }
        ])
        multi_layer = MarketResearchEngine(vm_layers=4).run([
            {
                "company": "Layered",
                "source_public": True,
                "company_sales": 50,
                "future_investment": 25,
                "merger_opportunity": 25,
                "tax_regulation_score": 0.7,
                "financing_regulation_score": 0.7,
            }
        ])

        self.assertGreater(
            multi_layer["patterns"][0]["layered_score"],
            single_layer["patterns"][0]["layered_score"],
        )


if __name__ == "__main__":
    unittest.main()
