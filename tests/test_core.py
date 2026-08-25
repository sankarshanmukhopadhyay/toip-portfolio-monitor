import unittest
from datetime import datetime, timezone

from toip_monitor.core import classify_kind, classify_portfolio, lifecycle, normalize_event, score_event
from toip_monitor.intelligence import consolidate_change_units, detect_cross_portfolio_seams, detect_lifecycle_changes


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

    def test_commit_timestamp_uses_nested_metadata(self):
        repo = {"full_name": "trustoverip/example", "portfolio": "Unclassified", "kind": "repository"}
        item = {"sha": "abc", "html_url": "https://example.test/abc", "commit": {"message": "docs: update", "committer": {"date": "2026-08-25T01:02:03Z"}}}
        event = normalize_event("commit", repo, item)
        self.assertEqual(event["timestamp"], "2026-08-25T01:02:03Z")
        self.assertEqual(event["sha"], "abc")

    def test_change_units_group_numbered_events(self):
        events = [
            {"kind": "issue", "repository": "trustoverip/example", "portfolio": "Test", "repo_kind": "repository", "timestamp": "2026-08-25T01:00:00Z", "title": "Track feature", "url": "https://example.test/issues/7", "number": 7, "materiality": 2},
            {"kind": "pull_request", "repository": "trustoverip/example", "portfolio": "Test", "repo_kind": "repository", "timestamp": "2026-08-25T02:00:00Z", "title": "Implement feature", "url": "https://example.test/pull/7", "number": 7, "state": "merged", "materiality": 4},
        ]
        units = consolidate_change_units(events)
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0]["event_count"], 2)
        self.assertEqual(units[0]["materiality"], 4)

    def test_lifecycle_changes_compare_snapshots(self):
        previous = [{"full_name": "trustoverip/example", "portfolio": "Test", "lifecycle": "active", "default_branch": "main", "url": "https://example.test"}]
        current = [{"full_name": "trustoverip/example", "portfolio": "Test", "lifecycle": "archived", "default_branch": "main", "url": "https://example.test"}]
        changes = detect_lifecycle_changes(current, previous)
        self.assertEqual(changes[0]["type"], "lifecycle")
        self.assertEqual(changes[0]["from"], "active")
        self.assertEqual(changes[0]["to"], "archived")

    def test_explicit_cross_portfolio_reference(self):
        repos = [
            {"name": "dtgwg-zkp-tf", "full_name": "trustoverip/dtgwg-zkp-tf", "portfolio": "DTG"},
            {"name": "tswg-tsp-specification", "full_name": "trustoverip/tswg-tsp-specification", "portfolio": "TSWG"},
        ]
        units = [{"id": "u1", "repository": "trustoverip/dtgwg-zkp-tf", "portfolio": "DTG", "title": "Align with tswg-tsp-specification", "materiality": 4, "evidence": ["https://example.test/u1"], "events": []}]
        seams = detect_cross_portfolio_seams(units, repos)
        explicit = [s for s in seams if s["strength"] == "explicit-reference"]
        self.assertEqual(len(explicit), 1)
        self.assertEqual(explicit[0]["target_portfolio"], "TSWG")


if __name__ == "__main__":
    unittest.main()
