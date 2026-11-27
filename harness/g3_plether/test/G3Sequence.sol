// SPDX-License-Identifier: MIT
pragma solidity 0.8.35;

import {BasePerpTest} from "../perps/BasePerpTest.sol";
import {CfdTypes} from "@plether/perps/CfdTypes.sol";
import {OrderV3Types} from "@plether/perps/OrderV3Types.sol";
import {IOrderLifecycleBook} from "@plether/perps/interfaces/IOrderLifecycleBook.sol";
import {stdStorage, StdStorage} from "forge-std/StdStorage.sol";

/// Shared setup/sequence helpers for generated G3 attacks. Never submit.
/// Generated settle mutators call inherited `_settleLpEpochForTest` (HousePool).
abstract contract G3Sequence is BasePerpTest {
    using stdStorage for StdStorage;

    address internal constant ATTACKER = address(0xA11CE);
    address internal constant VICTIM = address(0xB0B);

    IOrderLifecycleBook internal book;
    uint256 internal snapshotFree;
    uint256 internal snapshotNav;
    uint256 internal snapshotVictim;
    uint256 internal snapshotRebate;
    uint256 internal snapshotHwm;
    uint256 internal snapshotSenior;
    uint256 internal snapshotLiqReserve;
    uint256 internal snapshotTreasury;
    uint256 internal lastDepositRequest;
    uint256 internal openNonce;
    uint64 internal lastCommitId;

    function _riskParams() internal pure override returns (CfdTypes.RiskParams memory) {
        return CfdTypes.RiskParams({
            vpiFactor: 0.01e18,
            maxSkewRatio: 1e18,
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
        return _openReqAt(clientOrderId, side, window, 50_000e18, 50_000e6);
    }

    function _openReqAt(
        bytes32 clientOrderId,
        CfdTypes.Side side,
        uint32 window,
        uint256 sizeDelta,
        uint256 marginDelta
    ) internal view returns (OrderV3Types.OrderRequest memory request) {
        request.clientOrderId = clientOrderId;
        request.side = side;
        request.sizeDelta = sizeDelta;
        request.marginDelta = marginDelta;
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
        openNonce += 1;
        oid = _commitAs(who, _openReq(bytes32(openNonce ^ uint256(uint160(who))), side, window));
        router.executeOrder(oid, _mockPythUpdateData(1e8));
    }

    function _openThinFilled(address who, CfdTypes.Side side, uint32 window) internal returns (uint64 oid) {
        // Well-margined 50k/50k canaries stay solvent at a 1.5x print. A thin
        // margin makes some mark in the sweep actually unsafe.
        openNonce += 1;
        oid = _commitAs(who, _openReqAt(bytes32(openNonce ^ uint256(uint160(who))), side, window, 50_000e18, 2_000e6));
        router.executeOrder(oid, _mockPythUpdateData(1e8));
    }

    function _sweepUntilLiquidatable(address who) internal {
        uint256[12] memory marks;
        marks[0] = 1.02e8;
        marks[1] = 1.05e8;
        marks[2] = 1.10e8;
        marks[3] = 1.20e8;
        marks[4] = 1.50e8;
        marks[5] = 2e8;
        marks[6] = 5e8;
        marks[7] = 10e8;
        marks[8] = 0.98e8;
        marks[9] = 0.90e8;
        marks[10] = 0.50e8;
        marks[11] = 0.10e8;
        uint256 depth = pool.totalAssets();
        for (uint256 i = 0; i < marks.length; ++i) {
            if (engineLens.isLiquidatableAt(who, marks[i], depth)) {
                _publish(marks[i]);
                return;
            }
        }
        _publish(marks[4]);
    }

    function _openAtFirstLegalMark(address who, CfdTypes.Side side) internal returns (uint64 oid) {
        uint256[8] memory marks;
        marks[0] = 1.02e8;
        marks[1] = 1.05e8;
        marks[2] = 1.08e8;
        marks[3] = 1.10e8;
        marks[4] = 1.15e8;
        marks[5] = 1.20e8;
        marks[6] = 1.30e8;
        marks[7] = 1e8;
        for (uint256 i = 0; i < marks.length; ++i) {
            _publish(marks[i]);
            openNonce += 1;
            oid = _commitAs(who, _openReq(bytes32(openNonce ^ uint256(uint160(who))), side, 60));
            try router.executeOrder(oid, _mockPythUpdateData(marks[i])) returns (
                OrderV3Types.ExecutionResult memory result
            ) {
                if (uint8(result.status) == uint8(OrderV3Types.LifecycleStatus.Executed)) {
                    return oid;
                }
            } catch {}
        }
        revert("open admission found no legal mark");
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
        // requestDeposit returns the shared LP epoch id. Warping to its start is
        // the generic "mature the head" step; settle without it reverts NoLpEpochProgress.
        uint256 t = lastDepositRequest == 0
            ? block.timestamp + pool.LP_EPOCH_DURATION()
            : juniorVault.depositEpochStart(lastDepositRequest);
        if (block.timestamp < t + 1) {
            vm.warp(t + 1);
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

    function _snapshotNav() internal {
        snapshotNav = juniorVault.totalAssets();
        snapshotVictim = juniorVault.convertToAssets(juniorVault.balanceOf(address(this)));
    }

    function _rebateOf(address who) internal view returns (uint256) {
        return clearinghouse.vpiRebateReserveAssets(who);
    }

    function _snapshotRebate(address who) internal {
        snapshotRebate = _rebateOf(who);
    }

    function _snapshotHwm() internal {
        snapshotHwm = pool.seniorHighWaterMark();
        snapshotSenior = pool.seniorPrincipal();
    }

    function _snapshotLiqReserve(address who) internal {
        snapshotLiqReserve = clearinghouse.liquidationReserveAssets(who);
    }

    function _snapshotTreasury() internal {
        snapshotTreasury = clearinghouse.balanceAssets(engine.protocolTreasury());
    }

    function settleLpEpochForTry() public {
        _settleLpEpochForTest();
    }

    function _trySettleLpEpoch() internal {
        // try/catch requires an external call; the inherited helper is internal.
        try this.settleLpEpochForTry() {} catch {}
    }

    function _seedTraderClaim(address who, uint256 amount) internal {
        // Write leftover into the standing claim bucket. Do not open a live
        // position first: that path credits PnL pledge instead of free settlement.
        settlementToken.mint(address(pool), amount);
        uint256 accounted = pool.accountedAssets();
        stdstore.target(address(pool)).sig("accountedAssets()").checked_write(accounted + amount);
        uint256 current = engine.traderClaimBalanceAssets(who);
        stdstore.target(address(engine)).sig("traderClaimBalanceAssets(address)").with_key(who).checked_write(current + amount);
        uint256 total = engine.totalTraderClaimBalanceAssets();
        stdstore.target(address(engine)).sig("totalTraderClaimBalanceAssets()").checked_write(total + amount);
    }

    function _seedPendingRecap(uint256 amount) internal {
        settlementToken.mint(address(pool), amount);
        uint256 current = pool.pendingRecapitalizationAssets();
        stdstore.target(address(pool)).sig("pendingRecapitalizationAssets()").checked_write(current + amount);
    }

    function _seedUnownedResidual(uint256 amount) internal {
        // Do not call accountExcess: it books the mint into junior and can
        // freeze the next requestDeposit (DepositsUnavailable) or consume a
        // matured LP head. Write the leftover directly into the unassigned bucket.
        settlementToken.mint(address(pool), amount);
        uint256 current = pool.unassignedAssets();
        stdstore.target(address(pool)).sig("unassignedAssets()").checked_write(current + amount);
    }

    function _thinPool() internal {
        // Enough cash to open a 50k hedge under maxSkew=1, not the 1M junior buffer.
        _thinPoolTo(70_000e6);
    }

    function _thinPoolTo(uint256 keep) internal {
        uint256 raw = settlementToken.balanceOf(address(pool));
        if (raw > keep) {
            settlementToken.burn(address(pool), raw - keep);
        }
        if (pool.accountedAssets() > keep) {
            stdstore.target(address(pool)).sig("accountedAssets()").checked_write(keep);
        }
        if (pool.juniorPrincipal() > keep) {
            stdstore.target(address(pool)).sig("juniorPrincipal()").checked_write(keep);
        }
    }

    function _nearMaxSupply() internal {
        stdstore.target(address(juniorVault)).sig("totalSupply()").checked_write(type(uint256).max - 500);
    }

    function _commitClose(address who) internal returns (uint64 oid) {
        (uint256 size,,,, CfdTypes.Side side,,) = engine.positions(who);
        vm.prank(who);
        oid = router.commitOrder(side, size == 0 ? 50_000e18 : size, 0, 0, true);
    }

    function _closeFilled(address who) internal {
        // Close at the live mark. A hardcoded 1.5e8 shock makes any close move NAV,
        // so rebate/sharePrice probes cannot be distinguished from directional PnL.
        uint64 oid = _commitClose(who);
        uint256 mark = engine.lastMarkPrice();
        router.executeOrder(oid, _mockPythUpdateData(mark == 0 ? 1e8 : mark));
    }
}
