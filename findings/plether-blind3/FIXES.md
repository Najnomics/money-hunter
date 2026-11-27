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
| 17 | G3 coverage | Happy-path/code-fact experiments do not count as tested. |
| 18 | G4 freeze | A freeze-family G4 kill still requires the unreachable language to be treated as impact (reachability is a probe, not a disproof). |

Tests: `tests/test_plether_recall.py` (one case per miss) plus the existing `tests/test_recall_gates.py`.

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
| 99136 | C | NEVER_GENERATED | vocab | No `executionWindow` var | 16 | `test_never_generated_execution_window` |

## Counts

Catalog `tests/plether_misses.py` asserts 63 rows, 20 killed, 42 pair-only, 1 never-generated, and the six wrongly killed crits.
