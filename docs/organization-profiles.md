# Organization profiles

Trust Ecosystem Monitor separates organization-neutral collection and intelligence from ecosystem-specific classification. Each monitored GitHub organization is described by a TOML profile under `organizations/<profile-id>/profile.toml`.

## Current profiles

- `organizations/trustoverip/profile.toml` — Trust Over IP Foundation
- `organizations/decentralized-identity/profile.toml` — Decentralized Identity Foundation (DIF)

## Profile contract

A profile defines:

- a stable profile identifier;
- the public GitHub organization to discover;
- ecosystem display metadata and disclaimer text; and
- ordered portfolio rules using repository-name prefixes and contained fragments.

Rules are deterministic and evaluated in order. The first matching rule wins. Repositories that match no rule remain explicitly `Unclassified`.

`Unclassified` is a monitor-maintainer review state. It means the current taxonomy does not yet place the repository; it does not imply that the upstream repository is deficient or obligated to change.

## Profile-scoped state

Every profile owns separate retained and generated state:

```text
data/<profile-id>/snapshots/
data/<profile-id>/dispositions.json

docs/<profile-id>/index.html
docs/<profile-id>/findings.html
docs/<profile-id>/portfolios.html
docs/<profile-id>/lifecycle.html
docs/<profile-id>/seams.html
docs/<profile-id>/evidence.html
docs/<profile-id>/methodology.html
docs/<profile-id>/data/latest.json
```

The root `docs/index.html` is an ecosystem catalog. It does not merge the underlying evidence models and does not assert relationships between monitored ecosystems.

## TrustOverIP migration compatibility

The project originally retained TrustOverIP observations under the unscoped `data/snapshots/` path. During the first profile-scoped TrustOverIP run, that legacy snapshot set is used as the seed if `data/trustoverip/snapshots/` does not yet exist. This preserves lifecycle continuity.

The same fallback applies to the legacy `data/dispositions.json` ledger. Once scoped state exists, the scoped paths are authoritative.

Historical `toip-*` finding/change/seam identifiers remain stable. They are not renamed because dispositions and longitudinal references depend on them.

## Adding another ecosystem

A new ecosystem should normally be added as another profile rather than by cloning the monitor. Before admission:

1. identify the ecosystem's own governance/work-item/lifecycle vocabulary;
2. create conservative classification rules grounded in that vocabulary;
3. allow unmatched repositories to remain `Unclassified` rather than guessing;
4. run a first baseline and inspect classification gaps;
5. refine the taxonomy through explicit review; and
6. keep that ecosystem's evidence and dispositions profile-scoped.

Cross-ecosystem reporting is a separate capability. The existence of two profiles is not evidence of a technical dependency, governance relationship or standards alignment.
