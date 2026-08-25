import unittest

from toip_monitor.findings import CLASSIFICATION_SUMMARY, build_findings


class ClassificationFindingExplanationTests(unittest.TestCase):
    def test_classification_finding_locates_gap_in_monitor(self):
        snapshot = {
            "assertions": [
                {
                    "id": "toip-classification-example",
                    "category": "classification",
                    "subject": "trustoverip/example",
                    "summary": "Active repository requires portfolio classification.",
                    "materiality": 2,
                    "evidence": ["https://github.com/trustoverip/example"],
                }
            ],
            "lifecycle_changes": [],
            "cross_portfolio_seams": [],
            "change_units": [],
        }
        finding = build_findings(snapshot)[0]
        self.assertEqual(finding["summary"], CLASSIFICATION_SUMMARY)
        self.assertIn("monitor taxonomy gap", finding["summary"].lower())
        self.assertIn("not an upstream ToIP repository defect or obligation", finding["summary"])


if __name__ == "__main__":
    unittest.main()
