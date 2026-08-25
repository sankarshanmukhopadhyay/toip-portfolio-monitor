import json
import tempfile
import unittest
from pathlib import Path

from toip_monitor.site import render_site


class SiteTests(unittest.TestCase):
    def test_site_renders_decision_and_evidence_pages(self):
        snapshot = {
            "generated_at": "2026-08-25T03:00:00+00:00",
            "period": {"since": "2026-08-18T03:00:00+00:00", "until": "2026-08-25T03:00:00+00:00"},
            "provenance": {"source": "test"},
            "repositories": [{"name": "dtgwg-zkp-tf", "full_name": "trustoverip/dtgwg-zkp-tf", "url": "https://example.test/repo", "description": "test", "portfolio": "DTG", "kind": "task-force", "lifecycle": "active"}],
            "events": [{"timestamp": "2026-08-25T01:00:00Z", "portfolio": "DTG", "repository": "trustoverip/dtgwg-zkp-tf", "kind": "commit", "state": None, "url": "https://example.test/event", "title": "Update requirements"}],
            "change_units": [{"portfolio": "DTG", "repository": "trustoverip/dtgwg-zkp-tf", "title": "Update requirements", "materiality": 4, "evidence": ["https://example.test/event"]}],
            "findings": [{"id": "f1", "status": "open", "category": "material-change", "subject": "trustoverip/dtgwg-zkp-tf", "summary": "Update requirements", "materiality": 4, "urgency": 2, "assurance_impact": 2, "evidence": ["https://example.test/event"]}],
            "lifecycle_changes": [],
            "cross_portfolio_seams": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "data").mkdir(parents=True)
            (root / "docs" / "data" / "latest.json").write_text(json.dumps(snapshot), encoding="utf-8")
            render_site(root)
            for name in ("index.html", "findings.html", "portfolios.html", "lifecycle.html", "seams.html", "evidence.html", "methodology.html"):
                self.assertTrue((root / "docs" / name).exists(), name)
            overview = (root / "docs" / "index.html").read_text(encoding="utf-8")
            self.assertIn("What needs attention", overview)
            self.assertIn("Update requirements", overview)


if __name__ == "__main__":
    unittest.main()
