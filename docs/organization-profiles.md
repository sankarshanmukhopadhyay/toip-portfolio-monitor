# Organization profiles

Trust Ecosystem Monitor separates organization-neutral collection and intelligence from ecosystem-specific classification. Each monitored GitHub organization is described by a TOML profile under `organizations/<profile-id>/profile.toml`.

## Current profiles

- `organizations/trustoverip/profile.toml` — Trust Over IP Foundation
- `organizations/decentralized-identity/profile.toml` — Decentralized Identity Foundation (DIF)

## Profile contract

A profile defines:

- a stable profile identifier;
- the public GitHub organization to discover;
- ecosystem display metadata and disclaimer text;
- optional exact repository-to-portfolio overrides; and
- ordered portfolio rules using repository-name prefixes and contained fragments.

Classification precedence is:

```text
exact repository override
        ↓
ordered pattern rule
        ↓
Unclassified
```

An override should be used when the repository's own README, work-item declaration or governance material provides stronger evidence than its name. Pattern rules should cover stable repository families. Broad rules should not be introduced merely to drive the unclassified count toward zero.

Every newly generated repository record includes monitor-owned classification provenance:

```json
{
  "portfolio": "Claims & Credentials",
  "classification": {
    "method": "override",
    "rule": "credential-schemas",
    "profile": "decentralized-identity"
  }
}
```

For pattern matches, `method` is `rule` and `rule` identifies the matching prefix or contained fragment. For unmatched repositories, `method` is `unclassified` and `rule` is null.

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
docs/<profile-id>/taxonomy.html
docs/<profile-id>/methodology.html
docs/<profile-id>/data/latest.json
```

The `taxonomy.html` surface makes the profile decision auditable repository-by-repository. It describes how the monitor classified the repository; it is not an upstream governance assertion.

The root `docs/index.html` is an ecosystem catalog. Taxonomy-review items are counted separately from substantive findings so classification maintenance does not read as ecosystem operational risk. The catalog also distinguishes a first baseline from a stateful observation based on whether a previous retained snapshot was available.

## TrustOverIP migration compatibility

The project originally retained TrustOverIP observations under the unscoped `data/snapshots/` path. During the first profile-scoped TrustOverIP run, that legacy snapshot set is used as the seed if `data/trustoverip/snapshots/` does not yet exist. This preserves lifecycle continuity.

The same fallback applies to the legacy `data/dispositions.json` ledger. Once scoped state exists, the scoped paths are authoritative.

Historical `toip-*` finding/change/seam identifiers remain stable. They are not renamed because dispositions and longitudinal references depend on them.

## Adding another ecosystem

A new ecosystem should normally be added as another profile rather than by cloning the monitor. Before admission:

1. identify the ecosystem's own governance/work-item/lifecycle vocabulary;
2. create conservative classification rules grounded in that vocabulary;
3. use exact overrides only where repository-specific evidence justifies them;
4. allow unmatched repositories to remain `Unclassified` rather than guessing;
5. run a first baseline and inspect classification gaps;
6. refine the taxonomy through explicit review; and
7. keep that ecosystem's evidence and dispositions profile-scoped.

Cross-ecosystem reporting is a separate capability. The existence of two profiles is not evidence of a technical dependency, governance relationship or standards alignment.
