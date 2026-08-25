from __future__ import annotations

import json
import os
import shutil
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from . import core_backend as core
from .profile import (
    DEFAULT_PROFILE_PATH,
    OrganizationProfile,
    classify_portfolio_details,
    load_profile,
    profile_metadata,
)
from .site import render_catalog, render_site


class GitHubClient(core.GitHubClient):
    """Canonical client identity for the generalized monitor."""

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query = urllib.parse.urlencode(params or {})
        url = f"{core.API}{path}" + (f"?{query}" if query else "")
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "trust-ecosystem-monitor/0.2",
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
    """Configure the organization-neutral collection backend from a profile.

    The backend retains its historical collector API, while classification is
    delegated to the selected profile so exact overrides stay exact and pattern
    rules retain their documented order.
    """
    core.ORG = profile.organization
    core.RULES = tuple(
        core.Rule(rule.portfolio, prefixes=rule.prefixes, contains=rule.contains)
        for rule in profile.portfolio_rules
    )

    def profile_classifier(name: str) -> str:
        return str(classify_portfolio_details(name, profile)["portfolio"])

    core.classify_portfolio = profile_classifier
    core.GitHubClient = GitHubClient


def _normalize_project_identity(snapshot: dict[str, Any], profile: OrganizationProfile) -> None:
    snapshot["ecosystem_profile"] = profile_metadata(profile)
    snapshot.setdefault("provenance", {})["collector"] = "trust-ecosystem-monitor"

    portfolio_by_repository: dict[str, str] = {}
    for repository in snapshot.get("repositories", []):
        detail = classify_portfolio_details(str(repository.get("name", "")), profile)
        repository["portfolio"] = detail["portfolio"]
        repository["classification"] = {
            "method": detail["method"],
            "rule": detail["rule"],
            "profile": profile.id,
        }
        portfolio_by_repository[str(repository.get("full_name", ""))] = str(detail["portfolio"])

    # Keep downstream records aligned with the authoritative profile result.
    for event in snapshot.get("events", []):
        portfolio = portfolio_by_repository.get(str(event.get("repository", "")))
        if portfolio:
            event["portfolio"] = portfolio
    for unit in snapshot.get("change_units", []):
        portfolio = portfolio_by_repository.get(str(unit.get("repository", "")))
        if portfolio:
            unit["portfolio"] = portfolio
    for change in snapshot.get("lifecycle_changes", []):
        portfolio = portfolio_by_repository.get(str(change.get("repository", "")))
        if portfolio:
            change["portfolio"] = portfolio

    classification_summary = (
        "Monitor taxonomy does not yet classify this active repository. "
        "This is a monitor taxonomy gap, not an upstream repository defect or obligation."
    )
    for collection in ("assertions", "findings"):
        for item in snapshot.get(collection, []):
            if item.get("category") == "classification":
                item["summary"] = classification_summary
                continue
            summary = str(item.get("summary", ""))
            item["summary"] = summary.replace(
                "This is a monitor taxonomy gap, not an upstream ToIP repository defect or obligation.",
                "This is a monitor taxonomy gap, not an upstream repository defect or obligation.",
            )


def _seed_snapshots(root: Path, work_root: Path, profile: OrganizationProfile) -> None:
    """Seed profile work state, preserving the pre-scope ToIP baseline once."""
    scoped = root / "data" / profile.id / "snapshots"
    legacy = root / "data" / "snapshots"
    source = scoped if scoped.exists() else legacy if profile.id == "trustoverip" and legacy.exists() else None
    if source:
        target = work_root / "data" / "snapshots"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target, dirs_exist_ok=True)


def _seed_dispositions(root: Path, work_root: Path, profile: OrganizationProfile) -> None:
    scoped = root / "data" / profile.id / "dispositions.json"
    legacy = root / "data" / "dispositions.json"
    source = scoped if scoped.exists() else legacy if profile.id == "trustoverip" and legacy.exists() else None
    if source:
        target = work_root / "data" / "dispositions.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def _persist_profile_state(root: Path, work_root: Path, profile: OrganizationProfile) -> Path:
    data_root = root / "data" / profile.id
    docs_root = root / "docs" / profile.id
    data_root.mkdir(parents=True, exist_ok=True)

    work_snapshots = work_root / "data" / "snapshots"
    scoped_snapshots = data_root / "snapshots"
    if scoped_snapshots.exists():
        shutil.rmtree(scoped_snapshots)
    shutil.copytree(work_snapshots, scoped_snapshots)

    work_dispositions = work_root / "data" / "dispositions.json"
    scoped_dispositions = data_root / "dispositions.json"
    if work_dispositions.exists() and not scoped_dispositions.exists():
        shutil.copyfile(work_dispositions, scoped_dispositions)

    if docs_root.exists():
        shutil.rmtree(docs_root)
    shutil.copytree(work_root / "docs", docs_root)

    snapshots = sorted(scoped_snapshots.glob("*.json"), reverse=True)
    if not snapshots:
        raise RuntimeError(f"profile {profile.id} produced no retained snapshot")
    return snapshots[0]


def collect(
    lookback_days: int = 7,
    output_root: str | Path = ".",
    profile_path: str | Path = DEFAULT_PROFILE_PATH,
) -> Path:
    """Collect one ecosystem into profile-scoped durable state and Pages output."""
    profile = load_profile(profile_path)
    configure_core(profile)
    root = Path(output_root).resolve()

    with tempfile.TemporaryDirectory(prefix=f"trust-monitor-{profile.id}-") as temporary:
        work_root = Path(temporary)
        _seed_snapshots(root, work_root, profile)
        _seed_dispositions(root, work_root, profile)

        prior_cwd = Path.cwd()
        try:
            os.chdir(work_root)
            path = core.collect(lookback_days=lookback_days, output_root=work_root)
        finally:
            os.chdir(prior_cwd)

        snapshot = json.loads(path.read_text(encoding="utf-8"))
        _normalize_project_identity(snapshot, profile)
        serialized = json.dumps(snapshot, indent=2) + "\n"
        path.write_text(serialized, encoding="utf-8")

        # Re-render the backend's archived weekly brief from normalized evidence
        # so classification explanations and canonical provenance are consistent
        # across both archive and decision-grade report surfaces.
        core.render(snapshot, work_root)
        latest = work_root / "docs" / "data" / "latest.json"
        latest.parent.mkdir(parents=True, exist_ok=True)
        latest.write_text(serialized, encoding="utf-8")
        render_site(work_root)

        persisted = _persist_profile_state(root, work_root, profile)

    render_catalog(root)
    return persisted
