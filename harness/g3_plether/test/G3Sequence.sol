// SPDX-License-Identifier: MIT
pragma solidity 0.8.35;

import {BasePerpTest} from "../perps/BasePerpTest.sol";
import {CfdTypes} from "@plether/perps/CfdTypes.sol";
import {OrderV3Types} from "@plether/perps/OrderV3Types.sol";
import {IOrderLifecycleBook} from "@plether/perps/interfaces/IOrderLifecycleBook.sol";
import {stdStorage, StdStorage} from "forge-std/StdStorage.sol";

/// Shared setup/sequence helpers for generated G3 attacks. Never submit.
abstract contract G3Sequence is BasePerpTest {
    using stdStorage for StdStorage;

    address internal constant ATTACKER = address(0xA11CE);
    address internal constant VICTIM = address(0xB0B);

    IOrderLifecycleBook internal book;
    uint256 internal snapshotFree;
    uint256 internal lastDepositRequest;

    function _riskParams() internal pure override returns (CfdTypes.RiskParams memory) {
        return CfdTypes.RiskParams({
            vpiFactor: 0.01e18,
            maxSkewRatio: 0.4e18,
            maintMarginBps: 100,
            initMarginBps: 150,
            fadMarginBps: 300,
            baseCarryBps: 500,
            minBountyAssets: 1e6,
            bountyBps: 10,
            keeperShareBps: 5000,
            protocolShareBps: 0
        });
    }

    function setUp() public virtual override {
        super.setUp();
        book = IOrderLifecycleBook(address(router.lifecycleBook()));
        _fundTrader(ATTACKER, 200_000e6);
        _fundTrader(VICTIM, 200_000e6);
    }

    function _long() internal pure returns (CfdTypes.Side) {
        return CfdTypes.Side.LONG;
    }

    function _short() internal pure returns (CfdTypes.Side) {
        return CfdTypes.Side.SHORT;
    }

    function _openReq(
        bytes32 clientOrderId,
        CfdTypes.Side side,
        uint32 window
    ) internal view returns (OrderV3Types.OrderRequest memory request) {
        request.clientOrderId = clientOrderId;
        request.side = side;
        request.sizeDelta = 50_000e18;
        request.marginDelta = 50_000e6;
        request.targetPrice = (side == CfdTypes.Side.LONG) ? 1 : type(uint256).max;
        request.isClose = false;
        request.bounds = OrderV3Types.ExecutionBounds({
            submitBy: uint64(block.timestamp + router.maxExecutionWindowSeconds()),
            executionWindowSeconds: window,
            allowedExecutionModes: 7,
            expectedConfigHash: book.currentExecutionConfigHash(),
            maxExecutionBountyAssets: type(uint256).max,
            maxExecutionNotionalAssets: type(uint256).max,
            maxGrossAccountDebitAssets: type(uint256).max,
            maxActionChargeAssets: type(uint256).max,
            maxExplicitFeesAssets: type(uint256).max,
            maxPostPositionSize: type(uint256).max,
            minPostSettlementBalanceAssets: 0,
            minPostPositionEquityAssets: 0,
            maxPostLeverageBps: type(uint32).max
        });
    }

    function _commitAs(address who, OrderV3Types.OrderRequest memory req) internal returns (uint64) {
        vm.prank(who);
        return router.commitOrder(req);
    }

    function _openFilled(address who, CfdTypes.Side side, uint32 window) internal returns (uint64 oid) {
        oid = _commitAs(who, _openReq(bytes32(uint256(uint160(who)) ^ uint256(window)), side, window));
        router.executeOrder(oid, _mockPythUpdateData(1e8));
    }

    function _queueDeposit(address lp, uint256 amount) internal returns (uint256 requestId) {
        settlementToken.mint(lp, amount);
        vm.startPrank(lp);
        settlementToken.approve(address(juniorVault), amount);
        requestId = juniorVault.requestDeposit(amount, lp, lp);
        vm.stopPrank();
        lastDepositRequest = requestId;
    }

    function _warpToDepositEpoch() internal {
        uint256 t = lastDepositRequest == 0
            ? block.timestamp + 1 hours
            : juniorVault.depositEpochStart(lastDepositRequest);
        if (block.timestamp < t) {
            vm.warp(t);
        }
        uint256 mark = engine.lastMarkPrice();
        vm.prank(address(router));
        engine.updateMarkPrice(mark == 0 ? 1e8 : mark, uint64(block.timestamp));
    }

    function _publish(uint256 price) internal {
        router.updateMarkPrice(_mockPythUpdateData(price));
    }

    function _freeOf(address who) internal view returns (uint256) {
        uint256 bal = clearinghouse.balanceAssets(who);
        uint256 locked = clearinghouse.lockedMarginAssets(who);
        return bal > locked ? bal - locked : 0;
    }

    function _snapshotFree(address who) internal {
        snapshotFree = _freeOf(who);
    }

    function _seedUnownedResidual(uint256 amount) internal {
        settlementToken.mint(address(pool), amount);
        try pool.settleLpEpoch(0, 0) {} catch {}
        if (pool.unassignedAssets() == 0) {
            stdstore.target(address(pool)).sig("unassignedAssets()").checked_write(amount);
        }
    }

    function _nearMaxSupply() internal {
        stdstore.target(address(juniorVault)).sig("totalSupply()").checked_write(type(uint256).max - 500);
    }

    function _closeFilled(address who) internal {
        vm.prank(who);
        uint64 oid = router.commitOrder(CfdTypes.Side.LONG, 50_000e18, 0, 0, true);
        router.executeOrder(oid, _mockPythUpdateData(1.015e8));
    }
}
