# SCORE-K miss ledger

**Never submit.**

| ID | Sev | Bucket | Exact test | Class |
|---|---|---|---|---|
| 97591 | C | NAMED_OPEN | `test_attack_settleLpEpoch_sharePrice` | verified |
| 97906 | C | NAMED_OPEN | `test_attack_commitOrder_minPublishTime` | verified |
| 98172 | C | NAMED_OPEN | `test_attack_quoteDepositFromState_totalSupply` | verified |
| 99075 | C | NAMED_OPEN | `test_attack_settleLpEpoch_totalSupply` | verified |
| 98209 | C | NAMED_OPEN | `test_attack_assignUnassignedAssets_unassignedAssets` | verified |
| 98854 | C | NAMED_OPEN | `test_attack_addMargin_freeSettlement` | verified |
| 97628 | H | NAMED_OPEN | `test_attack_convertToShares_totalSupply` | verified |
| 97590 | H | NAMED_OPEN | `test_attack_executeClose_degradedMode` | verified |
| 97760 | H | NAMED_OPEN | `test_attack_settleLpEpoch_unassignedAssets` | verified |
| 97844 | H | NAMED_OPEN | `test_attack_reconcile_highWaterMark` | verified |
| 97968 | H | NAMED_OPEN | `test_attack_settleLpEpoch_unassignedAssets` | verified |
| 99735 | H | NAMED_OPEN | `test_attack_settleLpEpoch_seniorPrincipal` | verified |
| 97603 | M | NAMED_OPEN | `test_attack_executeOrder_acceptedBasket` | verified |
| 97848 | M | NAMED_OPEN | `test_attack_reconcile_unassignedAssets` | verified |
| 98994 | M | NAMED_OPEN | `test_attack_settleLpEpoch_unassignedAssets` | verified |
| 99501 | M | NAMED_OPEN | `test_attack_settleLpEpoch_unassignedAssets` | verified |
| 97715 | L | NAMED_OPEN | `test_attack_assignUnassignedAssets_highWaterMark` | verified |
| 97733 | L | NAMED_OPEN | `test_attack_withdraw_freeSettlement` | verified |
| 98961 | L | NAMED_OPEN | `test_attack_assignUnassignedAssets_highWaterMark` | verified |
| 99392 | L | NAMED_OPEN | `test_attack_commitOrder_freeSettlement` | verified |
| 97677 | C | NAMED_OPEN | `test_attack_settleLpEpoch_pnlPledgeAssets` | verified |
| 97858 | C | NAMED_OPEN | `test_attack_executeOrder_freeSettlement` | verified |
| 98014 | C | PAIR-ONLY | `test_attack_applyRouterConfigAfterOracle_acceptedBasket` | verified |
| 98035 | C | NAMED_OPEN | `test_attack_executeOpen_vpiRebateReserve` | verified |
| 98941 | C | NAMED_OPEN | `test_attack_executeLiquidationBatch_freeSettlement` | verified |
| 99280 | C | PAIR-ONLY | `test_attack_commitOrder_freeSettlement` | verified |
| 99536 | C | NAMED_OPEN | `test_attack_settleTraderClaim_freeSettlement` | verified |
| 99589 | C | NAMED_OPEN | `test_attack_settleLpEpoch_sharePrice` | verified |
| 99756 | C | PAIR-ONLY | `test_attack_settleLpEpoch_seniorPrincipal` | verified |
| 99855 | C | NAMED_OPEN | `test_attack_reconcile_unassignedAssets` | verified |
| 100087 | C | PAIR-ONLY | `test_attack_executeClose_traderClaimBalance` | verified |
| 97592 | H | PAIR-ONLY | `test_attack_retryPositionProtectionClose_degradedMode` | pin_fail |
| 97881 | H | PAIR-ONLY | `test_attack_settleLpEpoch_seniorPrincipal` | verified |
| 97903 | H | NAMED_OPEN | `test_attack_executeClose_vpiRebateReserve` | verified |
| 98416 | H | PAIR-ONLY | `test_attack_applyCalendarConfig_acceptedBasket` | verified |
| 97601 | M | PAIR-ONLY | `test_attack_applyCalendarConfig_acceptedBasket` | verified |
| 97605 | M | NAMED_OPEN | `test_attack_executeOpen_degradedMode` | verified |
| 97649 | M | PAIR-ONLY | `test_attack_executeLiquidationBatch_liquidationReserve` | verified |
| 97748 | M | NAMED_OPEN | `test_attack_executeClose_vpiRebateReserve` | verified |
| 98795 | M | PAIR-ONLY | `test_attack_applyOpen_liquidationReserve` | verified |
| 99422 | M | PAIR-ONLY | `test_attack_adverseLiquidationPrice_acceptedBasket` | verified |
| 99795 | M | NAMED_OPEN | `test_attack_withdraw_vpiRebateReserve` | verified |
| 97600 | L | PAIR-ONLY | `test_attack_requestRedeem_sharePrice` | still_open |
| 97602 | L | PAIR-ONLY | `test_attack_applyRouterConfig_currentExecutionConfigHash` | verified |
| 97610 | L | PAIR-ONLY | `test_attack_renounceOwnership_degradedMode` | pin_fail |
| 97622 | L | NAMED_OPEN | `test_attack_executeOrder_acceptedBasket` | verified |
| 97833 | L | PAIR-ONLY | `test_attack_assessCommittedOrder_freeSettlement` | verified |
| 97836 | L | PAIR-ONLY | `test_attack_executeLiquidationBatch_liquidationReserve` | verified |
| 97893 | L | NAMED_OPEN | `test_attack_executeOrder_acceptedBasket` | verified |
| 97971 | L | PAIR-ONLY | `test_attack_retryPositionProtectionClose_vpiRebateReserve` | verified |
| 98039 | L | NAMED_OPEN | `test_attack_settleLpEpoch_sharePrice` | verified |
| 98170 | L | PAIR-ONLY | `test_attack_evaluateOpen_freeSettlement` | verified |
| 98200 | L | PAIR-ONLY | `test_attack_assessCommittedOrder_freeSettlement` | verified |
| 98575 | L | PAIR-ONLY | `test_attack_withdraw_degradedMode` | pin_fail |
| 98727 | L | PAIR-ONLY | `test_attack_settleLpEpoch_protocolTreasury` | pin_fail |
| 98762 | L | PAIR-ONLY | `test_attack_evaluateOpen_acceptedBasket` | verified |
| 99470 | L | NAMED_OPEN | `test_attack_assignUnassignedAssets_highWaterMark` | verified |
| 99551 | L | PAIR-ONLY | `test_attack_commitOrder_traderClaimBalance` | verified |
| 99602 | L | NAMED_OPEN | `test_attack_executeOrder_acceptedBasket` | verified |
| 99663 | L | PAIR-ONLY | `test_attack_executeClose_sharePrice` | still_open |
| 99931 | L | PAIR-ONLY | `test_attack_arm_degradedMode` | pin_fail |
| 99933 | L | NAMED_OPEN | `test_attack_executeClose_vpiRebateReserve` | verified |
| 99136 | C | NAMED_OPEN | `test_attack_commitOrder_executionWindow` | verified |

Verified: 97590, 97591, 97601, 97602, 97603, 97605, 97622, 97628, 97649, 97677, 97715, 97733, 97748, 97760, 97833, 97836, 97844, 97848, 97858, 97881, 97893, 97903, 97906, 97968, 97971, 98014, 98035, 98039, 98170, 98172, 98200, 98209, 98416, 98762, 98795, 98854, 98941, 98961, 98994, 99075, 99136, 99280, 99392, 99422, 99470, 99501, 99536, 99551, 99589, 99602, 99735, 99756, 99795, 99855, 99933, 100087.

Still open: 97592 pin-FAIL no queued protection; 97600 / 99663 pin-PASS not distinguished by `zero_vpi`; 97610 / 98575 / 98727 / 99931 pin-FAIL.

Never submit.
