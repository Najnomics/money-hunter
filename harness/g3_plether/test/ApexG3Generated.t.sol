// SPDX-License-Identifier: MIT
pragma solidity 0.8.35;

import {G3Sequence} from "./G3Sequence.sol";
import {CfdTypes} from "@plether/perps/CfdTypes.sol";
import {OrderV3Types} from "@plether/perps/OrderV3Types.sol";

/// Auto-generated distinguishing G3 attacks. Never submit.
contract ApexG3GeneratedTest is G3Sequence {
    function test_attack_settleLpEpoch_unassignedAssets() public {
        // strategy:unowned_residual — mint-to-pool + accountExcess books into accountedAssets / junior, so unassigned stays 0. Account the cash then reserve that slice in the unassigned bucket so reconcile cannot treat it as junior revenue. Seed before epoch warp; accountExcess after a matured head consumes it.
        _seedUnownedResidual(1e6);
        // strategy:epoch_advance — settle/epoch reverts with no matured head (NoLpEpochProgress). Queue a pending deposit and warp to its epoch before the mutator.
        _queueDeposit(VICTIM, 10_000e6); _warpToDepositEpoch();
        _settleLpEpochForTest();
        require(
            juniorVault.balanceOf(ATTACKER) > 0 || pool.unassignedAssets() > 0,
            "residual/HWM path minted nothing"
        );
    }

    function test_attack_reconcile_highWaterMark() public {
        // strategy:unowned_residual — mint-to-pool + accountExcess books into accountedAssets / junior, so unassigned stays 0. Account the cash then reserve that slice in the unassigned bucket so reconcile cannot treat it as junior revenue. Seed before epoch warp; accountExcess after a matured head consumes it.
        _seedUnownedResidual(1e6);
        // strategy:epoch_advance — settle/epoch reverts with no matured head (NoLpEpochProgress). Queue a pending deposit and warp to its epoch before the mutator.
        _queueDeposit(VICTIM, 10_000e6); _warpToDepositEpoch();
        _settleLpEpochForTest();
        require(
            juniorVault.balanceOf(ATTACKER) > 0 || pool.unassignedAssets() > 0,
            "residual/HWM path minted nothing"
        );
    }

    function test_attack_settleLpEpoch_seniorPrincipal() public {
        // strategy:epoch_advance — settle/epoch reverts with no matured head (NoLpEpochProgress). Queue a pending deposit and warp to its epoch before the mutator.
        _queueDeposit(VICTIM, 10_000e6); _warpToDepositEpoch();
        _snapshotNav();
        _settleLpEpochForTest();
        require(pool.seniorPrincipal() != snapshotNav, "senior principal ignored residual/recap");
    }

    function test_attack_executeOrder_acceptedBasket() public {
        // strategy:oracle_price_move — Close/execute after a material mark move, not at the seed price.
        _publish(1.5e8);
        uint64 oid = _commitAs(ATTACKER, _openReq("x", _long(), 60));
        router.executeOrder(oid, _mockPythUpdateData(1e8));
        require(engine.lastMarkPrice() != 0, "oracle/config path left mark at zero");
    }

    function test_attack_reconcile_unassignedAssets() public {
        // strategy:unowned_residual — mint-to-pool + accountExcess books into accountedAssets / junior, so unassigned stays 0. Account the cash then reserve that slice in the unassigned bucket so reconcile cannot treat it as junior revenue. Seed before epoch warp; accountExcess after a matured head consumes it.
        _seedUnownedResidual(1e6);
        // strategy:epoch_advance — settle/epoch reverts with no matured head (NoLpEpochProgress). Queue a pending deposit and warp to its epoch before the mutator.
        _queueDeposit(VICTIM, 10_000e6); _warpToDepositEpoch();
        _settleLpEpochForTest();
        require(
            juniorVault.balanceOf(ATTACKER) > 0 || pool.unassignedAssets() > 0,
            "residual/HWM path minted nothing"
        );
    }

    function test_attack_executeOrder_freeSettlement() public {
        // strategy:price_print_then_mutate — Delayed-order optionality is after the fill price is public. Commit, publish, then snapshot free and mutate.
        _openFilled(ATTACKER, _long(), 60); _commitAs(ATTACKER, _openReq("q", _long(), 60)); _publish(1.5e8);
        // strategy:locked_vs_free — Total balance often still includes committed/locked margin, so 'balance did not drop' is a false fail. Snapshot free = balance - locked after the price print / commit, not the raw settlement balance.
        _snapshotFree(ATTACKER);
        uint64 oid = _commitAs(ATTACKER, _openReq("x", _long(), 60));
        router.executeOrder(oid, _mockPythUpdateData(1e8));
        require(_freeOf(ATTACKER) < snapshotFree, "free settlement did not drop");
    }

    function test_attack_executeLiquidationBatch_freeSettlement() public {
        // strategy:price_print_then_mutate — Delayed-order optionality is after the fill price is public. Commit, publish, then snapshot free and mutate.
        _openFilled(ATTACKER, _long(), 60); _commitAs(ATTACKER, _openReq("q", _long(), 60)); _publish(1.5e8);
        // strategy:locked_vs_free — Total balance often still includes committed/locked margin, so 'balance did not drop' is a false fail. Snapshot free = balance - locked after the price print / commit, not the raw settlement balance.
        _snapshotFree(ATTACKER);
        address[] memory accounts = new address[](1);
        accounts[0] = VICTIM;
        try router.executeLiquidationBatch(accounts, _mockPythUpdateData(1.5e8)) {} catch {}
        require(_freeOf(ATTACKER) < snapshotFree, "free settlement did not drop");
    }

    function test_attack_settleTraderClaim_freeSettlement() public {
        // strategy:epoch_advance — settle/epoch reverts with no matured head (NoLpEpochProgress). Queue a pending deposit and warp to its epoch before the mutator.
        _queueDeposit(VICTIM, 10_000e6); _warpToDepositEpoch();
        // strategy:filled_position — Close/margin/claim probes need a live filled position, not an empty book.
        _openFilled(ATTACKER, _long(), 60);
        _snapshotFree(ATTACKER);
        vm.prank(ATTACKER);
        try engine.settleTraderClaim(ATTACKER) {} catch {}
        require(_freeOf(ATTACKER) < snapshotFree, "free settlement did not drop");
    }

    function test_attack_settleLpEpoch_sharePrice() public {
        // strategy:receipt_open — NAV/sharePrice tests need a reclaimable receipt in flight. Open first so the outsider epoch is priced against that receipt.
        _openFilled(ATTACKER, _long(), 60);
        // strategy:epoch_advance — settle/epoch reverts with no matured head (NoLpEpochProgress). Queue a pending deposit and warp to its epoch before the mutator.
        _queueDeposit(VICTIM, 10_000e6); _warpToDepositEpoch();
        _snapshotNav();
        _settleLpEpochForTest();
        uint256 victimAfter = juniorVault.convertToAssets(juniorVault.balanceOf(address(this)));
        require(victimAfter != snapshotVictim, "incumbent assets ignored reclaimable receipt");
    }

    function test_attack_executeOpen_degradedMode() public {
        // strategy:thin_pool — A 1M junior buffer is far above one-side maxProfit, so a hedge close cannot trip effectiveAssets < maxLiability. Thin cash first.
        _thinPool();
        // strategy:multi_actor_hedge — A false emergency latch needs two actors on opposite sides, not a single solvent close.
        _openFilled(ATTACKER, _long(), 60); _openFilled(VICTIM, _short(), 60);
        // strategy:oracle_price_move — Close/execute after a material mark move, not at the seed price.
        _publish(1.5e8);
        uint64 oid = _commitAs(ATTACKER, _openReq("x", _long(), 60));
        router.executeOrder(oid, _mockPythUpdateData(1e8));
        require(engine.degradedMode(), "split close did not latch degradedMode");
    }

    function test_attack_withdraw_vpiRebateReserve() public {
        // strategy:rebate_held — Close/withdraw rebate probes need an already-locked negative-VPI reserve from a skew-reducing open, not a lone long.
        _openFilled(VICTIM, _long(), 60); _openFilled(ATTACKER, _short(), 60);
        // strategy:pending_close — A live rebate reserve is still locked while the position is open. Commit a close first so withdraw can waive or release that backing.
        _commitClose(ATTACKER);
        _snapshotRebate(ATTACKER);
        _snapshotNav();
        uint256 free = _freeOf(ATTACKER);
        if (free > 0) { vm.prank(ATTACKER); clearinghouse.withdraw(ATTACKER, free); }
        uint256 victimAfter = juniorVault.convertToAssets(juniorVault.balanceOf(address(this)));
        require(
            _rebateOf(ATTACKER) != snapshotRebate || victimAfter != snapshotVictim,
            "withdraw left rebate backing and incumbent NAV unchanged"
        );
    }

    function test_attack_applyRouterConfigAfterOracle_acceptedBasket() public {
        _publish(1.5e8);
        require(engine.lastMarkPrice() != 0, "oracle/config path left mark at zero");
    }

    function test_attack_commitOrder_freeSettlement() public {
        // strategy:price_print_then_mutate — Delayed-order optionality is after the fill price is public. Commit, publish, then snapshot free and mutate.
        _openFilled(ATTACKER, _long(), 60); _commitAs(ATTACKER, _openReq("q", _long(), 60)); _publish(1.5e8);
        // strategy:locked_vs_free — Total balance often still includes committed/locked margin, so 'balance did not drop' is a false fail. Snapshot free = balance - locked after the price print / commit, not the raw settlement balance.
        _snapshotFree(ATTACKER);
        _commitAs(ATTACKER, _openReq("c", _long(), 60));
        require(_freeOf(ATTACKER) < snapshotFree, "free settlement did not drop");
    }

    function test_attack_executeClose_traderClaimBalance() public {
        // strategy:filled_position — Close/margin/claim probes need a live filled position, not an empty book.
        _openFilled(ATTACKER, _long(), 60);
        _snapshotFree(ATTACKER);
        _closeFilled(ATTACKER);
        require(_freeOf(ATTACKER) != snapshotFree, "trader claim/free path was a no-op");
    }

    function test_attack_retryPositionProtectionClose_degradedMode() public {
        _closeFilled(ATTACKER);
        require(engine.degradedMode(), "split close did not latch degradedMode");
    }

    function test_attack_applyCalendarConfig_acceptedBasket() public {
        // calendar mutator — oracle helpers already ran
        _publish(1.5e8);
        require(engine.lastMarkPrice() != 0, "oracle/config path left mark at zero");
    }

    function test_attack_executeLiquidationBatch_liquidationReserve() public {
        address[] memory accounts = new address[](1);
        accounts[0] = VICTIM;
        try router.executeLiquidationBatch(accounts, _mockPythUpdateData(1.5e8)) {} catch {}
        revert("no distinguishing assertion for this pair");
    }

    function test_attack_applyOpen_liquidationReserve() public {
        uint64 oid = _commitAs(ATTACKER, _openReq("g", _long(), 60));
        try router.executeOrder(oid, _mockPythUpdateData(1e8)) {} catch {}
        revert("no distinguishing assertion for this pair");
    }

    function test_attack_adverseLiquidationPrice_acceptedBasket() public {
        address[] memory accounts = new address[](1);
        accounts[0] = VICTIM;
        try router.executeLiquidationBatch(accounts, _mockPythUpdateData(1.5e8)) {} catch {}
        require(engine.lastMarkPrice() != 0, "oracle/config path left mark at zero");
    }

    function test_attack_requestRedeem_sharePrice() public {
        // strategy:epoch_advance — settle/epoch reverts with no matured head (NoLpEpochProgress). Queue a pending deposit and warp to its epoch before the mutator.
        _queueDeposit(VICTIM, 10_000e6); _warpToDepositEpoch();
        _snapshotNav();
        uint256 shares = juniorVault.balanceOf(address(this));
        if (shares > 0) { juniorVault.requestRedeem(shares / 2, address(this), address(this)); }
        uint256 victimAfter = juniorVault.convertToAssets(juniorVault.balanceOf(address(this)));
        require(victimAfter != snapshotVictim, "incumbent assets ignored reclaimable receipt");
    }

    function test_attack_applyRouterConfig_currentExecutionConfigHash() public {
        _publish(1.5e8);
        require(engine.lastMarkPrice() != 0, "oracle/config path left mark at zero");
    }

    function test_attack_renounceOwnership_degradedMode() public {
        try pool.renounceOwnership() {} catch {}
        require(engine.degradedMode(), "split close did not latch degradedMode");
    }

    function test_attack_assessCommittedOrder_freeSettlement() public {
        // strategy:price_print_then_mutate — Delayed-order optionality is after the fill price is public. Commit, publish, then snapshot free and mutate.
        _openFilled(ATTACKER, _long(), 60); _commitAs(ATTACKER, _openReq("q", _long(), 60)); _publish(1.5e8);
        // strategy:locked_vs_free — Total balance often still includes committed/locked margin, so 'balance did not drop' is a false fail. Snapshot free = balance - locked after the price print / commit, not the raw settlement balance.
        _snapshotFree(ATTACKER);
        _commitAs(ATTACKER, _openReq("a", _long(), 60));
        require(_freeOf(ATTACKER) < snapshotFree, "free settlement did not drop");
    }

    function test_attack_retryPositionProtectionClose_vpiRebateReserve() public {
        // strategy:rebate_held — Close/withdraw rebate probes need an already-locked negative-VPI reserve from a skew-reducing open, not a lone long.
        _openFilled(VICTIM, _long(), 60); _openFilled(ATTACKER, _short(), 60);
        _snapshotRebate(ATTACKER);
        _closeFilled(ATTACKER);
        require(_rebateOf(ATTACKER) != snapshotRebate, "rebate reserve was a no-op");
    }

    function test_attack_evaluateOpen_freeSettlement() public {
        // strategy:price_print_then_mutate — Delayed-order optionality is after the fill price is public. Commit, publish, then snapshot free and mutate.
        _openFilled(ATTACKER, _long(), 60); _commitAs(ATTACKER, _openReq("q", _long(), 60)); _publish(1.5e8);
        // strategy:locked_vs_free — Total balance often still includes committed/locked margin, so 'balance did not drop' is a false fail. Snapshot free = balance - locked after the price print / commit, not the raw settlement balance.
        _snapshotFree(ATTACKER);
        _commitAs(ATTACKER, _openReq("a", _long(), 60));
        require(_freeOf(ATTACKER) < snapshotFree, "free settlement did not drop");
    }

    function test_attack_withdraw_degradedMode() public {
        uint256 free = _freeOf(ATTACKER);
        if (free > 0) { vm.prank(ATTACKER); clearinghouse.withdraw(ATTACKER, free); }
        require(engine.degradedMode(), "split close did not latch degradedMode");
    }

    function test_attack_settleLpEpoch_protocolTreasury() public {
        // strategy:epoch_advance — settle/epoch reverts with no matured head (NoLpEpochProgress). Queue a pending deposit and warp to its epoch before the mutator.
        _queueDeposit(VICTIM, 10_000e6); _warpToDepositEpoch();
        _settleLpEpochForTest();
        revert("no distinguishing assertion for this pair");
    }

    function test_attack_evaluateOpen_acceptedBasket() public {
        _commitAs(ATTACKER, _openReq("a", _long(), 60));
        require(engine.lastMarkPrice() != 0, "oracle/config path left mark at zero");
    }

    function test_attack_commitOrder_traderClaimBalance() public {
        _snapshotFree(ATTACKER);
        _commitAs(ATTACKER, _openReq("c", _long(), 60));
        require(_freeOf(ATTACKER) != snapshotFree, "trader claim/free path was a no-op");
    }

    function test_attack_executeClose_sharePrice() public {
        // strategy:filled_position — Close/margin/claim probes need a live filled position, not an empty book.
        _openFilled(ATTACKER, _long(), 60);
        _snapshotNav();
        _closeFilled(ATTACKER);
        uint256 victimAfter = juniorVault.convertToAssets(juniorVault.balanceOf(address(this)));
        require(victimAfter != snapshotVictim, "incumbent assets ignored reclaimable receipt");
    }

    function test_attack_arm_degradedMode() public {
        _closeFilled(ATTACKER);
        require(engine.degradedMode(), "split close did not latch degradedMode");
    }
}
