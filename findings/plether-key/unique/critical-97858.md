# #97858 [CRITICAL]

Source: https://reports.immunefi.com/plether/97858-sc-critical-owner-controlled-solvency-check-in-orderrouter-executeorder-lets-a-trader-void-and-revive-its-own-pending-open-leading-to-direct-theft-of-user-funds-from-lps

Brief/Intro
An open order's fill price is pinned to the first Pyth update after its commit, and anyone, its owner included, can execute it later. Execution checks the open against pool cash at that moment, and an open that no longer fits the solvency line fails as PlannerRejected , a terminal failure that refunds it. The order's owner moves that pool cash both ways after the commit with two permissionless calls. Router.settleLpEpoch pays out its own matured Junior redemption and lowers it. Router.executeLiquidation on its own thin SHORT moves that position's loss into the pool and raises it. So the attacker commits an open at the solvency line and, in the same transaction, pays out a 1,000 USDG redemption. From then on every execution of the order fails and refunds it, so a keeper that executes first can only cancel it. When the price moves the attacker's way, one transaction liquidates its SHORT and executes the open at the old price. This is component 3 of the pre-audit finding SC-M4, marked fixed, through a path the fix left open. In the run below, six hourly rounds of 30 bps moves end with the attacker 11,505.69 USDG richer in its own wallets after it withdraws everything, and the victim LP's Junior is worth 15,454.39 USDG less than with no trading. All four keeper executions of an armed open refunded it for 0.20 USDG, two of them before the attacker had seen any move. The same six orders without the arm lose 20,529.21 USDG.
Vulnerability Details
A trader commits an open through Router.commitOrder ( OrderRouter.sol:85-89 ). Its fill is priced from the first Pyth update after the commit: the oracle parses the update with minPublishTime = request.commitTime + 1 through parsePriceFeedUpdatesUnique ( PletherOracle.sol:610-614 ), and an update at or before the commit leaves the order pending ( OrderRouterExecutionSidecar.sol:450-452 ). Router.executeOrder has no caller restriction ( OrderRouter.sol:240-243 ).
Execution re-plans the open against pool state at that moment. The planner builds the solvency state from snap.poolCashAssets , the larger side's maximum profit and trader claims ( CfdEnginePlanLib.sol:754-758 ) and requires the settlement buffer after the open ( CfdEnginePlanLib.sol:770-772 , SolvencyAccountingLib.sol:93-101 ). An open that misses it returns SOLVENCY_EXCEEDED ( CfdEnginePlanLib.sol:421-424 ). That code maps to ProtocolStateInvalidated ( CfdEnginePlanLib.sol:119-126 ), and the Router records the failure as terminal PlannerRejected ( OrderRouterExecutionSidecar.sol:849-853 ). The margin reservation is released ( MarginClearinghouse.sol:663-673 ). The bounty goes back to the order's own account on self-execution ( OrderRouter.sol:336-337 ); a keeper that executes it is paid the bounty, at most 0.20 USDG.
The owner moves pool cash down and up after its commit:
- Down. Router.settleLpEpoch has no caller restriction ( OrderRouter.sol:479-484 ). It funds each matured redemption and transfers the assets out of the pool ( HousePool.sol:1007-1008 ). In the run, the attacker's own 1,000 USDG Junior lot is the redemption.
- Up. Router.executeLiquidation has no caller restriction either ( OrderRouter.sol:493-500 ). Liquidating the attacker's own thin 400,000 USDG SHORT after a 30 bps move moves 1,004.863629 USDG of its loss into pool cash in round 2.
The attacker sizes the open at the solvency line: 3,791,000.00 USDG notional, with other traders holding a hedged book of 6,200,000 USDG a side, so the line binds below the 4,004,032.63 USDG skew cap. One transaction commits the open and settles the epoch, so from its first block the open fails for any executor. When the attacker sees a favorable move, one transaction liquidates the SHORT and executes the open with its pinned update, and the open fills at the old price. When the move is adverse, or a keeper gets there first, the execution refunds the order.
SECURITY.md states the guarantee this breaks: "binding order semantics and the lack of a user cancellation path prevent traders from turning queued intents into free options" ( SECURITY.md:658-659 ). The pre-audit's SC-M4 component 3 is the same lever, "the attacker can trigger a full margin refund on the losing order by manipulating the vault depth", and its response is "Fixed in Plether-Fi/plether-core#24." ( audits/plether-pre-audit-report.pdf , SC-M4). At a82d4fef LP deposits and redemptions move only at epoch settlement, but the owner still decides at execution time whether its own order passes. The guard that should have stopped this is an execution rule under which a state change the owner causes after its commit cannot void or revive the order. There is none.
Vulnerable source code
1. The fill is pinned to the first update after the commit @ packages/perps/src/PletherOracle.sol:610-614
uint64 minPublishTime = request.commitTime + 1 ;
uint256 settlementDeadline = uint256 (request.commitTime) + orderSettlementWindow;
uint64 maxPublishTime = uint64 (settlementDeadline < block . timestamp ? settlementDeadline : block . timestamp );
try pyth.parsePriceFeedUpdatesUnique{ value : pythFee}(
pythUpdateData, pythFeedIds, minPublishTime, maxPublishTime
2. Anyone executes an order @ packages/perps/src/OrderRouter.sol:240-243
function executeOrder (
uint64 orderId,
bytes [] calldata pythUpdateData
) external payable nonReentrant returns ( OrderV3Types.ExecutionResult memory result ) {
3. Execution checks the open against pool cash at that moment @ packages/perps/src/libraries/CfdEnginePlanLib.sol:754-758
SolvencyAccountingLib.SolvencyState memory currentState = SolvencyAccountingLib.buildSolvencyState(
snap.poolCashAssets,
SolvencyAccountingLib.getMaxLiability(snap.longSide.maxProfitAssets, snap.shortSide.maxProfitAssets),
snap.totalTraderClaimBalanceAssets
4. Missing the line is SOLVENCY_EXCEEDED @ packages/perps/src/libraries/CfdEnginePlanLib.sol:421-424
if ( ! _applyOpenSettlementBufferAfterPlan(effectiveSnap, delta)) {
delta.revertCode = CfdEnginePlanTypes.OpenRevertCode.SOLVENCY_EXCEEDED;
return delta;
}
5. That is a protocol-state failure @ packages/perps/src/libraries/CfdEnginePlanLib.sol:119-126
if (
code = = CfdEnginePlanTypes.OpenRevertCode.DEGRADED_MODE
| | code = = CfdEnginePlanTypes.OpenRevertCode.SKEW_TOO_HIGH
| | code = = CfdEnginePlanTypes.OpenRevertCode.SOLVENCY_EXCEEDED
| | code = = CfdEnginePlanTypes.OpenRevertCode.NUMERIC_DOMAIN_EXCEEDED
) {
return CfdEnginePlanTypes.ExecutionFailurePolicyCategory.ProtocolStateInvalidated;
}
6. The Router makes it terminal @ packages/perps/src/OrderRouterExecutionSidecar.sol:849-853
) {
classification.terminal = true ;
classification.plannerFailure = true ;
classification.plannerIsClose = isClose = = 1 ;
classification.reason = OrderV3Types.TerminalReason.PlannerRejected;
7. Down: anyone settles the LP epoch @ packages/perps/src/OrderRouter.sol:479-484
function settleLpEpoch (
bytes [] calldata pythUpdateData
) external payable nonReentrant {
pythUpdateData;
_delegateToKeeperSidecar();
}
8. A funded redemption leaves the pool @ packages/perps/src/HousePool.sol:1007-1008
settlementToken.safeTransfer(vaultAddress, fundedAssets);
vault.fundRedeemEpoch(epochId, fundedShares, fundedAssets);
9. Up: anyone liquidates a position @ packages/perps/src/OrderRouter.sol:493-500
function executeLiquidation (
address account,
bytes [] calldata pythUpdateData
) external payable nonReentrant {
account;
pythUpdateData;
_delegateToKeeperSidecar();
}
10. The bounty returns to the owner on self-execution @ packages/perps/src/OrderRouter.sol:336-337
if (bountyRecipient = = order.account) {
clearinghouse.releaseReservedExecutionBountyToSource(order.account, bountyAssets);
Impact Details
- Impact row: "Direct theft of any user funds, whether at-rest or in-motion, other than unclaimed yield" (Critical). After six rounds the attacker withdraws all its margin, closes and withdraws its SHORT account, and redeems all its Junior. Its three wallets hold 331,505.692691 USDG against 320,000.000000 USDG at the start, +11,505.692691 USDG. Victim LP_J's Junior is worth 9,985,165.261182 USDG against 10,000,619.650908 USDG over the same hours with no trading, -15,454.389726 USDG, and -26,870.930659 USDG against the same orders traded without the arm.
- As per rules, the attack is profitable and repeatable hence its valid. There's current ambiguity towards the maximum damage an attacker can cause since it dependes on alot of things.
- A keeper cannot make the attacker lose on the open. Every keeper execution of an armed open refunded it, four of four, two of them at commit + 1 s, before the attacker had seen any move. The worst order P&L in the four rounds the attacker did not exercise is -0.200000 USDG, the bounty.
- The exercised rounds pay +8,116.261759 and +8,095.049696 USDG. The attacker's SHORT, liquidated in rounds 2 and 5 by the attacker and in round 4 by a keeper, costs -4,694.747262 USDG over the run, and its size is set by the switch lot, not by the open.
- The same six orders without the arm, each filled by a keeper at commit + 1 s, lose -20,529.206430 USDG.
- It repeats every hour. The switch is the attacker's own 1,000 USDG Junior lot, requested before each hour's cutoff and paid back at full value when the arm settles it.
- Prerequisites, all permissionless: 300,000 USDG of trading margin in a contract account that bundles the calls, 10,000 USDG of Junior bought through the public deposit queue, 10,000 USDG for the SHORT account, and a pool whose open interest puts the solvency line below the skew cap. The PoC prices both feeds with a 2 bps Pyth confidence, so every fill carries the release adverse-confidence shift.
- Every LP pays pro rata through the pool's trading P&L.
- Dedup note. SC-M4 is marked fixed. The program's rule is "For findings marked as fixed or Acknowledged in the reports above, a report on the same root cause is valid only if it shows that the fix at commit a82d4fefb02768e5b3bddcc97dee371eee24fea8 is incomplete or introduces a new bug." The run is at that commit. The known issue HIGH-1 (commit after an already published price) has a different root: here the order is committed before its tick, and the lever is the owner's control of its own order's outcome. The PoC also meets the HIGH-1 bar, "a proof of concept showing a repeatable, net-profitable extraction from LPs".
References
Order pricing and execution
- packages/perps/src/OrderRouter.sol:85-89 - commitOrder
- packages/perps/src/PletherOracle.sol:610-614 - fill pinned to the first update after commitTime
- packages/perps/src/OrderRouterExecutionSidecar.sol:450-452 - an update at or before the commit stays pending
- packages/perps/src/OrderRouter.sol:240-243 - executeOrder , any caller
Solvency failure
- packages/perps/src/libraries/CfdEnginePlanLib.sol:754-758 - solvency state from pool cash, max liability, claims
- packages/perps/src/libraries/CfdEnginePlanLib.sol:770-772 - settlement buffer required after the open
- packages/perps/src/libraries/SolvencyAccountingLib.sol:93-101 - hasRequiredSettlementBuffer
- packages/perps/src/libraries/CfdEnginePlanLib.sol:421-424 - SOLVENCY_EXCEEDED
- packages/perps/src/libraries/CfdEnginePlanLib.sol:119-126 - ProtocolStateInvalidated
- packages/perps/src/OrderRouterExecutionSidecar.sol:849-853 - terminal PlannerRejected
- packages/perps/src/MarginClearinghouse.sol:663-673 - margin reservation released
- packages/perps/src/OrderRouter.sol:336-337 - bounty back to the owner
The two levers
- packages/perps/src/OrderRouter.sol:479-484 - settleLpEpoch , any caller
- packages/perps/src/HousePool.sol:1007-1008 - funded redemption transferred out of the pool
- packages/perps/src/OrderRouter.sol:493-500 - executeLiquidation , any caller
Guarantee and prior finding
- packages/perps/SECURITY.md:658-659 - "lack of a user cancellation path"
- audits/plether-pre-audit-report.pdf, SC-M4 - component 3, "Fixed in Plether-Fi/plether-core#24."
Link to Proof of Concept
https://gist.github.com/decies-centena-millia/8c6e52b099c2fa098ee5c266f5e7b59c
