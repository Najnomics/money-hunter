# Plether Blind SCORE-I (honest)

**Never submit.** Pin `a82d4fe`. Same family-overlay oracle as SCORE-H.

## New verifies this round

| ID | Sev | Test | Overlay | Overlay fail |
|---|---|---|---|---|
| 97858 | C | `executeOrder_freeSettlement` | `pending_order` | `OrderRouter__NoOrdersToExecute` |
| 99589 | C | `settleLpEpoch_sharePrice` | `zero_vpi` | `incumbent assets ignored reclaimable receipt` |
| 98039 | L | same test | same | same |
| 97603 | M | `executeOrder_acceptedBasket` | `first_tick` | `execute after oracle/config print failed` |
| 97622 | L | same test | same | same |
| 97893 | L | same test | same | same |
| 99602 | L | same test | same | same |

`pending_order` now refuses execute while live size remains. `executeOrder` requires `LifecycleStatus.Executed` so a first-tick overlay cannot leave `lastMark` set and pass.

Parked: `withdraw_vpiRebateReserve` (99795) pin-FAIL — pending close + withdraw moves neither the rebate bucket nor incumbent NAV (`withdraw left rebate backing and incumbent NAV unchanged`).

## Totals

| Bucket | SCORE-H | **SCORE-I** |
|---|---:|---:|
| VERIFIED | 24 | **31** |
| NAMED_OPEN | 19 | **12** |
| PAIR-ONLY | 20 | **20** |

## By severity (V / K / O / P / N)

| Sev | n | SCORE-H | **SCORE-I** |
|---|---:|---|---|
| C | 18 | 10 / 0 / 5 / 3 / 0 | **12 / 0 / 3 / 3 / 0** |
| H | 10 | 3 / 0 / 4 / 3 / 0 | **3 / 0 / 4 / 3 / 0** |
| M | 11 | 1 / 0 / 6 / 4 / 0 | **2 / 0 / 5 / 4 / 0** |
| L | 24 | 10 / 0 / 4 / 10 / 0 | **14 / 0 / 0 / 10 / 0** |
| **All** | **63** | **24 / 0 / 19 / 20 / 0** | **31 / 0 / 12 / 20 / 0** |

Goal **63/63** not met. Still-open named: unassigned/HWM seed vs LP epoch, `executeLiquidationBatch_freeSettlement`, `settleTraderClaim_freeSettlement` (pin-FAIL free did not drop), `executeOpen_degradedMode` (pin-FAIL `PredictableOpenInvalid`), parked rebate withdraw.

Never submit.
