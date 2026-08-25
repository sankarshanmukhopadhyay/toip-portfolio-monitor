from __future__ import annotations

import html
import json
from pathlib import Path

from . import site_backend


PROJECT_TITLE = "Trust Ecosystem Monitor"


def _brand_html(text: str, profile: dict) -> str:
    organization = str(profile.get("organization", "trustoverip"))
    weekly_title = str(profile.get("weekly_brief_title", "Weekly Ecosystem Brief"))
    disclaimer = str(profile.get("disclaimer", "Independent observatory; not an official publication of the monitored ecosystem."))
    replacements = {
        "ToIP Portfolio Monitor": PROJECT_TITLE,
        "ToIP Weekly Portfolio Brief": weekly_title,
        "<code>trustoverip</code>": f"<code>{html.escape(organization)}</code>",
        "not an official Trust Over IP Foundation publication.": html.escape(disclaimer),
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def render_site(root: str | Path = ".") -> None:
    root = Path(root)
    site_backend.render_site(root)

    latest = root / "docs" / "data" / "latest.json"
    if not latest.exists():
        return
    snapshot = json.loads(latest.read_text(encoding="utf-8"))
    profile = snapshot.get("ecosystem_profile", {})
    docs = root / "docs"

    for path in docs.glob("*.html"):
        path.write_text(_brand_html(path.read_text(encoding="utf-8"), profile), encoding="utf-8")

    reports = docs / "reports"
    if reports.exists():
        for path in reports.glob("*.html"):
            path.write_text(_brand_html(path.read_text(encoding="utf-8"), profile), encoding="utf-8")
