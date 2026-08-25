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

The initial architecture is informed by `sankarshanmukhopadhyay/dtg-portfolio-monitor` v0.5.x, particularly its separation of collection, normalization, lifecycle-aware findings, machine-addressable assertions, provenance, decision-first reporting, bounded evidence retention, and governed finding disposition.

The ToIP monitor is **not** a larger DTG configuration. Its organization-level model adds dynamic repository discovery, portfolio classification, lifecycle classification, and explicit handling of newly discovered or unclassified repositories.

## Intended reporting model

The primary publication is a weekly organization brief with:

1. executive pulse;
2. portfolio movement;
3. specifications advancing;
4. new work and repository discovery;
5. cross-portfolio dependencies;
6. lifecycle movement;
7. attention-required findings; and
8. an auditable evidence register.

Collection may run more frequently than reporting so weekly outputs can be generated from incremental evidence without becoming a noisy activity feed.

## Governance boundary

The monitor observes public upstream activity. It does not automatically open issues, submit comments, merge changes, or modify repositories in the TrustOverIP organization. Upstream engagement remains a human governance decision.

## Status

Initial build-out is underway. The first development milestone is a reproducible organization-discovery and weekly-reporting baseline suitable for GitHub Pages.

## Licensing

This repository uses a dual-license model:

- **Source code:** Apache License 2.0.
- **Documentation, reports, diagrams, and other non-code content:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0), unless otherwise stated.

See `LICENSE`, `LICENSE-CONTENT.md`, and `LICENSES.md` for details.
