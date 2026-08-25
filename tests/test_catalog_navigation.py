from __future__ import annotations

import unittest

from trust_ecosystem_monitor.site import _add_catalog_nav


class CatalogNavigationTests(unittest.TestCase):
    def test_adds_catalog_link_to_standard_report_header(self) -> None:
        source = '<body><header><div class="bar"><span class="brand">Trust Ecosystem Monitor</span><a href="index.html">Overview</a></div></header></body>'
        rendered = _add_catalog_nav(source, "../index.html")
        self.assertIn('href="../index.html">All ecosystems</a>', rendered)
        self.assertEqual(rendered.count("All ecosystems"), 1)

    def test_archived_report_gets_fallback_catalog_link(self) -> None:
        source = '<!doctype html><html><body><h1>Weekly brief</h1></body></html>'
        rendered = _add_catalog_nav(source, "../../index.html")
        self.assertIn('href="../../index.html">← All ecosystems</a>', rendered)

    def test_catalog_link_is_idempotent(self) -> None:
        source = '<body><header><div class="bar"><span class="brand">Trust Ecosystem Monitor</span></div></header></body>'
        once = _add_catalog_nav(source, "../index.html")
        twice = _add_catalog_nav(once, "../index.html")
        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main()
