// SPDX-License-Identifier: MIT
pragma solidity 0.8.35;

import {BasePerpTest} from "../perps/BasePerpTest.sol";
import {CfdTypes} from "@plether/perps/CfdTypes.sol";
import {OrderV3Types} from "@plether/perps/OrderV3Types.sol";
import {IOrderLifecycleBook} from "@plether/perps/interfaces/IOrderLifecycleBook.sol";
import {IPositionProtectionActions} from "@plether/perps/interfaces/IPositionProtectionActions.sol";
import {PositionProtectionTypes} from "@plether/perps/interfaces/PositionProtectionTypes.sol";
import {stdStorage, StdStorage} from "forge-std/StdStorage.sol";

/// Shared setup/sequence helpers for generated G3 attacks. Never submit.
/// Generated settle mutators call inherited `_settleLpEpochForTest` (HousePool).
abstract contract G3Sequence is BasePerpTest {
    using stdStorage for StdStorage;

    address internal constant ATTACKER = address(0xA11CE);
    address internal constant VICTIM = address(0xB0B);
    address internal constant TREASURY = address(0xFEE);

    IOrderLifecycleBook internal book;
    IPositionProtectionActions internal protection;
    uint256 internal snapshotFree;
    uint256 internal snapshotNav;
    uint256 internal snapshotVictim;
    uint256 internal snapshotRebate;
    uint256 internal snapshotHwm;
    uint256 internal snapshotSenior;
    uint256 internal snapshotLiqReserve;
    uint256 internal snapshotTreasury;
    uint256 internal snapshotMark;
    uint256 internal snapshotSharePrice;
    bytes32 internal snapshotState;
    uint256 internal lastDepositRequest;
    uint256 internal openNonce;
    uint64 internal lastCommitId;
    uint64 internal lastProtectionId;

    function _riskParams() internal pure override returns (CfdTypes.RiskParams memory) {
        // Non-zero VPI and protocol share so sharePrice/treasury probes can search
        // fee config space instead of relying on a VPI-only overlay.
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
            protocolShareBps: 1000
        });
    }

    function setUp() public virtual override {
        super.setUp();
        book = IOrderLifecycleBook(address(router.lifecycleBook()));
        protection = IPositionProtectionActions(router.positionProtectionBook());
        engine.setProtocolTreasury(TREASURY);
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
        return _openAtFirstLegalMarkAt(who, side, 50_000e18, 50_000e6);
    }

    function _openAtFirstLegalMarkAt(
        address who,
        CfdTypes.Side side,
        uint256 sizeDelta,
        uint256 marginDelta
    ) internal returns (uint64 oid) {
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
            oid = _commitAs(
                who,
                _openReqAt(bytes32(openNonce ^ uint256(uint160(who))), side, 60, sizeDelta, marginDelta)
            );
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

    function _snapshotMark() internal {
        snapshotMark = engine.lastMarkPrice();
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

    function _sharePrice() internal view returns (uint256) {
        return juniorVault.convertToAssets(1e18);
    }

    function _snapshotSharePrice() internal {
        snapshotSharePrice = _sharePrice();
    }

    function _stateHash() internal view returns (bytes32) {
        return keccak256(
            abi.encode(
                clearinghouse.balanceAssets(engine.protocolTreasury()),
                clearinghouse.balanceAssets(ATTACKER),
                clearinghouse.balanceAssets(VICTIM),
                clearinghouse.balanceAssets(address(this)),
                juniorVault.totalAssets(),
                juniorVault.totalSupply(),
                juniorVault.balanceOf(ATTACKER),
                juniorVault.balanceOf(VICTIM),
                juniorVault.balanceOf(address(this)),
                juniorVault.maxRedeem(ATTACKER),
                juniorVault.maxRedeem(VICTIM),
                juniorVault.controllerRedeemHead(ATTACKER),
                juniorVault.controllerRedeemHead(VICTIM),
                _sharePrice(),
                pool.accountedAssets(),
                engine.degradedMode(),
                engine.owner(),
                engine.lastMarkPrice()
            )
        );
    }

    function _snapshotState() internal {
        snapshotState = _stateHash();
    }

    function _stateEffect() internal view returns (bool) {
        return _stateHash() != snapshotState;
    }

    function _enterDegradedMode() internal {
        // Open the hedge on full cash so both fills admit, then drain and close the
        // winner. No mocked degradedMode flag. The remaining opposite-side fill stays live.
        _openFilled(ATTACKER, _long(), 60);
        _openFilled(VICTIM, _short(), 60);
        _publish(1.5e8);
        _thinPoolTo(10_000e6);
        _closeFilled(ATTACKER);
        (uint256 live,,,,,,) = engine.positions(VICTIM);
        if (live == 0) {
            revert("hedge short did not remain after latch");
        }
    }

    function _protectionParams(address who) internal view returns (PositionProtectionTypes.PositionProtectionParams memory params) {
        (uint256 size,,,, CfdTypes.Side side,,) = engine.positions(who);
        size;
        uint256 mark = engine.lastMarkPrice();
        if (mark == 0) mark = 1e8;
        if (side == CfdTypes.Side.LONG) {
            params.takeProfitTriggerPrice = (mark * 90) / 100;
            params.stopLossTriggerPrice = (mark * 110) / 100;
        } else {
            params.takeProfitTriggerPrice = (mark * 110) / 100;
            params.stopLossTriggerPrice = (mark * 90) / 100;
        }
        params.closeLimits = PositionProtectionTypes.CloseFinancialLimits({
            maxExecutionNotionalAssets: type(uint256).max,
            maxGrossAccountDebitAssets: type(uint256).max,
            maxActionChargeAssets: type(uint256).max,
            maxExplicitFeesAssets: type(uint256).max
        });
    }

    function _armProtection(address who) internal returns (uint64 protectionId) {
        // Close/latch installs a newer engine mark than the live basket. Publish one
        // in-order tick so protection observation is not PriceOutOfOrder.
        uint256 mark = engine.lastMarkPrice();
        _publish(mark == 0 ? 1e8 : mark);
        // Read params before prank: engine.positions() is an external call and
        // would otherwise consume vm.prank, so create would run as the test contract.
        PositionProtectionTypes.PositionProtectionParams memory params = _protectionParams(who);
        vm.prank(who);
        protectionId = protection.createPositionProtection(params);
        lastProtectionId = protectionId;
    }

    function _expireQueued(uint64 oid) internal {
        uint64 deadline = book.orderTiming(oid).executionDeadline;
        if (block.timestamp <= deadline) {
            vm.warp(uint256(deadline) + 1);
        }
        try router.expireOrder(oid) {} catch {}
    }

    function _queueAndExpireProtection(address who) internal returns (uint64 protectionId) {
        // Arm, trigger a linked close, expire it without filling. Retry/amend then
        // acts on a latched protection while no live child remains queued.
        protectionId = _armProtection(who);
        PositionProtectionTypes.PositionProtectionParams memory params = _protectionParams(who);
        uint256 triggerMark = params.takeProfitTriggerPrice == 0
            ? params.stopLossTriggerPrice
            : params.takeProfitTriggerPrice;
        if (block.timestamp <= engine.lastMarkTime()) {
            vm.warp(uint256(engine.lastMarkTime()) + 1);
        }
        uint64 linked = protection.triggerPositionProtection(protectionId, _mockPythUpdateData(triggerMark));
        _expireQueued(linked);
        lastProtectionId = protectionId;
    }
}
