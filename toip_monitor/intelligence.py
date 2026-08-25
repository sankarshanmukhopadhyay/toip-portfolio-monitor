from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from typing import Any


def _unit_id(repository: str, key: str) -> str:
    digest = hashlib.sha256(f"{repository}|{key}".encode()).hexdigest()[:12]
    return f"toip-change-{digest}"


def _reference_key(event: dict[str, Any]) -> str | None:
    """Prefer an explicit issue/PR number when an event supplies one."""
    number = event.get("number")
    if number is not None:
        return f"number:{number}"
    match = re.search(r"#(\d+)", event.get("title") or "")
    if match:
        return f"number:{match.group(1)}"
    return None


def _semantic_key(event: dict[str, Any]) -> str:
    title = (event.get("title") or "untitled").lower()
    title = re.sub(r"\b(merge|merged|fix|feat|docs|chore|refactor|test)(\([^)]*\))?:?\s*", "", title)
    title = re.sub(r"[^a-z0-9]+", " ", title)
    words = [w for w in title.split() if len(w) > 2][:8]
    return "semantic:" + "-".join(words or [event.get("kind", "event")])


def consolidate_change_units(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse overlapping GitHub events into reviewable change units.

    Pull requests/issues are primarily grouped by repository + number. Commits and
    releases without an explicit number use a conservative normalized-title key.
    This intentionally favors false separation over accidental over-merging.
    """
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        repo = event["repository"]
        key = _reference_key(event) or _semantic_key(event)
        buckets[(repo, key)].append(event)

    units: list[dict[str, Any]] = []
    for (repo, key), members in buckets.items():
        members.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
        kinds = sorted({m["kind"] for m in members})
        materiality = max(int(m.get("materiality", 1)) for m in members)
        primary = max(
            members,
            key=lambda m: (
                int(m.get("materiality", 1)),
                {"release": 4, "pull_request": 3, "issue": 2, "commit": 1}.get(m["kind"], 0),
            ),
        )
        evidence = [m["url"] for m in members if m.get("url")]
        units.append(
            {
                "id": _unit_id(repo, key),
                "repository": repo,
                "portfolio": primary["portfolio"],
                "repo_kind": primary["repo_kind"],
                "title": primary["title"],
                "timestamp": members[0].get("timestamp"),
                "materiality": materiality,
                "event_kinds": kinds,
                "event_count": len(members),
                "evidence": list(dict.fromkeys(evidence)),
                "events": members,
            }
        )
    units.sort(key=lambda unit: unit.get("timestamp") or "", reverse=True)
    return units


def analyze_snapshot(snapshot: dict[str, Any], previous: dict[str, Any] | None = None) -> dict[str, Any]:
    """Extension point for portfolio intelligence layers."""
    snapshot["change_units"] = consolidate_change_units(snapshot.get("events", []))
    snapshot.setdefault("lifecycle_changes", [])
    snapshot.setdefault("cross_portfolio_seams", [])
    snapshot.setdefault("findings", [])
    return snapshot
