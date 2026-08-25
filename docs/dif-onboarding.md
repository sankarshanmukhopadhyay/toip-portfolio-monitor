# DIF onboarding

The Decentralized Identity Foundation (DIF) is the second ecosystem profile admitted to Trust Ecosystem Monitor.

## Why a profile, not another monitor

DIF presents the same organization-level observability problem as TrustOverIP: a large GitHub organization containing specifications, implementations, working-group repositories, tooling, governance material and archived work. The collection, evidence, lifecycle, findings and publication machinery therefore remains common. What differs is the ecosystem taxonomy.

The DIF profile is:

```text
organizations/decentralized-identity/profile.toml
```

and collects from:

```text
github.com/decentralized-identity
```

## Taxonomy basis

The taxonomy is grounded in DIF's published working-group/work-item structure, including active areas such as:

- Claims & Credentials;
- DID Methods;
- DIDComm;
- Identifiers & Discovery;
- Applied Crypto;
- Labs;
- Trusted AI Agents;
- Creator Assertions; and
- Hospitality & Travel.

The profile also preserves recognizable archived domains such as Secure Data Storage / DWN, Wallet Security and Sidetree / ION, because repository lifecycle history remains useful even after a working group is archived.

Representative pattern mappings include:

- `universal-resolver*` and `uni-resolver-driver-*` → Identifiers & Discovery;
- `didcomm*` → DIDComm;
- `presentation-exchange*` → Claims & Credentials;
- `cawg-*` → Creator Assertions;
- `did-peer-*` → DID Methods;
- `edv-*` → Secure Data Storage / DWN; and
- `sidetree*` → Sidetree / ION.

## What the first live baseline taught us

The first live DIF observation on 2026-08-25 discovered 268 repositories, including 63 active repositories. Twenty-seven active repositories were initially `Unclassified`. That was useful evidence: it showed where the conservative first-pass taxonomy was incomplete without requiring the monitor to guess.

The first refinement therefore adds two distinct mechanisms:

1. **stable family rules** for repository families such as `cawg-*`, `did-peer-*`, `edv-*`, Universal Resolver drivers and Universal Registrar drivers; and
2. **exact repository overrides** when an individual repository's own work-item declaration provides stronger evidence than its name.

Current explicit overrides include examples such as:

- `credential-schemas` → Claims & Credentials;
- `delegated-authority-report` and `delegated-authority-threat-model` → Trusted AI Agents;
- `kya-os-mcp` and `kya-os-schema` → Trusted AI Agents;
- `did-traits` → Identifiers & Discovery;
- `hatpro-schema-htwg` → Hospitality & Travel;
- `jsonld-common-java` → Implementations & Tooling;
- `thisdid` → Identifiers & Discovery; and
- `well-known-did-configuration` → Identifiers & Discovery.

Repositories such as `aries-rfcs`, `did-attested-resources`, `spec-up` and `specs` are deliberately not forced into a portfolio merely to reduce the unclassified count. They should remain reviewable until the portfolio boundary is justified.

## Classification provenance

Newly generated DIF repository records include the monitor-owned classification method and source:

```json
"classification": {
  "method": "override",
  "rule": "credential-schemas",
  "profile": "decentralized-identity"
}
```

The generated `taxonomy.html` report makes this visible for every repository. This provenance explains the monitor's decision; it does not claim that DIF itself has assigned the same label.

## Conservative boundary

Repositories that do not match a defensible override or rule remain `Unclassified`. Those findings mean:

> the monitor taxonomy does not yet classify the repository.

They do not mean that the DIF repository is misconfigured, deficient or required to adopt a particular governance label. Zero unclassified repositories is not a success criterion.

The top-level ecosystem catalog also reports taxonomy-review items separately from substantive and priority findings, so taxonomy maintenance is not presented as ecosystem operational risk.

## Separate retained state

DIF state is independent of TrustOverIP state:

```text
data/decentralized-identity/snapshots/
data/decentralized-identity/dispositions.json

docs/decentralized-identity/
```

A DIF run cannot overwrite TrustOverIP evidence or dispositions.

The next collection after this taxonomy refinement is the first opportunity to evaluate DIF as a stateful observation against the retained first baseline.

## Cross-ecosystem boundary

The top-level catalog may show TrustOverIP and DIF side by side, but that is only an observability convenience. It does not assert that two similarly named portfolios are equivalent, dependent or aligned.

A future cross-ecosystem seam detector should require explicit evidence such as repository references, specification citations, shared normative dependencies or other traceable relationships before presenting a cross-ecosystem claim.

## Sources for taxonomy maintenance

Taxonomy changes should be checked against current DIF material, especially:

- `https://identity.foundation/working-groups/`
- the relevant DIF working-group pages;
- working-group operating repositories; and
- repository README/work-item declarations.

The profile should follow DIF's own current structure rather than imposing TrustOverIP terminology on DIF.
