# Tool reference

## Default grouped tools

The default `core` toolset exposes **10 tools**. Each takes an `action` and a
`payload` object.

| Tool | Actions |
|---|---|
| `phase0_ground` | scope, rules, boundaries, environment |
| `phase1_research` | docs, audits, intel, cves |
| `phase2_model` | flows, invariants, vocab, sinks, skeleton, prediction |
| `phase3_verify` | ast, sweep, prediction_diff, inventory |
| `phase4_analyze` | dimensional, reverse, state, trust, assumptions, battery, chain, seed, never_generated |
| `phase5_experiment` | sandbox, test, record, cartesian |
| `phase6_validate` | disprove, citations, classify, coverage, round_start, round_close |
| `phase6_report` | draft, generate |
| `phase6_campaign` | start, status, close |
| `phase6_report_issue` | always available |

CLI example:

```bash
python main.py 4 analyze --action dimensional --payload '{"divergence_id":"DIV-0001"}'
```

Legacy one-action-per-tool names are available with
`APEX_TOOLSET=full` (all tools) or `APEX_TOOLSET=legacy` (old names only).

## Legacy tool details

The tables below document the underlying actions. Use them to fill `payload`;
use the grouped tool name for MCP/CLI calls.

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
| `review_past_audits` | `paths` (markdown **and PDF**) | `audits` |
| `check_intel` | `keywords` (empty = family terms), `corpus_path`, `kinds` | `intel` (always includes `data/intel-patterns/`) |
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
| `ast_divergence_mapper` | `paths`, `languages`, `model_flows`, `include_tests` | `ast_map` |
| `targeted_static_sweep` | `paths`, `tools`, `semgrep_config` | `static_sweep` |
| `diff_prediction` | `flow_id`, `verdict`, `expected`, `observed`, `file`, `line` | `prediction_diff` |
| `sweep_inventory` | `rule_name`, `pattern`, `paths`, `extensions` | `sweep_inventory` |

## Phase 4 — Specialist Analysis

Most lenses require a valid `divergence_id`. `seed` / `never_generated` /
empty `run_battery` will create a synthetic `DIV-SEED-*` if none exists.

| Tool | Input highlights | Writes |
|---|---|---|
| `dimensional_checker` | `divergence_id`, `focus`, `files` | `dimensional` |
| `reverse_engineer_tool` | `divergence_id`, `artifact_paths` | `reverse_engineer` |
| `state_machine_breaker` | `divergence_id`, `target_states` | `state_machine` |
| `trust_boundary_prober` | `divergence_id`, `boundaries` | `trust_boundary` |
| `assumption_inventory` | `assumptions[]` with class, violator, primitive, cost | `assumptions` |
| `run_battery` | `battery=vault/lifecycle/boundary`, `trigger`, `checks[]`. Empty vault checks load the default share-price families and seed hypotheses. | `batteries` |
| `chain_hypotheses` | `nodes[]` with pre/post facts, `chains[]` with edges and sink | `chains` |
| `seed_from_research` | optional `divergence_id`; intel + past audits + families → hypotheses; default `fill_never_generated` | `research_seeds` (+ `gap_fill`) |
| `never_generated_check` | optional `divergence_id`, `max_generate`, `queue_g3` (default true), `max_queue` (default 32). Public/external mutators plus high-EV `_apply`/`_arm`/liquidat stems; ALL_CAPS constants dropped. Delay-bound vars (`executionWindow`, …) always injected. Mechanism templates name same-RC pairs. ABI entrypoints outrank `_` / `settlement*` helpers in the top-N G3 queue. | `gap_fill` (+ Phase 5 `experiments`) |

## Phase 5 — Experiment

| Tool | Input highlights | Writes |
|---|---|---|
| `sandbox_forge` | `service`, `out_dir` | `sandbox` |
| `invariant_tester` | `hypothesis_id`, `test_code`, `execute`, `command`, `experiment_class` (default distinguishing) | `experiments` |
| `record_experiment` | `hypothesis_id`, `verdict`, `output_path`, `experiment_class`. confirmed/refuted require a distinguishing attack, not a happy-path or code-fact check. | `experiments` |
| `queue_cartesian_g3` | `max_queue` (default 32). Writes prepared distinguishing tests for the top ranked public mutator × value-sink pairs. Never executes. | `experiments` |
| `execute_queued_g3` | `execute=true` (required), `max_run` (default 96), `include_named_open`. Exact `test_attack_<fn>_<var>` on the real pin (`harness/g3_plether`). No family fallback. Pass → `confirmed`; no test → `inconclusive`. Never submits. | `experiments` |

## Phase 6 — Validate & Report

| Tool | Input highlights | Writes |
|---|---|---|
| `disprove_finding` | `hypothesis_id`, `checks[]`, `variant` (required to kill a family hyp; kill is per-variant). Overflow/revert that freezes a value flow is not 'unreachable'. Wrong-protocol kills require an excerpt→in-scope function map. | `disproofs` |
| `verify_citations` | `phases`, `include_markdown` | `citations` |
| `classify_finding` | `hypothesis_id`, `impact`, `trigger`, `reachability`, `human_approved` | `classifications` |
| `coverage_check` | `max_gaps`. Fails closed (ratio 0) if any critical flow is unmapped. | `coverage` |
| `start_round` | `gaps[]`, `max_gaps` | `round` + `.apex/rounds/` |
| `close_round` | `round`, `outcome`, counts, `remaining_gaps` | `round` + `.apex/rounds/` |
| `close_session` | `status`, `resume_state`, `backlog[]` | `session` + death-note |
| `start_campaign` | `workspace`, `policy`, `repos`, `endpoints` | `config.json` (binds target; any phase) |
| `campaign_status` | optional `workspace` | gate progress + strict readiness (any phase) |
| `report_issue` | `kind`, `title`, `description`, `tool`, `severity`, `requested_change` | `issues` (available at any phase) |
| `draft_finding_report` | `hypothesis_id`, title, summary, intended, actual, impact, proof, recommendations | `finding_drafts` |
| `generate_report` | mirror fields, `include_theoretical` | `06_final_report.md` + `.apex/reports/` |

## Common argument forms

```bash
--repos src contracts
--repos src,contracts
--repos '["src","contracts"]'
--json '{"divergence_id":"DIV-0001"}'
--args-file args.json
```

Every MCP tool also accepts an optional `workspace` field, but the normal
workflow is to bind once with `start_campaign`:

```json
{"workspace": "/absolute/path/to/target", "policy": "standard", "repos": ["."]}
```

After that, `phase0_ground` and later grouped tools use the binding. If the
client restarts, bind again. Per-call `workspace` remains available as an
override.
