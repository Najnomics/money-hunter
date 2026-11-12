# Tool reference

Every tool is available in two forms:

- MCP: `phase0_parse_scope`
- CLI: `python main.py 0 parse_scope --key value`

Run `python main.py --list` to print the live list.

## Phase 0 — Ground Zero

| Tool | Input highlights | Writes |
|---|---|---|
| `parse_scope` | `repos`, `endpoints`, `addresses`, `binaries`, `profile` | `scope` |
| `set_rules` | `invariants`, `policy_files`, `bounty_url` | `rules` |
| `lock_boundaries` | `out_of_scope`, `rate_limits`, `forbidden_actions` | `boundaries` |
| `assess_environment` | `checks[]` with `kind=identity/tool/fixture`, `offline_limits` | `environment` |

## Phase 1 — Research

| Tool | Input highlights | Writes |
|---|---|---|
| `ingest_docs` | `paths` | `docs` |
| `review_past_audits` | `paths` | `audits` |
| `check_intel` | `keywords`, `corpus_path`, `kinds` | `intel` |
| `cves_intel` | `packages[]`, `allow_network` | `cves` |

## Phase 2 — Model

| Tool | Input highlights | Writes |
|---|---|---|
| `map_state_flows` | `actors`, `flows`, `state_variables` | `flows` |
| `define_invariants` | `invariants[]` | `invariants` |
| `define_state_vocabulary` | `states[]` with `var`, `file` | `state_vocab` |
| `define_sinks` | `sinks[]` with `id`, `var` or `vars` + `expr` | `sinks` |
| `make_blind_skeleton` | `flow_id`, `paths` | `skeletons` |
| `record_prediction` | `flow_id`, `provenance`, `expected`, `surprises[]`, `boundary_semantics` | `predictions` |

## Phase 3 — Verify Divergence

| Tool | Input highlights | Writes |
|---|---|---|
| `ast_divergence_mapper` | `paths`, `languages`, `model_flows` | `ast_map` |
| `targeted_static_sweep` | `paths`, `tools`, `semgrep_config` | `static_sweep` |
| `diff_prediction` | `flow_id`, `verdict`, `expected`, `observed`, `file`, `line` | `prediction_diff` |
| `sweep_inventory` | `rule_name`, `pattern`, `paths`, `extensions` | `sweep_inventory` |

## Phase 4 — Specialist Analysis

Every tool requires a valid `divergence_id`.

| Tool | Input highlights | Writes |
|---|---|---|
| `dimensional_checker` | `divergence_id`, `focus`, `files` | `dimensional` |
| `reverse_engineer_tool` | `divergence_id`, `artifact_paths` | `reverse_engineer` |
| `state_machine_breaker` | `divergence_id`, `target_states` | `state_machine` |
| `trust_boundary_prober` | `divergence_id`, `boundaries` | `trust_boundary` |
| `assumption_inventory` | `assumptions[]` with class, violator, primitive, cost | `assumptions` |
| `run_battery` | `battery=vault/lifecycle/boundary`, `trigger`, `checks[]` | `batteries` |
| `chain_hypotheses` | `nodes[]` with pre/post facts, `chains[]` with edges and sink | `chains` |

## Phase 5 — Experiment

| Tool | Input highlights | Writes |
|---|---|---|
| `sandbox_forge` | `service`, `out_dir` | `sandbox` |
| `invariant_tester` | `hypothesis_id`, `test_code`, `execute`, `command` | `experiments` |
| `record_experiment` | `hypothesis_id`, `verdict`, `output_path` | `experiments` |

## Phase 6 — Validate & Report

| Tool | Input highlights | Writes |
|---|---|---|
| `disprove_finding` | `hypothesis_id`, `checks[]` | `disproofs` |
| `verify_citations` | `phases`, `include_markdown` | `citations` |
| `classify_finding` | `hypothesis_id`, `impact`, `trigger`, `reachability`, `human_approved` | `classifications` |
| `coverage_check` | `max_gaps` | `coverage` |
| `start_round` | `gaps[]`, `max_gaps` | `round` + `.apex/rounds/` |
| `close_round` | `round`, `outcome`, counts, `remaining_gaps` | `round` + `.apex/rounds/` |
| `close_session` | `status`, `resume_state`, `backlog[]` | `session` + death-note |
| `report_issue` | `kind`, `title`, `description`, `tool`, `severity`, `requested_change` | `issues` (available at any phase) |
| `generate_report` | mirror fields, `include_theoretical` | `06_final_report.md` |

## Common argument forms

```bash
--repos src contracts
--repos src,contracts
--repos '["src","contracts"]'
--json '{"divergence_id":"DIV-0001"}'
--args-file args.json
```

Every MCP tool also accepts an optional `workspace` field. Use it when one
global MCP server serves multiple targets:

```json
{"workspace": "/absolute/path/to/target", "repos": ["."]}
```
