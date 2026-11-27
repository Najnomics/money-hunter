# #98854 [CRITICAL]

Source: https://reports.immunefi.com/plether/98854-sc-critical-missing-pending-order-check-in-cfdengine-addmargin-lets-a-trader-rescue-an-increase-that-fails-its-initial-margin-check-at-its-pinned-price-leading-to-direct-theft-of-user-funds-from

Brief/Intro
An order fills at the first Pyth price after its commit, and anyone can execute it. The commit screen rejects an increase that would fail its initial-margin check, but it previews the live position only and ignores the same account's queued orders. So a trader queues a small increase first and then a large one margined to the commit-screen threshold. At the pinned price, once the small one has filled, the large one fails the initial-margin check. That failure ends the order for good, unless the owner first calls CfdEngine.addMargin , which is instant and reads no pending order. The trader now holds a free option on the pre-release price. I ran it on a fork of the deployed v2.0.0 at the US payrolls release of 6 November 2026, replaying that minute's keeper ticks and their signed Pyth prices. The trader arms 4,000,000 USDG one second before 13:30:00 and reads the release from public trades two seconds after it. It rescues the order at the pre-release price, closes on the next real tick, and withdraws 1,864.915179 USDG more than it put in. The LP pool ends 3,508.918763 USDG below the same window without the attacker. On the same release, the same option on the other side is declined and the deployment's own executor kills it for the 0.20 USDG bounty.
Vulnerability Details
- The attacker holds a thin base position, 10,000 USDG of notional with 3,000 USDG of margin. One second before a scheduled release it commits two same-side increases. The first is a 100,000 USDG pre-order. The second is the 4,000,000 USDG arm, margined to the commit-screen threshold plus 1 USDG. No user execution bound is set: minPostPositionEquityAssets = 0 and maxPostLeverageBps = type(uint32).max .
- The commit screen previews each open against the live position only ( OrderLiquidationBatchLogic.sol:430-432 ). The queued-order projection in _queuedPosition ( OrderLiquidationBatchLogic.sol:367-402 ) feeds only the opposing-side check ( OrderLiquidationBatchLogic.sol:423-428 ). So both previews count the same base-margin excess, and both pass.
- The screen is the guard that should stop this. With a mark younger than the staleness limit it rejects predictably invalid opens ( OrderLiquidationBatchLogic.sol:437-445 ). INSUFFICIENT_INITIAL_MARGIN is one of the codes classed as rejectable at commit ( CfdEnginePlanLib.sol:85-93 ). In the run the stored mark is 31 s old, inside the 60 s limit, so the screen runs and lets the arm through.
- Both orders pin to the first unique Pyth update after the commit ( PletherOracle.sol:610-614 ). The parsed basket stays the price even when storage holds newer prices ( PletherOracle.sol:620-622 ). Router.executeOrder has no caller restriction ( OrderRouter.sol:240-243 ).
- At the pinned price the pre-order fills first and spends the base excess. The arm then fails the post-open initial-margin check ( CfdEnginePlanLib.sol:431-436 ). The failure is recorded as terminal PlannerRejected ( OrderRouterExecutionSidecar.sol:846-853 ). The order is deleted as Failed , and its bounty is paid to the executor ( OrderRouter.sol:304-311 , :331-342 ).
- CfdEngine.addMargin checks only the caller, the amount and that a position exists ( CfdEngine.sol:505-515 ). It then locks free settlement as position margin ( CfdEngine.sol:520-523 ). It never reads the account's pending orders.
- After the release, one transaction executes the pre-order, calls addMargin(5,000 USDG) and executes the arm. The arm passes and fills at the pre-release pinned price.
- The deployment's executor finalizes failing heads too: the reference keeper has "No reward filter" ( packages/perps-aa-client/src/keeperExecution.ts:21-28 ). So an adverse move costs the attacker the 0.20 USDG bounty, paid when the executor kills the order.
- The guarantee this breaks: "binding order semantics and the lack of a user cancellation path prevent traders from turning queued intents into free options" ( SECURITY.md:658-659 ).
Vulnerable source code
1. the commit screen projects queued orders only for the opposing side, then previews the live position @ packages/perps/src/router/OrderLiquidationBatchLogic.sol:423-432
// Project the live position through earlier account orders before checking the requested side.
QueuedPositionView memory queuedPosition = _queuedPosition(host, engine, account);
uint8 opposingCode = uint8 (CfdEnginePlanTypes.OpenRevertCode.MUST_CLOSE_OPPOSING);
if (queuedPosition.exists & & queuedPosition.side ! = side) {
revert OrderRouter__PredictableOpenInvalid(opposingCode);
}
uint64 commitMarkTime = engine.lastMarkTime();
uint8 revertCode =
host.engineLensForCommit().previewOpenRevertCode(account, side, sizeDelta, marginDelta, commitPrice);
2. an initial-margin failure is meant to be rejected at commit @ packages/perps/src/libraries/CfdEnginePlanLib.sol:85-93
| | code = = CfdEnginePlanTypes.OpenRevertCode.SKEW_TOO_HIGH
| | code = = CfdEnginePlanTypes.OpenRevertCode.INSUFFICIENT_INITIAL_MARGIN
| | code = = CfdEnginePlanTypes.OpenRevertCode.SOLVENCY_EXCEEDED
| | code = = CfdEnginePlanTypes.OpenRevertCode.INVALID_SIZE_QUANTUM
| | code = = CfdEnginePlanTypes.OpenRevertCode.LIQUIDATION_RESERVE_UNFUNDED
| | code = = CfdEnginePlanTypes.OpenRevertCode.VPI_REBATE_RESERVE_UNFUNDED
| | code = = CfdEnginePlanTypes.OpenRevertCode.NUMERIC_DOMAIN_EXCEEDED
) {
return CfdEnginePlanTypes.OpenFailurePolicyCategory.CommitTimeRejectable;
3. the initial-margin check at execution, on the post-queue position @ packages/perps/src/libraries/CfdEnginePlanLib.sol:431-436
if (
postOpenRiskState.liquidatable
| | postOpenRiskState.equityAssets < = int256 (openState.initialMarginRequirementAssets)
) {
delta.revertCode = CfdEnginePlanTypes.OpenRevertCode.INSUFFICIENT_INITIAL_MARGIN;
return delta;
4. the failure is terminal @ packages/perps/src/OrderRouterExecutionSidecar.sol:846-853
if (
knownCode & & category = = uint256 (expectedCategory)
& & expectedCategory ! = CfdEnginePlanTypes.ExecutionFailurePolicyCategory.None
) {
classification.terminal = true ;
classification.plannerFailure = true ;
classification.plannerIsClose = isClose = = 1 ;
classification.reason = OrderV3Types.TerminalReason.PlannerRejected;
5. addMargin: owner, amount and position checks, no pending-order check @ packages/perps/src/CfdEngine.sol:505-515
if ( msg . sender ! = account) {
revert CfdEngine__NotAccountOwner();
}
if (amount = = 0 ) {
revert CfdEngine__ZeroAmount();
}
StoredPosition storage pos = _positions[account];
if (pos.lots = = 0 ) {
revert CfdEngine__NoOpenPosition();
}
6. the fill is pinned to the first update after the commit @ packages/perps/src/PletherOracle.sol:610-614
uint64 minPublishTime = request.commitTime + 1 ;
uint256 settlementDeadline = uint256 (request.commitTime) + orderSettlementWindow;
uint64 maxPublishTime = uint64 (settlementDeadline < block . timestamp ? settlementDeadline : block . timestamp );
try pyth.parsePriceFeedUpdatesUnique{ value : pythFee}(
pythUpdateData, pythFeedIds, minPublishTime, maxPublishTime
Impact Details
- Impact row: "Direct theft of any user funds, whether at-rest or in-motion, other than unclaimed yield" (Critical). The attacker mints 60,000.000000 USDG and ends with 61,864.915179 USDG in its own wallet after it withdraws everything, +1,864.915179 USDG. HousePool.totalAssets ends 3,508.918763 USDG below the same window without the attacker, and Junior carries all of it (Senior 0). The treasury takes the other 1,644.003584 USDG as execution fees. 1,864.915179 + 1,644.003584 = 3,508.918763, to the atom, and the deployed USDG contract's own Transfer events show the same flows (Output).
- The attacker needs no view on direction before the release. On the same release, the same option on the SHORT side is declined. The executor kills it at its 13:30:05 median, and that holder ends -235.539148 USDG. The same SHORT orders without the rescue end -8,816.584829 USDG. Both options held end +1,629.376031 USDG, against -6,952.061650 USDG for the same four orders without the option.
- Everything is production state. The run forks the deployed v2.0.0 at block 326633764 and asserts the runtime code hash of all 15 manifest contracts and the DEPLOYMENT.md release configuration. It replays the three real keeper ticks of the window, and every fill uses a real signed Pyth payload taken from those ticks' own calldata, verified by the deployed Pyth contract. The book is the real one: 35.98M USDG net LONG on a 102.18M USDG pool.
- The decision uses public data that had printed by then. Binance EUR/USDT, from the public daily trade file on data.binance.vision (sha256 equal to its published checksum), fell 8.05 bp by 13:30:02.300. 92% of the EUR traded since 13:30:00 was sold. A falling EUR/USD means a falling USD-quoted basket, and a LONG gains.
- The exercise lands 3 s after the commit. On 6 November the deployment's only executor, 0x5a71a4094Ec81165Ada48AA4c27dA48ec27E0d6B , finalized 42 orders 3 to 9 s after commit, 40 of them at 4 s or later. The program: "Feasibility limitations do not change the impact or severity of a finding, only the amount paid for it."
- Prerequisites, all permissionless: an open position, free margin (60,000 USDG in the run), a contract account that bundles addMargin and executeOrder , and a scheduled release. The arm is sized at 4,000,000 USDG, inside the 40% skew room the real book left.
- The victim sees ordinary fills. The rescued arm is an Executed order at its own pinned price, and every LP pays pro rata through the pool's trading P&L.
- It repeats at every release. Each account holds up to 5 pending orders ( router.maxPendingOrders() ), and an unexercised arm costs 0.20 USDG.
- Dedup note.
- HIGH-1 ( SECURITY.md:701-713 ) is a commit after an already published price. Here the commit is at 13:29:59, before the 13:30:00 publication it pins to. The program's carve-out for a HIGH-1 report reads: "valid only with a proof of concept showing a repeatable, net-profitable extraction from LPs".
- Cecuro MED-16 and LOW-57 ("Opens committed against a stale cached price, and the keeper bounty sized from it") need a stale mark. Here the mark is 31 s old, inside the limit, and the commit screen runs.
- My report #98732 uses the same addMargin lever on two user-set bounds. This report needs no user bound: the check it beats is the protocol's own initial-margin check, which the commit screen is meant to enforce. The fix proposed in #98732 (guard addMargin while a pending order carries a nonzero minPostPositionEquityAssets or a finite maxPostLeverageBps ) leaves this PoC unchanged, because both bounds are off here. The patch in the Low that #98732 was merged into changes how a VPI rebate-reserve increase is funded ( CfdEnginePlanLib.sol:561-566 ). The LONG arm here adds skew, so it has no rebate-reserve increase.
- Fix: reject addMargin while the account has a pending open.
References
Commit screen
- packages/perps/src/router/OrderLiquidationBatchLogic.sol:367-402 - _queuedPosition , the queued-order projection
- packages/perps/src/router/OrderLiquidationBatchLogic.sol:423-428 - the projection used only for the opposing-side check
- packages/perps/src/router/OrderLiquidationBatchLogic.sol:430-432 - the preview on the live position
- packages/perps/src/router/OrderLiquidationBatchLogic.sol:437-445 - predictably invalid opens rejected while the mark is fresh
- packages/perps/src/libraries/CfdEnginePlanLib.sol:85-93 - INSUFFICIENT_INITIAL_MARGIN is CommitTimeRejectable
Execution and the terminal failure
- packages/perps/src/libraries/CfdEnginePlanLib.sol:431-436 - the initial-margin check at execution
- packages/perps/src/OrderRouterExecutionSidecar.sol:846-853 - recorded as terminal PlannerRejected
- packages/perps/src/OrderRouter.sol:304-311 - terminal order deleted with status Failed
- packages/perps/src/OrderRouter.sol:331-342 - the failed order's bounty paid to the executor
- packages/perps-aa-client/src/keeperExecution.ts:21-28 - the keeper has no reward filter
The owner's lever
- packages/perps/src/CfdEngine.sol:5
