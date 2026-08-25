from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

from . import site_backend


PROJECT_TITLE = "Trust Ecosystem Monitor"


def _brand_html(text: str, profile: dict) -> str:
    organization = str(profile.get("organization", "unknown"))
    weekly_title = str(profile.get("weekly_brief_title", "Weekly Ecosystem Brief"))
    disclaimer = str(
        profile.get(
            "disclaimer",
            "Independent observatory; not an official publication of the monitored ecosystem.",
        )
    )
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
    """Render one profile's site in a staging root."""
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


def _ecosystem_cards(root: Path) -> list[dict]:
    cards: list[dict] = []
    docs = root / "docs"
    if not docs.exists():
        return cards
    for candidate in sorted(docs.iterdir()):
        latest = candidate / "data" / "latest.json"
        if not candidate.is_dir() or not latest.exists():
            continue
        try:
            snapshot = json.loads(latest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        profile = snapshot.get("ecosystem_profile", {})
        findings = snapshot.get("findings", [])
        repositories = snapshot.get("repositories", [])
        cards.append(
            {
                "id": profile.get("id") or candidate.name,
                "display_name": profile.get("display_name") or snapshot.get("organization") or candidate.name,
                "organization": snapshot.get("organization", ""),
                "generated_at": snapshot.get("generated_at", ""),
                "repositories": len(repositories),
                "active": sum(r.get("lifecycle") == "active" for r in repositories),
                "open_findings": sum(f.get("status") == "open" for f in findings),
                "unclassified": sum(
                    r.get("portfolio") == "Unclassified" and r.get("lifecycle") == "active"
                    for r in repositories
                ),
            }
        )
    return cards


def render_catalog(root: str | Path = ".") -> None:
    """Render the top-level multi-ecosystem landing page."""
    root = Path(root)
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    cards = _ecosystem_cards(root)

    rendered_cards = []
    for card in cards:
        generated = card["generated_at"]
        try:
            generated_label = datetime.fromisoformat(generated).strftime("%Y-%m-%d %H:%M UTC")
        except (TypeError, ValueError):
            generated_label = generated or "not yet generated"
        rendered_cards.append(
            "<article class='card'>"
            f"<h2>{html.escape(str(card['display_name']))}</h2>"
            f"<p><code>{html.escape(str(card['organization']))}</code></p>"
            "<div class='metrics'>"
            f"<span><strong>{card['repositories']}</strong> repositories</span>"
            f"<span><strong>{card['active']}</strong> active</span>"
            f"<span><strong>{card['open_findings']}</strong> open findings</span>"
            f"<span><strong>{card['unclassified']}</strong> active unclassified</span>"
            "</div>"
            f"<p class='muted'>Generated {html.escape(generated_label)}</p>"
            f"<p><a class='button' href='{html.escape(str(card['id']))}/index.html'>Open ecosystem brief →</a></p>"
            "</article>"
        )

    body = "".join(rendered_cards) or (
        "<article class='card'><h2>No ecosystem reports yet</h2>"
        "<p>Run collection for at least one organization profile.</p></article>"
    )
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{PROJECT_TITLE}</title>
<style>
:root{{--ink:#172033;--muted:#657083;--line:#d9dee7;--panel:#f6f8fb;--accent:#075985}}
*{{box-sizing:border-box}}body{{margin:0;font:16px/1.55 system-ui,-apple-system,sans-serif;color:var(--ink)}}
header{{border-bottom:1px solid var(--line)}}header div,main,footer{{max-width:1180px;margin:auto;padding:1.2rem 1.4rem}}
h1{{margin:.3rem 0}}.lede{{max-width:850px;color:#39465b;font-size:1.08rem}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:1rem;margin:2rem 0}}
.card{{border:1px solid var(--line);border-radius:.65rem;padding:1.2rem;background:white}}.metrics{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.5rem;margin:1rem 0}}.metrics span{{background:var(--panel);padding:.65rem;border-radius:.4rem}}.metrics strong{{display:block;font-size:1.35rem}}
.muted{{color:var(--muted)}}a{{color:var(--accent)}}.button{{font-weight:650;text-decoration:none}}code{{background:var(--panel);padding:.1rem .25rem;border-radius:.2rem}}footer{{border-top:1px solid var(--line);color:var(--muted)}}
</style></head><body>
<header><div><strong>{PROJECT_TITLE}</strong></div></header>
<main><h1>Monitored trust ecosystems</h1>
<p class="lede">Independent, evidence-backed observation of GitHub-based trust ecosystems. Each ecosystem keeps its own taxonomy, retained state, findings, dispositions and reporting surface.</p>
<div class="grid">{body}</div>
<h2>Interpretation boundary</h2>
<p>Co-location in this catalog does not assert a technical, governance or dependency relationship between ecosystems. Cross-ecosystem analysis is a separate capability and must be supported by explicit evidence.</p>
</main><footer>Trust Ecosystem Monitor · independently maintained</footer></body></html>"""
    (docs / "index.html").write_text(page, encoding="utf-8")

    manifest = {
        "project": "trust-ecosystem-monitor",
        "ecosystems": cards,
    }
    (docs / "ecosystems.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
