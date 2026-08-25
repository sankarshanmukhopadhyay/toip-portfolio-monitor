from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from . import core_backend as core
from .profile import DEFAULT_PROFILE_PATH, OrganizationProfile, load_profile, profile_metadata
from .site import render_site


class GitHubClient(core.GitHubClient):
    """Canonical client identity for the generalized monitor."""

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query = urllib.parse.urlencode(params or {})
        url = f"{core.API}{path}" + (f"?{query}" if query else "")
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "trust-ecosystem-monitor/0.1",
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


def configure_core(profile: OrganizationProfile) -> None:
    """Configure the organization-neutral collection backend from a profile."""
    core.ORG = profile.organization
    core.RULES = tuple(
        core.Rule(rule.portfolio, prefixes=rule.prefixes, contains=rule.contains)
        for rule in profile.portfolio_rules
    )
    core.GitHubClient = GitHubClient


def _normalize_project_identity(snapshot: dict[str, Any], profile: OrganizationProfile) -> None:
    snapshot["ecosystem_profile"] = profile_metadata(profile)
    snapshot.setdefault("provenance", {})["collector"] = "trust-ecosystem-monitor"
    for collection in ("assertions", "findings"):
        for item in snapshot.get(collection, []):
            summary = str(item.get("summary", ""))
            item["summary"] = summary.replace(
                "This is a monitor taxonomy gap, not an upstream ToIP repository defect or obligation.",
                "This is a monitor taxonomy gap, not an upstream repository defect or obligation.",
            )


def collect(
    lookback_days: int = 7,
    output_root: str | Path = ".",
    profile_path: str | Path = DEFAULT_PROFILE_PATH,
) -> Path:
    profile = load_profile(profile_path)
    configure_core(profile)
    root = Path(output_root)
    path = core.collect(lookback_days=lookback_days, output_root=root)

    snapshot = json.loads(path.read_text(encoding="utf-8"))
    _normalize_project_identity(snapshot, profile)
    serialized = json.dumps(snapshot, indent=2) + "\n"
    path.write_text(serialized, encoding="utf-8")

    latest = root / "docs" / "data" / "latest.json"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(serialized, encoding="utf-8")

    render_site(root)
    return path
