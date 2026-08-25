# Trust Ecosystem Monitor

> An independent, evidence-backed observatory for GitHub-based trust ecosystems.

Trust Ecosystem Monitor discovers repositories through organization profiles, classifies them into ecosystem-specific portfolios and lifecycle states, records auditable activity evidence, consolidates related activity into reviewable change units, and publishes decision-oriented weekly reporting about material movement.

The monitor is independently maintained. It is not an official publication of any monitored organization.

## Why this exists

GitHub exposes repository-by-repository activity. It does not naturally answer ecosystem-level questions such as:

- What materially changed this week?
- Which specifications, workgroups, or implementation efforts are advancing?
- Where has new work appeared?
- Which repositories changed lifecycle state or still need monitor-side classification?
- Where are cross-portfolio review seams emerging?
- Which observations require attention, and what evidence supports them?

This project adds that portfolio-intelligence layer while keeping interpretation subordinate to traceable evidence.

## Current monitored ecosystem

The first organization profile is TrustOverIP:

```text
organizations/trustoverip/profile.toml
```

It defines the `trustoverip` GitHub organization and the ordered portfolio rules for DTG, AIMWG, KERI Suite, CTWG, TSWG, EGWG, vLEI/EGF, Spec-Up, governance, legacy deliverables, and explicit `Unclassified` fall-through.

TrustOverIP-specific taxonomy and disclaimers belong to that profile. They are no longer the identity of the monitor itself.

A Decentralized Identity Foundation profile is planned as the next ecosystem onboarding step. It will be grounded in DIF's own working-group and work-item lifecycle model rather than cloning the TrustOverIP taxonomy.

## Architecture

The architecture is informed by `sankarshanmukhopadhyay/dtg-portfolio-monitor` v0.5.x, particularly its separation of collection, normalization, lifecycle-aware findings, machine-addressable assertions, provenance, decision-first reporting, bounded evidence retention, and governed finding disposition.

Trust Ecosystem Monitor adds an organization-profile boundary above that machinery:

```text
organization profile
      |
      v
repository discovery + taxonomy
      |
      v
normalized evidence
      |
      +--> change units
      +--> lifecycle deltas
      +--> cross-portfolio review seams
      +--> stable findings + dispositions
      |
      v
weekly Pages + machine-readable evidence
```

The profile carries organization identity, report metadata, disclaimer text, and ordered portfolio rules. The engine owns collection and evidence semantics; profiles own ecosystem-specific interpretation inputs.

See `docs/organization-profiles.md`.

## Current capabilities

The implementation provides:

- profile-selected discovery of public GitHub organization repositories;
- externally configured deterministic portfolio classification;
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
- profile compatibility tests that prevent silent taxonomy drift; and
- scheduled/manual GitHub Actions collection and Pages deployment.

## Canonical package and CLI

The canonical Python package is:

```text
trust_ecosystem_monitor
```

The canonical command is:

```bash
trust-ecosystem-monitor
```

During the rename transition, the former `toip_monitor` import path and `toip-monitor` console command remain as compatibility aliases. New integrations should use the canonical names.

Local operation:

```bash
python -m unittest discover -s tests
python -m trust_ecosystem_monitor validate
GITHUB_TOKEN=... python -m trust_ecosystem_monitor collect --lookback-days 7
python -m trust_ecosystem_monitor site
```

To select a profile explicitly:

```bash
GITHUB_TOKEN=... python -m trust_ecosystem_monitor collect \
  --profile organizations/trustoverip/profile.toml \
  --lookback-days 7
```

Python 3.11 or later is sufficient; the monitor uses only the standard library, including `tomllib` for organization profiles.

## GitHub Pages information architecture

The generated publication separates the decision surface from the evidence surface:

- `docs/index.html` — weekly executive overview and priority findings;
- `docs/findings.html` — stable finding register and disposition status;
- `docs/portfolios.html` — ecosystem portfolio and repository registry;
- `docs/lifecycle.html` — state changes against the prior retained observation;
- `docs/seams.html` — evidence-graded cross-portfolio review seams;
- `docs/evidence.html` — normalized source evidence register;
- `docs/methodology.html` — interpretation and governance boundaries;
- `docs/data/latest.json` — latest complete machine-readable state; and
- `docs/data/site-manifest.json` — publication manifest and counts.

The selected profile supplies the monitored organization and ecosystem-specific disclaimer. The product shell remains Trust Ecosystem Monitor.

## Weekly operation

The `Collect and publish weekly ecosystem brief` workflow can be run manually and is scheduled for Sunday 21:30 UTC. It currently defaults to the TrustOverIP profile and:

1. runs the test suite, including profile compatibility checks;
2. loads the selected organization profile;
3. discovers the organization and collects seven days of evidence;
4. builds change units, lifecycle deltas, seams, and findings;
5. applies any authorized durable dispositions;
6. renders the decision-grade Pages site using the canonical project identity plus profile-specific context;
7. validates generated state;
8. commits changed `data/` and `docs/` evidence back to the repository; and
9. deploys `docs/` through GitHub Pages Actions.

## Compatibility and evidence continuity

The project was originally bootstrapped as `toip-portfolio-monitor`. The repository was renamed after organization discovery and taxonomy were externalized behind profiles.

The rename does **not** rewrite historical evidence. In particular, existing stable `toip-*` assertion/finding IDs are retained as a historical identifier namespace so durable dispositions and longitudinal references do not break. New project branding does not invalidate previously recorded evidence.

The TrustOverIP profile compatibility contract compares profile-derived classifications with the retained ToIP snapshot. A mismatch fails CI, making taxonomy changes explicit review decisions rather than accidental consequences of engine refactoring.

## Evidence and interpretation boundary

Raw GitHub events and repository metadata remain the evidence layer. Change units, lifecycle deltas, portfolio classification, review seams, scoring, and findings are deterministic transformations preserved in the snapshot.

An active repository that does not match a known portfolio rule is surfaced as `Unclassified`; it is not silently omitted. This means the **monitor taxonomy** has not yet classified the repository. It does not imply a defect or obligation in the upstream repository.

A cross-portfolio seam is a reason for review, not an assertion that a formal dependency exists. `explicit-reference` is stronger evidence than `related-co-movement`, and the distinction remains machine-readable.

## Finding governance

Generated observations do not erase human review decisions. `data/dispositions.json` records durable finding states using stable finding IDs.

Supported states are `open`, `accepted`, `resolved`, and `suppressed`. Any non-open state must record an explicit authority, rationale, timestamp, and evidence. The monitor applies these decisions deterministically but never creates them automatically. See `docs/finding-dispositions.md`.

## Governance boundary

The monitor observes public upstream activity. It does not automatically open issues, submit comments, merge changes, or modify repositories in monitored organizations. Upstream engagement remains a human governance decision.

## Licensing

This repository uses a dual-license model:

- **Source code:** Apache License 2.0.
- **Documentation, reports, diagrams, and other non-code content:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0), unless otherwise stated.

See `LICENSE`, `LICENSE-CONTENT.md`, and `LICENSES.md` for details.
