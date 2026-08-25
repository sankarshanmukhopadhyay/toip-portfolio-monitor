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

from .intelligence import analyze_snapshot

# Organization identity and portfolio rules are configured by toip_monitor.engine
# from an external organization profile before collection begins. Keeping these
# runtime slots here preserves the existing collector API without embedding a
# TrustOverIP taxonomy in the engine.
ORG = ""
API = "https://api.github.com"
CURRENT_SCHEMA_VERSION = "0.2"


@dataclass(frozen=True)
class Rule:
    portfolio: str
    prefixes: tuple[str, ...] = ()
    contains: tuple[str, ...] = ()


RULES: tuple[Rule, ...] = ()


class GitHubClient:
    def __init__(self, token: str | None = None) -> None:
        self.token = token

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query = urllib.parse.urlencode(params or {})
        url = f"{API}{path}" + (f"?{query}" if query else "")
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "toip-portfolio-monitor/0.2",
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
        if not ORG:
            raise RuntimeError("organization profile is not configured")
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
        "id": repo.get("id"),
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


def _commit_timestamp(item: dict[str, Any]) -> str | None:
    commit = item.get("commit") or {}
    committer = commit.get("committer") or {}
    author = commit.get("author") or {}
    return committer.get("date") or author.get("date")


def normalize_event(kind: str, repo: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    timestamp = (
        _commit_timestamp(item) if kind == "commit" else
        item.get("published_at") or item.get("merged_at") or item.get("closed_at") or item.get("updated_at")
    )
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
        "sha": item.get("sha") if kind == "commit" else None,
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
            for item in client.get(endpoint, params):
                if kind == "issue" and "pull_request" in item:
                    continue
                event = normalize_event(kind, repo, item)
                timestamp = parse_dt(event.get("timestamp"))
                if timestamp and timestamp >= since:
                    events.append(event)
        except Exception as exc:
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
            assertions.append({"id": assertion_id("new-repository", repo["full_name"], repo["created_at"]), "category": "new-repository", "subject": repo["full_name"], "status": "open", "materiality": 4, "summary": f"New repository discovered in {repo['portfolio']}: {repo['name']}", "evidence": [repo["url"]]})
        if repo["portfolio"] == "Unclassified" and repo["lifecycle"] == "active":
            assertions.append({"id": assertion_id("classification", repo["full_name"], "unclassified"), "category": "classification", "subject": repo["full_name"], "status": "open", "materiality": 2, "summary": "Active repository requires portfolio classification.", "evidence": [repo["url"]]})
    for event in events:
        event["materiality"] = score_event(event)
    for error in errors:
        subject = error.split(":", 1)[0]
        assertions.append({"id": assertion_id("collection", subject, error), "category": "collection", "subject": subject, "status": "open", "materiality": 3, "summary": error, "evidence": []})
    return assertions


def _previous_snapshot(snapshot_dir: Path) -> dict[str, Any] | None:
    snapshots = sorted(snapshot_dir.glob("*.json"), reverse=True)
    if not snapshots:
        return None
    try:
        return json.loads(snapshots[0].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def collect(lookback_days: int = 7, output_root: str | Path = ".") -> Path:
    if not ORG or not RULES:
        raise RuntimeError("organization profile is not configured; use the profile-aware collection entry point")
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=lookback_days)
    root = Path(output_root)
    snapshot_dir = root / "data" / "snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    previous = _previous_snapshot(snapshot_dir)
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
        "schema_version": CURRENT_SCHEMA_VERSION,
        "organization": ORG,
        "generated_at": now.isoformat(),
        "period": {"since": since.isoformat(), "until": now.isoformat(), "lookback_days": lookback_days},
        "provenance": {"source": "GitHub REST API", "collector": "toip-portfolio-monitor", "deterministic_classification": True, "previous_snapshot": previous.get("generated_at") if previous else None},
        "repositories": repositories,
        "events": events,
        "assertions": assertions,
        "collection_errors": errors,
    }
    snapshot = analyze_snapshot(snapshot, previous)
    path = snapshot_dir / f"{now.date().isoformat()}.json"
    path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    render(snapshot, root)
    retain_snapshots(snapshot_dir, keep=12)
    return path


def retain_snapshots(directory: Path, keep: int) -> None:
    for old in sorted(directory.glob("*.json"), reverse=True)[keep:]:
        old.unlink()


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def link(url: str, label: str) -> str:
    return f'<a href="{esc(url)}">{esc(label)}</a>' if url else esc(label)


def _list(values: list[str], empty: str) -> str:
    return "<ul>" + "".join(f"<li>{value}</li>" for value in values) + "</ul>" if values else f"<p class=\"muted\">{esc(empty)}</p>"


def render(snapshot: dict[str, Any], root: Path) -> None:
    repos = snapshot["repositories"]
    events = snapshot["events"]
    units = snapshot.get("change_units", [])
    assertions = snapshot["assertions"]
    portfolios = sorted({r["portfolio"] for r in repos})
    material_units = [u for u in units if u.get("materiality", 0) >= 4]
    new_repos = [a for a in assertions if a["category"] == "new-repository"]
    attention = [a for a in assertions if a["category"] in {"classification", "collection"}]
    rows = []
    for portfolio in portfolios:
        members = [r for r in repos if r["portfolio"] == portfolio]
        p_units = [u for u in units if u["portfolio"] == portfolio]
        rows.append(f"<tr><td>{esc(portfolio)}</td><td>{len(members)}</td><td>{sum(r['lifecycle']=='active' for r in members)}</td><td>{len(p_units)}</td><td>{sum(u.get('materiality',0)>=4 for u in p_units)}</td></tr>")

    generated = snapshot["generated_at"]
    period = snapshot["period"]
    week = datetime.fromisoformat(generated).isocalendar()
    week_label = f"{week.year}-W{week.week:02d}"
    spec_units = [u for u in units if u["repo_kind"] == "specification" and u["materiality"] >= 3][:40]
    body = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ToIP Weekly Portfolio Brief — {esc(week_label)}</title>
<style>body{{font:16px/1.55 system-ui,sans-serif;max-width:1180px;margin:auto;padding:2rem;color:#1f2937}}h1,h2{{color:#111827}}a{{color:#075985}}table{{border-collapse:collapse;width:100%;margin:1rem 0}}th,td{{border-bottom:1px solid #ddd;padding:.55rem;text-align:left;vertical-align:top}}.metric{{display:inline-block;margin:.25rem .5rem .25rem 0;padding:.65rem .8rem;background:#f3f4f6;border-radius:.45rem}}.muted{{color:#6b7280}}code{{background:#f3f4f6;padding:.1rem .25rem}}</style></head><body>
<h1>ToIP Weekly Portfolio Brief</h1><p class="muted">Independent observatory · {esc(week_label)} · generated {esc(generated)}</p><p>This report summarizes public GitHub activity across the <code>trustoverip</code> organization. It is independently maintained and is not an official Trust Over IP Foundation publication.</p>
<h2>Executive pulse</h2><div class="metric"><strong>{len(repos)}</strong> repositories</div><div class="metric"><strong>{sum(r['lifecycle']=='active' for r in repos)}</strong> active</div><div class="metric"><strong>{len(events)}</strong> raw events</div><div class="metric"><strong>{len(units)}</strong> change units</div><div class="metric"><strong>{len(material_units)}</strong> material units</div><div class="metric"><strong>{len(new_repos)}</strong> new repositories</div><p>Observation window: {esc(period['since'])} to {esc(period['until'])}.</p>
<h2>Portfolio movement</h2><table><thead><tr><th>Portfolio</th><th>Repos</th><th>Active</th><th>Change units</th><th>Material</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>Material changes</h2>{_list([f"<strong>{esc(u['portfolio'])}</strong> · {esc(u['repository'])}: {link(u['evidence'][0] if u['evidence'] else '', u['title'])} <span class='muted'>({', '.join(u['event_kinds'])}; {u['event_count']} evidence event(s))</span>" for u in material_units[:60]], 'No consolidated change units crossed the materiality threshold.')}
<h2>Specifications advancing</h2>{_list([f"{esc(u['repository'])}: {link(u['evidence'][0] if u['evidence'] else '', u['title'])}" for u in spec_units], 'No specification change unit crossed the reporting threshold.')}
<h2>New work and repository discovery</h2>{_list([f"{esc(a['summary'])} — {link(a['evidence'][0], a['subject'])}" for a in new_repos], 'No newly created repositories were discovered in the observation window.')}
<h2>Attention required</h2>{_list([f"<strong>{esc(a['subject'])}</strong>: {esc(a['summary'])}" for a in attention], 'No classification or collection attention items were generated.')}
<h2>Evidence register</h2><table><thead><tr><th>Time</th><th>Portfolio</th><th>Repository</th><th>Type</th><th>Materiality</th><th>Evidence</th></tr></thead><tbody>{''.join(f"<tr><td>{esc(e['timestamp'])}</td><td>{esc(e['portfolio'])}</td><td>{esc(e['repository'])}</td><td>{esc(e['kind'])}</td><td>{e.get('materiality',score_event(e))}</td><td>{link(e['url'], e['title'])}</td></tr>" for e in events[:250])}</tbody></table>
<h2>Method boundary</h2><p>Raw GitHub events are preserved as evidence but reporting is organized around conservative consolidated change units. Classification and materiality are deterministic. The monitor does not modify upstream repositories or automatically file findings with ToIP projects.</p></body></html>"""
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


def validate(root: str | Path = ".", require_generated: bool = False) -> list[str]:
    """Validate source structure, optionally requiring current generated state.

    Pull-request and push validation checks the repository itself and verifies that
    any committed generated snapshot is valid JSON. The collection workflow uses
    ``require_generated=True`` after regeneration, which additionally requires the
    current schema and complete intelligence collections. This keeps source CI
    independent from intentionally retained legacy output while making publication
    fail closed on stale or incomplete generated evidence.
    """
    root = Path(root)
    errors: list[str] = []
    for rel in ["README.md", "LICENSE", "LICENSE-CONTENT.md", "LICENSES.md", "pyproject.toml"]:
        if not (root / rel).exists():
            errors.append(f"missing required file: {rel}")

    latest = root / "docs" / "data" / "latest.json"
    if not latest.exists():
        if require_generated:
            errors.append("missing generated snapshot: docs/data/latest.json")
        return errors

    try:
        payload = json.loads(latest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid latest snapshot JSON: {exc}")
        return errors

    for key in ("schema_version", "organization", "repositories", "events", "provenance"):
        if key not in payload:
            errors.append(f"latest snapshot missing base key: {key}")

    if require_generated:
        if payload.get("schema_version") != CURRENT_SCHEMA_VERSION:
            errors.append(
                f"generated snapshot schema is {payload.get('schema_version')!r}; expected {CURRENT_SCHEMA_VERSION!r}"
            )
        for key in (
            "change_units",
            "lifecycle_changes",
            "cross_portfolio_seams",
            "findings",
            "assertions",
            "collection_errors",
        ):
            if key not in payload:
                errors.append(f"current generated snapshot missing key: {key}")
    return errors
