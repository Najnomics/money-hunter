# Plether Blind SCORE-G (honest)

**Never submit.** Pin `a82d4fe`. Same family-overlay oracle as SCORE-F.

## New verifies this round

| ID | Sev | Test | Overlay | Overlay fail |
|---|---|---|---|---|
| 98170 | L | `evaluateOpen_freeSettlement` | `pending_order` | `OrderRouter__SettlementFloorOrderPending(0)` |

`evaluateOpen` now uses the pending-order print-then-mutate sequence (first commit left orderMargin=0, so SCORE-F overlay did not fail).

NAV `executeClose`/`executeOpen`/`requestRedeem`/`retry*` × sharePrice/rebate still PASS under `zero_vpi` after closing at the live mark (not distinguished; leftover PnL/fees still move incumbent assets).

`withdraw_vpiRebateReserve` pin-FAILs the NAV assertion (still_open).

## Totals

| Bucket | SCORE-F | **SCORE-G** |
|---|---:|---:|
| VERIFIED | 18 | **19** |
| NAMED_OPEN | 23 | 23 |
| PAIR-ONLY | 22 | **21** |

## By severity (V / K / O / P / N)

| Sev | n | SCORE-F | **SCORE-G** |
|---|---:|---|---|
| C | 18 | 9 / 0 / 6 / 3 / 0 | 9 / 0 / 6 / 3 / 0 |
| H | 10 | 2 / 0 / 5 / 3 / 0 | 2 / 0 / 5 / 3 / 0 |
| M | 11 | 0 / 0 / 7 / 4 / 0 | 0 / 0 / 7 / 4 / 0 |
| L | 24 | 7 / 0 / 5 / 12 / 0 | **8 / 0 / 5 / 11 / 0** |
| **All** | **63** | **18 / 0 / 23 / 22 / 0** | **19 / 0 / 23 / 21 / 0** |

Goal **63/63** not met. Still-open classes: pin_fail, pin_pass_not_distinguished (close×rebate / sharePrice).

Never submit.
