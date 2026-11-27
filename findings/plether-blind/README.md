# Plether blind campaign (phase 1)

Apex-core 1.1.0 + boss-skill hunts on the Immunefi Plether pin, **without reading contest finding bodies**.

| | |
|---|---|
| Repo | https://github.com/immunefi-team/audit-comp-plether |
| Commit | `a82d4fefb02768e5b3bddcc97dee371eee24fea8` |
| Policy | `strict` |
| Verified findings | **0** |
| Live G1 leads | L-CH-001, L-CH-002 (PoCs queued, not executed) |

## Files

| File | What |
|---|---|
| [SCOPE.md](SCOPE.md) | Contest scope, repo, commit, OOS, severity. No finding bodies. |
| [PIPELINE.md](PIPELINE.md) | Phases 0–6 and hunter passes as actually run. |
| [LEDGER.md](LEDGER.md) | Every lead, including G1–G4 kills. |
| [POC-QUEUE.md](POC-QUEUE.md) | Precise PoC specs for a Composer agent. **No PoC code here.** |
| [ISSUES.md](ISSUES.md) | Pipeline ISS-* (matching, slither cap, missing tools). |
| [hunters/](hunters/) | Raw L-CH / L-OR / L-LP JSON (keep/kill + reasons). |
| [campaign/](campaign/) | Copy of `.apex/06_final_report.md`, death-note, backlog, reports index. |
| [slither-high-medium.csv](slither-high-medium.csv) | Independent slither High/Medium (apex sweep admitted 0). |

Phase 2 (fetch 69 Immunefi reports into `findings/plether-key/` and classify) starts only after this directory is committed.
