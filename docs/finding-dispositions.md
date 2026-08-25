# Finding dispositions

The monitor regenerates observations, but review decisions should remain durable.

`data/dispositions.json` is therefore the governed ledger for finding lifecycle decisions. Entries are keyed by the stable `finding_id` generated from the finding category, subject, and evidence key.

Supported states are:

- `open` — no disposition has been made;
- `accepted` — the observation is understood and intentionally accepted;
- `resolved` — the underlying condition has been addressed; and
- `suppressed` — the finding should not be presented as actionable under the recorded rationale.

Any non-open disposition must record all of the following:

```json
{
  "finding_id": "toip-finding-...",
  "status": "resolved",
  "authority": "maintainer or named review authority",
  "rationale": "why this disposition is justified",
  "timestamp": "2026-08-25T00:00:00Z",
  "evidence": ["https://example.org/review-evidence"]
}
```

The monitor applies the ledger deterministically when generating a new snapshot. It does not infer or auto-authorize dispositions.

This boundary is intentional: collection and analysis may be automated, but accepting, resolving, or suppressing a finding is a governance decision.
