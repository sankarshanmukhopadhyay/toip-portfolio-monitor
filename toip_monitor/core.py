from __future__ import annotations

import hashlib
import html
import json
import os
import shutil
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ORG = "trustoverip"
API = "https://api.github.com"


@dataclass(frozen=True)
class Rule:
    portfolio: str
    prefixes: tuple[str, ...] = ()
    contains: tuple[str, ...] = ()


RULES = (
    Rule("DTG", prefixes=("dtgwg-",)),
    Rule("AIMWG", prefixes=("aimwg-",)),
    Rule("KERI Suite", prefixes=("kswg-",), contains=("keri", "acdc", "kerisuite")),
    Rule("CTWG", prefixes=("ctwg-",), contains=("concepts-and-terminology",)),
    Rule("TSWG", prefixes=("tswg-",), contains=("technology-stack",)),
    Rule("EGWG", prefixes=("egwg-",)),
    Rule("vLEI / EGF", prefixes=("vlei-", "egf-")),
    Rule("Spec-Up", prefixes=("spec-up",)),
    Rule("Governance", prefixes=("governance",), contains=("governance-stack",)),
    Rule("Legacy deliverables", prefixes=("tss", "wp00", "tip00", "trtf-")),
)


class GitHubClient:
    def __init__(self, token: str | None = None) -> None:
        self.token = token

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query = urllib.parse.urlencode(params or {})
        url = f"{API}{path}" + (f"?{query}" if query else "")
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "toip-portfolio-monitor/0.1",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API {exc.code} for {path}: {body[:300]}") from exc

    def org_repositories(self) -> list[dict[str, Any]]:
        repos: list[dict[str, Any]] = []
        page = 1
        while True:
            batch = self.get(f"/orgs/{ORG}/repos", {"type": "public", "per_page": 100, "page": page})
            repos.extend(batch)
            if len(batch) < 100:
                return repos
            page += 1


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def classify_portfolio(name: str) -> str:
    lowered = name.lower()
    for rule in RULES:
        if any(lowered.startswith(prefix) for prefix in rule.prefixes):
            return rule.portfolio
        if any(fragment in lowered for fragment in rule.contains):
            return rule.portfolio
    return "Unclassified"


def classify_kind(name: str) -> str:
    lowered = name.lower()
    if "public-review" in lowered or "review" in lowered:
        return "public-review"
    if "template" in lowered:
        return "template"
    if lowered.startswith("spec-up") or "toolkit" in lowered:
        return "tooling"
    if lowered.endswith("-tf") or "task-force" in lowered:
        return "task-force"
    if "specification" in lowered or lowered.startswith("tss") or "-spec" in lowered:
        return "specification"
    if lowered.endswith("wg") or "-wg" in lowered:
        return "workgroup"
    if "glossary" in lowered or "terminology" in lowered:
        return "terminology"
    if "governance" in lowered:
        return "governance"
    return "repository"


def lifecycle(repo: dict[str, Any], now: datetime) -> str:
    if repo.get("archived"):
        return "archived"
    pushed = parse_dt(repo.get("pushed_at"))
    if pushed and now - pushed > timedelta(days=365):
        return "dormant"
    return "active"


def repo_record(repo: dict[str, Any], now: datetime) -> dict[str, Any]:
    return {
        "name": repo["name"],
        "full_name": repo["full_name"],
        "url": repo["html_url"],
        "description": repo.get("description"),
        "created_at": repo.get("created_at"),
        "updated_at": repo.get("updated_at"),
        "pushed_at": repo.get("pushed_at"),
        "archived": bool(repo.get("archived")),
        "fork": bool(repo.get("fork")),
        "default_branch": repo.get("default_branch"),
        "portfolio": classify_portfolio(repo["name"]),
        "kind": classify_kind(repo["name"]),
        "lifecycle": lifecycle(repo, now),
    }


def normalize_event(kind: str, repo: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    timestamp = item.get("published_at") or item.get("merged_at") or item.get("closed_at") or item.get("updated_at")
    title = item.get("name") or item.get("title") or (item.get("commit") or {}).get("message", "").splitlines()[0]
    url = item.get("html_url") or ""
    state = item.get("state")
    if kind == "pull_request" and item.get("merged_at"):
        state = "merged"
    return {
        "kind": kind,
        "repository": repo["full_name"],
        "portfolio": repo["portfolio"],
        "repo_kind": repo["kind"],
        "timestamp": timestamp,
        "title": title or "(untitled)",
        "url": url,
        "number": item.get("number"),
        "state": state,
    }


def collect_repo_activity(client: GitHubClient, repo: dict[str, Any], since: datetime) -> tuple[list[dict[str, Any]], list[str]]:
    owner_repo = repo["full_name"]
    path = f"/repos/{owner_repo}"
    since_iso = since.isoformat().replace("+00:00", "Z")
    events: list[dict[str, Any]] = []
    errors: list[str] = []

    endpoints = (
        ("commit", f"{path}/commits", {"since": since_iso, "per_page": 100}),
        ("issue", f"{path}/issues", {"state": "all", "since": since_iso, "per_page": 100}),
        ("pull_request", f"{path}/pulls", {"state": "all", "sort": "updated", "direction": "desc", "per_page": 100}),
        ("release", f"{path}/releases", {"per_page": 100}),
    )
    for kind, endpoint, params in endpoints:
        try:
            items = client.get(endpoint, params)
            for item in items:
                if kind == "issue" and "pull_request" in item:
                    continue
                event = normalize_event(kind, repo, item)
                timestamp = parse_dt(event.get("timestamp"))
                if kind in {"pull_request", "release"} and timestamp and timestamp < since:
                    continue
                if timestamp and timestamp >= since:
                    events.append(event)
        except Exception as exc:  # isolate individual streams
            errors.append(f"{owner_repo}:{kind}: {exc}")
    return events, errors


def score_event(event: dict[str, Any]) -> int:
    base = {"release": 5, "pull_request": 3, "issue": 2, "commit": 1}.get(event["kind"], 1)
    if event["kind"] == "pull_request" and event.get("state") == "merged":
        base = 4
    if event.get("repo_kind") == "specification":
        base += 1
    return min(base, 5)


def assertion_id(category: str, subject: str, key: str) -> str:
    digest = hashlib.sha256(f"{category}|{subject}|{key}".encode()).hexdigest()[:12]
    return f"toip-{category}-{digest}"


def build_assertions(repos: list[dict[str, Any]], events: list[dict[str, Any]], errors: list[str], since: datetime) -> list[dict[str, Any]]:
    assertions: list[dict[str, Any]] = []
    for repo in repos:
        created = parse_dt(repo.get("created_at"))
        if created and created >= since:
            assertions.append({
                "id": assertion_id("new-repository", repo["full_name"], repo["created_at"]),
                "category": "new-repository",
                "subject": repo["full_name"],
                "status": "open",
                "materiality": 4,
                "summary": f"New repository discovered in {repo['portfolio']}: {repo['name']}",
                "evidence": [repo["url"]],
            })
        if repo["portfolio"] == "Unclassified" and repo["lifecycle"] == "active":
            assertions.append({
                "id": assertion_id("classification", repo["full_name"], "unclassified"),
                "category": "classification",
                "subject": repo["full_name"],
                "status": "open",
                "materiality": 2,
                "summary": "Active repository requires portfolio classification.",
                "evidence": [repo["url"]],
            })
    for event in events:
        materiality = score_event(event)
        event["materiality"] = materiality
        if materiality >= 4:
            assertions.append({
                "id": assertion_id("material-change", event["repository"], event["url"] or event["title"]),
                "category": "material-change",
                "subject": event["repository"],
                "status": "open",
                "materiality": materiality,
                "summary": f"{event['kind'].replace('_', ' ').title()}: {event['title']}",
                "evidence": [event["url"]] if event["url"] else [],
            })
    for error in errors:
        subject = error.split(":", 1)[0]
        assertions.append({
            "id": assertion_id("collection", subject, error),
            "category": "collection",
            "subject": subject,
            "status": "open",
            "materiality": 3,
            "summary": error,
            "evidence": [],
        })
    return assertions


def collect(lookback_days: int = 7, output_root: str | Path = ".") -> Path:
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=lookback_days)
    client = GitHubClient(os.environ.get("GITHUB_TOKEN"))
    repositories = [repo_record(repo, now) for repo in client.org_repositories()]
    repositories.sort(key=lambda r: (r["portfolio"], r["name"].lower()))

    events: list[dict[str, Any]] = []
    errors: list[str] = []
    active = [repo for repo in repositories if repo["lifecycle"] != "archived"]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(collect_repo_activity, client, repo, since): repo for repo in active}
        for future in as_completed(futures):
            repo_events, repo_errors = future.result()
            events.extend(repo_events)
            errors.extend(repo_errors)
    events.sort(key=lambda e: e.get("timestamp") or "", reverse=True)
    assertions = build_assertions(repositories, events, errors, since)

    snapshot = {
        "schema_version": "0.1",
        "organization": ORG,
        "generated_at": now.isoformat(),
        "period": {"since": since.isoformat(), "until": now.isoformat(), "lookback_days": lookback_days},
        "provenance": {"source": "GitHub REST API", "collector": "toip-portfolio-monitor", "deterministic_classification": True},
        "repositories": repositories,
        "events": events,
        "assertions": assertions,
        "collection_errors": errors,
    }

    root = Path(output_root)
    snapshot_dir = root / "data" / "snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    path = snapshot_dir / f"{now.date().isoformat()}.json"
    path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    render(snapshot, root)
    retain_snapshots(snapshot_dir, keep=12)
    return path


def retain_snapshots(directory: Path, keep: int) -> None:
    snapshots = sorted(directory.glob("*.json"), reverse=True)
    for old in snapshots[keep:]:
        old.unlink()


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def link(url: str, label: str) -> str:
    return f'<a href="{esc(url)}">{esc(label)}</a>' if url else esc(label)


def render(snapshot: dict[str, Any], root: Path) -> None:
    repos = snapshot["repositories"]
    events = snapshot["events"]
    assertions = snapshot["assertions"]
    portfolios = sorted({r["portfolio"] for r in repos})
    material = [e for e in events if e.get("materiality", score_event(e)) >= 4]
    new_repos = [a for a in assertions if a["category"] == "new-repository"]
    attention = [a for a in assertions if a["category"] in {"classification", "collection"}]

    rows = []
    for portfolio in portfolios:
        members = [r for r in repos if r["portfolio"] == portfolio]
        portfolio_events = [e for e in events if e["portfolio"] == portfolio]
        rows.append(
            f"<tr><td>{esc(portfolio)}</td><td>{len(members)}</td><td>{sum(r['lifecycle']=='active' for r in members)}</td>"
            f"<td>{len(portfolio_events)}</td><td>{sum(score_event(e)>=4 for e in portfolio_events)}</td></tr>"
        )

    spec_items = [e for e in events if e["repo_kind"] == "specification" and score_event(e) >= 3][:40]
    evidence_items = events[:200]
    generated = snapshot["generated_at"]
    period = snapshot["period"]
    week = datetime.fromisoformat(generated).isocalendar()
    week_label = f"{week.year}-W{week.week:02d}"

    def items(values: list[str], empty: str) -> str:
        return "<ul>" + "".join(f"<li>{value}</li>" for value in values) + "</ul>" if values else f"<p>{esc(empty)}</p>"

    body = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ToIP Weekly Portfolio Brief — {esc(week_label)}</title>
<style>body{{font:16px/1.55 system-ui,sans-serif;max-width:1180px;margin:auto;padding:2rem;color:#1f2937}}h1,h2{{color:#111827}}table{{border-collapse:collapse;width:100%;margin:1rem 0}}th,td{{border-bottom:1px solid #ddd;padding:.55rem;text-align:left}}.metric{{display:inline-block;margin:.25rem 1rem .25rem 0;padding:.6rem .8rem;background:#f3f4f6;border-radius:.4rem}}.muted{{color:#6b7280}}code{{background:#f3f4f6;padding:.1rem .25rem}}</style></head><body>
<h1>ToIP Weekly Portfolio Brief</h1>
<p class="muted">Independent observatory · {esc(week_label)} · generated {esc(generated)}</p>
<p>This report summarizes public GitHub activity across the <code>trustoverip</code> organization. It is independently maintained and is not an official Trust Over IP Foundation publication.</p>
<h2>Executive pulse</h2>
<div class="metric"><strong>{len(repos)}</strong> repositories discovered</div><div class="metric"><strong>{sum(r['lifecycle']=='active' for r in repos)}</strong> active</div><div class="metric"><strong>{len(events)}</strong> evidence events</div><div class="metric"><strong>{len(material)}</strong> material changes</div><div class="metric"><strong>{len(new_repos)}</strong> new repositories</div>
<p>Observation window: {esc(period['since'])} to {esc(period['until'])}.</p>
<h2>Portfolio movement</h2><table><thead><tr><th>Portfolio</th><th>Repos</th><th>Active</th><th>Events</th><th>Material</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>Specifications advancing</h2>{items([f"{link(e['url'], e['repository'])}: {esc(e['title'])} ({esc(e['kind'])})" for e in spec_items], 'No specification activity crossed the reporting threshold.')}
<h2>New work and repository discovery</h2>{items([f"{esc(a['summary'])} — {link(a['evidence'][0], a['subject'])}" for a in new_repos], 'No newly created repositories were discovered in the observation window.')}
<h2>Attention required</h2>{items([f"<strong>{esc(a['subject'])}</strong>: {esc(a['summary'])}" for a in attention], 'No classification or collection attention items were generated.')}
<h2>Evidence register</h2><table><thead><tr><th>Time</th><th>Portfolio</th><th>Repository</th><th>Type</th><th>Materiality</th><th>Evidence</th></tr></thead><tbody>{''.join(f"<tr><td>{esc(e['timestamp'])}</td><td>{esc(e['portfolio'])}</td><td>{esc(e['repository'])}</td><td>{esc(e['kind'])}</td><td>{score_event(e)}</td><td>{link(e['url'], e['title'])}</td></tr>" for e in evidence_items)}</tbody></table>
<h2>Method boundary</h2><p>Classification and materiality are deterministic and machine-addressable. Generated narrative remains subordinate to source evidence. The monitor does not modify upstream repositories or automatically file findings with ToIP projects.</p>
</body></html>"""

    docs = root / "docs"
    reports = docs / "reports"
    data = docs / "data"
    reports.mkdir(parents=True, exist_ok=True)
    data.mkdir(parents=True, exist_ok=True)
    report_path = reports / f"{week_label}.html"
    report_path.write_text(body, encoding="utf-8")
    shutil.copyfile(report_path, docs / "index.html")
    shutil.copyfile(report_path, reports / "latest.html")
    (data / "latest.json").write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")


def validate(root: str | Path = ".") -> list[str]:
    root = Path(root)
    errors: list[str] = []
    required = ["README.md", "LICENSE", "LICENSE-CONTENT.md", "LICENSES.md", "pyproject.toml"]
    for rel in required:
        if not (root / rel).exists():
            errors.append(f"missing required file: {rel}")
    if (root / "docs" / "data" / "latest.json").exists():
        try:
            payload = json.loads((root / "docs" / "data" / "latest.json").read_text(encoding="utf-8"))
            for key in ("schema_version", "organization", "repositories", "events", "assertions", "provenance"):
                if key not in payload:
                    errors.append(f"latest snapshot missing key: {key}")
        except json.JSONDecodeError as exc:
            errors.append(f"invalid latest snapshot JSON: {exc}")
    return errors
