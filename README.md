# Trust Ecosystem Monitor

> An independent, evidence-backed observatory for GitHub-based trust ecosystems.

Trust Ecosystem Monitor discovers repositories from configured organization profiles, classifies them into ecosystem-specific portfolios and lifecycle states, records auditable GitHub activity evidence, consolidates related activity into reviewable change units, and publishes decision-oriented weekly reporting.

It is independently maintained. Monitoring an ecosystem does **not** make this project an official publication of that ecosystem.

## Monitored ecosystems

The current profiles are:

- **Trust Over IP Foundation** — `organizations/trustoverip/profile.toml`
- **Decentralized Identity Foundation (DIF)** — `organizations/decentralized-identity/profile.toml`

Each ecosystem retains its own taxonomy, snapshots, dispositions and generated report tree. One ecosystem run cannot overwrite another.

## Why this exists

GitHub exposes repository-level activity. It does not naturally answer portfolio questions such as:

- What materially changed across an ecosystem this week?
- Which specifications, workgroups or implementations are advancing?
- Where has new work appeared?
- Which repositories changed lifecycle state?
- Which repositories are not yet classified by the monitor taxonomy?
- Where are cross-portfolio review seams emerging?
- Which observations require attention, and what evidence supports them?

The monitor adds this portfolio-intelligence layer while keeping interpretation subordinate to traceable evidence.

## Architecture

```text
Trust Ecosystem Monitor
        │
        ├── organization profile
        │     ├── GitHub organization
        │     ├── display metadata
        │     └── ordered portfolio taxonomy
        │
        ├── organization-neutral collector
        ├── change-unit and lifecycle analysis
        ├── findings + governed dispositions
        └── profile-scoped publication

organizations/
├── trustoverip/profile.toml
└── decentralized-identity/profile.toml

data/
├── trustoverip/
│   ├── snapshots/
│   └── dispositions.json
└── decentralized-identity/
    ├── snapshots/
    └── dispositions.json

docs/
├── index.html                 # ecosystem catalog
├── ecosystems.json            # machine-readable catalog
├── trustoverip/               # ToIP report surface
└── decentralized-identity/    # DIF report surface
```

The original pre-multi-profile ToIP state under `data/snapshots/` is treated as a legacy migration seed. The first scoped ToIP collection carries that history forward rather than resetting lifecycle comparison.

## Evidence model

The monitor keeps several layers distinct:

1. **Raw evidence** — repository metadata, commits, issues, pull requests and releases from the GitHub REST API.
2. **Change units** — conservative consolidation of related activity so a single work item is not represented as unrelated noise.
3. **Lifecycle deltas** — changes against the immediately preceding retained observation for the same ecosystem.
4. **Review seams** — evidence-graded reasons to inspect activity across portfolio boundaries. A seam is not automatically a formal dependency.
5. **Findings** — stable observations with separate materiality, urgency and assurance-impact dimensions.
6. **Dispositions** — explicit maintainer decisions such as `accepted`, `resolved` or `suppressed`, with authority, rationale, timestamp and evidence.

Historical `toip-*` stable identifiers are intentionally preserved where they already exist. They are an identifier namespace, not the current product name; rewriting them would break dispositions and longitudinal references.

## Classification boundary

Portfolio taxonomy is profile-specific and deterministic. The first matching rule wins.

A repository that does not match a profile rule remains **`Unclassified`**. This means the monitor taxonomy does not yet classify the repository. It does **not** imply a defect, governance failure or obligation in the upstream project.

The initial DIF profile is deliberately conservative. It is grounded in DIF's working-group/work-item structure and is expected to improve through review of the first real baseline rather than through speculative classification.

See `docs/organization-profiles.md` and `docs/dif-onboarding.md`.

## Local use

Python 3.11 or later is sufficient; the monitor uses the standard library.

Run tests and source validation:

```bash
python -m unittest discover -s tests
python -m trust_ecosystem_monitor validate
```

Collect one ecosystem:

```bash
GITHUB_TOKEN=... python -m trust_ecosystem_monitor collect \
  --profile organizations/trustoverip/profile.toml \
  --lookback-days 7
```

or:

```bash
GITHUB_TOKEN=... python -m trust_ecosystem_monitor collect \
  --profile organizations/decentralized-identity/profile.toml \
  --lookback-days 7
```

Render the top-level catalog after one or more profile runs:

```bash
python -m trust_ecosystem_monitor site
```

Validate that every configured profile has current generated evidence:

```bash
python -m trust_ecosystem_monitor validate --require-generated
```

The former `toip-monitor` / `toip_monitor` entry points remain temporary compatibility aliases; new usage should use the canonical Trust Ecosystem Monitor names.

## Weekly operation

The **Collect and publish weekly ecosystem briefs** workflow runs manually or on Sunday at 21:30 UTC. It:

1. runs the test suite;
2. collects TrustOverIP into its scoped state/report tree;
3. collects DIF into its scoped state/report tree;
4. renders the top-level ecosystem catalog;
5. validates current generated state for every configured profile;
6. commits changed `data/` and `docs/` evidence; and
7. deploys `docs/` through GitHub Pages Actions.

The workflow uses current Node.js 24-capable major versions of the first-party Actions used directly by this repository.

## Pages information architecture

The root Pages site is a catalog of monitored ecosystems. Each ecosystem report then exposes its own decision and evidence surfaces:

- `index.html` — weekly executive overview;
- `findings.html` — stable finding register and disposition state;
- `portfolios.html` — portfolio/repository registry;
- `lifecycle.html` — state changes against the prior retained observation;
- `seams.html` — evidence-graded cross-portfolio review seams;
- `evidence.html` — normalized source evidence;
- `methodology.html` — method and interpretation boundaries;
- `data/latest.json` — complete machine-readable current state.

## Cross-ecosystem boundary

ToIP and DIF appearing in the same catalog does **not** establish a relationship between them. Cross-ecosystem dependency, convergence or standards-seam analysis is a separate capability and should only be added when supported by explicit evidence.

## Governance boundary

The monitor observes public upstream activity. It does not automatically open issues, submit comments, merge changes or modify monitored upstream repositories. Upstream engagement remains a human governance decision.

## Licensing

This repository uses a dual-license model:

- **Source code:** Apache License 2.0.
- **Documentation, reports, diagrams and other non-code content:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0), unless otherwise stated.

See `LICENSE`, `LICENSE-CONTENT.md`, and `LICENSES.md`.
