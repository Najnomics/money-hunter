# Apex improvements after the Plether blind miss

Blind campaign: **0 verified findings**. Official unique paid findings: **63** (18C / 10H / 11M / 24L). Operator “69” is not a published unique-finding total. See `findings/plether-key/CLASSIFICATION.md`.

Root causes ranked by impact on that miss. Items 1–7 are implemented on `cursor/recall-fixes-f6d2` (this branch). Items 8–10 are process/corpus; not code in this patch.

## 1. Hunter hypothesis space never included the winning families (impact: 62/63 never generated)

**Cause.** Boss-skill hunts asked “can X steal Y?” on CH / orders / pool and killed 43/45 leads. They never generated: refundable VPI in Junior NAV (CRITICAL-97591 and siblings), delayed-order optionality after the price print, Junior share-supply overflow, recap/HWM/`unassignedAssets`, oracle watermark/calendar, false `degradedMode` via a hedged pair.

**Fix (this branch).** `SYSTEM_PROMPT.md` now requires those six contest-recall families. A Gate 1 kill of a *nearby* hypothesis is not coverage.

**Not in this patch.** A separate Composer still has to run PoCs (`findings/plether-blind/POC-QUEUE.md`). Expanding boss-skill YAML lives outside this repo.

## 2. AST / skeleton matching used ABI types, so Phase 3 mapped 0 of 8 critical flows

**Cause.** `_match_surfaces` split on the last `(` token, so `depositFor(address,uint256)` became `uint256`. All critical flows emitted `unmapped_critical_flow`. `make_blind_skeleton` fell back to the first N surfaces (alphabetically OOS `CfdClosePreview.sol`).

`entry_token()` in `tools/_shared.py` already stripped types correctly; Phase 3 did not call it.

**Fix (this branch).** `_match_surfaces` and `make_blind_skeleton` use `entry_token`. Skeleton no longer falls back to unrelated files. Tests in `tests/test_entry_match.py`.

## 3. Slither stdout cap 2MB + rc 255 → 0 static DIVs

**Cause.** `fsutil.run_command` truncated stdout at 2e6 bytes; slither `--json -` exceeded it; parse returned `[]`. Slither exits 255 when detectors fire; sweep treated only 0/1 as `ran`.

Independent dump: 188 detectors, none of which were unique paid chiefs — so this is **not** why 97591 was missed, but it zeroes Phase 3 static recall on every large Solidity target.

**Fix (this branch).** EVM slither writes `--json {json_out}` under `.apex/sweep/`. Parser reads that file (up to 50MB). rc 255 counts as `ran`.

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

## 8. No intel corpus / PDF past-audit parse (not in this patch)

`check_intel` returned 0. `review_past_audits` skipped PDFs. Would have helped known-issue indexing, not 97591.

## 9. Vault battery had no “refundable receipt in NAV” trigger (not in this patch)

`run_battery` only records analyst-supplied checks. Add a default vault prompt in a later change: share price vs reclaimable VPI/rebate/pending fills.

## 10. Coverage 57% of modelled flows was treated as done

8/14 flows “covered” while 0 critical flows mapped. Coverage should be 0 when AST mapping is empty. Follow-up: `coverage_check` must fail closed if any critical flow is `unmapped_critical_flow`.

## Top 10 (summary)

1. Require VPI-NAV / delayed-order optionality / overflow / recap / oracle-calendar / false-degraded families.
2. Match `Contract.fn` not ABI types.
3. Slither JSON file + rc 255.
4. Stop `settlement*` getter noise; raise undocumented cap.
5. Lens hits prefer the DIV line, not constructors.
6. Do not Gate-1-kill documented limitations that still pay.
7. Keep Gate 3 honest; execute the PoC queue separately.
8. Ship an intel corpus and PDF audit ingest.
9. Default vault battery: refundable receipts in share price.
10. Coverage fails if critical flows are unmapped.
