# Plether Blind SCORE-F (honest)

**Never submit.** Pin `a82d4fe`. Same family-overlay oracle as SCORE-E; this round expands `pending_order` to withdraw and stacked commit.

## New verifies this round

| ID | Sev | Test | Overlay | Overlay fail |
|---|---|---|---|---|
| 97733 | L | `withdraw_freeSettlement` | `pending_order` | `MarginClearinghouse__InsufficientFreeEquity` |
| 99392 | L | `commitOrder_freeSettlement` | `pending_order` | `OrderRouter__SettlementFloorOrderPending(0)` |
| 99280 | C | same test | same | same |
| 97833 | L | `assessCommittedOrder_freeSettlement` | `pending_order` | `OrderRouter__SettlementFloorOrderPending(0)` |
| 98200 | L | same test | same | same |

`evaluateOpen_freeSettlement` still PASSes under `pending_order` (first commit, no stacked pending). Stays open.

NAV `executeClose`/`executeOpen`/`requestRedeem`/`retry*` × sharePrice/rebate still PASS under `zero_vpi` (not distinguished).

## Totals

| Bucket | SCORE-E | **SCORE-F** |
|---|---:|---:|
| VERIFIED | 13 | **18** |
| NAMED_OPEN | 25 | **23** |
| PAIR-ONLY | 25 | **22** |

## By severity (V / K / O / P / N)

| Sev | n | SCORE-E | **SCORE-F** |
|---|---:|---|---|
| C | 18 | 8 / 0 / 6 / 4 / 0 | **9 / 0 / 6 / 3 / 0** |
| H | 10 | 2 / 0 / 5 / 3 / 0 | 2 / 0 / 5 / 3 / 0 |
| M | 11 | 0 / 0 / 7 / 4 / 0 | 0 / 0 / 7 / 4 / 0 |
| L | 24 | 3 / 0 / 7 / 14 / 0 | **7 / 0 / 5 / 12 / 0** |
| **All** | **63** | **13 / 0 / 25 / 25 / 0** | **18 / 0 / 23 / 22 / 0** |

Goal **63/63** not met. Still-open classes: pin_fail (incomplete sequence / no assertion), pin_pass_not_distinguished (`evaluateOpen` freeSettlement, close×rebate).

Never submit.
