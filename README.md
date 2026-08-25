# ToIP Portfolio Monitor

> An independent, evidence-backed weekly observatory for activity across the TrustOverIP GitHub organization.

The ToIP Portfolio Monitor discovers public repositories in the `trustoverip` GitHub organization, classifies them into meaningful portfolios and lifecycle states, records auditable activity evidence, and produces decision-oriented weekly reporting about material movement across the ecosystem.

This repository is independently maintained and is **not** an official Trust Over IP Foundation publication.

## Why this exists

GitHub exposes repository-by-repository activity. It does not answer organization-level questions such as:

- What materially changed across ToIP this week?
- Which specifications or workgroups are advancing?
- Where has new work appeared?
- Which repositories changed lifecycle state or require classification?
- Where are cross-portfolio dependencies or review seams emerging?
- What evidence supports each observation?

This project adds that portfolio-intelligence layer while keeping generated narrative subordinate to traceable evidence.

## Design baseline

The architecture is informed by `sankarshanmukhopadhyay/dtg-portfolio-monitor` v0.5.x, particularly its separation of collection, lifecycle-aware findings, machine-addressable assertions, provenance, decision-first reporting, bounded evidence retention, and governed review boundaries.

The ToIP monitor is **not** a larger DTG configuration. Its organization-level model adds dynamic repository discovery, portfolio classification, lifecycle classification, and explicit handling of newly discovered or unclassified repositories.

## v0.1 development baseline

The initial implementation provides:

- dynamic discovery of public repositories under `trustoverip`;
- deterministic portfolio classification for DTG, AIMWG, KERI Suite, CTWG, TSWG, EGWG, vLEI/EGF, Spec-Up, governance, and legacy deliverables;
- repository-kind and active/dormant/archived lifecycle classification;
- bounded collection of recent commits, issues, pull requests, and releases;
- per-stream collection isolation so one upstream failure does not abort the whole run;
- deterministic materiality scoring;
- machine-addressable assertions for new repositories, material changes, classification gaps, and collection failures;
- provenance in every generated snapshot;
- bounded snapshot retention;
- a decision-first weekly HTML brief and machine-readable latest JSON snapshot;
- unit tests and repository validation; and
- scheduled/manual GitHub Actions collection with static GitHub Pages deployment.

The next layer will deepen consolidated change units, cross-portfolio dependency detection, lifecycle-transition evidence, and governed finding disposition rather than adding opaque narrative generation.

## Weekly reporting model

The primary publication is a weekly organization brief with:

1. executive pulse;
2. portfolio movement;
3. specifications advancing;
4. new work and repository discovery;
5. cross-portfolio dependencies as that detector matures;
6. lifecycle movement;
7. attention-required findings; and
8. an auditable evidence register.

Collection may run more frequently than reporting in later releases; the v0.1 baseline performs a seven-day collection for each weekly brief.

## Local use

Python 3.11 or later is sufficient; the baseline collector uses only the standard library.

```bash
python -m unittest discover -s tests
python -m toip_monitor validate
GITHUB_TOKEN=... python -m toip_monitor collect --lookback-days 7
```

Generated outputs are written to:

- `data/snapshots/YYYY-MM-DD.json` — retained evidence snapshot;
- `docs/data/latest.json` — latest machine-readable state;
- `docs/reports/YYYY-Www.html` — weekly report;
- `docs/reports/latest.html` — latest report alias; and
- `docs/index.html` — GitHub Pages landing report.

## GitHub Pages operation

The `Collect and publish weekly ToIP brief` workflow can be run manually and is scheduled for Sunday 21:30 UTC. It tests first, collects and validates evidence, commits generated `data/` and `docs/` outputs when they change, and deploys `docs/` using GitHub Pages Actions.

Configure **Settings → Pages → Source: GitHub Actions**, then run the workflow once manually to establish the first baseline report.

## Evidence and interpretation boundary

Source events and repository metadata remain the evidence layer. Portfolio classification, lifecycle classification, scoring, and assertions are deterministic transformations recorded in the generated snapshot. Narrative is deliberately subordinate to those machine-readable observations.

An active repository that does not match a known portfolio rule is surfaced as `Unclassified`; it is not silently omitted. This makes organization growth and taxonomy gaps visible rather than requiring a manually maintained repository allow-list.

## Governance boundary

The monitor observes public upstream activity. It does not automatically open issues, submit comments, merge changes, or modify repositories in the TrustOverIP organization. Upstream engagement remains a human governance decision.

## Licensing

This repository uses a dual-license model:

- **Source code:** Apache License 2.0.
- **Documentation, reports, diagrams, and other non-code content:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0), unless otherwise stated.

See `LICENSE`, `LICENSE-CONTENT.md`, and `LICENSES.md` for details.
