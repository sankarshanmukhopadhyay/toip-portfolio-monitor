# Organization profiles

Trust Ecosystem Monitor uses organization profiles to separate reusable monitoring machinery from ecosystem-specific discovery and taxonomy.

The project itself is organization-neutral. Each monitored ecosystem supplies a TOML profile under:

```text
organizations/<profile-id>/profile.toml
```

The first profile is:

```text
organizations/trustoverip/profile.toml
```

## Profile contract

A profile currently defines:

- a stable profile identifier;
- the public GitHub organization to discover;
- ecosystem display metadata and weekly-brief title;
- an ecosystem-specific independence/disclaimer statement; and
- ordered portfolio rules using repository-name prefixes and contained fragments.

Repositories that match no rule remain explicitly `Unclassified`. The first matching rule wins, preserving deterministic semantics.

## Runtime boundary

The canonical collection path is:

```bash
python -m trust_ecosystem_monitor collect \
  --profile organizations/trustoverip/profile.toml \
  --lookback-days 7
```

The engine loads the profile before repository discovery and configures the collector with the selected GitHub organization and portfolio rules. Evidence normalization, change-unit construction, lifecycle comparison, review seams, findings, dispositions, retention, validation, and publication remain shared engine behavior.

## Product identity versus ecosystem identity

The product shell is **Trust Ecosystem Monitor**. A profile does not rename the product.

Profile-specific content includes the monitored organization, taxonomy, ecosystem labels, weekly brief title, and disclaimer. This lets the same engine monitor different organizations without implying that one ecosystem's governance model applies to another.

The former `toip_monitor` package and `toip-monitor` console command remain temporary compatibility aliases after the repository rename. New work should use `trust_ecosystem_monitor` and `trust-ecosystem-monitor`.

## TrustOverIP compatibility contract

`tests/test_profile_compatibility.py` treats the retained `docs/data/latest.json` TrustOverIP snapshot as a compatibility fixture: every retained repository classification must be reproduced by `organizations/trustoverip/profile.toml`. Representative historical mappings are also locked explicitly.

A mismatch fails CI. Changes to the TrustOverIP taxonomy therefore remain explicit review decisions rather than accidental side effects of engine changes.

Historical `toip-*` assertion/finding identifiers are retained so existing dispositions and longitudinal references remain stable. The project rename does not rewrite historical evidence.

## Adding another ecosystem

A new ecosystem should normally be introduced as another profile rather than by cloning this repository. Before admission, its taxonomy should be grounded in that ecosystem's own governance, working-group, work-item, specification, and lifecycle model.

For example:

```text
organizations/decentralized-identity/profile.toml
```

should be based on DIF's own working-group and work-item lifecycle semantics rather than copied from TrustOverIP.

A new profile should include:

1. explicit organization identity;
2. evidence-backed taxonomy rules and any curated overrides required by repository naming;
3. representative classification tests;
4. an initial baseline review of `Unclassified` repositories;
5. a profile-specific disclaimer; and
6. documentation of any lifecycle semantics that differ from the shared default.

## Cross-ecosystem reporting

Supporting multiple profiles does not itself prove relationships between ecosystems. Cross-ecosystem seams, convergence, or dependency reporting should remain a separate evidence-graded capability and should only be added once at least two ecosystem profiles have stable baselines.
