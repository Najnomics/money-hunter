# The seven phases

Each phase answers one question and leaves one artifact. A tool from phase N
will refuse to run until every earlier gate is complete.

## Phase 0 — Ground Zero

**Question:** What are we allowed to touch, and what are the rules?

| Tool | What it does |
|---|---|
| `parse_scope` | Turns repos, endpoints, addresses, and binaries into an allowlist and detects the `TargetProfile`. |
| `set_rules` | Records stated invariants, policy, bounty rules, and severity definitions. |
| `lock_boundaries` | Records out-of-scope items, rate limits, non-destructive rules, and forbidden actions. |
| `assess_environment` | Proves the sandbox works: identity, tools, fixtures, offline limits. |

Writes `.apex/00_ground_zero.json`.

## Phase 1 — Research

**Question:** What is the system supposed to do, and what has gone wrong in
similar systems?

| Tool | What it does |
|---|---|
| `ingest_docs` | Reads specs, READMEs, and API schemas. Extracts every “must/should/never” claim and every ambiguity. |
| `review_past_audits` | Indexes past audits and known issues so the agent does not rediscover them. |
| `check_intel` | Searches the local `bugbounty-intel` corpus for comparable bug patterns. |
| `cves_intel` | Optional: queries OSV or local advisory indexes for dependency CVEs. |

Writes `.apex/01_research.json`.

## Phase 2 — Model

**Question:** What do we expect to happen, before we read the code?

| Tool | What it does |
|---|---|
| `map_state_flows` | Records actors, flows, state transitions, trust boundaries, and critical flows. |
| `define_invariants` | Records falsifiable properties that must always hold. |
| `define_state_vocabulary` | Names the variables that outlive a step. |
| `define_sinks` | Names where an attacker wants to end up. |
| `make_blind_skeleton` | Prints declarations only, so a prediction can be written without seeing bodies. |
| `record_prediction` | Stores the blind prediction, its provenance, and boundary semantics. |

Writes `.apex/02_mental_model.json`.

## Phase 3 — Verify Divergence

**Question:** Where does the implementation differ from the model?

| Tool | What it does |
|---|---|
| `ast_divergence_mapper` | Maps implementation surfaces to flows and flags missing entrypoints, missing checks, and sink-shaped functions. |
| `targeted_static_sweep` | Runs the profile’s static analysers and converts raw hits into divergence candidates. |
| `diff_prediction` | Compares a blind prediction with reality and emits a divergence. |
| `sweep_inventory` | Saves a regex rule’s hits and diffs them against the previous run. |

Writes `.apex/03_divergences.json`. Every divergence gets a `DIV-*` id.

## Phase 4 — Specialist Analysis

**Question:** Given one divergence, what is the most plausible root cause?

Every tool requires a valid `divergence_id`.

| Tool | Lens |
|---|---|
| `dimensional_checker` | Arithmetic, decimals, rates, unit conservation |
| `reverse_engineer_tool` | Bytecode, binaries, minified code |
| `state_machine_breaker` | Init order, async paths, callbacks, reentrancy |
| `trust_boundary_prober` | Inputs, auth, oracles, privilege paths |
| `assumption_inventory` | The beliefs the code silently makes |
| `run_battery` | Triggered tests: vault, lifecycle, boundary |
| `chain_hypotheses` | Joins hypotheses on state facts into multi-step chains |

Writes `.apex/04_hypotheses.json`. Every hypothesis gets an `H-*` id.

## Phase 5 — Experiment

**Question:** Can we actually make the prediction happen?

| Tool | What it does |
|---|---|
| `sandbox_forge` | Creates a local harness matching the profile. |
| `invariant_tester` | Writes and optionally executes a test. |
| `record_experiment` | Records an executed result and its captured evidence. |

Writes `.apex/05_experiments.json`. A `prepared` test is not evidence.

## Phase 6 — Validate & Report

**Question:** What survived, what is still open, and what should we do next?

| Tool | What it does |
|---|---|
| `disprove_finding` | Adversarial kill-pass for one hypothesis. |
| `verify_citations` | Resolves every `path:line` claim. |
| `classify_finding` | Derives severity from impact × trigger, capped by reachability. |
| `coverage_check` | Measures coverage and ranks open gaps. |
| `start_round` | Opens a bounded coverage round. |
| `close_round` | Records whether the round made progress. |
| `close_session` | Writes a death-note and backlog for resume. |
| `start_campaign` | Binds a target and policy once; available at any phase. |
| `campaign_status` | Shows the next phase and whether strict mode is ready. |
| `report_issue` | Records pipeline friction or a missing capability. |
| `generate_report` | Compiles the final report. |

Writes `.apex/06_final_report.md` plus metadata.

## Which tools are mandatory?

It depends on the policy:

| Phase | `light` | `standard` | `strict` |
|---|---|---|---|
| 0 | scope + rules + boundaries | same | + environment |
| 1 | docs + audits + intel | same | same |
| 2 | flows + invariants | same | + state vocab + sinks |
| 3 | ast map + static sweep | same | + predictions for critical flows |
| 4 | any one lens | same | + at least 4 assumptions |
| 5 | sandbox + one experiment | same | same |
| 6 | report | + coverage + citations | + classification of confirmed findings |

Within a phase, tools can be combined freely. Phase 4 is the most flexible: use
the lens that matches the divergence, and chain multiple lenses if useful.
