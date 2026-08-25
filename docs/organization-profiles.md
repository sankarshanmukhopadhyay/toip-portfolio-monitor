# Organization profiles

The monitor is transitioning from a TrustOverIP-specific implementation to a reusable organization-monitoring engine. This document records the architecture at the **pre-rename compatibility point**.

The visible project identity remains **ToIP Portfolio Monitor** for now. The repository name, Python package, CLI command, workflow names, generated Pages branding, assertion identifiers, and existing snapshot schema are intentionally unchanged until the maintainer performs the planned manual rename.

## What has been generalized

Organization discovery and portfolio taxonomy are now selected through an external TOML profile. The default profile is:

```text
organizations/trustoverip/profile.toml
```

It carries the GitHub organization identifier and the ordered portfolio-classification rules that were previously maintained directly in Python.

The collection entry point loads that profile and configures the existing collector runtime before discovery begins. As a result, the default command remains backward compatible:

```bash
python -m toip_monitor collect --lookback-days 7
```

The equivalent explicit form is:

```bash
python -m toip_monitor collect \
  --profile organizations/trustoverip/profile.toml \
  --lookback-days 7
```

## Profile contract

A profile currently defines:

- a stable profile identifier;
- the public GitHub organization to discover;
- display/product metadata reserved for the later rename/generalization step; and
- ordered portfolio rules using repository-name prefixes and contained fragments.

Repositories that match no rule remain explicitly `Unclassified`. The first matching rule wins, preserving the current deterministic semantics.

## Compatibility boundary

This stage deliberately does **not** change the generated ToIP report. The current profile retains the same organization (`trustoverip`), portfolio names, matching order, visible report identity, snapshot schema, evidence model, lifecycle logic, change-unit logic, findings, dispositions, and Pages information architecture.

`tests/test_profile_compatibility.py` treats the currently retained `docs/data/latest.json` snapshot as a compatibility fixture: every retained repository classification must be reproduced by `organizations/trustoverip/profile.toml`. Representative historical mappings are also locked explicitly.

This means the externalization can be reviewed as an architectural change without silently re-baselining the ToIP taxonomy.

## What remains intentionally ToIP-specific

Until the manual rename, the following remain intentionally unchanged:

- repository and product name;
- `toip_monitor` Python package;
- `toip-monitor` CLI entry point;
- GitHub Actions workflow names;
- rendered Pages branding and disclaimer;
- current assertion/finding identifier namespace; and
- current generated data locations.

Those names are compatibility surfaces, not evidence that the organization/taxonomy engine is still hard-wired to TrustOverIP.

## Adding another ecosystem later

After the project is renamed, a new organization should normally be introduced as another profile rather than by cloning the repository. A future profile can live under, for example:

```text
organizations/<profile-id>/profile.toml
```

Before such a profile is admitted, its taxonomy should be grounded in that ecosystem's own governance and lifecycle model, and it should receive its own baseline compatibility and classification review.

Cross-ecosystem reporting is a separate capability and should not be inferred merely because more than one organization profile exists.
