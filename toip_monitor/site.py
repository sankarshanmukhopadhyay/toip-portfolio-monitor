from __future__ import annotations

import html
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def link(url: str, label: str) -> str:
    return f'<a href="{esc(url)}">{esc(label)}</a>' if url else esc(label)


STYLE = """
:root{--ink:#172033;--muted:#657083;--line:#d9dee7;--panel:#f6f8fb;--accent:#075985;--warn:#92400e}
*{box-sizing:border-box}body{margin:0;font:15.5px/1.55 system-ui,-apple-system,sans-serif;color:var(--ink);background:white}
header{border-bottom:1px solid var(--line);background:#fff;position:sticky;top:0;z-index:3}.bar{max-width:1240px;margin:auto;padding:.8rem 1.4rem;display:flex;gap:1.2rem;align-items:center;flex-wrap:wrap}.brand{font-weight:750;margin-right:auto}.bar a{text-decoration:none;color:var(--accent)}
main{max-width:1240px;margin:auto;padding:2rem 1.4rem 4rem}h1{font-size:2rem;margin:.2rem 0 .5rem}h2{margin-top:2.2rem}h3{margin-top:1.6rem}.lede{font-size:1.08rem;color:#39465b;max-width:900px}.muted{color:var(--muted)}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:.7rem;margin:1.4rem 0}.metric{background:var(--panel);border:1px solid var(--line);padding:.9rem;border-radius:.55rem}.metric strong{font-size:1.55rem;display:block}.metric span{color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:1rem}.card{border:1px solid var(--line);border-radius:.55rem;padding:1rem;background:white}.card h3{margin-top:0}.priority{border-left:4px solid var(--warn)}
table{border-collapse:collapse;width:100%;margin:1rem 0;font-size:.94rem}th,td{padding:.55rem;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{background:var(--panel);position:sticky;top:52px}code{background:var(--panel);padding:.1rem .25rem;border-radius:.2rem}a{color:var(--accent)}
.pill{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:.12rem .48rem;font-size:.8rem;margin-right:.25rem}.open{border-color:#f59e0b}.resolved,.accepted{border-color:#16a34a}.suppressed{border-color:#64748b}
footer{max-width:1240px;margin:auto;border-top:1px solid var(--line);padding:1.3rem;color:var(--muted)}
"""


def nav() -> str:
    return """<header><div class="bar"><span class="brand">ToIP Portfolio Monitor</span><a href="index.html">Overview</a><a href="findings.html">Findings</a><a href="portfolios.html">Portfolios</a><a href="lifecycle.html">Lifecycle</a><a href="seams.html">Review seams</a><a href="evidence.html">Evidence</a><a href="methodology.html">Method</a></div></header>"""


def page(title: str, body: str, generated: str) -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · ToIP Portfolio Monitor</title><style>{STYLE}</style></head><body>{nav()}<main>{body}</main><footer>Independent observatory · generated {esc(generated)} · not an official Trust Over IP Foundation publication.</footer></body></html>"""


def _evidence_links(values: list[str]) -> str:
    return " · ".join(link(url, "source") for url in values[:4]) or "—"


def render_site(root: str | Path = ".") -> None:
    root = Path(root)
    source = root / "docs" / "data" / "latest.json"
    if not source.exists():
        raise FileNotFoundError("docs/data/latest.json does not exist; run collect first")
    snapshot = json.loads(source.read_text(encoding="utf-8"))
    docs = root / "docs"
    generated = snapshot["generated_at"]
    repositories = snapshot.get("repositories", [])
    events = snapshot.get("events", [])
    units = snapshot.get("change_units", [])
    findings = snapshot.get("findings", [])
    changes = snapshot.get("lifecycle_changes", [])
    seams = snapshot.get("cross_portfolio_seams", [])
    open_findings = [f for f in findings if f.get("status") == "open"]
    critical = [f for f in open_findings if int(f.get("materiality", 0)) >= 4]
    unclassified = [r for r in repositories if r.get("portfolio") == "Unclassified" and r.get("lifecycle") == "active"]
    portfolios = sorted({r.get("portfolio", "Unclassified") for r in repositories})
    period = snapshot.get("period", {})
    week = datetime.fromisoformat(generated).isocalendar()
    week_label = f"{week.year}-W{week.week:02d}"

    priority_cards = []
    for finding in critical[:8]:
        priority_cards.append(f"<div class='card priority'><h3>{esc(finding['subject'])}</h3><p>{esc(finding['summary'])}</p><p><span class='pill open'>open</span> materiality {finding['materiality']} · urgency {finding['urgency']} · assurance {finding['assurance_impact']}</p><p>{_evidence_links(finding.get('evidence', []))}</p></div>")
    if not priority_cards:
        priority_cards.append("<div class='card'><h3>No high-materiality open findings</h3><p class='muted'>The current observation has no open finding at materiality 4 or 5.</p></div>")

    overview = f"""
<h1>Weekly organization brief · {esc(week_label)}</h1>
<p class="lede">A decision-first view of material movement across public repositories in the <code>trustoverip</code> GitHub organization. Raw activity remains available as auditable evidence, but the overview prioritizes findings, lifecycle changes, and cross-portfolio review seams.</p>
<p class="muted">Observation window: {esc(period.get('since'))} → {esc(period.get('until'))}</p>
<div class="metrics"><div class="metric"><strong>{len(repositories)}</strong><span>repositories observed</span></div><div class="metric"><strong>{sum(r.get('lifecycle')=='active' for r in repositories)}</strong><span>active repositories</span></div><div class="metric"><strong>{len(units)}</strong><span>change units</span></div><div class="metric"><strong>{len(open_findings)}</strong><span>open findings</span></div><div class="metric"><strong>{len(changes)}</strong><span>lifecycle deltas</span></div><div class="metric"><strong>{len(seams)}</strong><span>review seams</span></div></div>
<h2>What needs attention</h2><div class="grid">{''.join(priority_cards)}</div>
<h2>Organization pulse</h2><div class="grid"><div class="card"><h3>Lifecycle movement</h3><p><strong>{len(changes)}</strong> repository-state changes detected against the prior retained observation.</p><p><a href="lifecycle.html">Review lifecycle deltas →</a></p></div><div class="card"><h3>Cross-portfolio review</h3><p><strong>{sum(s.get('strength')=='explicit-reference' for s in seams)}</strong> explicit cross-portfolio references and <strong>{sum(s.get('strength')=='related-co-movement' for s in seams)}</strong> weaker co-movement signals.</p><p><a href="seams.html">Review seams →</a></p></div><div class="card"><h3>Classification hygiene</h3><p><strong>{len(unclassified)}</strong> active repositories remain explicitly unclassified.</p><p><a href="portfolios.html">Inspect portfolio registry →</a></p></div></div>
<h2>Material change units</h2><table><thead><tr><th>Portfolio</th><th>Repository</th><th>Change</th><th>Materiality</th><th>Evidence</th></tr></thead><tbody>{''.join(f"<tr><td>{esc(u['portfolio'])}</td><td>{esc(u['repository'])}</td><td>{esc(u['title'])}</td><td>{u['materiality']}</td><td>{_evidence_links(u.get('evidence', []))}</td></tr>" for u in units if int(u.get('materiality',0))>=4) or '<tr><td colspan=5>No material change units in this observation.</td></tr>'}</tbody></table>
"""
    (docs / "index.html").write_text(page("Weekly overview", overview, generated), encoding="utf-8")

    findings_body = f"""<h1>Findings</h1><p class="lede">Stable, machine-addressable observations with separate materiality, urgency, and assurance-impact dimensions. Non-open states are applied only from the governed disposition ledger.</p><table><thead><tr><th>Status</th><th>Category</th><th>Subject</th><th>Finding</th><th>M/U/A</th><th>Evidence</th></tr></thead><tbody>{''.join(f"<tr><td><span class='pill {esc(f['status'])}'>{esc(f['status'])}</span></td><td>{esc(f['category'])}</td><td>{esc(f['subject'])}</td><td>{esc(f['summary'])}<br><code>{esc(f['id'])}</code></td><td>{f['materiality']}/{f['urgency']}/{f['assurance_impact']}</td><td>{_evidence_links(f.get('evidence', []))}</td></tr>" for f in findings) or '<tr><td colspan=6>No findings generated.</td></tr>'}</tbody></table><p>Governance decisions are recorded in <code>data/dispositions.json</code>; the monitor never auto-authorizes a disposition.</p>"""
    (docs / "findings.html").write_text(page("Findings", findings_body, generated), encoding="utf-8")

    by_portfolio: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for repo in repositories:
        by_portfolio[repo.get("portfolio", "Unclassified")].append(repo)
    rows = []
    for portfolio in portfolios:
        members = by_portfolio[portfolio]
        p_units = [u for u in units if u.get("portfolio") == portfolio]
        rows.append(f"<tr><td>{esc(portfolio)}</td><td>{len(members)}</td><td>{sum(r.get('lifecycle')=='active' for r in members)}</td><td>{sum(r.get('lifecycle')=='dormant' for r in members)}</td><td>{sum(r.get('lifecycle')=='archived' for r in members)}</td><td>{len(p_units)}</td><td>{sum(int(u.get('materiality',0))>=4 for u in p_units)}</td></tr>")
    repo_rows = "".join(f"<tr><td>{esc(r['portfolio'])}</td><td>{link(r['url'],r['name'])}</td><td>{esc(r['kind'])}</td><td>{esc(r['lifecycle'])}</td><td>{esc(r.get('description'))}</td></tr>" for r in repositories)
    portfolios_body = f"<h1>Portfolio registry</h1><p class='lede'>Dynamic organization discovery with deterministic portfolio, repository-kind, and lifecycle classification. <strong>Unclassified</strong> is an explicit review state, not an omission.</p><h2>Portfolio summary</h2><table><thead><tr><th>Portfolio</th><th>Repos</th><th>Active</th><th>Dormant</th><th>Archived</th><th>Change units</th><th>Material</th></tr></thead><tbody>{''.join(rows)}</tbody></table><h2>Repository registry</h2><table><thead><tr><th>Portfolio</th><th>Repository</th><th>Kind</th><th>Lifecycle</th><th>Description</th></tr></thead><tbody>{repo_rows}</tbody></table>"
    (docs / "portfolios.html").write_text(page("Portfolio registry", portfolios_body, generated), encoding="utf-8")

    lifecycle_body = f"<h1>Lifecycle movement</h1><p class='lede'>Changes are computed against the immediately preceding retained organization snapshot.</p><table><thead><tr><th>Type</th><th>Portfolio</th><th>Repository</th><th>From</th><th>To</th></tr></thead><tbody>{''.join(f"<tr><td>{esc(c['type'])}</td><td>{esc(c['portfolio'])}</td><td>{link(c.get('url',''),c['repository'])}</td><td>{esc(c.get('from'))}</td><td>{esc(c.get('to'))}</td></tr>" for c in changes) or '<tr><td colspan=5>No lifecycle deltas are available. The first baseline observation intentionally has no prior state.</td></tr>'}</tbody></table>"
    (docs / "lifecycle.html").write_text(page("Lifecycle movement", lifecycle_body, generated), encoding="utf-8")

    seams_body = f"<h1>Cross-portfolio review seams</h1><p class='lede'>A seam is a reason to review across portfolio boundaries, not a claim that a formal technical dependency exists. <code>explicit-reference</code> is stronger evidence than <code>related-co-movement</code>.</p><table><thead><tr><th>Strength</th><th>Portfolios</th><th>Repositories</th><th>Why surfaced</th><th>Evidence</th></tr></thead><tbody>{''.join(f"<tr><td><span class='pill'>{esc(s['strength'])}</span></td><td>{esc(s['source_portfolio'])} → {esc(s['target_portfolio'])}</td><td>{esc(s['source_repository'])}<br>{esc(s['target_repository'])}</td><td>{esc(s['summary'])}</td><td>{_evidence_links(s.get('evidence', []))}</td></tr>" for s in seams) or '<tr><td colspan=5>No cross-portfolio seams surfaced.</td></tr>'}</tbody></table>"
    (docs / "seams.html").write_text(page("Cross-portfolio review seams", seams_body, generated), encoding="utf-8")

    evidence_body = f"<h1>Evidence register</h1><p class='lede'>Normalized source events remain the audit trail underneath change units, findings, and the weekly brief.</p><table><thead><tr><th>Time</th><th>Portfolio</th><th>Repository</th><th>Type</th><th>State</th><th>Evidence</th></tr></thead><tbody>{''.join(f"<tr><td>{esc(e.get('timestamp'))}</td><td>{esc(e.get('portfolio'))}</td><td>{esc(e.get('repository'))}</td><td>{esc(e.get('kind'))}</td><td>{esc(e.get('state'))}</td><td>{link(e.get('url',''),e.get('title',''))}</td></tr>" for e in events[:500])}</tbody></table><p><a href='data/latest.json'>Download latest machine-readable snapshot →</a></p>"
    (docs / "evidence.html").write_text(page("Evidence register", evidence_body, generated), encoding="utf-8")

    methodology_body = f"""<h1>Method and governance boundary</h1><p class="lede">The monitor separates discovery, evidence collection, normalization, change-unit consolidation, organization semantics, findings, dispositions, and publication.</p><div class="grid"><div class="card"><h3>Discovery</h3><p>Public repositories are dynamically enumerated from <code>trustoverip</code>. New repositories cannot silently fall outside a hand-maintained watch list.</p></div><div class="card"><h3>Evidence</h3><p>Commits, issues, pull requests, releases, and repository metadata are normalized into auditable source records.</p></div><div class="card"><h3>Interpretation</h3><p>Materiality and classification are deterministic. Change units intentionally favor false separation over accidental over-merging.</p></div><div class="card"><h3>Review seams</h3><p>Explicit references and related co-movement are evidence-graded. A seam requests cross-review; it does not assert a dependency.</p></div><div class="card"><h3>Disposition</h3><p>Accepting, resolving, or suppressing a finding requires explicit authority, rationale, timestamp, and evidence in the durable ledger.</p></div><div class="card"><h3>Upstream boundary</h3><p>The monitor observes public activity but does not automatically open issues, comment, merge changes, or otherwise modify TrustOverIP repositories.</p></div></div><h2>Snapshot provenance</h2><pre>{esc(json.dumps(snapshot.get('provenance',{}),indent=2))}</pre>"""
    (docs / "methodology.html").write_text(page("Methodology", methodology_body, generated), encoding="utf-8")

    manifest = {
        "generated_at": generated,
        "week": week_label,
        "pages": ["index.html", "findings.html", "portfolios.html", "lifecycle.html", "seams.html", "evidence.html", "methodology.html"],
        "counts": {"repositories": len(repositories), "events": len(events), "change_units": len(units), "findings": len(findings), "open_findings": len(open_findings), "lifecycle_changes": len(changes), "cross_portfolio_seams": len(seams)},
    }
    (docs / "data" / "site-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
