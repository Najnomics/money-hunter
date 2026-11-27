# SCORE-E miss ledger

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
| 97760 | H | NAMED_OPEN | `test_attack_settleLpEpoch_unassignedAssets` | still_open |
| 97844 | H | NAMED_OPEN | `test_attack_reconcile_highWaterMark` | still_open |
| 97968 | H | NAMED_OPEN | `test_attack_settleLpEpoch_unassignedAssets` | still_open |
| 99735 | H | NAMED_OPEN | `test_attack_settleLpEpoch_seniorPrincipal` | still_open |
| 97603 | M | NAMED_OPEN | `test_attack_executeOrder_acceptedBasket` | still_open |
| 97848 | M | NAMED_OPEN | `test_attack_reconcile_unassignedAssets` | still_open |
| 98994 | M | NAMED_OPEN | `test_attack_settleLpEpoch_unassignedAssets` | still_open |
| 99501 | M | NAMED_OPEN | `test_attack_settleLpEpoch_unassignedAssets` | still_open |
| 97715 | L | NAMED_OPEN | `test_attack_assignUnassignedAssets_highWaterMark` | verified |
| 97733 | L | NAMED_OPEN | `test_attack_withdraw_freeSettlement` | still_open |
| 98961 | L | NAMED_OPEN | `test_attack_assignUnassignedAssets_highWaterMark` | verified |
| 99392 | L | NAMED_OPEN | `test_attack_commitOrder_freeSettlement` | still_open |
| 97677 | C | NAMED_OPEN | `test_attack_settleLpEpoch_pnlPledgeAssets` | verified |
| 97858 | C | NAMED_OPEN | `test_attack_executeOrder_freeSettlement` | still_open |
| 98014 | C | PAIR-ONLY | `test_attack_applyRouterConfigAfterOracle_acceptedBasket` | still_open |
| 98035 | C | NAMED_OPEN | `test_attack_executeOpen_vpiRebateReserve` | still_open |
| 98941 | C | NAMED_OPEN | `test_attack_executeLiquidationBatch_freeSettlement` | still_open |
| 99280 | C | PAIR-ONLY | `test_attack_commitOrder_freeSettlement` | still_open |
| 99536 | C | NAMED_OPEN | `test_attack_settleTraderClaim_freeSettlement` | still_open |
| 99589 | C | NAMED_OPEN | `test_attack_settleLpEpoch_sharePrice` | still_open |
| 99756 | C | PAIR-ONLY | `test_attack_settleLpEpoch_seniorPrincipal` | still_open |
| 99855 | C | NAMED_OPEN | `test_attack_reconcile_unassignedAssets` | still_open |
| 100087 | C | PAIR-ONLY | `test_attack_executeClose_traderClaimBalance` | still_open |
| 97592 | H | PAIR-ONLY | `test_attack_retryPositionProtectionClose_degradedMode` | still_open |
| 97881 | H | PAIR-ONLY | `test_attack_settleLpEpoch_seniorPrincipal` | still_open |
| 97903 | H | NAMED_OPEN | `test_attack_executeClose_vpiRebateReserve` | still_open |
| 98416 | H | PAIR-ONLY | `test_attack_applyCalendarConfig_acceptedBasket` | still_open |
| 97601 | M | PAIR-ONLY | `test_attack_applyCalendarConfig_acceptedBasket` | still_open |
| 97605 | M | NAMED_OPEN | `test_attack_executeOpen_degradedMode` | still_open |
| 97649 | M | PAIR-ONLY | `test_attack_executeLiquidationBatch_liquidationReserve` | still_open |
| 97748 | M | NAMED_OPEN | `test_attack_executeClose_vpiRebateReserve` | still_open |
| 98795 | M | PAIR-ONLY | `test_attack_applyOpen_liquidationReserve` | still_open |
| 99422 | M | PAIR-ONLY | `test_attack_adverseLiquidationPrice_acceptedBasket` | still_open |
| 99795 | M | NAMED_OPEN | `test_attack_withdraw_vpiRebateReserve` | still_open |
| 97600 | L | PAIR-ONLY | `test_attack_requestRedeem_sharePrice` | still_open |
| 97602 | L | PAIR-ONLY | `test_attack_applyRouterConfig_currentExecutionConfigHash` | still_open |
| 97610 | L | PAIR-ONLY | `test_attack_renounceOwnership_degradedMode` | still_open |
| 97622 | L | NAMED_OPEN | `test_attack_executeOrder_acceptedBasket` | still_open |
| 97833 | L | PAIR-ONLY | `test_attack_assessCommittedOrder_freeSettlement` | still_open |
| 97836 | L | PAIR-ONLY | `test_attack_executeLiquidationBatch_liquidationReserve` | still_open |
| 97893 | L | NAMED_OPEN | `test_attack_executeOrder_acceptedBasket` | still_open |
| 97971 | L | PAIR-ONLY | `test_attack_retryPositionProtectionClose_vpiRebateReserve` | still_open |
| 98039 | L | NAMED_OPEN | `test_attack_settleLpEpoch_sharePrice` | still_open |
| 98170 | L | PAIR-ONLY | `test_attack_evaluateOpen_freeSettlement` | still_open |
| 98200 | L | PAIR-ONLY | `test_attack_assessCommittedOrder_freeSettlement` | still_open |
| 98575 | L | PAIR-ONLY | `test_attack_withdraw_degradedMode` | still_open |
| 98727 | L | PAIR-ONLY | `test_attack_settleLpEpoch_protocolTreasury` | still_open |
| 98762 | L | PAIR-ONLY | `test_attack_evaluateOpen_acceptedBasket` | still_open |
| 99470 | L | NAMED_OPEN | `test_attack_assignUnassignedAssets_highWaterMark` | verified |
| 99551 | L | PAIR-ONLY | `test_attack_commitOrder_traderClaimBalance` | still_open |
| 99602 | L | NAMED_OPEN | `test_attack_executeOrder_acceptedBasket` | still_open |
| 99663 | L | PAIR-ONLY | `test_attack_executeClose_sharePrice` | still_open |
| 99931 | L | PAIR-ONLY | `test_attack_arm_degradedMode` | still_open |
| 99933 | L | NAMED_OPEN | `test_attack_executeClose_vpiRebateReserve` | still_open |
| 99136 | C | NAMED_OPEN | `test_attack_commitOrder_executionWindow` | verified |

Verified: 97590, 97591, 97628, 97677, 97715, 97906, 98172, 98209, 98854, 98961, 99075, 99136, 99470.

Never submit.
