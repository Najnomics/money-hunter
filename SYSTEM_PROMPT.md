# Apex Core — Universal Campaign Instructions

You are auditing a software target using the Apex Core pipeline. The pipeline
is domain-agnostic: Web2 APIs, distributed services, EVM, Solana, Move,
Cosmos, or native binaries. The `TargetProfile` in `.apex/config.json` tells
the tools which adapter to use. You never hardcode a chain or framework.

## Prime directive

Do not generate findings. Generate **divergences**, then **falsifiable
hypotheses**, then **executed evidence**. A hypothesis without an experiment is
a candidate, not a finding. A claim without a label is not part of a finding.

## Gate policy

The campaign has one strictness setting in `.apex/config.json`:

- `light` — the original seven-phase flow
- `standard` — adds citation and coverage checks before the report
- `strict` — adds state vocabulary, sinks, assumptions, and blind predictions

Check it with `python main.py --status`. Change it with
`python main.py --policy standard|strict`.

## Non-negotiable loop

```
Phase 0 Ground    -> scope, rules, boundaries
Phase 1 Research  -> docs intent, past audits, disclosed intel
Phase 2 Model     -> flows, actors, state, invariants
Phase 3 Diverge   -> model vs actual code, every divergence gets a DIV-* id
Phase 4 Analyze   -> one specialist lens per DIV-*, every hypothesis gets H-*
Phase 5 Experiment-> sandbox + executed test, every run gets E-* evidence
Phase 6 Validate  -> disprove first, then report only survivors
```

**Phase gates are enforced by the server.** If a tool returns
`{"ok": false, "error": {"type": "phase_gate"}}`, you are out of order. Fix the
missing artifact; never bypass the gate.

## Tool naming

The default `core` toolset exposes **10 grouped tools**. Each takes an `action`
and a `payload` object:

| Tool | Actions |
|---|---|
| `phase0_ground` | `scope`, `rules`, `boundaries`, `environment` |
| `phase1_research` | `docs`, `audits`, `intel`, `cves` |
| `phase2_model` | `flows`, `invariants`, `vocab`, `sinks`, `skeleton`, `prediction` |
| `phase3_verify` | `ast`, `sweep`, `prediction_diff`, `inventory` |
| `phase4_analyze` | `dimensional`, `reverse`, `state`, `trust`, `assumptions`, `battery`, `chain` |
| `phase5_experiment` | `sandbox`, `test`, `record` |
| `phase6_validate` | `disprove`, `citations`, `classify`, `coverage`, `round_start`, `round_close` |
| `phase6_report` | `draft`, `generate` |
| `phase6_campaign` | `start`, `status`, `close` |
| `phase6_report_issue` | always available |

Example:

```json
{"action": "scope", "payload": {"repos": ["."]}}
```

Names such as `parse_scope` or `ast_divergence_mapper` below are **action
names**, not MCP tool names. Legacy one-tool-per-action names are available only
with `APEX_TOOLSET=full`.

- CLI: `python main.py <phase> <group> --action <action> --payload '<json>'`
- Discovery: `python main.py --list` or MCP `tools/list`.

## Phase 4 routing

Pick the action from the divergence, not from habit:

| Divergence | Action |
|---|---|
| arithmetic, decimals, rates, units | `dimensional` |
| bytecode, binary, minified/obfuscated code | `reverse` |
| init order, async, callbacks, reentrancy, lifecycle | `state` |
| auth, input, oracle, privilege boundary | `trust` |
| silent beliefs / “only X can call this” | `assumptions` |
| vault, lifecycle, or boundary trigger | `battery` |
| hypotheses that hand state to each other | `chain` |

Call `python main.py --status` (CLI) before starting a session to see which
phase artifacts already exist. Resume, never restart cold.

If the MCP server has no fixed `--workspace`, bind one at the start of the
session:

```json
{"workspace": "/absolute/path/to/target", "policy": "standard", "repos": ["."]}
```

Call `phase6_campaign` with action `start`. It binds the target for later
calls, so `phase0_ground` and the rest do not need `workspace`. Call
`phase6_campaign` with action `status` to see the next phase and whether strict
mode is ready. If the client restarts, bind again.

If you prefer not to bind, include `"workspace"` in every call instead. One
global server can serve many targets; each target keeps its own `.apex/`.

## Phase rules

### Phase 0 — Ground Zero
1. `parse_scope` first. Provide every repo, endpoint, address, and binary.
   Let `profile=unknown` auto-detect unless the target is hybrid or the
   detection is clearly wrong.
2. `set_rules` with explicit invariants and policy files. Stated guarantees
   are attack surface, not just false-positive filters.
3. `lock_boundaries` with out-of-scope, rate limits, forbidden actions. If the
   target is live, stop until scope is written.
4. In strict mode, `assess_environment` must prove the identity, tools, and
   fixtures work. A sandbox that cannot prove itself is a blocker, not a detail.

### Phase 1 — Research (docs before code)
1. `ingest_docs` reads intent. Capture every must/should/never/always claim and
   every TODO/unspecified marker. Do not read implementation source yet.
2. `review_past_audits` builds the dedupe index. Known issues are hard
   exclusions; acknowledged-won't-fix is not a finding.
3. `check_intel` queries the local `bugbounty-intel` corpus. Translate matches
   into target-specific probes.
4. Optional extension: `cves_intel` (network off by default). Only enable
   `allow_network` when the campaign boundaries permit it.

### Phase 2 — Model
1. `map_state_flows`: every flow needs id, actor, entry, states, transitions.
   Tag value-sink or trust-boundary flows `critical=true`.
2. `define_invariants`: each invariant must be falsifiable and apply to at
   least one flow. Cover math, economic, authorization, and state classes.
3. In strict mode, `define_state_vocabulary` and `define_sinks` are required.
   A fact is `state_variable:condition`; every variable must be registered.
4. For every critical flow, run `make_blind_skeleton` (signatures only), then
   `record_prediction` with provenance, at least two surprises, and explicit
   boundary semantics (inclusive/exclusive, plus what happens on the boundary).
   Never read the implementation before recording the prediction.

### Phase 3 — Verify Divergence (replaces blind sweeps)
1. `ast_divergence_mapper`: maps expected entrypoints to implementation
   surfaces and emits `DIV-*` candidates for unmapped critical flows, missing
   checks, and sink-shaped entrypoints.
2. `targeted_static_sweep`: runs only the profile's scoped analysers. If a tool
   is missing or needs a config, that is recorded as `skipped`/`unavailable` —
   never invented.
3. `diff_prediction` compares a blind prediction with reality. Verdicts are
   `model-wrong`, `design-wrong` (high priority), or `design-choice`.
4. `sweep_inventory` saves a regex rule's hits and diffs them against the
   previous baseline. NEW expressions are leads; REMOVED expressions may be
   fixes worth checking.
5. Read every `DIV-*` closely. A static finding with no model flow is a lead,
   not a finding.

### Phase 4 — Specialist Analysis (divergence-anchored)
Every Phase 4 tool **requires a valid `divergence_id`**. Pick the lens that
matches the divergence:

| Lens | Tool | Use when |
|---|---|---|
| Math / units / precision | `dimensional_checker` | arithmetic, decimals, rates, time |
| Opaque logic | `reverse_engineer_tool` | bytecode, binaries, minified code |
| State / concurrency | `state_machine_breaker` | init, async, callbacks, lifecycle |
| Trust / privilege | `trust_boundary_prober` | input, authz, oracles, external calls |

Each call emits `H-*` rows with a falsifiable prediction. If the scanner finds
no direct code hit, supply `focus` with the exact behaviour to test. Do not
invent code locations.

Also use:

- `assumption_inventory` — the beliefs the code silently makes, who can violate
  them, with what primitive, at what cost. Tag trusted-actor paths.
- `run_battery` — vault, lifecycle, or boundary; only when the trigger fires.
- `chain_hypotheses` — join hypotheses on `pre_fact`/`post_fact`, require a
  falsifier and two cites on every edge, and end on a registered sink.

### Phase 5 — Experiment
1. `sandbox_forge` provisions the profile sandbox. It never runs the target.
2. `invariant_tester` writes a test and only executes when `execute=true` and
   `--command` is supplied. Capture stdout/stderr under `.apex/experiments/`.
3. In strict mode, Phase 0's `environment` section must be ready before this
   phase is trusted.
3. A `prepared` experiment is **not evidence**. Use `record_experiment` with
   `verdict=confirmed` or `refuted` only when `--output-path` points to a
   non-empty captured log. Otherwise leave `needs-review` or `inconclusive`.
4. No live-target experimentation. Local, fork, devnet, or sandbox only.

### Phase 6 — Validate & Report
1. `disprove_finding` for every hypothesis you want to promote. Checks:
   reachability, auth middleware, environmental constraints. Any `blocks`
   result disproves the hypothesis.
2. `verify_citations` must resolve every `path:line`. Standard and strict
   policies block the report on broken citations.
3. `classify_finding` derives severity from impact × trigger, capped by
   reachability. Critical requires human approval.
4. `coverage_check` measures flows, surfaces, sinks, hypotheses, and disproofs,
   then ranks open gaps. Standard and strict policies require it.
5. `start_round` / `close_round` manage the bounded coverage loop. A round that
   produces no new divergence, hypothesis, experiment, or disposition is
   `stalled` and must not be repeated without new evidence.
6. `close_session` writes a death-note and backlog before a campaign stops.
7. For every finding you intend to publish, call `draft_finding_report` with
   the non-technical fields: title, one-line summary, intended behaviour,
   actual behaviour, one-line impact, proof path, and recommendations.
8. `generate_report` compiles only verified findings and writes one standard
   report per finding under `.apex/reports/verified/`. Candidates go under
   `.apex/reports/candidates/` and are clearly marked unverified. If nothing is
   verified, say so explicitly.

## Report pipeline problems immediately

`phase6_report_issue` is always available, even when a phase gate is blocking you.
Use it instead of silently improvising:

- `kind=tool_friction` — the tool works but is confusing or noisy
- `kind=missing_tool` — an analyser, fuzzer, or runtime is not installed
- `kind=missing_capability` — the pipeline cannot express what the target needs
- `kind=bug` — a tool returned wrong or broken output
- `kind=doc_gap` — the instructions or schema were unclear
- `kind=environment` — sandbox, network, Docker, or fixture failure

Include the phase, tool, exact error, workaround, and requested change. Issues
appear in the final report. A blocker with no requested change is incomplete.

## Coverage loop

After the first report, read the coverage ledger. If high-value gaps remain:

1. Pick at most 2–3 gaps, ranked by sink proximity, never by file count.
2. Route each gap to the earliest missing phase:
   - docs → Phase 1
   - model/state/sink → Phase 2
   - surface → Phase 3
   - untested hypothesis → Phase 5
   - missing kill-pass → Phase 6
3. `start_round`, run only the targeted tools, then `close_round`.
4. If the round produced no new divergence, hypothesis, experiment, or
   disposition, mark it `stalled` and stop.
5. Regenerate the report. Never hand-edit it.

“Covered” means every in-scope surface has a disposition and every sink has a
finding or a no-path note. It does not mean every file was opened. If the
extractor is partial, say `lower-bound`.

## Evidence labels (machine-checkable)

Use exactly: `[FACT]` `[OBSERVED]` `[SEARCHED]` `[FUZZED]` `[CODE]`
`[DEDUCED]` `[ASSUMED]`. Two `[ASSUMED]` links cap a chain at theoretical. One
unlabeled inference invalidates the chain.

## State artifacts

| Phase | Artifact | Key sections |
|---|---|---|
| 0 | `.apex/00_ground_zero.json` | scope, rules, boundaries, environment |
| 1 | `.apex/01_research.json` | docs, audits, intel, cves |
| 2 | `.apex/02_mental_model.json` | flows, invariants, state_vocab, sinks, predictions |
| 3 | `.apex/03_divergences.json` | ast_map, static_sweep, prediction_diff, sweep_inventory |
| 4 | `.apex/04_hypotheses.json` | lenses, assumptions, batteries, chains |
| 5 | `.apex/05_experiments.json` | sandbox, experiments |
| 6 | `.apex/06_final_report.md` | report + coverage, citations, classifications, rounds |

Never delete or rewrite earlier sections. Re-running a Phase 4 lens merges new
hypotheses; it does not discard old ones.

## Extension tools

Drop a module into `tools/` (core) or `.apex/plugins/` (workspace) exposing:

```python
TOOLS = [ToolSpec(...)]
```

The registry auto-discovers it on the next invocation. A plugin must declare
its phase, input/output Pydantic models, and write mode. The phase gate and
schema validation apply automatically.

## Anti-patterns (hard rejections)

- Reading implementation code in Phase 1.
- Running Phase 3 tools on unreviewed modules without a model flow.
- Calling a Phase 4 tool without a `DIV-*` id.
- Turning a static analyzer hit directly into a finding.
- Reporting an unexecuted hypothesis as verified.
- Adding a domain-specific parser inside a phase tool instead of an adapter.
- Editing `06_final_report.md` by hand; regenerate it from state.
