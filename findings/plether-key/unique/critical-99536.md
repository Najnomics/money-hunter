# #99536 [CRITICAL]

Source: https://reports.immunefi.com/plether/99536-sc-critical-missing-pending-order-check-in-cfdengine-settletraderclaim-lets-an-owner-cancel-its-own-pinned-open-after-the-fill-price-is-public-leading-to-direct-theft-of-lp-funds

Brief/Intro
The open planner counts a trader's standing claim as collateral when it admits a queued open, but the commit locks only margin and bounty and settleTraderClaim has no check for a pending open. An order's fill price is pinned to the first oracle tick after commit and is public about one second later, so the owner sees the price before acting. On a favourable move the owner lets the open fill at the stale tick and closes for a gain the LP pool pays. On an adverse move the owner calls settleTraderClaim , the claim leaves the open's margin math, the open fails its initial-margin check and refunds in full, and the claim lands in the owner's withdrawable balance. The owner is any account holding a trader claim. It takes LP USDG on a favourable move and loses nothing on an adverse move.
Vulnerability Details
The value moves in this order.
-
An order's fill price is pinned to the first Pyth tick after commitTime ( PletherOracle.sol:610-614 , minPublishTime = commitTime + 1 ) and Router.executeOrder has no caller restriction ( OrderRouter.sol:240-243 ), so the owner knows the fill price before choosing whether to execute.
-
A trader claim is an unpaid price payout the pool owes the account ( ACCOUNTING_SPEC.md:50 ), recorded when a payout exceeds the pool's free cash ( CfdEngine.sol:849-856 ). The planner counts it as reachable collateral when it admits an open: reachableCollateralAssets = delta.positionMarginAfterOpen + snap.traderClaimBalanceForAccount ( CfdEnginePlanLib.sol:667 ), and the commit screen reads the same term ( CfdEngineLens.sol:312 , CfdOrderPolicyEvaluatorBase.sol:248 ). An open whose own margin is below the initial-margin line is admitted because the claim bridges the gap.
-
The commit reserves only margin and the open bounty ( OrderReservationAccounting.sol:145 ). It never reserves the claim, so the claim sits free while the order is queued.
-
settleTraderClaim ( CfdEngine.sol:559-590 ) checks only msg.sender == account , a nonzero claim, and that pool cash covers all claims. It has no check for a pending open that counted the claim. When the account is flat it pays the claim into withdrawable free settlement ( _payTraderClaim , CfdEngine.sol:242 , the settleAssets branch) and zeroes the balance.
-
At execution the planner re-reads the live snapshot with the claim now zero ( CfdEngineSettlementSidecar.sol:216 ). Post-open equity drops by the claim, so postOpenRiskState.equityAssets <= initialMarginRequirement and the plan returns INSUFFICIENT_INITIAL_MARGIN ( CfdEnginePlanLib.sol:431-436 ). That open code maps to UserInvalid ( CfdEnginePlanLib.sol:112-128 ), a terminal PlannerRejected that refunds the committed margin.
The guard that should stop this exists for a live position only. The spec requires paid claim value not to become withdrawable while its value is counted in a collectible cap ( ACCOUNTING_SPEC.md:772-774 ). The code honours that for a live position by crediting the PnL pledge ( CfdEngine.sol:239-240 ), and takes the other branch for a flat account, which frees the claim and defunds the open that counted it.
Vulnerable source code
1. the open's margin check counts the claim as reachable collateral @ packages/perps/src/libraries/CfdEnginePlanLib.sol:667
uint256 reachableCollateralAssets = delta.positionMarginAfterOpen + snap.traderClaimBalanceForAccount;
2. the commit reserves margin only, never the claim @ packages/perps/src/router/OrderReservationAccounting.sol:145
clearinghouse.reserveCommittedOrderMargin(account, orderId, marginDelta);
3. settleTraderClaim gates on the caller only, no pending-order check @ packages/perps/src/CfdEngine.sol:559-564
function settleTraderClaim (
address account
) external nonReentrant {
if ( msg . sender ! = account) {
revert CfdEngine__NotAccountOwner();
}
4. the flat account pays the claim into withdrawable free settlement @ packages/perps/src/CfdEngine.sol:238-243
pool.payOut( address (clearinghouse), amountAssets);
if (positionRemainsOpen) {
clearinghouse.creditPnlPledge(account, amountAssets);
} else {
clearinghouse.settleAssets(account, int256 (amountAssets));
}
5. execution re-reads the claim live, now zero @ packages/perps/src/CfdEngineSettlementSidecar.sol:216
snap.traderClaimBalanceForAccount = engine.traderClaimBalanceAssets(account);
6. equity below the init line returns INSUFFICIENT_INITIAL_MARGIN @ packages/perps/src/libraries/CfdEnginePlanLib.sol:431-436
if (
postOpenRiskState.liquidatable
| | postOpenRiskState.equityAssets < = int256 (openState.initialMarginRequirementAssets)
) {
delta.revertCode = CfdEnginePlanTypes.OpenRevertCode.INSUFFICIENT_INITIAL_MARGIN;
return delta;
}
7. that code maps to UserInvalid, a terminal refund @ packages/perps/src/libraries/CfdEnginePlanLib.sol:119-128
if (
code = = CfdEnginePlanTypes.OpenRevertCode.DEGRADED_MODE
| | code = = CfdEnginePlanTypes.OpenRevertCode.SKEW_TOO_HIGH
| | code = = CfdEnginePlanTypes.OpenRevertCode.SOLVENCY_EXCEEDED
| | code = = CfdEnginePlanTypes.OpenRevertCode.NUMERIC_DOMAIN_EXCEEDED
) {
return CfdEnginePlanTypes.ExecutionFailurePolicyCategory.ProtocolStateInvalidated;
}
return CfdEnginePlanTypes.ExecutionFailurePolicyCategory.UserInvalid;
Impact Details
- Impact row: "Direct theft of any user funds, whether at-rest or in-motion, other than unclaimed yield" (Critical). In the matched control below, the only difference between the two runs is the settleTraderClaim call, and it moves LP backing by 1,599.998062 USDG on a single adverse round at a 1,000,000 USDG open and a 15 bp move. On the favourable move the LP pool pays the stale-tick gain and the owner withdraws it to its own wallet: the clearinghouse emits an ERC20 transfer of USDG to the attacker EOA. The loss is LP principal held in HousePool, not yield.
- The option scales with the claim. The standing claim in the run is 199,679.999984 USDG. The 1,000,000 USDG open here is conservative: derived from the asserted 20 bps initial-margin rate, that claim admits an open up to about 99,800,000 USDG of notional before the init line binds (199,679.99 / 0.002), so the favourable-exercise payoff scales with the claim, not with a fee band. This bound is arithmetic from the config, not run.
- Prerequisites, all permissionless: a standing trader claim, trading margin, and the public calls commitOrder , settleTraderClaim , executeOrder and withdraw . No LP position, no privileged role. A trader claim is documented normal state, created when a winning close or a liquidation residual exceeds free cash ( ACCOUNTING_SPEC.md:35,767 ), and it persists after the pool recovers, so the attack runs in a healthy pool.
- The LP never sees it. The claim is settled between the pinned tick and the keeper's execution, inside one keeper-latency window, and the open disappears as a terminal refund.
- Dedup note. This is the same class as the confirmed Critical lp-settlement-cancels-own-open , whose root is the pre-audit finding SC-M4 component 3, marked fixed. The program's rule is "For findings marked as fixed or Acknowledged in the reports above, a report on the same root cause is valid only if it shows that the fix at commit a82d4fefb02768e5b3bddcc97dee371eee24fea8 is incomplete or introduces a new bug." SC-M4 component 3 voids an open by changing vault depth so the plan returns SOLVENCY_EXCEEDED . This voids an open by removing the per-account trader claim term so the plan returns INSUFFICIENT_INITIAL_MARGIN . The lever is settleTraderClaim , a different entry point; the removed state is a senior claim liability, not free cash or vault depth; and the fix (reserve the claim or block settle while an open is pending) is in a different place. Locking pool cash does not reserve the claim, so the SC-M4 fix at the scoped commit does not close this.
Not a known issue or an accepted risk
The protocol's own docs expect this not to happen, so it is not a signed-off tradeoff.
- SECURITY.md:658-659 says binding orders and the absence of a cancel path stop traders from turning queued intents into free options. This attack is that free option, built with settleTraderClaim instead of a cancel.
- ACCOUNTING_SPEC.md:772-774 says a paid claim must not become withdrawable while its value is still counted in a cap. The code enforces this only for a live position ( CfdEngine.sol:239-240 ), so a pending open that counted the same claim is left uncovered.
- The commit reserves margin only ( OrderReservationAccounting.sol:145 ) and the reservation model ( ACCOUNTING_SPEC.md:784 onward) never lists the claim, so nothing locks it while the order is queued.
- The Known Limitations list ( SECURITY.md:1328 onward) does not mention settling a claim out of a pending open, and the git history shows the live versus flat split only ever weighed a live position against a flat account, never a flat account with a pending open counting the claim.
References
Admission counts the claim
- packages/perps/src/libraries/CfdEnginePlanLib.sol:667 - open margin check uses margin plus the trader claim
- packages/perps/src/CfdEngineLens.sol:312 - commit screen uses the same term
- packages/perps/src/CfdOrderPolicyEvaluatorBase.sol:248 - snapshot reads the claim at commit
- packages/perps/src/router/OrderReservationAccounting.sol:145 - commit reserves margin only, not the claim
The lever
- packages/perps/src/CfdEngine.sol:559-590 - settleTraderClaim , no pending-order check
- packages/perps/src/CfdEngine.sol:238-243 - flat account pays the claim into withdrawable free settlement
- packages/perps/src/CfdEngine.sol:849-856 - the claim is recorded when a payout exceeds free cash
Terminal refund and public execution
- packages/perps/src/CfdEngineSettlementSidecar.sol:216 - execution re-reads the claim, now zero
- packages/perps/src/libraries/CfdEnginePlanLib.sol:431-436 - equity below init returns INSUFFICIENT_INITIAL_MARGIN
- packages/perps/src/libraries/CfdEnginePlanLib.sol:119-128 - that code is UserInvalid, a terminal refund
- packages/perps/src/OrderRouter.sol:240-243 - executeOrder , any caller
Spec
- packages/perps/ACCOUNTING_SPEC.md:463 - the claim is counted for open, increase and withdraw health
- packages/perps/ACCOUNTING_SPEC.md:772-774 - paid claim value must not become withdrawable while already counted in a cap
Link to Proof of Concept
https://gist.github.com/decies-centena-millia/80609647ee4d96fdc7eb212a4f7b73c5
Proof of Concept
Proof of Concept
One test file proves it in the repo's own packages/perps Foundry suite at commit a82d4fef , on the FindingBase fixture with the DEPLOYMENT.md release parameters asserted at the top of each test via _assertReleaseConfig() . Only USDG and Pyth are the repo's mocks. Every impact number is read back from the system: the order outcome is the Router's own ExecutionResult.terminalReason , the LP loss is pool.totalAssets() and pool assets net of claims, and the money leaving the protocol is the ERC20 Transfer event captured with vm.recordLogs() .
- test_A_favourableExercise_LPfundsLeaveToAttackerWallet fills the claim-bridged open at the stale tick on a favourable move, the LP pool pays the gain, and the owner withdraws USDG to its own wallet.
- test_B_voidLever_vs_bindingControl_isolatesBugLoss runs the same pinned price and the same committed open twice, differing only by the settleTraderClaim void, so the LP-backing difference is caused by the lever alone, not by counterparty P&L.
The live v2.0.0 deployment on Arbitrum Sepolia (chain 421614) runs this exact code: EXTCODEHASH of the deployed CfdEngine ( 0xca18a6...6baa ), HousePool ( 0xeb5604...131e ) and MarginClearinghouse ( 0xb5b851...b89a ) match the v2.0.0 manifest runtime hashes ( 0xa0f8e5be... , 0x5e684cc8... , 0xc8e49658... ), and the manifest's release.sourceCommit is 1209ca8a .
Tools: forge 1.8.5 (commit 51a52c59 ), solc 0.8.35 , via_ir = true , optimizer 200 (the repo's unmodified packages/perps/foundry.toml ). Place the file under packages/perps/test/findings/X01/settletraderclaim-defunds-pinned-open/ of the shared suite checkout, then from p
