import unittest
from datetime import datetime, timezone

from toip_monitor.core import classify_kind, classify_portfolio, lifecycle, score_event


class ClassificationTests(unittest.TestCase):
    def test_portfolio_prefixes(self):
        self.assertEqual(classify_portfolio("dtgwg-zkp-tf"), "DTG")
        self.assertEqual(classify_portfolio("aimwg-tmcp-specification"), "AIMWG")
        self.assertEqual(classify_portfolio("kswg-keri-specification"), "KERI Suite")
        self.assertEqual(classify_portfolio("ctwg-main-glossary"), "CTWG")
        self.assertEqual(classify_portfolio("tswg-trust-registry-protocol"), "TSWG")

    def test_unclassified_is_explicit(self):
        self.assertEqual(classify_portfolio("unexpected-new-project"), "Unclassified")

    def test_kind_detection(self):
        self.assertEqual(classify_kind("dtgwg-zkp-tf"), "task-force")
        self.assertEqual(classify_kind("tswg-tsp-specification"), "specification")
        self.assertEqual(classify_kind("ctwg-main-glossary"), "terminology")

    def test_archived_lifecycle_wins(self):
        repo = {"archived": True, "pushed_at": "2026-08-25T00:00:00Z"}
        self.assertEqual(lifecycle(repo, datetime.now(timezone.utc)), "archived")

    def test_materiality(self):
        self.assertEqual(score_event({"kind": "release", "repo_kind": "repository"}), 5)
        self.assertEqual(score_event({"kind": "pull_request", "state": "merged", "repo_kind": "specification"}), 5)
        self.assertEqual(score_event({"kind": "commit", "repo_kind": "repository"}), 1)


if __name__ == "__main__":
    unittest.main()
