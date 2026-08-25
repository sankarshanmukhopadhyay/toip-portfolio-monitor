# ToIP Portfolio Monitor

> An independent, evidence-backed weekly observatory for activity across the TrustOverIP GitHub organization.

The ToIP Portfolio Monitor discovers public repositories in the `trustoverip` GitHub organization, classifies them into meaningful portfolios and lifecycle states, records auditable activity evidence, consolidates related activity into reviewable change units, and produces decision-oriented weekly reporting about material movement across the ecosystem.

This repository is independently maintained and is **not** an official Trust Over IP Foundation publication.

## Why this exists

GitHub exposes repository-by-repository activity. It does not answer organization-level questions such as:

- What materially changed across ToIP this week?
- Which specifications or workgroups are advancing?
- Where has new work appeared?
- Which repositories changed lifecycle state or require classification?
- Where are cross-portfolio review seams emerging?
- Which observations require attention, and what evidence supports them?

This project adds that portfolio-intelligence layer while keeping interpretation subordinate to traceable evidence.

## Design baseline

The architecture is informed by `sankarshanmukhopadhyay/dtg-portfolio-monitor` v0.5.x, particularly its separation of collection, normalization, lifecycle-aware findings, machine-addressable assertions, provenance, decision-first reporting, bounded evidence retention, and governed finding disposition.

The ToIP monitor is **not** a larger DTG configuration. Its organization-level model adds dynamic repository discovery, portfolio classification, lifecycle comparison across observations, explicit handling of newly discovered or unclassified repositories, and evidence-graded cross-portfolio review seams.

## Current development baseline

The implementation now provides:

- dynamic discovery of public repositories under `trustoverip`;
- deterministic portfolio classification for DTG, AIMWG, KERI Suite, CTWG, TSWG, EGWG, vLEI/EGF, Spec-Up, governance, and legacy deliverables;
- repository-kind and active/dormant/archived lifecycle classification;
- bounded collection of recent commits, issues, pull requests, and releases;
- correct commit timestamp normalization from GitHub commit metadata;
- per-stream collection isolation so one upstream failure does not abort the whole run;
- conservative consolidated change units over the raw evidence stream;
- comparison with the previous retained snapshot for repository lifecycle, portfolio, branch, discovery, and disappearance changes;
- explicit-reference and weaker related-co-movement cross-portfolio review seams;
- stable decision-grade findings with separate materiality, urgency, and assurance-impact dimensions;
- a governed finding disposition ledger requiring authority, rationale, timestamp, and evidence for non-open states;
- provenance in every generated snapshot and bounded snapshot retention;
- a decision-first multi-page GitHub Pages site plus machine-readable latest JSON;
- unit tests and repository validation; and
- scheduled/manual GitHub Actions collection and Pages deployment.

## GitHub Pages information architecture

The generated publication separates the decision surface from the evidence surface:

- `docs/index.html` — weekly executive overview and priority findings;
- `docs/findings.html` — stable finding register and disposition status;
- `docs/portfolios.html` — organization portfolio and repository registry;
- `docs/lifecycle.html` — state changes against the prior retained observation;
- `docs/seams.html` — evidence-graded cross-portfolio review seams;
- `docs/evidence.html` — normalized source evidence register;
- `docs/methodology.html` — interpretation and governance boundaries;
- `docs/data/latest.json` — latest complete machine-readable state; and
- `docs/data/site-manifest.json` — publication manifest and counts.

The original weekly report remains archived under `docs/reports/` while the decision-grade renderer owns the Pages landing experience.

## Local use

Python 3.11 or later is sufficient; the monitor uses only the standard library.

```bash
python -m unittest discover -s tests
python -m toip_monitor validate
GITHUB_TOKEN=... python -m toip_monitor collect --lookback-days 7
python -m toip_monitor site
```

## Weekly operation

The `Collect and publish weekly ToIP brief` workflow can be run manually and is scheduled for Sunday 21:30 UTC. It:

1. runs the test suite;
2. discovers the organization and collects seven days of evidence;
3. builds change units, lifecycle deltas, seams, and findings;
4. applies any authorized durable dispositions;
5. renders the decision-grade Pages site;
6. validates generated state;
7. commits changed `data/` and `docs/` evidence back to the repository; and
8. deploys `docs/` through GitHub Pages Actions.

Configure **Settings → Pages → Source: GitHub Actions**, then run the workflow once manually to establish the first baseline report. The first observation intentionally has no lifecycle deltas because no prior state exists; the second and later runs establish stateful comparison.

## Evidence and interpretation boundary

Raw GitHub events and repository metadata remain the evidence layer. Change units, lifecycle deltas, portfolio classification, review seams, scoring, and findings are deterministic transformations preserved in the snapshot.

An active repository that does not match a known portfolio rule is surfaced as `Unclassified`; it is not silently omitted. A cross-portfolio seam is a reason for review, not an assertion that a formal dependency exists. `explicit-reference` is stronger evidence than `related-co-movement` and the distinction remains machine-readable.

## Finding governance

Generated observations do not erase human review decisions. `data/dispositions.json` records durable finding states using stable finding IDs.

Supported states are `open`, `accepted`, `resolved`, and `suppressed`. Any non-open state must record an explicit authority, rationale, timestamp, and evidence. The monitor applies these decisions deterministically but never creates them automatically. See `docs/finding-dispositions.md`.

## Governance boundary

The monitor observes public upstream activity. It does not automatically open issues, submit comments, merge changes, or modify repositories in the TrustOverIP organization. Upstream engagement remains a human governance decision.

## Licensing

This repository uses a dual-license model:

- **Source code:** Apache License 2.0.
- **Documentation, reports, diagrams, and other non-code content:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0), unless otherwise stated.

See `LICENSE`, `LICENSE-CONTENT.md`, and `LICENSES.md` for details.
