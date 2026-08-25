import json
import tempfile
import unittest
from pathlib import Path

from trust_ecosystem_monitor.engine import _seed_snapshots
from trust_ecosystem_monitor.profile import load_profile, classify_portfolio
from trust_ecosystem_monitor.site import render_catalog


class MultiProfileTests(unittest.TestCase):
    def test_dif_profile_identity_and_conservative_taxonomy(self):
        profile = load_profile("organizations/decentralized-identity/profile.toml")
        self.assertEqual(profile.id, "decentralized-identity")
        self.assertEqual(profile.organization, "decentralized-identity")
        self.assertEqual(classify_portfolio("didcomm-messaging", profile), "DIDComm")
        self.assertEqual(classify_portfolio("universal-resolver", profile), "Identifiers & Discovery")
        self.assertEqual(classify_portfolio("presentation-exchange", profile), "Claims & Credentials")
        self.assertEqual(classify_portfolio("trusted-ai-agents", profile), "Trusted AI Agents")
        self.assertEqual(classify_portfolio("unexpected-future-work-item", profile), "Unclassified")

    def test_legacy_toip_snapshots_seed_scoped_baseline(self):
        profile = load_profile("organizations/trustoverip/profile.toml")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            work = Path(tmp) / "work"
            legacy = root / "data" / "snapshots"
            legacy.mkdir(parents=True)
            (legacy / "2026-08-25.json").write_text('{"organization":"trustoverip"}', encoding="utf-8")
            _seed_snapshots(root, work, profile)
            self.assertTrue((work / "data" / "snapshots" / "2026-08-25.json").exists())

    def test_catalog_keeps_ecosystems_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for profile_id, display_name, org in (
                ("trustoverip", "Trust Over IP Foundation", "trustoverip"),
                ("decentralized-identity", "Decentralized Identity Foundation", "decentralized-identity"),
            ):
                target = root / "docs" / profile_id / "data"
                target.mkdir(parents=True)
                payload = {
                    "organization": org,
                    "generated_at": "2026-08-25T12:00:00+00:00",
                    "ecosystem_profile": {"id": profile_id, "display_name": display_name},
                    "repositories": [{"lifecycle": "active", "portfolio": "Unclassified"}],
                    "findings": [{"status": "open"}],
                }
                (target / "latest.json").write_text(json.dumps(payload), encoding="utf-8")
            render_catalog(root)
            page = (root / "docs" / "index.html").read_text(encoding="utf-8")
            self.assertIn("trustoverip/index.html", page)
            self.assertIn("decentralized-identity/index.html", page)
            self.assertIn("Trust Over IP Foundation", page)
            self.assertIn("Decentralized Identity Foundation", page)
            manifest = json.loads((root / "docs" / "ecosystems.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["ecosystems"]), 2)


if __name__ == "__main__":
    unittest.main()
