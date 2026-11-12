# State, gates, and the three policies

## The case file: `.apex/`

Every target keeps its campaign state in `.apex/` inside the target folder.

```
.apex/
  config.json               TargetProfile + gate policy + timestamps
  00_ground_zero.json       scope, rules, boundaries, environment
  01_research.json          docs, audits, intel, cves
  02_mental_model.json      flows, invariants, state vocab, sinks, predictions
  03_divergences.json       ast map, static sweep, prediction diffs, inventories
  04_hypotheses.json        hypotheses, assumptions, batteries, chains
  05_experiments.json       sandbox, experiments
  06_final_report.md        report
  06_report_meta.json       coverage, citations, classifications, rounds, session
  predictions/              blind skeletons and prediction markdown
  reports/                  index + one standard report per finding
  experiments/              generated tests and captured logs
  sandbox/                  provisioned harnesses
  sweep/                    saved inventory files
  rounds/                   one JSON file per coverage round
  tool-runs.jsonl           append-only audit log of tool calls
  plugins/                  optional workspace extensions
```

Nothing is stored in the agent’s memory. A new session reads the files and
resumes.

## What a gate is

A gate is a checklist. A tool in phase N may run only when every earlier gate is
complete. Gates are based on **artifacts**, not on the agent saying “I did it.”

Example error:

```json
{
  "ok": false,
  "error": {
    "type": "phase_gate",
    "phase": 2,
    "missing": ["section:invariants"]
  }
}
```

The fix is to run the missing tool, not to edit JSON by hand.

## The three policies

The policy is stored in `.apex/config.json` and can be changed at any time:

```bash
python main.py --policy light   --workspace /target
python main.py --policy standard --workspace /target
python main.py --policy strict  --workspace /target
```

### `light`

The original seven-phase flow. Good for small targets or a quick first pass.

### `standard` (default)

Adds two Phase 6 requirements:

- `coverage_check` must have measured coverage
- `verify_citations` must have resolved every `path:line` citation

This prevents “looks complete” reports with broken evidence.

### `strict`

Adds the deeper campaign machinery:

- Phase 0 must have `assess_environment`
- Phase 2 must have `state_vocab` and `sinks`
- Phase 3 must have a blind prediction for every critical flow
- Phase 4 must have at least four assumption rows
- Phase 6 must classify every confirmed experiment

Use strict for serious contests and multi-session hunts.

## Citations

A citation is `path:line` or `path:line-range`, for example:

```text
src/withdraw.py:42
contracts/Vault.sol:118-126
docs/SPEC.md:7
```

The citation must:

- point inside the target workspace
- point at a file that exists
- point at a line that exists

`verify_citations` checks all of them. `standard` and `strict` block the report
while any citation is broken.

## Severity is arithmetic

No free-text severity. Every classification uses two axes:

| Impact | Meaning |
|---|---|
| `T` | value or data taken/corrupted |
| `F+` | permanent freeze |
| `F-` | temporary freeze |
| `C` | correctness only |

| Trigger | Meaning |
|---|---|
| `A` | anyone, anytime |
| `K` | anyone, conditional |
| `R+` | role the attacker can acquire |
| `R-` | role the attacker cannot acquire |

`unverified` reachability caps severity at medium. `critical` requires
`human_approved: true`. The matrix lives in `validation.py`, so every tool uses
the same rules.

## Resume and death notes

Long campaigns die from quotas, context limits, or infrastructure. `close_session`
writes:

- `.apex/death-note.md` — what stopped, exact resume state, remaining gaps
- `.apex/backlog.md` — every untested idea with a next action

A later session reads those files first. A campaign should never restart cold.
