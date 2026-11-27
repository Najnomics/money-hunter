# #99136 [CRITICAL]

Source: https://reports.immunefi.com/plether/99136-sc-critical-missing-minimum-execution-window-in-the-orderrouter-commit-check-turns-every-pinned-order-into-a-free-option-and-leads-to-direct-theft-of-lp-funds

Brief/Intro
An order fills at the first Pyth update after its commit, but the trader picks the order's deadline, and the only floor is one second. Past the deadline the order is Expired and its whole margin goes back to the trader. The deployment's executor reaches an order 4 to 7 seconds after its commit, so an order with a 2 or 3 second window is filled by its owner or by nobody. The owner reads the move after the pinned update, fills the order at the old price when the move is in its favour, and lets it lapse for free when it is not. I commit a LONG and a SHORT at the largest size the protocol allows, fill the winner at the stale price and let the loser expire. Over six 30 bps releases the attacker withdraws 50,065.40 USDG more than it put in, and the victim LP's Junior is worth 59,632.68 USDG less than with no attacker.
Vulnerability Details
- Router.commitOrder checks the trader's executionWindowSeconds only against zero and the 60 s maximum ( router/OrderLiquidationBatchLogic.sol:287-289 , default maximum at router/OrderExecutionOrchestrator.sol:11,14 ). There is no minimum tied to keeper latency or to the 15 s orderSettlementWindow ( PletherOracle.sol:87 ). The floor is a hardcoded == 0 check, and the admin setter bounds only the maximum ( OrderRouterAdmin.sol:338-343 ), so no setting raises it.
- The lifecycle Book stores executionDeadline = commitTimestamp + executionWindowSeconds once ( OrderLifecycleBook.sol:287-295 , documented at SECURITY.md:783-786 ).
- The fill price is the first update with publishTime >= commitTime + 1 , whoever executes ( PletherOracle.sol:610-614 ). The price is fixed and public one second after the commit.
- Router.executeOrder has no caller restriction ( OrderRouter.sol:240-243 ), so the owner's own account executes its order. On the way to its target id, executeOrder finalizes every head that is terminal before oracle work, expired heads included ( OrderRouterExecutionSidecar.sol:147-192 ).
- Once block.timestamp > executionDeadline the order is classified Expire before any oracle work ( OrderRouterExecutionSidecar.sol:910-912 ) and settled with TerminalReason.Expired ( OrderRouterExecutionSidecar.sol:388-394 ). Anyone calls Router.expireOrder after the deadline ( OrderRouter.sol:191-196 , OrderRecoverySidecar.sol:49-64 ). Settlement releases the whole committed margin ( OrderRouter.sol:303 ) and returns the bounty to the account when the account is the executor ( OrderRouter.sol:336-337 ). A third-party cleaner gets the open bounty, at most 0.20 USDG.
- The v2.0.0 deployment's executor reached the six consecutive orders 183 to 188 of 6 Nov 2026 after 4, 6, 7, 4, 5 and 6 seconds (all 269 v2.0.0 orders: median 5 s). A 2 s order and a 3 s order are both expired when it arrives.
- The attacker runs two plain accounts. In one block it commits a SHORT and a LONG, leg 1 with a 2 s window and leg 2 with a 3 s window, both pinned to the same update. When the move favours leg 1, the owner executes leg 1 at commit + 2. When it favours leg 2, the owner executes leg 2 at commit + 3, and that one call finalizes the expired leg 1 (step 4). Every round the winner fills and the loser expires, whichever side wins and whichever leg comes first.
- The guard that should stop this is the lifecycle rule at SECURITY.md:658-659 : "binding order semantics and the lack of a user cancellation path prevent traders from turning queued intents into free options". A deadline the trader sets below keeper latency is a user cancellation path. Nothing compares the window to the time a keeper needs to reach the order.
Vulnerable source code
1. The only window check at commit: zero, or above the maximum @ packages/perps/src/router/OrderLiquidationBatchLogic.sol:287-289
if (bounds.executionWindowSeconds = = 0 | | bounds.executionWindowSeconds > host.maxExecutionWindowSeconds()) {
revert OrderRouter__InvalidExecutionWindow();
}
2. The deadline is the commit time plus the trader's window @ packages/perps/src/OrderLifecycleBook.sol:287-295
uint256 deadline = block . timestamp + uint256 (request.bounds.executionWindowSeconds);
if ( block . timestamp > type ( uint64 ). max | | deadline > type ( uint64 ). max ) {
revert OrderLifecycleBook__TerminalClockOverflow();
}
OrderV3Types.OrderTiming memory timing = OrderV3Types.OrderTiming({
submitBy: request.bounds.submitBy,
executionWindowSeconds: request.bounds.executionWindowSeconds,
commitTimestamp: uint64 ( block . timestamp ),
executionDeadline: uint64 (deadline)
3. The fill is pinned to the first update after the commit @ packages/perps/src/PletherOracle.sol:610-614
uint64 minPublishTime = request.commitTime + 1 ;
uint256 settlementDeadline = uint256 (request.commitTime) + orderSettlementWindow;
uint64 maxPublishTime = uint64 (settlementDeadline < block . timestamp ? settlementDeadline : block . timestamp );
try pyth.parsePriceFeedUpdatesUnique{ value : pythFee}(
pythUpdateData, pythFeedIds, minPublishTime, maxPublishTime
4. Past the deadline the order expires before any oracle work @ packages/perps/src/OrderRouterExecutionSidecar.sol:910-912
if ( block . timestamp > pending.timing.executionDeadline) {
return (IOrderRouterExecutionHost.ItemAction.Expire, true );
}
5. The expired order is settled as Expired @ packages/perps/src/OrderRouterExecutionSidecar.sol:388-394
if ( block . timestamp > pending.timing.executionDeadline) {
return _settleNonEngine(
request,
OrderV3Types.TerminalReason.Expired,
OrderV3Types.FailureDetails( bytes4 ( 0 ), 0 , 0 , OrderV3Types.ConstraintKind.None, 0 , 0 , bytes32 ( 0 ))
);
}
6. Anyone finalizes an order once its deadline passes @ packages/perps/src/OrderRecoverySidecar.sol:57-63
if ( block . timestamp < = pending.timing.executionDeadline) {
revert OrderRouter__OrderNotExpired();
}
IOrderRouterExecutionHost.ItemRequest memory request = _cleanupRequest(
host, orderId, true , IOrderLifecycleBook(host.lifecycleBook()).currentExecutionConfigHash()
);
return host.executeOrderItemFromSidecar(request);
7. The whole committed margin is released @ packages/perps/src/OrderRouter.sol:302-303
(, CfdTypes.Order memory order) = _pendingOrder(orderId);
clearinghouse.releaseOrderReservationForTerminalCleanup(orderId);
8. The bounty goes back when the owner's account is the executor @ packages/perps/src/OrderRouter.sol:336-337
if (bountyRecipient = = order.account) {
clearinghouse.releaseReservedExecutionBountyToSource(order.account, bountyAssets);
Impact Details
- Impact row: "Direct theft of any user funds, whether at-rest or in-motion, other than unclaimed yield" (Critical). Over six 30 bps releases the attacker's wallet goes from 800,000.000000 to 850,065.401618 USDG, +50,065.401618 USDG. The victim LP_J's Junior is worth 9,940,367.323914 USDG against 9,999,999.999943 USDG with no attacker, -59,632.676029 USDG, and HousePool.totalAssets ends 59,632.681698 USDG lower. Each round the pool pays the winner's PnL out of LP capital ( HousePool::payOut of 11,588.40 USDG in round 1).
- One release the size of the 6 Nov 2026 payrolls move (-13.04 bp, the deployment's own pinned mark 96,318,319 to its next mark 96,192,674) pays the attacker +1,592.724089 USDG and costs the LP 3,191.043866 USDG.
- Every round wins, in both directions and in both leg orders: +8,386.52, +8,335.18, +8,369.72, +8,318.49, +8,310.54 and +8,344.95 USDG. No losing leg fills; each ends status: 3, terminalReason: 2 ( Expired ).
- The same binding orders, filled by the executor at the pinned price, lose 139,550.07 USDG. The free cancel is the whole difference.
- Size is the protocol's own maximum from CfdEngineLens.quoteMaxOpen , bound by the 40% skew cap: 3,976,100 to 3,996,000 USDG per leg on a 10,000,000 USDG pool. The take per release grows with pool depth.
- Prerequisites, all permissionless: 800,000 USDG of trading capital in two contract accounts, and the public calls commitOrder , executeOrder and withdrawMargin . No LP position, no keeper or owner role, no special pool state.
- The victim never sees a cancellation. The loser ends with the same Expired receipt as any order that timed out. There is no pool-depth change, no LP settlement and no liquidation.
- It repeats at every release and no setting closes it: the window is a field of every order request, and the floor is a hardcoded == 0 check.
- Dedup. SC-M4 in the pre-audit report is a free-option attack, "Risk Free Option in 60Sec Oracle Window", marked "Fixed in Plether-Fi/plether-core#24." The program rule is: "For findings marked as fixed or Acknowledged in the reports above, a report on the same root cause is valid only if it shows that the fix at commit a82d4fefb02768e5b3bddcc97dee371eee24fea8 is incomplete or introduces a new bug." The run is at that commit. My confirmed report #97858 and my other reports in this family void the losing order with a state lever ( settleLpEpoch , liquidation cleanup, withdraw , addMargin ), and the order fails as PlannerRejected or AccountLiquidated . This report uses no lever: the trader's own deadline voids the order as Expired . The root is the one-second floor on executionWindowSeconds together with the full refund on expiry. The fix is a minimum window above keeper latency plus orderSettlementWindow , or letting anyone fill an expired order at its pinned update, or making expiry forfeit a fee. None of the other fixes touches this path.
References
Window, deadline and pin
- packages/perps/src/router/OrderLiquidationBatchLogic.sol:287-289 - window checked only against 0 and the maximum
- packages/perps/src/router/OrderExecutionOrchestrator.sol:11,14 - default maximum 60 s
- packages/perps/src/OrderRouterAdmin.sol:338-343 - admin bound on the maximum only
- packages/perps/src/OrderLifecycleBook.sol:287-295 - deadline stored as commit time plus window
- packages/perps/src/PletherOracle.sol:87 - orderSettlementWindow = 15
- packages/perps/src/PletherOracle.sol:610-614 - fill pinned to the first update after the commit
Execution and expiry
- packages/perps/src/OrderRouter.sol:240-243 - executeOrder , any caller
- packages/perps/src/OrderRouterExecutionSidecar.sol:147-192 - expired heads finalized before the target executes
- packages/perps/src/OrderRouterExecutionSidecar.sol:910-912 - Expire before oracle work
- packages/perps/src/OrderRouterExecutionSidecar.sol:388-394 - settled as TerminalReason.Expired
- packages/perps/src/OrderRouter.sol:191-196 - expireOrder , any caller
- packages/perps/src/OrderRecoverySidecar.sol:49-64 - expiry allowed once the deadline passes
- packages/perps/src/OrderRouter.sol:303 - committed margin released
- packages/perps/src/OrderRouter.sol:336-337 - bounty back to the account when it executes
Guarantee and prior finding
- packages/perps/SECURITY.md:658-659 - "the lack of a user cancellation path prevent traders from turning queued intents into free options"
- packages/perps/SECURITY.md:783-786 - deadline mechanics
- audits/plether-pre-audit-report.pdf, SC-M4 - "Fixed in Plether-Fi/plether-core#24."
Deployment data
- gist keeper-latency-v2.0.0-summary.txt - commit-to-terminal latency of all 269 v2.0.0 orders, per day; orders 183 to 188: 4, 6, 7, 4, 5, 6 s
Link to Proof of Concept
https://gist.github.com/decies-centena-millia/206645fe13831cd4e3e2320e6c1768be
Proof of Concept
Proof of Concept
One Foundry test file on the repo's own BasePerpTest with the DEPLOYMENT.md release parameters, asserted in setUp . Only USDG and Pyth are the repo's mocks. Every fill is an explicit Pyth update at commit + 1, every size comes from CfdEngineLens.quoteMaxOpen , the executor arrives at the deployment's measured latency, and every number is read back from the contracts.
All files and every raw output ( -vv , one -vvvv trace per test, versions, SHA-256 sums) are in the secret gist: https://gist.github.com/decies-centena-millia/206645fe13831cd4e3e2320e6c1768be
git clone --recurse-submodules https://github.com/immunefi-team/audit-comp-plether.git && cd audit-comp-plether && git checkout --detach a82d4fefb02768e5b3bddcc97dee371eee24fea8 
