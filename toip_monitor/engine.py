from __future__ import annotations

from pathlib import Path

from . import core
from .profile import DEFAULT_PROFILE_PATH, OrganizationProfile, load_profile


def configure_core(profile: OrganizationProfile) -> None:
    """Apply an organization profile to the existing collector runtime.

    This compatibility adapter is intentionally narrow for the pre-rename
    transition: it moves organization discovery and portfolio taxonomy out of
    Python while preserving the current collector, snapshot schema, finding IDs,
    CLI/package identity, and rendered ToIP report.
    """

    core.ORG = profile.organization
    core.RULES = tuple(
        core.Rule(rule.portfolio, prefixes=rule.prefixes, contains=rule.contains)
        for rule in profile.portfolio_rules
    )


def collect(
    lookback_days: int = 7,
    output_root: str | Path = ".",
    profile_path: str | Path = DEFAULT_PROFILE_PATH,
) -> Path:
    profile = load_profile(profile_path)
    configure_core(profile)
    return core.collect(lookback_days=lookback_days, output_root=output_root)
