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

The initial taxonomy is grounded in DIF's published working-group/work-item structure, including active areas such as:

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

Representative mappings include:

- `universal-resolver` → Identifiers & Discovery;
- `didcomm-messaging` → DIDComm;
- `presentation-exchange` → Claims & Credentials;
- `trusted-ai-agents` → Trusted AI Agents;
- `decentralized-web-node` → Secure Data Storage / DWN; and
- `sidetree` → Sidetree / ION.

## Conservative first baseline

DIF has a large and historically diverse repository estate. The first profile therefore does **not** attempt to classify every repository by broad heuristics.

Repositories that do not match a defensible rule remain `Unclassified`. Those findings mean:

> the monitor taxonomy does not yet classify the repository.

They do not mean that the DIF repository is misconfigured, deficient or required to adopt a particular governance label.

The first generated DIF report should be treated as a taxonomy-review baseline. The most useful follow-up is to examine active `Unclassified` repositories and decide whether each should:

1. extend an existing DIF portfolio rule;
2. establish a new portfolio/category;
3. be explicitly treated as organization-wide tooling or governance;
4. remain intentionally unclassified; or
5. eventually be excluded from portfolio intelligence if it is operational noise.

## Separate retained state

DIF state is independent of TrustOverIP state:

```text
data/decentralized-identity/snapshots/
data/decentralized-identity/dispositions.json

docs/decentralized-identity/
```

A DIF run cannot overwrite TrustOverIP evidence or dispositions.

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
