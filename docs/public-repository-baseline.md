# Public repository baseline

This record captures controls reviewed under issue #27. It is repository assurance evidence, not external certification.

| Control | State | Evidence | Residual risk |
|---|---|---|---|
| Purpose/adoption/taxonomy boundaries | PASS | `README.md`, organization profiles, docs | Monitor taxonomy is not upstream authority. |
| Licensing | PASS | `LICENSE`, `LICENSE-CONTENT.md`, `LICENSES.md` | None identified. |
| Security reporting | PASS | `SECURITY.md` | Hosted private-reporting enablement remains platform evidence. |
| Contribution/community/support | PASS | `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md`, issue/PR templates | None identified. |
| Dependency updates | PASS | `.github/dependabot.yml` | Hosted Dependabot enablement remains platform evidence. |
| Default-branch protection | EVIDENCE REQUIRED | rulesets API returned no active ruleset on 2026-09-05 | Tracked separately as a repository-setting control. |
| Tests/evidence/publication | PASS / bounded | tests, workflows, generated docs/evidence | Workflow green does not make external taxonomy claims authoritative. |
| Versioning | PASS | `VERSION` | Publication remains maintainer judgment. |

## Completion boundary

Repository-owned baseline gaps are closed by the remediation PR. Default-branch protection is a GitHub-hosted residual and is tracked separately rather than represented as PASS.
