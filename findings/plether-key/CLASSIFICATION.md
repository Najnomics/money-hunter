# Classification of 63 unique paid Plether findings vs the blind campaign

Blind campaign verified findings: **0**. Live G1 keeps: L-CH-001 (degradedMode surplus withdraw), L-CH-002 (liquidation preview includes VPI reserve). Neither is a unique paid Immunefi chief.

Buckets are exclusive. Primary cause only.

| Bucket | Meaning |
|---|---|
| found | Same root cause as a G1-keep lead (L-CH-001/002) |
| killed_before_validation | Matching lead existed and was killed at G1 (code-review / “known issue”) |
| killed_after_validation | Matching H-* was disproved at G4 |
| never_generated | No campaign lead with this root cause |
| out_of_coverage | OOS file, known-issue exclusion, or Insight-only |
| tooling_failure | Apex produced or would have ingested a detector/surface for this locus and dropped it (ISS-0002/0003) **and** no hunter lead existed |
| budget_cutoff | Surface past the undocumented_entrypoint cap of 50, not otherwise generated |

`tooling_failure` is **not** used for “AST was broken so theoretically Phase 3 could not help.” Boss-skill hunts still ran on those contracts. A miss there is `never_generated` unless Slither independently flagged the same function and apex dropped it.

Independent Slither High on in-scope files (after OOS-lens filter): only `PletherOracle` `arbitrary-send-eth`, `weak-prng`, two `reentrancy-eth`. None of those are unique paid chiefs. Therefore **no unique paid finding is classified tooling_failure via Slither**. AST matching still explains *why apex Phase 3 added zero real DIVs*, but hunters are the recall path that should have fired.

## Totals (63 unique paid)

| Bucket | n | % of 63 |
|---|---:|---:|
| found | 0 | 0.0% |
| killed_before_validation | 1 | 1.6% |
| killed_after_validation | 0 | 0.0% |
| never_generated | 62 | 98.4% |
| out_of_coverage | 0 | 0.0% |
| tooling_failure | 0 | 0.0% |
| budget_cutoff | 0 | 0.0% |

## By severity

| Severity | n | found | killed_before | killed_after | never_generated | other |
|---|---:|---:|---:|---:|---:|---:|
| Critical | 18 | 0 (0%) | 0 (0%) | 0 (0%) | 18 (100%) | 0 |
| High | 10 | 0 (0%) | 0 (0%) | 0 (0%) | 10 (100%) | 0 |
| Medium | 11 | 0 (0%) | 0 (0%) | 0 (0%) | 11 (100%) | 0 |
| Low | 24 | 0 (0%) | 1 (4.2%) | 0 (0%) | 23 (95.8%) | 0 |

Related but **not** counted as found:

- L-CH-001 vs HIGH-97590: both involve `degradedMode`, but 97590 is a **false latch via a zero-carry hedged pair that freezes matured Junior LP deposits**. L-CH-001 is surplus CH withdraw after an already-latched flag. Different root cause and victim surface.
- L-CH-002 vs CRITICAL-97591: both mention VPI, but 97591 is **Junior NAV share pricing**; L-CH-002 is a liquidation **preview field**. Preview-only correctness is not a unique paid chief.

## Per-finding table

| ID | Sev | Title (official) | Class | Why |
|---|---|---|---|---|
| 97591 | C | Junior NAV ignores signed vpiAccrued | never_generated | No hunter lead on refundable VPI in `buildReconcileSnapshot` / share price. L-LP-003/008/010 killed unrelated NAV hypotheses. |
| 97677 | C | Uncollected flat-short PnL pledge funds Junior redemption | never_generated | L-CH-005 killed “claims spent as cash”; not this pledge-vs-redemption path. |
| 97858 | C | Owner pool-cash swings void/revive a pinned open | never_generated | No lead on owner recap/payout vs queued open optionality. |
| 97906 | C | Stale first post-commit Pyth tick at macro releases | never_generated | L-OR-013 killed generic fail-open freshness, not first-tick-after-commit. |
| 98014 | C | Oracle rotation drops per-feed watermarks | never_generated | L-OR-010 killed digest-field omission, not watermark reset. |
| 98035 | C | Open-time VPI rebate has no lifetime floor | never_generated | L-CH-011 killed rounding, not unclamped rebate after depth collapse. |
| 98172 | C | Junior share supply overflow freezes redemptions | never_generated | L-LP-004 killed escrow desync, not uint256/VIRTUAL_SHARES overflow. |
| 98209 | C | assignUnassignedAssets mints at zero Junior mark | never_generated | L-LP-010 killed “unassigned accrues to existing NAV without mint” (opposite). |
| 98854 | C | addMargin rescues a failing queued increase | never_generated | No addMargin-vs-commit-screen lead. |
| 98941 | C | Liquidation cleanup cancels a pinned open | never_generated | L-CH-004 killed reservation double-release, not liq cleanup cancel. |
| 99075 | C | Junior maintenance-fee supply overflow freezes settlement | never_generated | Same family as 98172; not hypothesized. |
| 99136 | C | Trader-set executionWindowSeconds as free option | never_generated | No min-window / latency lead (L-OR-018 was FIFO close-only). |
| 99280 | C | Queued increase voids a committed close | never_generated | L-OR-004 killed “trader can cancel queued intent”; not this increase-vs-close admission. |
| 99536 | C | Queued open fill/void after pinned price is public | never_generated | Same family as delayed-order optionality; not generated. |
| 99589 | C | Committed unexecuted opens add no LP liability | never_generated | No pending-order-in-NAV lead. |
| 99756 | C | Zero-value Senior head defers Junior exit | never_generated | L-LP-001 killed “Junior funded while Senior demand remains” as false; did not keep the zero-head variant. |
| 99855 | C | Pending trading revenue booked gross of payouts | never_generated | No gross-vs-net pending revenue lead. |
| 100087 | C | Partial close vs claim strips residual to MM+1 | never_generated | No claim-netted partial-close lead. |
| 97590 | H | Hedged-pair close latches degradedMode, freezes Junior deposits | never_generated | Related L-CH-001 is surplus *withdraw*, not LP-deposit freeze / hedge latch. |
| 97592 | H | retryPositionProtectionClose consumes Latched before owner amend | never_generated | L-OR-008 killed bounty payee, not retry vs amend. |
| 97628 | H | Near-zero Junior principal inflates shares until quote overflow | never_generated | Overflow family; not generated. |
| 97760 | H | Stale pendingRecapitalizationAssets zeroes free assets / reverts settle | never_generated | No stale-recap-residual lead. |
| 97844 | H | Repeated reconcile overwrites Senior HWM | never_generated | Recap/HWM family; not generated. |
| 97881 | H | Frozen-window Senior exit strands fee on seed floor | never_generated | No frozen Senior-fee seed lead. |
| 97903 | H | Unbounded close VPI at small positive depth | never_generated | Distinct from 98035 (open rebate). Not generated. |
| 97968 | H | Recap lands in unassignedAssets after Senior-gap-first | never_generated | Recap/HWM family. |
| 98416 | H | Back-to-back override days freeze past fadMaxStaleness | never_generated | Calendar/oracle family. L-OR-013 killed fail-open, not holiday length. |
| 99735 | H | Extra settlement pass shifts Junior principal to impaired Senior | never_generated | Recap/settlement-pass family. |
| 97601 | M | Whole-UTC-day overrides miss partial-day Pyth closures | never_generated | Calendar family. |
| 97603 | M | Batch cache reuse checks newest component time | never_generated | L-OR-012 killed historical cache reuse executing skipped ticks (different). |
| 97605 | M | Open admission counts marked gain as pool backing | never_generated | L-CH-009 killed “opens leave E<L without latch” as false; did not keep this admission-backing bug. |
| 97649 | M | Self-liquidation skips frozen-close spread | never_generated | No self-liq spread-skip lead. |
| 97748 | M | Skew-reducing close nets VPI rebate against execution fee | never_generated | L-CH-006 killed frozen-spread-to-treasury; not fee-vs-rebate netting. |
| 97848 | M | Reversible MTM truncates unassignedAssets | never_generated | Recap/unassigned family. |
| 98795 | M | Liquidation reserve ratchets on open/increase | never_generated | No liq-reserve ratchet lead. |
| 98994 | M | Collecting pledged loss at zero tranche principal reassigns unassigned | never_generated | Recap/unassigned family. |
| 99422 | M | Frozen liq applies SHORT shift to capped mark | never_generated | Incomplete MED-10; not generated. |
| 99501 | M | First post-recap settlement strands recap in unassigned | never_generated | Recap family. |
| 99795 | M | Withdraw before full close waives positive VPI charge | never_generated | L-CH-008 killed withdraw-of-locked-buckets; not this waive. |
| 97600 | L | Planted ERC-7540 head hides funded claim | never_generated | L-LP-002 killed double-claim, not planted foreign head. |
| 97602 | L | Scheduled treasury rotation changes config hash / bounty sniping | **killed_before_validation** | L-OR-011 described this and **killed it as documented ConfigMismatch**. That over-kill is the only G1 false-negative against a unique paid Low. |
| 97610 | L | CfdEngine default renounceOwnership latches degradedMode forever | never_generated | L-LP-011 killed EmergencyPauseCoordinator unpause, not Engine renounce. |
| 97622 | L | TP/SL creation reverts after fill (accepted basket lags Engine mark) | never_generated | No mark-vs-accepted-basket lead. |
| 97715 | L | Post-wipe recap resets Senior HWM | never_generated | Recap/HWM. |
| 97733 | L | Binding order cancelled by withdrawing free settlement | never_generated | Delayed-order optionality family. |
| 97833 | L | Commit-time carry escapes pinned debit caps | never_generated | No commit-carry vs financial-limits lead. |
| 97836 | L | executeLiquidationBatch stops at 0 if keeper has a position | never_generated | L-OR-015 killed batch mutate-other-account; not gas-budget-at-0. |
| 97893 | L | Execution shifts already-capped basket (vs shift-then-cap liq) | never_generated | MED-10 sibling; not generated. |
| 97971 | L | Self-trigger TP/SL collects carry outside close ceilings | never_generated | L-OR-008 bounty; not carry ceilings. |
| 98039 | L | LP epoch before execution refunds a losing committed open | never_generated | No settle-vs-pending-open optionality lead. |
| 98170 | L | Open preflight ignores account’s own queued orders | never_generated | No projection-vs-live admission lead. |
| 98200 | L | Close bounds checked before commitment carry | never_generated | Carry/bounds family. |
| 98575 | L | Withdraw health ok for same-block frozen liquidatable | never_generated | L-CH-008 locked buckets; not frozen-window health. |
| 98727 | L | Withheld execution fee unattributed when pool cash short | never_generated | Fee attribution. |
| 98762 | L | Open admission ignores adverse confidence shift | never_generated | Oracle/admission. |
| 98961 | L | Dust Senior redemption removes too much HWM | never_generated | HWM rounding. |
| 99392 | L | Zero gross-debit bound makes close cancellable | never_generated | Order optionality. |
| 99470 | L | assignUnassignedAssets credits Junior while Senior below HWM | never_generated | Related to 98209 but distinct unique Low. |
| 99551 | L | Close commit validates Router projection vs Engine live position | never_generated | Projection mismatch. |
| 99602 | L | Live-commit / freeze-execute uses mark older than commit | never_generated | Oracle freeze timing. |
| 99663 | L | Unfillable queued close lets dust partial bypass min notional | never_generated | Min-notional bypass. |
| 99931 | L | Attached TP/SL already triggered at parent fill | never_generated | Protection trigger-at-fill. |
| 99933 | L | Partial close with cash-capped VPI rebate erases carry | never_generated | Carry/VPI partial close. |

## Why recall was 0 (mechanism, not a bucket)

1. **Hunter hypothesis space never included the winning families** (VPI-in-NAV, delayed-order optionality, share-supply overflow, recap/HWM, oracle watermarks/calendar). 43/45 hunter leads were killed; the two keeps were not unique chiefs.
2. **Apex Phase 3 AST matching used the last `(` token**, so 8/8 critical flows were `unmapped_critical_flow` and skeletons fell back to OOS `CfdClosePreview.sol`. Phase 3 could not emit design-wrong DIVs on `settleLpEpoch` / `commitOrder` / `executeOrder`.
3. **Slither JSON truncated + rc 255** → 0 static DIVs. Independent dump did not hit the unique chiefs anyway.
4. **Gate 3 execute=false** would have capped even L-CH-001/002 at unverified. That explains 0 *verified* findings even if a unique chief had been generated.

## Insights (45)

Not in the 63 paid set. Closest campaign overlap: insight 99180 / 100063 `deposit(address,uint256)` missing `nonReentrant` — never generated (L-CH-007 was FOT, killed). Insight 99192 close-preview fee vs VPI — related to L-CH-002 preview-field family; still never generated as that insight.
