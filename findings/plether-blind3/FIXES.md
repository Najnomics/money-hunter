# Blind2 miss → root cause → fix → test

Inventory of every unique paid finding Blind2 dropped (`origin/cursor/plether-blind2` `SCORE.md` + named rows in `LEDGER.md`). Machine-readable twin: `tests/plether_misses.py`.

**Never submit.** A Plether re-run after these patches is a regression fixture, not a clean recall measurement (see `APEX-IMPROVEMENTS.md`).

## Score reminder (Blind2)

| Bucket | n | What happened |
|---|---:|---|
| VERIFIED | 0 | Nothing survived Gate 4 as confirmed. |
| KILLED | 20 | A named lead had the same root cause; G4/G2 closed it, or G3 `needs-evidence` after a happy-path/code-fact analog. |
| PAIR-ONLY | 42 | Cartesian `fn × var` existed; no named same-RC hypothesis, no distinguishing G3. |
| NEVER_GENERATED | 1 | 99136 — vocab had no `executionWindow`. |

## Fixes in this branch

| Fix | Gate | What it hardens |
|---|---|---|
| 11 | G4 | Overflow/revert that freezes a value flow is not 'unreachable'. Real Plether kill language (`supply unreachable`, `astronomical`) is ignored as a BLOCKS check. |
| 12 | G3 | Distinguishing attack only. Real stall logs (`minPublishTime=commitTime+1`, `DegradedModeLifecycle PASS`, `zero-hash commit PASS`, `unassigned <= NAV`) are happy-path/code-fact and cannot pass/kill. Coverage emits `GAP-DISTINGUISHING-*` so a stall is not "tested". |
| 13 | G4 | Family kills are per variant. Mint-to-pool NAV PASS does not kill VPI-in-NAV; overflow on `quoteDepositFromState` does not kill `settleLpEpoch`. |
| 14 | cartesian | Public/high-EV mutators (including `commit`/`reconcile`/`apply`/`assign`/`retry`/`evaluate`/`assess`/`renounce`/`arm` and high-EV `_` stems) × value sinks; mechanism templates name the same-RC; top-N auto-queue as distinguishing G3. |
| 15 | G2 | Intel/PDF excerpt maps onto in-scope functions **or** family surfaces (HWM rounding → `assignUnassignedAssets`) before a wrong-protocol kill. |
| 16 | never-generated | Always inject delay-bound vars (`executionWindow`, `minPublishTime`, `minDelay`, …) and family sink tokens, even when Phase 2 vocab is already long. |
| 19 | cartesian rank | ABI entrypoints outrank `_` / `settlement*` helpers so `commitOrder × executionWindow` lands in top-N. |
| 20 | G3 execute | `execute_queued_g3` runs local forge family attacks (`execute=true`). Prepared scaffolds are not evidence. |
| 17 | G3 coverage | Happy-path/code-fact experiments do not count as tested. |
| 18 | G4 freeze | A freeze-family G4 kill still requires the unreachable language to be treated as impact (reachability is a probe, not a disproof). |

## Generic G3 harness improvements (SCORE-I / SCORE-J)

Selected from `(function, var, family)` tokens only. No finding ids in the generic path. Each row has a unit test.

| Fix | File / function | Unit test | Future classes it detects |
|---|---|---|---|
| 21 | `g3_poc_generator._act` — execute pending FIFO head via `router.nextExecuteId()` | `test_execute_order_freesettlement_executes_the_pending_head` | Delayed-order optionality after a public print when a later commit is not the queue head |
| 22 | `g3_sequence.thin_pool` / executeOpen at the seed mark, 70k buffer | `test_execute_open_degraded_opens_into_thin_cash_not_a_second_long` | False-emergency admission when a second long or 1.5x print is skew-illegal |
| 23 | `g3_sequence.epoch_advance` matches LP settle/epoch only, not `settleTraderClaim` | `test_settle_trader_claim_seeds_claim_not_lp_epoch_or_live_fill` | Trader-claim probes that were starved by an unrelated LP-epoch warp |
| 24 | `G3Sequence._seedTraderClaim` + `claim_seed` | `test_sequence_helpers_seed_claim_and_recap_buckets`, `test_settle_trader_claim_emits_claim_seed_and_pending_print` | Empty claim-bucket reverts; standing-claim vs queued-intent optionality |
| 25 | `g3_sequence.pending_then_print` — commit + print without a live fill | `test_settle_trader_claim_seeds_claim_not_lp_epoch_or_live_fill` | Claim settlement that would otherwise take the live-position pledge branch |
| 26 | `g3_poc_generator._act` — liquidation of the delayed-order account (not a bystander) | `test_execute_liquidation_delayed_order_targets_the_pending_account` | Liquidation cleanup that refunds a pinned open on the same account |
| 27 | `g3_overlay.pending_order` — block `settleTraderClaim` while order margin is reserved | `test_pending_order_also_guards_withdraw_and_stacked_commit` | Owner-reachable claim payout that defunds a queued open |
| 28 | `g3_overlay.pending_order` — block liquidation cleanup while live orders remain | same | Owner-reachable liquidation that cancels a queued intent |
| 29 | `G3Sequence._seedPendingRecap` / `_snapshotHwm` + `pending_recap` / `second_pass` | `test_hwm_reconcile_seeds_recap_and_takes_a_second_pass` | Recap residual and non-idempotent HWM overwrite on a second observation |
| 30 | `g3_overlay.assign_outstanding` — HWM only increases | `test_assign_outstanding_keeps_hwm_monotonic` | Repeated reconcile that erases a senior recovery watermark |
| 31 | `g3_sequence.counterparty_open` + close the winner after executeOpen | `test_execute_open_degraded_closes_the_counterparty` | Admission that spends cash already owed to an opposite-side winner |
| 32 | `g3_harness.run_distinguishing` — `--match-contract ApexG3Generated` | `test_harness_matches_g3_contracts_not_a_glob_path` | Forge versions that drop `test/apex_g3/*` globs or `^name$` match-test anchors and report no tests |
| 33 | `g3_sequence.second_epoch` — queue+warp a second matured head *before* leftover residual | `test_settle_unassigned_seeds_unowned_residual`, `test_hwm_reconcile_seeds_recap_and_takes_a_second_pass`, `test_settle_unassigned_does_not_queue_after_residual` | LP-epoch freeze when residual remaining blocks `requestDeposit` on a second observation |
| 34 | `g3_poc_generator._act` — second LP observation settles the pre-queued head; no mid-queue | `test_hwm_reconcile_emits_second_pass_and_hwm_snapshot` | Non-idempotent HWM/senior overwrite after recap residual is already live |
| 35 | `g3_overlay.assign_outstanding` — epoch settle consumes leftover residual and does not freeze no-progress | `test_assign_outstanding_keeps_hwm_monotonic` | Residual that reserves free cash / blocks deposit processing on every `settleLpEpoch` |
| 36 | `G3Sequence._openThinFilled` + `_sweepUntilLiquidatable` + `unsafe_price_sweep` | `test_liquidation_freesettlement_sweeps_until_unsafe`, `test_sequence_helpers_search_marks_and_sweep_liquidation` | Liquidation cleanup that only fires when a live position is actually unsafe, not at a fixed 1.5x mark |
| 37 | `G3Sequence._openAtFirstLegalMark` + `legal_mark_search` | `test_execute_open_degraded_closes_the_counterparty`, `test_sequence_helpers_search_marks_and_sweep_liquidation` | Admission / false-emergency probes that are skew-illegal at the seed mark or a hardcoded shock |
| 38 | `g3_poc_generator._assert` — `liquidationReserve` / `protocolTreasury` snapshots | `test_execute_liquidation_reserve_asserts_bucket_move` | Pair-only reserve/treasury sinks that previously had no distinguishing assertion |

Tests: `tests/test_g3_sequence.py`, `tests/test_g3_poc_generator.py`, `tests/test_g3_overlay.py`, plus `tests/test_plether_recall.py` and `tests/test_recall_gates.py`.

## Per-finding map

| ID | Sev | Bucket | Drop | Root cause | Fix | Test |
|---|---|---|---|---|---|---|
| 97591 | C | KILLED | G4 H-0001 mint-to-pool | Family kill closed VPI-in-NAV | 13 | `test_killed_family_variant_stays_live` |
| 97906 | C | KILLED | G3 H-ORD-03 code-fact | `minPublishTime=commitTime+1` ≠ first-tick PoC | 12, 17 | `test_killed_g3_stall_is_not_a_pass_or_kill` |
| 98172 | C | KILLED | G4 H-0002 unreachable | Revert-at-uint-max **is** the freeze | 11, 18 | `test_killed_overflow_g4_survives` |
| 99075 | C | KILLED | G4 H-0002 on settleLpEpoch | Same overflow, different mutator | 11, 13 | `test_killed_overflow_g4_survives` |
| 98209 | C | KILLED | G3 H-0003 | `unassigned <= NAV` ≠ zero-NAV assign | 12, 17 | `test_killed_g3_stall_is_not_a_pass_or_kill` |
| 98854 | C | KILLED | G3 H-ORD-04 | Zero-hash commit PASS ≠ addMargin rescue | 12, 13 | `test_killed_g3_stall_is_not_a_pass_or_kill` |
| 97628 | H | KILLED | G4 H-0002 | Near-zero principal is reachability, not a disproof | 11 | `test_killed_overflow_g4_survives` |
| 97590 | H | KILLED | G3 H-0006 | Latch PASS ≠ hedged false-trip | 12, 17 | `test_killed_g3_stall_is_not_a_pass_or_kill` |
| 97760 | H | KILLED | G3 H-0003 | Recap residual never distinguished | 12 | `test_killed_g3_stall_is_not_a_pass_or_kill` |
| 97844 | H | KILLED | G3 H-0003 | Repeated reconcile vs HWM never executed | 12 | `test_killed_g3_stall_is_not_a_pass_or_kill` |
| 97968 | H | KILLED | G3 H-0003 | Senior-gap-first landing never executed | 12 | `test_killed_g3_stall_is_not_a_pass_or_kill` |
| 99735 | H | KILLED | G3 H-POOL-03 | Extra settlement pass never executed | 12 | `test_killed_g3_stall_is_not_a_pass_or_kill` |
| 97603 | M | KILLED | G3 DIV-0202 | Newest-component cache never got a batch PoC | 12 | `test_killed_g3_stall_is_not_a_pass_or_kill` |
| 97848 | M | KILLED | G3 H-0003 | Unassigned truncation never executed | 12 | `test_killed_g3_stall_is_not_a_pass_or_kill` |
| 98994 | M | KILLED | G3 H-0003 | Zero-principal pledge collection never executed | 12 | `test_killed_g3_stall_is_not_a_pass_or_kill` |
| 99501 | M | KILLED | G3 H-0003 | First post-recap settlement never executed | 12 | `test_killed_g3_stall_is_not_a_pass_or_kill` |
| 97715 | L | KILLED | G3 H-0003 | Post-wipe HWM reset never executed | 12 | `test_killed_g3_stall_is_not_a_pass_or_kill` |
| 97733 | L | KILLED | G3 H-ORD-04 | Withdraw-after-print is another delayed-order variant | 12, 13 | `test_killed_g3_stall_is_not_a_pass_or_kill` |
| 98961 | L | KILLED | G2 PDF | "Wrong protocol" on an in-scope HWM excerpt | 15 | `test_killed_pdf_wrong_protocol_blocked` |
| 99392 | L | KILLED | G3 H-0004 | Trader bounds as free option vs zero-hash PASS | 12 | `test_killed_g3_stall_is_not_a_pass_or_kill` |
| 97677 | C | PAIR-ONLY | cartesian | `settleLpEpoch × pnlPledgeAssets` unnamed | 14, 16 | `test_pair_only_is_named_and_queued` |
| 97858 | C | PAIR-ONLY | cartesian | `executeOrder × freeSettlement` unnamed | 14, 13 | `test_pair_only_is_named_and_queued` |
| 98014 | C | PAIR-ONLY | cartesian | `_applyRouterConfigAfterOracle × acceptedBasket` dropped/unranked | 14, 16 | `test_pair_only_is_named_and_queued` |
| 98035 | C | PAIR-ONLY | cartesian | `executeOpen × vpiRebateReserve` unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 98941 | C | PAIR-ONLY | cartesian | `executeLiquidationBatch × freeSettlement` unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 99280 | C | PAIR-ONLY | cartesian | `commitOrder` was not high-EV | 14 | `test_pair_only_is_named_and_queued` |
| 99536 | C | PAIR-ONLY | cartesian | `settleTraderClaim × freeSettlement` unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 99589 | C | PAIR-ONLY | cartesian | pending-open NAV unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 99756 | C | PAIR-ONLY | cartesian | zero Senior head unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 99855 | C | PAIR-ONLY | cartesian | `reconcile` was not high-EV | 14 | `test_pair_only_is_named_and_queued` |
| 100087 | C | PAIR-ONLY | cartesian | partial-close claim unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 97592 | H | PAIR-ONLY | cartesian | `retryPositionProtectionClose` unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 97881 | H | PAIR-ONLY | cartesian | frozen Senior fee unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 97903 | H | PAIR-ONLY | cartesian | close rebate unnamed (≠ 98035) | 14, 13 | `test_pair_only_is_named_and_queued` |
| 98416 | H | PAIR-ONLY | cartesian | `applyCalendarConfig × acceptedBasket` unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 97601 | M | PAIR-ONLY | cartesian | calendar partial-day unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 97605 | M | PAIR-ONLY | cartesian | admission backing unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 97649 | M | PAIR-ONLY | cartesian | self-liq spread unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 97748 | M | PAIR-ONLY | cartesian | close rebate vs fee unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 98795 | M | PAIR-ONLY | cartesian | `_applyOpen × liquidationReserve` dropped | 14 | `test_pair_only_is_named_and_queued` |
| 99422 | M | PAIR-ONLY | cartesian | `_adverseLiquidationPrice` dropped | 14 | `test_pair_only_is_named_and_queued` |
| 99795 | M | PAIR-ONLY | cartesian | withdraw × rebate unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 97600 | L | PAIR-ONLY | cartesian | `requestRedeem` unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 97602 | L | PAIR-ONLY | cartesian | `_applyRouterConfig × currentExecutionConfigHash` unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 97610 | L | PAIR-ONLY | cartesian | `renounceOwnership × degradedMode` unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 97622 | L | PAIR-ONLY | cartesian | `acceptedBasket` unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 97833 | L | PAIR-ONLY | cartesian | `assessCommittedOrder` unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 97836 | L | PAIR-ONLY | cartesian | liq batch gas-at-0 unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 97893 | L | PAIR-ONLY | cartesian | execution vs liq cap unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 97971 | L | PAIR-ONLY | cartesian | protection carry unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 98039 | L | PAIR-ONLY | cartesian | settle vs pending open unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 98170 | L | PAIR-ONLY | cartesian | `evaluateOpen` unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 98200 | L | PAIR-ONLY | cartesian | assess close bounds unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 98575 | L | PAIR-ONLY | cartesian | withdraw frozen health unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 98727 | L | PAIR-ONLY | cartesian | `protocolTreasury` unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 98762 | L | PAIR-ONLY | cartesian | open vs confidence unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 99470 | L | PAIR-ONLY | cartesian | assign × HWM unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 99551 | L | PAIR-ONLY | cartesian | close projection vs live unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 99602 | L | PAIR-ONLY | cartesian | freeze-execute older mark unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 99663 | L | PAIR-ONLY | cartesian | dust min-notional unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 99931 | L | PAIR-ONLY | cartesian | `_arm` dropped | 14 | `test_pair_only_is_named_and_queued` |
| 99933 | L | PAIR-ONLY | cartesian | partial close rebate unnamed | 14 | `test_pair_only_is_named_and_queued` |
| 99136 | C | NEVER_GENERATED | vocab + rank | No `executionWindow` var; Blind3 then buried `commitOrder × executionWindow` under settlement internals | 16, 19 | `test_never_generated_execution_window`, `test_commit_order_execution_window_in_top_n_among_settlement_internals` |

## Counts

Catalog `tests/plether_misses.py` asserts 63 rows, 20 killed, 42 pair-only, 1 never-generated, and the six wrongly killed crits.
