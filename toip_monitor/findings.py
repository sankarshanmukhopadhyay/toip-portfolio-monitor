from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

VALID_STATUSES = {"open", "accepted", "resolved", "suppressed"}
CLASSIFICATION_SUMMARY = (
    "Monitor taxonomy does not yet classify this active repository. "
    "This is a monitor taxonomy gap, not an upstream ToIP repository defect or obligation."
)


def finding_id(category: str, subject: str, key: str) -> str:
    digest = hashlib.sha256(f"{category}|{subject}|{key}".encode()).hexdigest()[:12]
    return f"toip-finding-{digest}"


def _finding(category: str, subject: str, key: str, summary: str, materiality: int, urgency: int, assurance_impact: int, evidence: list[str]) -> dict[str, Any]:
    return {
        "id": finding_id(category, subject, key),
        "category": category,
        "subject": subject,
        "status": "open",
        "materiality": materiality,
        "urgency": urgency,
        "assurance_impact": assurance_impact,
        "summary": summary,
        "evidence": list(dict.fromkeys(evidence)),
        "disposition": None,
    }


def build_findings(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for assertion in snapshot.get("assertions", []):
        if assertion["category"] in {"classification", "collection"}:
            summary = CLASSIFICATION_SUMMARY if assertion["category"] == "classification" else assertion["summary"]
            findings.append(_finding(assertion["category"], assertion["subject"], assertion["id"], summary, int(assertion["materiality"]), 3 if assertion["category"] == "collection" else 2, 2, assertion.get("evidence", [])))
    for change in snapshot.get("lifecycle_changes", []):
        if change["type"] in {"missing", "lifecycle", "portfolio"}:
            materiality = 4 if change["type"] in {"missing", "lifecycle"} else 3
            findings.append(_finding("lifecycle", change["repository"], f"{change['type']}:{change.get('from')}:{change.get('to')}", f"{change['type']} changed from {change.get('from')} to {change.get('to')}", materiality, 3, 3, [change.get("url", "")] if change.get("url") else []))
    for seam in snapshot.get("cross_portfolio_seams", []):
        if seam["strength"] == "explicit-reference":
            findings.append(_finding("cross-portfolio-seam", seam["source_repository"], seam["id"], seam["summary"], max(3, int(seam["materiality"])), 2, 3, seam.get("evidence", [])))
    for unit in snapshot.get("change_units", []):
        if int(unit.get("materiality", 0)) >= 5:
            findings.append(_finding("material-change", unit["repository"], unit["id"], unit["title"], int(unit["materiality"]), 2, 2, unit.get("evidence", [])))
    deduped = {f["id"]: f for f in findings}
    return sorted(deduped.values(), key=lambda f: (-f["materiality"], -f["urgency"], f["id"]))


def load_dispositions(path: str | Path = "data/dispositions.json") -> list[dict[str, Any]]:
    file = Path(path)
    if not file.exists():
        return []
    payload = json.loads(file.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("disposition ledger must be a JSON array")
    validate_dispositions(payload)
    return payload


def validate_dispositions(dispositions: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for entry in dispositions:
        finding = entry.get("finding_id")
        status = entry.get("status")
        if not finding or finding in seen:
            raise ValueError("each disposition requires a unique finding_id")
        seen.add(finding)
        if status not in VALID_STATUSES:
            raise ValueError(f"invalid disposition status for {finding}: {status}")
        if status != "open":
            for field in ("authority", "rationale", "timestamp", "evidence"):
                if not entry.get(field):
                    raise ValueError(f"non-open disposition {finding} requires {field}")
            try:
                datetime.fromisoformat(str(entry["timestamp"]).replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError(f"invalid disposition timestamp for {finding}") from exc
            if not isinstance(entry["evidence"], list):
                raise ValueError(f"disposition evidence for {finding} must be an array")


def apply_dispositions(findings: list[dict[str, Any]], dispositions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ledger = {entry["finding_id"]: entry for entry in dispositions}
    for finding in findings:
        entry = ledger.get(finding["id"])
        if entry:
            finding["status"] = entry["status"]
            finding["disposition"] = entry
    return findings
