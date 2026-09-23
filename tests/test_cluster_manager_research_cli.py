import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "cluster_manager.py"


class ClusterManagerResearchCliTests(unittest.TestCase):
    def run_cli(self, payload: str):
        return subprocess.run(
            [sys.executable, str(CLI), "--mode", "research"],
            input=payload,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_missing_records_key_fails(self):
        result = self.run_cli("{}")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("records field", result.stderr)

    def test_records_not_array_fails(self):
        result = self.run_cli('{"records":"bad"}')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("records as an array", result.stderr)

    def test_valid_payload_returns_json(self):
        result = self.run_cli(
            json.dumps(
                {
                    "records": [
                        {
                            "company": "Acme",
                            "source_public": True,
                            "company_sales": 10,
                            "future_investment": 5,
                            "merger_opportunity": 2,
                            "tax_regulation_score": 0.8,
                            "financing_regulation_score": 0.8,
                        }
                    ]
                }
            )
        )
        self.assertEqual(result.returncode, 0)
        parsed = json.loads(result.stdout)
        self.assertIn("patterns", parsed)


if __name__ == "__main__":
    unittest.main()
