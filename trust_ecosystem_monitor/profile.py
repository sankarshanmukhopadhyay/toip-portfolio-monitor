from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_PROFILE_PATH = Path("organizations/trustoverip/profile.toml")


@dataclass(frozen=True)
class PortfolioRule:
    portfolio: str
    prefixes: tuple[str, ...] = ()
    contains: tuple[str, ...] = ()


@dataclass(frozen=True)
class OrganizationProfile:
    schema_version: str
    id: str
    organization: str
    display_name: str
    monitor_title: str
    weekly_brief_title: str
    disclaimer: str
    portfolio_rules: tuple[PortfolioRule, ...]


def load_profile(path: str | Path = DEFAULT_PROFILE_PATH) -> OrganizationProfile:
    path = Path(path)
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    required = ("schema_version", "id", "organization", "display_name", "monitor_title", "weekly_brief_title", "disclaimer")
    missing = [field for field in required if not payload.get(field)]
    if missing:
        raise ValueError(f"organization profile {path} missing required fields: {', '.join(missing)}")

    rules: list[PortfolioRule] = []
    for raw in payload.get("portfolio_rules", []):
        portfolio = str(raw.get("portfolio", "")).strip()
        if not portfolio:
            raise ValueError(f"organization profile {path} contains a portfolio rule without a portfolio name")
        rules.append(
            PortfolioRule(
                portfolio=portfolio,
                prefixes=tuple(str(value).lower() for value in raw.get("prefixes", [])),
                contains=tuple(str(value).lower() for value in raw.get("contains", [])),
            )
        )

    if not rules:
        raise ValueError(f"organization profile {path} must define at least one portfolio rule")

    return OrganizationProfile(
        schema_version=str(payload["schema_version"]),
        id=str(payload["id"]),
        organization=str(payload["organization"]),
        display_name=str(payload["display_name"]),
        monitor_title=str(payload["monitor_title"]),
        weekly_brief_title=str(payload["weekly_brief_title"]),
        disclaimer=str(payload["disclaimer"]),
        portfolio_rules=tuple(rules),
    )


def classify_portfolio(name: str, profile: OrganizationProfile) -> str:
    lowered = name.lower()
    for rule in profile.portfolio_rules:
        if any(lowered.startswith(prefix) for prefix in rule.prefixes):
            return rule.portfolio
        if any(fragment in lowered for fragment in rule.contains):
            return rule.portfolio
    return "Unclassified"


def profile_metadata(profile: OrganizationProfile) -> dict[str, Any]:
    return {
        "schema_version": profile.schema_version,
        "id": profile.id,
        "organization": profile.organization,
        "display_name": profile.display_name,
        "monitor_title": profile.monitor_title,
        "weekly_brief_title": profile.weekly_brief_title,
        "disclaimer": profile.disclaimer,
    }
