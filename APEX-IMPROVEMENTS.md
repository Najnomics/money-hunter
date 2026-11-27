# Apex improvements after the Plether blind miss

Blind campaign: **0 verified findings**. Official unique paid findings: **63** (18C / 10H / 11M / 24L). Operator “69” is not a published unique-finding total. See `findings/plether-key/CLASSIFICATION.md`.

Root causes ranked by impact on that miss. Items 1–10 are on `cursor/recall-fixes-f6d2`. Items 11–15 landed on `cursor/recall-fixes-2-f6d2`. Items 16–18 (this branch, `cursor/recall-fixes-3`) harden 11–15 against the **real Blind2 kill language** and close the remaining 42 pair-only + 1 never-generated misses. Mapping: `findings/plether-blind3/FIXES.md`.

## Honest caveat (read this before re-running Plether)

The hunter families, bundled `data/intel-patterns/` cards, and default vault battery were **derived from the Plether unique paid set and then rewritten as protocol-agnostic patterns**. After this patch, a Plether re-run is **not a clean recall measurement**: the harness now contains the answer-key families (NAV vs reclaimable receipts, delayed-order optionality, share-supply overflow, HWM/recap, oracle watermark/calendar, false emergency mode). Use a *different* contest to measure recall. Plether remains useful as a regression fixture for matcher/slither/coverage bugs, not as a blinded score.

## 1. Hunter hypothesis space never included the winning families (impact: 62/63 never generated)

**Cause.** Boss-skill hunts asked “can X steal Y?” on CH / orders / pool and killed 43/45 leads. They never generated: refundable receipts in share price, delayed-order optionality after the price print, share-supply overflow, recap/HWM/unassigned buckets, oracle watermark/calendar, false degraded/emergency-mode via a hedged pair.

**Fix (this branch).** `tools/protocol_families.py` ships six protocol-agnostic families (no protocol-specific type or function names). `SYSTEM_PROMPT.md` requires them. Empty `run_battery` vault checks and `seed_from_research` emit them. A Gate 1 kill of a *nearby* hypothesis is not coverage.

**Still outside this repo.** Expanding boss-skill YAML. A separate Composer still has to run PoCs (`findings/plether-blind/POC-QUEUE.md`).

## 2. AST / skeleton matching used ABI types, so Phase 3 mapped 0 of 8 critical flows

**Cause.** `_match_surfaces` split on the last `(` token, so `depositFor(address,uint256)` became `uint256`. All critical flows emitted `unmapped_critical_flow`. `make_blind_skeleton` fell back to the first N surfaces (alphabetically OOS `CfdClosePreview.sol`).

`entry_token()` in `tools/_shared.py` already stripped types correctly; Phase 3 did not call it.

**Fix (this branch).** `_match_surfaces` and `make_blind_skeleton` use `entry_token`. Skeleton no longer falls back to unrelated files. Tests in `tests/test_entry_match.py`.

## 3. Slither stdout cap 2MB + rc 255 → 0 static DIVs

**Cause.** `fsutil.run_command` truncated stdout at 2e6 bytes; slither `--json -` exceeded it; parse returned `[]`. Slither exits 255 when detectors fire; sweep treated only 0/1 as `ran`.

Independent dump: 188 detectors, none of which were unique paid chiefs — so this is **not** why 97591 was missed, but it zeroes Phase 3 static recall on every large Solidity target.

**Fix (this branch).** EVM slither writes `--json {json_out}` under `.apex/sweep/`. Parser reads that file (up to 50MB). rc 255 counts as `ran`. Tests cover json-out argv and detector parse.

## 4. `undocumented_entrypoint` noise (`settle` ⊂ `settlementAsset`) and cap 50

**Cause.** Sink-word regex matched getters (`settlementAsset`, `onlyAdmin`). Cap 50 hid the rest of the ABI, including real mutators.

**Fix (this branch).** Cap 200; skip `only*` / `get*` / `preview*` / `settlementAsset|Token|Sidecar`.

## 5. Phase 4 lenses bound to `constructor(` instead of the DIV line

**Cause.** `scan_files` returned the first regex hit in file order. `STATE_PATTERNS` includes `constructor`, so hypotheses for DIV-0067 cited line 139.

**Fix (this branch).** `scan_files(..., prefer_file, prefer_line)` ranks hits by distance to the divergence cite.

## 6. Known-issue over-kill (1/63: LOW-97602)

**Cause.** L-OR-011 described scheduled treasury activation changing `currentExecutionConfigHash` and **killed it as documented ConfigMismatch**. That exact unique Low paid.

**Fix (this branch).** Phase 1 instructions: documented limitations stay live unless the **program page** lists them OOS. SECURITY.md mentioning a mechanism is not a kill.

## 7. Gate 3 with execute=false cannot promote anything

**Cause.** By design, verified findings need executed logs. Operator instruction was “do not write PoCs.” Result: 0 verified even for L-CH-001/002.

**Fix.** Not a code change. Queue remains `findings/plether-blind/POC-QUEUE.md`. Do not weaken Gate 3.

## 8. Intel corpus + PDF past-audit ingest feeding hypothesis generation

**Cause.** `check_intel` returned 0 when `bugbounty-intel` was missing. `review_past_audits` skipped PDFs. Intel matches never became hypotheses.

**Fix (this branch).**

- Bundled corpus at `data/intel-patterns/` (INDEX, techniques.md, six pattern cards). `check_intel` always scans it; empty keywords default to family terms. Optional external `bugbounty-intel` still overlays when present.
- `review_past_audits` walks `.pdf` and extracts text via `pdftotext`, `pypdf`, or a zlib/literal-string fallback (`tools/pdftext.py`). Findings carry an `excerpt` for seeding.
- New Phase 4 action `seed` (`seed_from_research`) turns intel matches, past-audit findings, and protocol families into `H-*` rows (creates `DIV-SEED-*` if Phase 3 is empty).

Would have helped known-issue indexing more than 97591 specifically; together with item 1 it now generates the missing families.

## 9. Default vault/share-price battery

**Cause.** `run_battery` only recorded analyst-supplied checks. No default trigger for refundable receipts in NAV, overflow, HWM/recap, delayed-order optionality, oracle staleness, or false emergency mode.

**Fix (this branch).** Empty `checks` on `battery=vault` loads all six protocol-agnostic family checks (inconclusive until an experiment fires) and seeds matching hypotheses. `lifecycle` / `boundary` batteries load the families tagged for those triggers. Families are worded without protocol-specific names.

## 10. Coverage fails closed when any critical flow is unmapped

**Cause.** `coverage_check` treated any divergence with a `flow_id` as covering that flow. `unmapped_critical_flow` stubs produced “8/14 flows covered (57%)” while 0 critical flows mapped.

**Fix (this branch).** Unmapped-kind DIVs do not count. If any critical flow lacks a real AST mapping (or a non-unmapped divergence), ratio = 0, confidence = `fail-closed`, `summary.fail_closed = 1`. The report prints the fail-closed banner. Tests in `tests/test_coverage.py`.

## Never-generated self-check (cross-cutting)

**Cause.** 62/63 unique chiefs were never even hypothesized. Coverage of “we looked at CH” is not coverage of `redeem × sharePrice`.

**Fix (this branch).** After hypothesis generation, `never_generated_check` (also the default tail of `seed`) enumerates each state-changing external function × each value-bearing state var. If no hypothesis mentions both tokens, it generates one. Leftover pairs and a skipped self-check are high-EV coverage gaps. Item 14 tightens this to public/external mutators and auto-queues G3.

## 11. G4 must not kill overflow/revert as 'unreachable' when the revert blocks a value flow

**Cause.** Blind2 G4 killed the share-supply overflow family because a cap/revert was labelled unreachable. The revert *is* the impact: deposits, redemptions, or settlement freeze (Immunefi F+/F-).

**Fix (this branch).** `disprove_finding` ignores BLOCKS checks that use unreachable language against a freeze/overflow hypothesis. Freeze = impact. Tests in `tests/test_recall_gates.py`.

## 12. G3 must run the distinguishing attack PoC, never the happy path

**Cause.** Gate 3 treated a solvent round-trip, a seeded fixture, or a natspec/code-fact read as a pass or kill. Those do not distinguish the attack from intended behaviour.

**Fix (this branch).** `record_experiment` confirms or refutes only when `experiment_class` (inferred from observation/command/log, not just the label) is `distinguishing`: attacker path, adversarial ordering, first-tick/zero-state. Happy-path and code-fact raise. Unknown class is inconclusive, not a pass/kill. Default invariant scaffolds are distinguishing attacks, not `assert True`.

## 13. Family-level G4 kills apply per variant, not per family

**Cause.** One G4 kill of H-0001 (mint-to-pool analog) or H-0002 (overflow) closed the whole family. Other public mutators in the same family stayed untested.

**Fix (this branch).** Family hypotheses require `variant=<public mutator or pair>` to kill. The verdict is `disproved-variant` (scope=`variant`); the family stays open. Missing variant → `needs-variant`. Coverage emits `GAP-VARIANT-*`. `generate_report` only drops a hyp on a family-wide `disproved`.

## 14. Rank cartesian public/external mutators × value sinks; drop `_` internals; auto-queue top-N G3 tests

**Cause.** The cartesian included `_` helpers and ALL_CAPS immutables, exploding pair count and burying the real ABI. Pairs were hypothesized but never turned into Gate 3 tests.

**Fix (this branch).** `list_mutators` keeps public/external mutators only. Pairs are ranked (deposit/redeem/mint/settle/… × sharePrice/totalSupply/nav/…). `never_generated_check` auto-queues the top-N as prepared distinguishing experiments. Phase 5 action `cartesian` (`queue_cartesian_g3`) re-materializes the queue; it never executes.

## 15. Map intel/PDF excerpts to in-scope functions before any G2 'wrong protocol' kill

**Cause.** Analogs were killed as the wrong protocol without checking whether the write-up named an in-scope function.

**Fix (this branch).** `seed` maps intel/PDF excerpts onto Phase 3 public surfaces (`mapped-surface:Name` + `[CODE] file:line`, or `analog-unmapped`). `disprove_finding` will not take a wrong-protocol BLOCKS until that mapping has run; if it hits an in-scope function, the analog stays live.

## Tests added

- `tests/test_entry_match.py` — matcher, contract disambiguation, slither rc 255, `--json {json_out}`, detector parse
- `tests/test_coverage.py` — fail-closed vs mapped critical flow; missing self-check gap
- `tests/test_intel_pdf.py` — bundled intel, PDF ingest, family seeding, default vault battery (no protocol-specific names)
- `tests/test_never_generated.py` — cartesian fill, getters skipped, already-covered pairs skipped, `_` internals and constants dropped
- `tests/test_recall_gates.py` — freeze-is-impact G4, distinguishing vs happy-path/code-fact G3, per-variant family kills, public cartesian G3 queue, ABI-over-internal ranking, excerpt→in-scope mapping before wrong-protocol kill
- `tests/test_plether_recall.py` — one regression per Blind2 miss (6 wrongly killed crits, highs 97628/97590, every other killed M/L, all 42 pair-only, never-generated 99136)
- `tests/test_g3_execute.py` — forge execute=true confirms overflow freeze and 99136 window attack; Gate 4 verifies
- `tests/plether_misses.py` — catalog of the 63 drops (gate, locus, family, kill text)

## Top 15 (summary)

1. Require protocol-agnostic refundable-receipt / delayed-order / overflow / recap / oracle-calendar / false-emergency families (answer-key-derived; Plether recall is contaminated).
2. Match `Contract.fn` not ABI types.
3. Slither JSON file + rc 255.
4. Stop `settlement*` getter noise; raise undocumented cap.
5. Lens hits prefer the DIV line, not constructors.
6. Do not Gate-1-kill documented limitations that still pay.
7. Keep Gate 3 honest; execute the PoC queue separately.
8. Ship an intel corpus and PDF audit ingest that feed `seed`.
9. Default vault battery: refundable receipts in share price and the sibling families.
10. Coverage fails closed if critical flows are unmapped.
11. Overflow/revert that freezes a value flow is not a G4 'unreachable' kill.
12. Gate 3 requires a distinguishing attack PoC; happy-path and code-fact are not pass/kill.
13. Family G4 kills are per variant, not per family.
14. Cartesian is public/external mutators × value sinks; top-N auto-queue as G3 tests. ABI entrypoints outrank `_` / `settlement*` helpers (fix 19).
15. Map intel/PDF excerpts to in-scope functions before a wrong-protocol kill.
16. Always inject delay-bound value vars (`executionWindow`, `minPublishTime`, `minDelay`, …) and family sink tokens, even when Phase 2 vocab is already long. Rank `commit`/`reconcile`/`apply`/`assign`/`retry`/`evaluate`/`assess`/`renounce`/`arm` and high-EV `_` stems. Mechanism templates name the same-RC cartesian row (pledge-vs-redemption, watermark-rotation, unclamped-rebate, …) and G3-queue it.
17. Happy-path / code-fact experiments are not coverage. `coverage_check` emits `GAP-DISTINGUISHING-*` and does not treat a G3 stall as tested.
18. Freeze-family G4 still treats `supply unreachable` / `revert confirmed at uint max` / `astronomical` as impact, not a kill. A variant-scoped overflow kill (quoteDeposit) does not close `settleLpEpoch`.

## 16. Delay-bound vocab + mechanism-named cartesian (pair-only + 99136)

**Cause.** Blind2 cartesian used a 25-var Phase 2 vocab with no `executionWindow`, so 99136 was never generated. `commitOrder` / `reconcile` / `apply*` were not high-EV, so 11 crits stayed CSV-only generic rows. High-EV `_applyRouterConfigAfterOracle` was dropped as an internal.

**Fix (this branch).** `list_value_vars` always merges `DELAY_BOUND_VARS` and family sink tokens. `HIGH_EV_MUTATOR_RE` includes commit/reconcile/apply/assign/retry/evaluate/assess/renounce/arm/adverse. High-EV `_` stems stay in the cartesian. `tools/pair_templates.py` names the mechanism (family + statement) instead of "fn can move var". Default G3 queue is 32.

## 17. G3 stall is not coverage

**Cause.** SCORE.md counted `needs-evidence` after a happy-path analog as a kill for recall. Coverage treated any experiment (including `DegradedModeLifecycle PASS`) as tested, so `GAP-HYP` disappeared.

**Fix (this branch).** `tested_ids` is distinguishing-only. Happy-path/code-fact logs (`minPublishTime=commitTime+1`, `zero-hash commit PASS`, `unassigned <= NAV`, `latch works`) raise on confirm/refute and emit `GAP-DISTINGUISHING-*` plus `GAP-HYP-*` when recorded as inconclusive.

## 18. Real overflow kill language is freeze impact

**Cause.** Blind2 G4 evidence said "supply unreachable; revert confirmed at uint max; astronomical". Fix 11's regex missed some of that phrasing, and a family-level overflow kill still threatened `settleLpEpoch` (99075) after `quoteDepositFromState` (98172).

**Fix (this branch).** `UNREACHABLE_RE` / `FREEZE_HYP_RE` include the Blind2 phrases. Combined with fix 13, an overflow BLOCKS check survives (or is variant-scoped), never a family-wide disprove.

## 19. ABI entrypoints outrank settlement internals in the G3 top-N

**Cause.** Blind3 auto-queued `_applyLiquidationSettlementPlan`, `_settleProtocolFeeTopUp`, and `settlementApply*` because those names match high-EV stems (`apply`/`settle`) and pair templates. `commitOrder × executionWindow` (99136) was generated but missed the top-N.

**Fix (this branch).** `pair_rank` adds `PUBLIC_ENTRY_BONUS` for non-helper ABI names and `INTERNAL_HELPER_PENALTY` for `_foo` and camelCase `settlementApply*` helpers. High-EV internals stay enumerable. Regression: `test_commit_order_execution_window_in_top_n_among_settlement_internals`.

## 20. Gate 3 execute=true runs local forge distinguishing attacks

**Cause.** Blind3 queued 96 prepared Python scaffolds (`execute=false`) and recorded 0 verified. `queue_cartesian_g3` refused to execute. Recall stayed at 0.

**Fix (this branch).** `execute_queued_g3` (`experiment execute_g3`) requires `execute=true` and runs family Foundry attacks under `harness/g3` with local forge. A passing distinguishing attack is `verdict=confirmed` and Gate 4 can verify. Failures are `inconclusive`, not kills. Never submit. Tests: `tests/test_g3_execute.py`.
