# #99280 [CRITICAL]

Source: https://reports.immunefi.com/plether/99280-sc-critical-close-admission-in-orderliquidationbatchlogic-counts-the-account-s-pending-increases-so-an-owner-can-cancel-its-own-committed-close-after-the-pinned-price-prints-leading-to-direct-th

Brief/Intro
A committed close is binding and fills at the first Pyth price after its commit. Close admission sizes the close against the live position plus the account's own pending same-side increases. Execution re-plans the close against the live position only, and a close bigger than that fails for good, at no cost. So a trader commits a small partial close, a tiny increase and a close of the whole position, all pinned to one price. The whole close now fills only if the tiny increase fills, and the trader decides that after the price prints: one withdrawal of free settlement leaves the increase unable to pay its fee. I ran it in the repo's Foundry suite with the production config and the real signed Pyth prices of the 6 November 2026 US payrolls release. The trader arms the close of a 25.34M USDG LONG at 13:29:59. At 13:30:02 it reads the release in public Binance trades, cancels the close for 0.11 USDG, keeps the LONG through the move, and withdraws 10,709.71 USDG more than it put in. The victim Junior LP ends 33,075.93 USDG below the same orders with the close binding. On the same release the same rule keeps the close for a SHORT holder, so the trader gets the better of holding and closing on either side.
Vulnerability Details
- The trader holds a LONG of 263,124 lots (25.34M USDG). At 13:29:59 one transaction commits C0 (close 24 lots), I0 (increase 11 lots, marginDelta 0) and C1 (close 263,111 lots, which is live - c0 + i0). All three pin to the first Pyth publication after the commit, 13:30:00 ( PletherOracle.sol:610-614 ). Router.executeOrder has no caller restriction ( OrderRouter.sol:240-243 ).
- Close admission checks the close against _queuedPosition ( OrderLiquidationBatchLogic.sol:344-353 ). That projection adds every pending same-side increase to the live size ( OrderLiquidationBatchLogic.sol:392-398 ). So C1 is admitted at 263,124 - 24 + 11 = 263,111 lots. The same C1 without I0 reverts OrderRouter__SizeExceedsQueued . A close carries no bounty ( OrderLiquidationBatchLogic.sol:235-240 ).
- A close larger than the live size reverts at commit ( CloseCommitmentLib.sol:23-25 ). That is why C0 comes first: it keeps C1 at or below the live size at commit, while C1 exceeds live - c0 once C0 fills.
- At execution C1 is re-planned against the live position. If I0 did not fill, the live size is 263,100 and C1 fails CLOSE_SIZE_EXCEEDS ( CfdEnginePlanLib.sol:825-828 ). Close failures are classed user-invalid ( CfdEnginePlanLib.sol:135-143 ) and recorded as terminal PlannerRejected ( OrderRouterExecutionSidecar.sol:846-853 ). The LONG stays open.
- The owner controls I0 after the pin. With marginDelta 0, I0 pays its trade cost from free settlement ( MarginClearinghouseAccountingLib.sol:157-161 ), or fails MARGIN_DRAINED_BY_FEES ( CfdEnginePlanLib.sol:357-364 ). That code is an execution-time code ( CfdEnginePlanLib.sol:100-102 ), so the commit screen admits I0 ( OrderLiquidationBatchLogic.sol:437-445 ). C0's fill puts 18.67 USDG back in free settlement, more than I0's 4.36 USDG cost. One withdrawMargin ( MarginClearinghouse.sol:414-419 ) right after C0 fills takes it out. The withdrawal guard checks only the position's health and a fresh mark ( CfdEngineSettlementSidecar.sol:255-284 ).
- I0 adds no new pledge, so it can fill only if C0's trimmed liquidation reserve covers I0's reserve ( CfdEnginePlanLib.sol:551-577 ). At the pin's real basket confidence (8,058, 0.8366 bp) that needs at least 263,029 lots after C0. I measured the threshold by execution.
- The guarantee this breaks: "binding order semantics and the lack of a user cancellation path prevent traders from turning queued intents into free options" ( SECURITY.md:658-659 ), and "Users cannot cancel queued orders once committed" ( SECURITY.md:366 ). The guard that should stop it is close admission sizing a close against the live position less earlier pending closes. It counts pending increases instead, and nothing at execution ties the close back to the increase it was admitted on.
Vulnerable source code
1. close admission projects the position through the account's queued orders @ packages/perps/src/router/OrderLiquidationBatchLogic.sol:344-353
function _validateCloseAdmission (
IOrderLiquidationBatchHost host,
address account,
CfdTypes.Side side,
uint256 sizeDelta
) private view {
ICfdEngineCore engine = host.engine();
QueuedPositionView memory queuedPosition = _queuedPosition(host, engine, account);
OrderValidationLib.validateCloseCommit(
queuedPosition.exists, queuedPosition.size, queuedPosition.side, side, sizeDelta
2. the projection adds pending same-side increases @ packages/perps/src/router/OrderLiquidationBatchLogic.sol:392-398
} else if ( ! queuedPosition.exists) {
queuedPosition.exists = true ;
queuedPosition.side = pending.side;
queuedPosition.size = pending.sizeDelta;
} else if (pending.side = = queuedPosition.side) {
queuedPosition.size + = pending.sizeDelta;
}
3. execution re-plans the close against the live position @ packages/perps/src/libraries/CfdEnginePlanLib.sol:825-828
if (pos.size < order.sizeDelta) {
delta.revertCode = CfdEnginePlanTypes.CloseRevertCode.CLOSE_SIZE_EXCEEDS;
return delta;
}
4. the failure is terminal @ packages/perps/src/OrderRouterExecutionSidecar.sol:846-853
if (
knownCode & & category = = uint256 (expectedCategory)
& & expectedCategory ! = CfdEnginePlanTypes.ExecutionFailurePolicyCategory.None
) {
classification.terminal = true ;
classification.plannerFailure = true ;
classification.plannerIsClose = isClose = = 1 ;
classification.reason = OrderV3Types.TerminalReason.PlannerRejected;
5. the increase pays its trade cost from free settlement @ packages/perps/src/libraries/MarginClearinghouseAccountingLib.sol:157-161
if (tradeCostAssets > 0 ) {
plan.settlementDebitAssets = uint256 (tradeCostAssets);
if (plan.settlementDebitAssets > freeSettlementAssets) {
plan.insufficientFreeEquity = true ;
return plan;
6. or fails with an execution-time code @ packages/perps/src/libraries/CfdEnginePlanLib.sol:357-364
MarginClearinghouseAccountingLib.OpenCostPlan memory openCostPlan =
MarginClearinghouseAccountingLib.planOpenCostApplication(
openCostBuckets, delta.marginDeltaAssets, delta.tradeCostAssets
);
if (openCostPlan.insufficientFreeEquity) {
delta.revertCode = CfdEnginePlanTypes.OpenRevertCode.MARGIN_DRAINED_BY_FEES;
return delta;
}
7. the fill is pinned to the first update after the commit @ packages/perps/src/PletherOracle.sol:610-614
uint64 minPublishTime = request.commitTime + 1 ;
uint256 settlementDeadline = uint256 (request.commitTime) + orderSettlementWindow;
uint64 maxPublishTime = uint64 (settlementDeadline < block . timestamp ? settlementDeadline : block . timestamp );
try pyth.parsePriceFeedUpdatesUnique{ value : pythFee}(
pythUpdateData, pythFeedIds, minPublishTime, maxPublishTime
Impact Details
- Impact row: "Direct theft of any user funds, whether at-rest or in-motion, other than unclaimed yield" (Critical). The attacker mints 300,000.000000 USDG and ends with 310,709.710983 USDG in its own wallet after it withdraws everything, +10,709.710983 USDG. The victim LP_J's Junior is worth 10,007,357.092660 USDG, against 10,040,433.025872 USDG with the same orders and the close binding (-33,075.933212) and 10,037,946.036337 USDG with no attacker (-30,588.943677). Senior is unchanged. The attacker's +33,085.163350 against the binding run equals the pool's -33,075.935811 plus the treasury's -9.227539, to the atom.
- The rule pays on either side of the release. In the companion test (gist) the lever on I0 is its own maxPostLeverageBps bound, which works for a LONG or a SHORT, and the same 25.34M position runs as a LONG and as a SHORT on the same window. The trader follows one rule read from the public print: keep the position if the print favours it, otherwise keep the close. The LONG gets the holder's result (+10,709.71 against the honest closer's -22,366.15). The SHORT gets the closer's result (-19,782.93 against the honest holder's -52,807.10). Across both sides the rule beats always-hold by 33,012.70 USDG and always-close by 33,066.72 USDG, and LP_J ends 33,038.71 and 33,068.25 USDG worse.
- Everything is production state. Every router, oracle, engine, pool and tranche parameter is the value read by eth_call from the deployed v2.0.0 at block 326633764, and setUp asserts each one. The five ticks are the real keeper ticks of 13:28:22 to 13:30:35, decoded from the signed Pyth payloads in their calldata. After every tick the test asserts the engine mark equals the deployed engine's real lastMarkPrice .
- The decision uses public data that had printed by then. Binance EUR/USDT, from the public daily trade file on data.binance.vision (sha256 equal to its published checksum), was 8.05 bp below its last pre-release trade by 13:30:02.300, over 55 trades. A falling EUR/USD means a falling USD-quoted basket, and a LONG gains.
- The cancel lands at commit + 3 s. On 6 November the deployment's executor finalized 42 orders 3 to 9 s after commit, 40 of them at 4 s or later. When the executor is first, the trader gets the binding close and loses nothing extra. The program: "Feasibility limitations do not change the impact or severity of a finding, only the amount paid for it."
- Prerequisites, all permissionless: a LONG of at least 263,029 lots after C0 at this pin's confidence (25.34M USDG, 250,000 USDG of margin), a contract account that bundles executeOrder and withdrawMargin , and a scheduled release. The pool is 10M Junior and 25M Senior, inside the release caps, with an unrelated 12.6M SHORT on the book. The cancel costs I0's bounty, 0.105944 USDG.
- The victim sees ordinary orders: C0 fills, I0 and C1 end as PlannerRejected like any order that fails at execution, and the LONG closes later at a public price. Every LP pays pro rata through the pool's trading P&L.
- It repeats at every scheduled release. The orders are three commits, and an account holds up to 5 pending orders.
- Dedup note.
- #97733 (withdraw cancels a rebate-reserve open), #98732 and my report "Missing pending-order check in CfdEngine.addMargin lets a trader rescue an increase that fails its initial-margin check at its pinned price" ( addMargin revives an open), and #97858 (LP-epoch settlement voids an open) each make an open fail or fill. Here the order cancelled is a close of the whole position, and close admission ties its fate to a separate 11-lot order.
- The lever on that 11-lot order is interchangeable, so a fix to any one lever leaves this open. The companion test applies the strictest form of the withdrawal fix (no withdrawal while the account has a pending open, sibling-fix.patch in the gist). The withdrawal cancel then reverts CfdEngine__WithdrawBlockedByOpenPosition . On the same patched build, the same close dies through I0's own maxPostLeverageBps bound, with an addMargin to keep it. The attacker still ends +10,709.710975 USDG, and LP_J ends -33,075.847460 USDG against the run where the close binds. Only a change to close admission closes both.
- HIGH-1 ( SECURITY.md:701-713 ) is a commit after an already published price. Here the commit is at 13:29:59, before the 13:30:00 publication it pins to. The program's carve-out for a HIGH-1 report reads: "valid only with a proof of concept showing a repeatable, net-profitable extraction from LPs".
- ACCOUNTING_SPEC.md:1096-1098 documents the projection for an open behind a queued close, and an execution recheck when that close fails. Nothing documents a close admitted against a pending increase.
- Fix: admit a close only against the live size minus earlier pending closes, and ignore pending increases.
References
Close admission
- packages/perps/src/router/OrderLiquidationBatchLogic.sol:235-240 - a close takes no bounty
- packages/perps/src/router/OrderLiquidationBatchLogic.sol:344-353 - _validateCloseAdmission on the queued projection
- packages/perps/src/router/OrderLiquidationBatchLogic.sol:367-402 - _queuedPosition
- packages/perps/src/router/OrderLiquidati
