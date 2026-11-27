# Plether Blind3b vs Blind2 / Blind3

Scored after Gate 3 `execute=true` (local forge family attacks in `harness/g3`). **Never submit.**

Evidence is a distinguishing Foundry attack of the same root-cause family, not the Immunefi gist PoC and not a live submission.

## Execution

| Set | n | forge |
|---|---:|---|
| Prepared Blind3 G3 queue | 96 | 96 PASS |
| NAMED_OPEN catalog | 38 | 38 PASS |
| Target 6 crits + 2 highs | 8 | 8 PASS |

Command: `forge test --root harness/g3 --match-contract <FamilyAttack> [--match-test test_attack_<fn>_<var>]`. Failures would be `inconclusive`, not kills.

## Totals

| Bucket | Blind2 | Blind3 | Blind3b |
|---|---:|---:|---:|
| VERIFIED | 0 | 0 | 38 |
| KILLED | 20 | 0 | 0 |
| NAMED_OPEN | — | 38 | 0 |
| PAIR-ONLY | 42 | 25 | 25 |
| NEVER_GENERATED | 1 | 0 | 0 |
| Unique chiefs | 63 | 63 | 63 |

## By severity (V / K / named-open / pair-only / never)

| Sev | n | Blind2 | Blind3 | Blind3b |
|---|---:|---|---|---|
| C | 18 | 0 / 6 / 11 / 1 | 0 / 0 / 14 / 4 / 0 | 14 / 0 / 0 / 4 / 0 |
| H | 10 | 0 / 6 / 4 / 0 | 0 / 0 / 7 / 3 / 0 | 7 / 0 / 0 / 3 / 0 |
| M | 11 | 0 / 4 / 7 / 0 | 0 / 0 / 7 / 4 / 0 | 7 / 0 / 0 / 4 / 0 |
| L | 24 | 0 / 4 / 20 / 0 | 0 / 0 / 10 / 14 / 0 | 10 / 0 / 0 / 14 / 0 |
| **All** | **63** | **0 / 20 / 42 / 1** | **0 / 0 / 38 / 25 / 0** | **38 / 0 / 0 / 25 / 0** |

## Target eight

| ID | Sev | Blind2 | Blind3 | Blind3b | Gate that used to drop it | Fixture |
|---|---|---|---|---|---|---|
| 97591 | C | KILLED | NAMED_OPEN | VERIFIED | G4 family mint-to-pool | `NavReceiptAttack` `settleLpEpoch × sharePrice` |
| 97906 | C | KILLED | NAMED_OPEN | VERIFIED | G3 code-fact minPublishTime | `OracleStaleAttack` `commitOrder × minPublishTime` |
| 98172 | C | KILLED | NAMED_OPEN | VERIFIED | G4 overflow unreachable | `OverflowFreezeAttack` `quoteDepositFromState × totalSupply` |
| 99075 | C | KILLED | NAMED_OPEN | VERIFIED | G4 overflow on settleLpEpoch | `OverflowFreezeAttack` `settleLpEpoch × totalSupply` |
| 98209 | C | KILLED | NAMED_OPEN | VERIFIED | G3 unassigned<=NAV | `HwmRecapAttack` `assignUnassignedAssets × unassignedAssets` |
| 98854 | C | KILLED | NAMED_OPEN | VERIFIED | G3 zero-hash commit | `DelayedOrderAttack` `addMargin × freeSettlement` |
| 97628 | H | KILLED | NAMED_OPEN | VERIFIED | G4 overflow convertToShares | `OverflowFreezeAttack` `convertToShares × totalSupply` |
| 97590 | H | KILLED | NAMED_OPEN | VERIFIED | G3 latch works | `FalseEmergencyAttack` `executeClose × degradedMode` |

## Per finding

| ID | Sev | Blind2 | Blind3 | Blind3b | Why |
|---|---|---|---|---|---|
| 97591 | C | KILLED | NAMED_OPEN | VERIFIED | forge PASS `settleLpEpoch × sharePrice` family `refundable-receipt-in-nav` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 97906 | C | KILLED | NAMED_OPEN | VERIFIED | forge PASS `commitOrder × minPublishTime` family `oracle-staleness-calendar-watermark` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 98172 | C | KILLED | NAMED_OPEN | VERIFIED | forge PASS `quoteDepositFromState × totalSupply` family `share-supply-overflow` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 99075 | C | KILLED | NAMED_OPEN | VERIFIED | forge PASS `settleLpEpoch × totalSupply` family `share-supply-overflow` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 98209 | C | KILLED | NAMED_OPEN | VERIFIED | forge PASS `assignUnassignedAssets × unassignedAssets` family `hwm-recap-accounting` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 98854 | C | KILLED | NAMED_OPEN | VERIFIED | forge PASS `addMargin × freeSettlement` family `delayed-order-optionality` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 97628 | H | KILLED | NAMED_OPEN | VERIFIED | forge PASS `convertToShares × totalSupply` family `share-supply-overflow` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 97590 | H | KILLED | NAMED_OPEN | VERIFIED | forge PASS `executeClose × degradedMode` family `false-emergency-mode` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 97760 | H | KILLED | NAMED_OPEN | VERIFIED | forge PASS `settleLpEpoch × unassignedAssets` family `hwm-recap-accounting` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 97844 | H | KILLED | NAMED_OPEN | VERIFIED | forge PASS `reconcile × highWaterMark` family `hwm-recap-accounting` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 97968 | H | KILLED | NAMED_OPEN | VERIFIED | forge PASS `settleLpEpoch × unassignedAssets` family `hwm-recap-accounting` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 99735 | H | KILLED | NAMED_OPEN | VERIFIED | forge PASS `settleLpEpoch × seniorPrincipal` family `hwm-recap-accounting` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 97603 | M | KILLED | NAMED_OPEN | VERIFIED | forge PASS `executeOrder × acceptedBasket` family `oracle-staleness-calendar-watermark` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 97848 | M | KILLED | NAMED_OPEN | VERIFIED | forge PASS `reconcile × unassignedAssets` family `hwm-recap-accounting` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 98994 | M | KILLED | NAMED_OPEN | VERIFIED | forge PASS `settleLpEpoch × unassignedAssets` family `hwm-recap-accounting` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 99501 | M | KILLED | NAMED_OPEN | VERIFIED | forge PASS `settleLpEpoch × unassignedAssets` family `hwm-recap-accounting` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 97715 | L | KILLED | NAMED_OPEN | VERIFIED | forge PASS `assignUnassignedAssets × highWaterMark` family `hwm-recap-accounting` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 97733 | L | KILLED | NAMED_OPEN | VERIFIED | forge PASS `withdraw × freeSettlement` family `delayed-order-optionality` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 98961 | L | KILLED | NAMED_OPEN | VERIFIED | forge PASS `assignUnassignedAssets × highWaterMark` family `hwm-recap-accounting` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 99392 | L | KILLED | NAMED_OPEN | VERIFIED | forge PASS `commitOrder × freeSettlement` family `delayed-order-optionality` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 97677 | C | PAIR-ONLY | NAMED_OPEN | VERIFIED | forge PASS `settleLpEpoch × pnlPledgeAssets` family `refundable-receipt-in-nav` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 97858 | C | PAIR-ONLY | NAMED_OPEN | VERIFIED | forge PASS `executeOrder × freeSettlement` family `delayed-order-optionality` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 98014 | C | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `oracle-staleness-calendar-watermark` nearby; locus `_applyRouterConfigAfterOracle × acceptedBasket` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 98035 | C | PAIR-ONLY | NAMED_OPEN | VERIFIED | forge PASS `executeOpen × vpiRebateReserve` family `refundable-receipt-in-nav` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 98941 | C | PAIR-ONLY | NAMED_OPEN | VERIFIED | forge PASS `executeLiquidationBatch × freeSettlement` family `delayed-order-optionality` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 99280 | C | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `delayed-order-optionality` nearby; locus `commitOrder × freeSettlement` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 99536 | C | PAIR-ONLY | NAMED_OPEN | VERIFIED | forge PASS `settleTraderClaim × freeSettlement` family `delayed-order-optionality` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 99589 | C | PAIR-ONLY | NAMED_OPEN | VERIFIED | forge PASS `settleLpEpoch × sharePrice` family `refundable-receipt-in-nav` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 99756 | C | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `hwm-recap-accounting` nearby; locus `settleLpEpoch × seniorPrincipal` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 99855 | C | PAIR-ONLY | NAMED_OPEN | VERIFIED | forge PASS `reconcile × unassignedAssets` family `hwm-recap-accounting` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 100087 | C | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `refundable-receipt-in-nav` nearby; locus `executeClose × traderClaimBalance` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 97592 | H | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `delayed-order-optionality` nearby; locus `retryPositionProtectionClose × degradedMode` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 97881 | H | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `hwm-recap-accounting` nearby; locus `settleLpEpoch × seniorPrincipal` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 97903 | H | PAIR-ONLY | NAMED_OPEN | VERIFIED | forge PASS `executeClose × vpiRebateReserve` family `refundable-receipt-in-nav` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 98416 | H | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `oracle-staleness-calendar-watermark` nearby; locus `applyCalendarConfig × acceptedBasket` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 97601 | M | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `oracle-staleness-calendar-watermark` nearby; locus `applyCalendarConfig × acceptedBasket` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 97605 | M | PAIR-ONLY | NAMED_OPEN | VERIFIED | forge PASS `executeOpen × degradedMode` family `false-emergency-mode` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 97649 | M | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `delayed-order-optionality` nearby; locus `executeLiquidationBatch × liquidationReserve` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 97748 | M | PAIR-ONLY | NAMED_OPEN | VERIFIED | forge PASS `executeClose × vpiRebateReserve` family `refundable-receipt-in-nav` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 98795 | M | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `delayed-order-optionality` nearby; locus `_applyOpen × liquidationReserve` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 99422 | M | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `oracle-staleness-calendar-watermark` nearby; locus `_adverseLiquidationPrice × acceptedBasket` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 99795 | M | PAIR-ONLY | NAMED_OPEN | VERIFIED | forge PASS `withdraw × vpiRebateReserve` family `refundable-receipt-in-nav` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 97600 | L | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `refundable-receipt-in-nav` nearby; locus `requestRedeem × sharePrice` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 97602 | L | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `oracle-staleness-calendar-watermark` nearby; locus `_applyRouterConfig × currentExecutionConfigHash` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 97610 | L | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `false-emergency-mode` nearby; locus `renounceOwnership × degradedMode` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 97622 | L | PAIR-ONLY | NAMED_OPEN | VERIFIED | forge PASS `executeOrder × acceptedBasket` family `oracle-staleness-calendar-watermark` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 97833 | L | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `delayed-order-optionality` nearby; locus `assessCommittedOrder × freeSettlement` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 97836 | L | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `delayed-order-optionality` nearby; locus `executeLiquidationBatch × liquidationReserve` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 97893 | L | PAIR-ONLY | NAMED_OPEN | VERIFIED | forge PASS `executeOrder × acceptedBasket` family `oracle-staleness-calendar-watermark` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 97971 | L | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `delayed-order-optionality` nearby; locus `retryPositionProtectionClose × vpiRebateReserve` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 98039 | L | PAIR-ONLY | NAMED_OPEN | VERIFIED | forge PASS `settleLpEpoch × sharePrice` family `delayed-order-optionality` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 98170 | L | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `delayed-order-optionality` nearby; locus `evaluateOpen × freeSettlement` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 98200 | L | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `delayed-order-optionality` nearby; locus `assessCommittedOrder × freeSettlement` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 98575 | L | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `delayed-order-optionality` nearby; locus `withdraw × degradedMode` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 98727 | L | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `refundable-receipt-in-nav` nearby; locus `settleLpEpoch × protocolTreasury` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 98762 | L | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `oracle-staleness-calendar-watermark` nearby; locus `evaluateOpen × acceptedBasket` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 99470 | L | PAIR-ONLY | NAMED_OPEN | VERIFIED | forge PASS `assignUnassignedAssets × highWaterMark` family `hwm-recap-accounting` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 99551 | L | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `delayed-order-optionality` nearby; locus `commitOrder × traderClaimBalance` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 99602 | L | PAIR-ONLY | NAMED_OPEN | VERIFIED | forge PASS `executeOrder × acceptedBasket` family `oracle-staleness-calendar-watermark` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 99663 | L | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `delayed-order-optionality` nearby; locus `executeClose × sharePrice` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 99931 | L | PAIR-ONLY | PAIR-ONLY | PAIR-ONLY | Family `delayed-order-optionality` nearby; locus `_arm × degradedMode` still unnamed in Blind3 cartesian. Not G3-queued as this pair. |
| 99933 | L | PAIR-ONLY | NAMED_OPEN | VERIFIED | forge PASS `executeClose × vpiRebateReserve` family `refundable-receipt-in-nav` (execute=true). G4 confirmed distinguishing. Not submitted. |
| 99136 | C | NEVER_GENERATED | NAMED_OPEN | VERIFIED | forge PASS `commitOrder × executionWindow` family `delayed-order-optionality` (execute=true). G4 confirmed distinguishing. Not submitted. |

## Remaining gap

25 PAIR-ONLY loci still lack a named `fn × var` hypothesis (public mutators such as `commitOrder × freeSettlement`, `applyCalendarConfig × acceptedBasket`, `retryPositionProtectionClose`, `renounceOwnership`). Ranking fix 19 will surface more of them on the next cartesian pass. Do not treat family-fixture PASS as coverage of an unnamed pair.

Never submit.
