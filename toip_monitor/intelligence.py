from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from typing import Any


def _unit_id(repository: str, key: str) -> str:
    digest = hashlib.sha256(f"{repository}|{key}".encode()).hexdigest()[:12]
    return f"toip-change-{digest}"


def _reference_key(event: dict[str, Any]) -> str | None:
    number = event.get("number")
    if number is not None:
        return f"number:{number}"
    match = re.search(r"#(\d+)", event.get("title") or "")
    return f"number:{match.group(1)}" if match else None


def _semantic_key(event: dict[str, Any]) -> str:
    title = (event.get("title") or "untitled").lower()
    title = re.sub(r"\b(merge|merged|fix|feat|docs|chore|refactor|test)(\([^)]*\))?:?\s*", "", title)
    title = re.sub(r"[^a-z0-9]+", " ", title)
    words = [w for w in title.split() if len(w) > 2][:8]
    return "semantic:" + "-".join(words or [event.get("kind", "event")])


def consolidate_change_units(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        key = _reference_key(event) or _semantic_key(event)
        buckets[(event["repository"], key)].append(event)
    units: list[dict[str, Any]] = []
    for (repo, key), members in buckets.items():
        members.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
        primary = max(members, key=lambda m: (int(m.get("materiality", 1)), {"release": 4, "pull_request": 3, "issue": 2, "commit": 1}.get(m["kind"], 0)))
        units.append({
            "id": _unit_id(repo, key), "repository": repo, "portfolio": primary["portfolio"], "repo_kind": primary["repo_kind"],
            "title": primary["title"], "timestamp": members[0].get("timestamp"),
            "materiality": max(int(m.get("materiality", 1)) for m in members),
            "event_kinds": sorted({m["kind"] for m in members}), "event_count": len(members),
            "evidence": list(dict.fromkeys(m["url"] for m in members if m.get("url"))), "events": members,
        })
    units.sort(key=lambda unit: unit.get("timestamp") or "", reverse=True)
    return units


def detect_lifecycle_changes(current: list[dict[str, Any]], previous: list[dict[str, Any]]) -> list[dict[str, Any]]:
    old = {r["full_name"]: r for r in previous}
    new = {r["full_name"]: r for r in current}
    changes: list[dict[str, Any]] = []
    for name, repo in new.items():
        if name not in old:
            changes.append({"type": "discovered", "repository": name, "portfolio": repo["portfolio"], "from": None, "to": repo["lifecycle"], "url": repo["url"]})
            continue
        prior = old[name]
        if repo["lifecycle"] != prior.get("lifecycle"):
            changes.append({"type": "lifecycle", "repository": name, "portfolio": repo["portfolio"], "from": prior.get("lifecycle"), "to": repo["lifecycle"], "url": repo["url"]})
        if repo["portfolio"] != prior.get("portfolio"):
            changes.append({"type": "portfolio", "repository": name, "portfolio": repo["portfolio"], "from": prior.get("portfolio"), "to": repo["portfolio"], "url": repo["url"]})
        if repo.get("default_branch") != prior.get("default_branch"):
            changes.append({"type": "default-branch", "repository": name, "portfolio": repo["portfolio"], "from": prior.get("default_branch"), "to": repo.get("default_branch"), "url": repo["url"]})
    for name, repo in old.items():
        if name not in new:
            changes.append({"type": "missing", "repository": name, "portfolio": repo.get("portfolio", "Unclassified"), "from": repo.get("lifecycle"), "to": None, "url": repo.get("url", "")})
    return sorted(changes, key=lambda c: (c["type"], c["repository"]))


def analyze_snapshot(snapshot: dict[str, Any], previous: dict[str, Any] | None = None) -> dict[str, Any]:
    snapshot["change_units"] = consolidate_change_units(snapshot.get("events", []))
    snapshot["lifecycle_changes"] = detect_lifecycle_changes(snapshot.get("repositories", []), (previous or {}).get("repositories", [])) if previous else []
    snapshot.setdefault("cross_portfolio_seams", [])
    snapshot.setdefault("findings", [])
    return snapshot
