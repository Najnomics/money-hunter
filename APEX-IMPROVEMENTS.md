# Apex improvements after the Plether blind miss

Blind campaign: **0 verified findings**. Official unique paid findings: **63** (18C / 10H / 11M / 24L). Operator “69” is not a published unique-finding total. See `findings/plether-key/CLASSIFICATION.md`.

Root causes ranked by impact on that miss. Items 1–10 are implemented on `cursor/recall-fixes-f6d2` (this branch).

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

**Fix (this branch).** After hypothesis generation, `never_generated_check` (also the default tail of `seed`) enumerates each state-changing external function × each value-bearing state var. If no hypothesis mentions both tokens, it generates one. Leftover pairs and a skipped self-check are high-EV coverage gaps.

## Tests added

- `tests/test_entry_match.py` — matcher, contract disambiguation, slither rc 255, `--json {json_out}`, detector parse
- `tests/test_coverage.py` — fail-closed vs mapped critical flow; missing self-check gap
- `tests/test_intel_pdf.py` — bundled intel, PDF ingest, family seeding, default vault battery (no protocol-specific names)
- `tests/test_never_generated.py` — cartesian fill, getters skipped, already-covered pairs skipped

## Top 10 (summary)

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
