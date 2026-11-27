// SPDX-License-Identifier: MIT
pragma solidity 0.8.35;

import {G3Sequence} from "./G3Sequence.sol";
import {CfdTypes} from "@plether/perps/CfdTypes.sol";
import {OrderV3Types} from "@plether/perps/OrderV3Types.sol";

/// Auto-generated distinguishing G3 attacks. Never submit.
contract ApexG3GeneratedTest is G3Sequence {
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

    function test_attack_commitOrder_minPublishTime() public {
        // strategy:oracle_first_tick — Fill with the first post-commit tick (commitTime+1), not a later keeper delay.
        uint64 oid = _commitAs(ATTACKER, _openReq("t", _long(), 60));
        router.executeOrder(oid, _mockPythUpdateData(1e8));
        uint64 tickOid = _commitAs(ATTACKER, _openReq("tick", _long(), 60));
        OrderV3Types.ExecutionResult memory result = router.executeOrder(tickOid, _mockPythUpdateData(1e8));
        require(uint8(result.status) == uint8(OrderV3Types.LifecycleStatus.Executed), "first tick failed");
    }

    function test_attack_quoteDepositFromState_totalSupply() public {
        // strategy:supply_headroom — Overflow/freeze probes drive virtual-offset supply to uint max before the mutator.
        _nearMaxSupply();
        try juniorVault.quoteDepositFromState(1e6, 1e6, type(uint256).max - 500, 0) returns (uint256) {} catch {}
        try juniorVault.convertToShares(1e6) returns (uint256) {
            revert("conversion not frozen");
        } catch {}
    }

    function test_attack_settleLpEpoch_totalSupply() public {
        // strategy:epoch_advance — settle/epoch reverts with no matured head (NoLpEpochProgress). Queue a pending deposit and warp to its epoch before the mutator.
        _queueDeposit(VICTIM, 10_000e6); _warpToDepositEpoch();
        // strategy:supply_headroom — Overflow/freeze probes drive virtual-offset supply to uint max before the mutator.
        _nearMaxSupply();
        _settleLpEpochForTest();
        try juniorVault.convertToShares(1e6) returns (uint256) {
            revert("conversion not frozen");
        } catch {}
    }

    function test_attack_assignUnassignedAssets_unassignedAssets() public {
        // strategy:unowned_residual — Write leftover into the unassigned bucket after the deposit is queued. Minting it before requestDeposit freezes the vault; accountExcess after a matured head consumes the epoch.
        _seedUnownedResidual(1e6);
        pool.assignUnassignedAssets(false, ATTACKER);
        require(
            juniorVault.balanceOf(ATTACKER) > 0 || pool.unassignedAssets() > 0
                || pool.pendingRecapitalizationAssets() > 0,
            "residual/HWM path minted nothing"
        );
    }

    function test_attack_addMargin_freeSettlement() public {
        // strategy:price_print_then_mutate — Delayed-order optionality is after the fill price is public. Commit, publish, then snapshot free and mutate. Liquidation uses unsafe_price_sweep instead of a fixed mark.
        _openFilled(ATTACKER, _long(), 60); lastCommitId = _commitAs(ATTACKER, _openReq("q", _long(), 60)); _publish(1.5e8);
        // strategy:locked_vs_free — Total balance often still includes committed/locked margin, so 'balance did not drop' is a false fail. Snapshot free = balance - locked after the price print / commit, not the raw settlement balance.
        _snapshotFree(ATTACKER);
        vm.prank(ATTACKER);
        engine.addMargin(ATTACKER, 1e6);
        require(_freeOf(ATTACKER) < snapshotFree, "free settlement did not drop");
    }

    function test_attack_convertToShares_totalSupply() public {
        // strategy:supply_headroom — Overflow/freeze probes drive virtual-offset supply to uint max before the mutator.
        _nearMaxSupply();
        try juniorVault.convertToShares(1e6) returns (uint256) {} catch {}
        try juniorVault.convertToShares(1e6) returns (uint256) {
            revert("conversion not frozen");
        } catch {}
    }

    function test_attack_executeClose_degradedMode() public {
        // strategy:thin_pool — A 1M junior buffer is far above one-side maxProfit, so a hedge close cannot trip effectiveAssets < maxLiability. Thin cash first.
        _thinPool();
        // strategy:multi_actor_hedge — A false emergency latch needs two actors on opposite sides, not a single solvent close.
        _openFilled(ATTACKER, _long(), 60); _openFilled(VICTIM, _short(), 60);
        // strategy:oracle_price_move — Close/execute after a material mark move, not at the seed price.
        _publish(1.5e8);
        // strategy:drain_cash — After the hedge is open, drain pool cash well below one-side maxProfit. A close that credits the pool still leaves cash < remaining maxLiability.
        _thinPoolTo(10_000e6);
        _closeFilled(ATTACKER);
        require(engine.degradedMode(), "split close did not latch degradedMode");
    }

    function test_attack_settleLpEpoch_unassignedAssets() public {
        // strategy:epoch_advance — settle/epoch reverts with no matured head (NoLpEpochProgress). Queue a pending deposit and warp to its epoch before the mutator.
        _queueDeposit(VICTIM, 10_000e6); _warpToDepositEpoch();
        // strategy:second_epoch — A leftover residual freezes the next requestDeposit. Queue a second matured epoch before seeding residual so a later observation still has a head.
        _queueDeposit(VICTIM, 1_000e6); _warpToDepositEpoch();
        // strategy:unowned_residual — Write leftover into the unassigned bucket after the deposit is queued. Minting it before requestDeposit freezes the vault; accountExcess after a matured head consumes the epoch.
        _seedUnownedResidual(1e6);
        _trySettleLpEpoch();
        require(
            juniorVault.balanceOf(ATTACKER) > 0 || pool.unassignedAssets() > 0
                || pool.pendingRecapitalizationAssets() > 0,
            "residual/HWM path minted nothing"
        );
    }

    function test_attack_reconcile_highWaterMark() public {
        // strategy:epoch_advance — settle/epoch reverts with no matured head (NoLpEpochProgress). Queue a pending deposit and warp to its epoch before the mutator.
        _queueDeposit(VICTIM, 10_000e6); _warpToDepositEpoch();
        // strategy:second_epoch — A leftover residual freezes the next requestDeposit. Queue a second matured epoch before seeding residual so a later observation still has a head.
        _queueDeposit(VICTIM, 1_000e6); _warpToDepositEpoch();
        // strategy:unowned_residual — Write leftover into the unassigned bucket after the deposit is queued. Minting it before requestDeposit freezes the vault; accountExcess after a matured head consumes the epoch.
        _seedUnownedResidual(1e6);
        // strategy:pending_recap — HWM/senior overwrite needs a leftover recap bucket. An unowned mint alone does not create a claimant residual for a second observation.
        _seedPendingRecap(1e6);
        // strategy:second_pass — HWM/recap overwrite is a second observation of the same books, not the first solvent epoch. The second matured head is queued in second_epoch before residual; do not requestDeposit after leftover is live.
        _snapshotHwm();
        _trySettleLpEpoch();
        _trySettleLpEpoch();
        require(
            pool.seniorHighWaterMark() != snapshotHwm
                || pool.pendingRecapitalizationAssets() > 0,
            "HWM path was a no-op"
        );
    }

    function test_attack_settleLpEpoch_seniorPrincipal() public {
        // strategy:epoch_advance — settle/epoch reverts with no matured head (NoLpEpochProgress). Queue a pending deposit and warp to its epoch before the mutator.
        _queueDeposit(VICTIM, 10_000e6); _warpToDepositEpoch();
        // strategy:second_epoch — A leftover residual freezes the next requestDeposit. Queue a second matured epoch before seeding residual so a later observation still has a head.
        _queueDeposit(VICTIM, 1_000e6); _warpToDepositEpoch();
        // strategy:pending_recap — HWM/senior overwrite needs a leftover recap bucket. An unowned mint alone does not create a claimant residual for a second observation.
        _seedPendingRecap(1e6);
        // strategy:second_pass — HWM/recap overwrite is a second observation of the same books, not the first solvent epoch. The second matured head is queued in second_epoch before residual; do not requestDeposit after leftover is live.
        _snapshotHwm();
        _trySettleLpEpoch();
        _trySettleLpEpoch();
        require(
            pool.seniorPrincipal() != snapshotSenior
                || pool.pendingRecapitalizationAssets() > 0,
            "senior principal ignored residual/recap"
        );
    }

    function test_attack_executeOrder_acceptedBasket() public {
        // strategy:oracle_price_move — Close/execute after a material mark move, not at the seed price.
        _publish(1.5e8);
        uint64 oid = _commitAs(ATTACKER, _openReq("x", _long(), 60));
        OrderV3Types.ExecutionResult memory execResult = router.executeOrder(oid, _mockPythUpdateData(1e8));
        require(
            uint8(execResult.status) == uint8(OrderV3Types.LifecycleStatus.Executed),
            "execute after oracle/config print failed"
        );
        require(engine.lastMarkPrice() != 0, "oracle/config path left mark at zero");
    }

    function test_attack_reconcile_unassignedAssets() public {
        // strategy:epoch_advance — settle/epoch reverts with no matured head (NoLpEpochProgress). Queue a pending deposit and warp to its epoch before the mutator.
        _queueDeposit(VICTIM, 10_000e6); _warpToDepositEpoch();
        // strategy:second_epoch — A leftover residual freezes the next requestDeposit. Queue a second matured epoch before seeding residual so a later observation still has a head.
        _queueDeposit(VICTIM, 1_000e6); _warpToDepositEpoch();
        // strategy:unowned_residual — Write leftover into the unassigned bucket after the deposit is queued. Minting it before requestDeposit freezes the vault; accountExcess after a matured head consumes the epoch.
        _seedUnownedResidual(1e6);
        _trySettleLpEpoch();
        require(
            juniorVault.balanceOf(ATTACKER) > 0 || pool.unassignedAssets() > 0
                || pool.pendingRecapitalizationAssets() > 0,
            "residual/HWM path minted nothing"
        );
    }

    function test_attack_assignUnassignedAssets_highWaterMark() public {
        // strategy:unowned_residual — Write leftover into the unassigned bucket after the deposit is queued. Minting it before requestDeposit freezes the vault; accountExcess after a matured head consumes the epoch.
        _seedUnownedResidual(1e6);
        // strategy:pending_recap — HWM/senior overwrite needs a leftover recap bucket. An unowned mint alone does not create a claimant residual for a second observation.
        _seedPendingRecap(1e6);
        _snapshotHwm();
        pool.assignUnassignedAssets(false, ATTACKER);
        require(
            pool.seniorHighWaterMark() != snapshotHwm
                || pool.pendingRecapitalizationAssets() > 0,
            "HWM path was a no-op"
        );
    }

    function test_attack_withdraw_freeSettlement() public {
        // strategy:filled_position — Close/margin probes need a live filled position, not an empty book.
        _openFilled(ATTACKER, _long(), 60);
        // strategy:price_print_then_mutate — Delayed-order optionality is after the fill price is public. Commit, publish, then snapshot free and mutate. Liquidation uses unsafe_price_sweep instead of a fixed mark.
        _openFilled(ATTACKER, _long(), 60); lastCommitId = _commitAs(ATTACKER, _openReq("q", _long(), 60)); _publish(1.5e8);
        // strategy:locked_vs_free — Total balance often still includes committed/locked margin, so 'balance did not drop' is a false fail. Snapshot free = balance - locked after the price print / commit, not the raw settlement balance.
        _snapshotFree(ATTACKER);
        uint256 free = _freeOf(ATTACKER);
        if (free > 0) { vm.prank(ATTACKER); clearinghouse.withdraw(ATTACKER, free); }
        require(_freeOf(ATTACKER) < snapshotFree, "free settlement did not drop");
    }

    function test_attack_commitOrder_freeSettlement() public {
        // strategy:price_print_then_mutate — Delayed-order optionality is after the fill price is public. Commit, publish, then snapshot free and mutate. Liquidation uses unsafe_price_sweep instead of a fixed mark.
        _openFilled(ATTACKER, _long(), 60); lastCommitId = _commitAs(ATTACKER, _openReq("q", _long(), 60)); _publish(1.5e8);
        // strategy:locked_vs_free — Total balance often still includes committed/locked margin, so 'balance did not drop' is a false fail. Snapshot free = balance - locked after the price print / commit, not the raw settlement balance.
        _snapshotFree(ATTACKER);
        _commitAs(ATTACKER, _openReq("c", _long(), 60));
        require(_freeOf(ATTACKER) < snapshotFree, "free settlement did not drop");
    }

    function test_attack_settleLpEpoch_pnlPledgeAssets() public {
        // strategy:receipt_open — NAV/sharePrice tests need a reclaimable receipt in flight. Open first so the outsider epoch is priced against that receipt.
        _openFilled(ATTACKER, _long(), 60);
        // strategy:epoch_advance — settle/epoch reverts with no matured head (NoLpEpochProgress). Queue a pending deposit and warp to its epoch before the mutator.
        _queueDeposit(VICTIM, 10_000e6); _warpToDepositEpoch();
        _snapshotNav();
        _settleLpEpochForTest();
        uint256 victimAfter = juniorVault.convertToAssets(juniorVault.balanceOf(address(this)));
        require(victimAfter != snapshotVictim, "incumbent assets ignored reclaimable receipt");
    }

    function test_attack_executeOrder_freeSettlement() public {
        // strategy:price_print_then_mutate — Delayed-order optionality is after the fill price is public. Commit, publish, then snapshot free and mutate. Liquidation uses unsafe_price_sweep instead of a fixed mark.
        _openFilled(ATTACKER, _long(), 60); lastCommitId = _commitAs(ATTACKER, _openReq("q", _long(), 60)); _publish(1.5e8);
        // strategy:locked_vs_free — Total balance often still includes committed/locked margin, so 'balance did not drop' is a false fail. Snapshot free = balance - locked after the price print / commit, not the raw settlement balance.
        _snapshotFree(ATTACKER);
        OrderV3Types.ExecutionResult memory execResult = router.executeOrder(router.nextExecuteId(), _mockPythUpdateData(1.5e8));
        require(
            uint8(execResult.status) == uint8(OrderV3Types.LifecycleStatus.Executed),
            "pending execute after print failed"
        );
    }

    function test_attack_executeOpen_vpiRebateReserve() public {
        // strategy:skew_seed — Rebate reserve is max(-vpiAccrued, 0). A first same-side open pays positive VPI and never locks the bucket. Seed opposite-side skew first.
        _openFilled(VICTIM, _long(), 60);
        _snapshotRebate(ATTACKER);
        uint64 oid = _commitAs(ATTACKER, _openReq("x", _short(), 60));
        OrderV3Types.ExecutionResult memory execResult = router.executeOrder(oid, _mockPythUpdateData(1e8));
        require(
            uint8(execResult.status) == uint8(OrderV3Types.LifecycleStatus.Executed),
            "execute after oracle/config print failed"
        );
        require(_rebateOf(ATTACKER) != snapshotRebate, "rebate reserve was a no-op");
    }

    function test_attack_executeLiquidationBatch_freeSettlement() public {
        // strategy:unsafe_price_sweep — Liquidation cleanup only voids a queued open if the live position is actually unsafe. Sweep marks until isLiquidatableAt, do not print 1.5x.
        _openThinFilled(ATTACKER, _long(), 60); lastCommitId = _commitAs(ATTACKER, _openReqAt("q", _long(), 60, 1_000e18, 100e6)); _sweepUntilLiquidatable(ATTACKER);
        // strategy:locked_vs_free — Total balance often still includes committed/locked margin, so 'balance did not drop' is a false fail. Snapshot free = balance - locked after the price print / commit, not the raw settlement balance.
        _snapshotFree(ATTACKER);
        address[] memory accounts = new address[](1);
        accounts[0] = ATTACKER;
        uint256 liqMark = engine.lastMarkPrice();
        if (liqMark == 0) liqMark = 1.5e8;
        router.executeLiquidationBatch(accounts, _mockPythUpdateData(liqMark));
        require(
            router.nextExecuteId() == 0 || _freeOf(ATTACKER) != snapshotFree,
            "liq cleanup left the pending order binding"
        );
    }

    function test_attack_settleTraderClaim_freeSettlement() public {
        // strategy:claim_seed — settleTraderClaim reverts with an empty claim bucket. Seed leftover into the standing claim before the mutator.
        _seedTraderClaim(ATTACKER, 1e6);
        // strategy:pending_then_print — A standing claim can void a queued open only after the fill price is public. Commit and print without a live position, which would take the pledge branch.
        lastCommitId = _commitAs(ATTACKER, _openReq("q", _long(), 60)); _publish(1.5e8);
        // strategy:locked_vs_free — Total balance often still includes committed/locked margin, so 'balance did not drop' is a false fail. Snapshot free = balance - locked after the price print / commit, not the raw settlement balance.
        _snapshotFree(ATTACKER);
        vm.prank(ATTACKER);
        engine.settleTraderClaim(ATTACKER);
        require(_freeOf(ATTACKER) != snapshotFree, "claim/free path was a no-op");
    }

    function test_attack_executeClose_vpiRebateReserve() public {
        // strategy:rebate_held — Close/withdraw rebate probes need an already-locked negative-VPI reserve from a skew-reducing open, not a lone long.
        _openFilled(VICTIM, _long(), 60); _openFilled(ATTACKER, _short(), 60);
        _snapshotRebate(ATTACKER);
        _closeFilled(ATTACKER);
        require(_rebateOf(ATTACKER) != snapshotRebate, "rebate reserve was a no-op");
    }

    function test_attack_executeOpen_degradedMode() public {
        // strategy:thin_pool — A 1M junior buffer is far above one-side maxProfit, so a hedge close cannot trip effectiveAssets < maxLiability. Thin cash first.
        _thinPool();
        // strategy:counterparty_open — Admission backing is revealed when an opposite-side winner already exists. A lone open into thin cash does not latch degradedMode.
        _openFilled(VICTIM, _short(), 60);
        // strategy:drain_after_hedge — After the counterparty fill, drain remaining cash so admission spends backing already owed to the winner.
        _thinPoolTo(25_000e6);
        // strategy:legal_mark_search — A hardcoded seed or 1.5x print is often skew-illegal after a counterparty fill. Search marks until executeOpen admits, then close the winner.
        _closeFilled(VICTIM);
        _openAtFirstLegalMark(ATTACKER, _long());
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

    function test_attack_commitOrder_executionWindow() public {
        // strategy:price_print_then_mutate — Delayed-order optionality is after the fill price is public. Commit, publish, then snapshot free and mutate. Liquidation uses unsafe_price_sweep instead of a fixed mark.
        _openFilled(ATTACKER, _long(), 60); lastCommitId = _commitAs(ATTACKER, _openReq("q", _long(), 60)); _publish(1.5e8);
        // strategy:warp_past_window — After commit, warp past the trader-chosen window before expire/execute.
        uint64 oid = _commitAs(ATTACKER, _openReq("w", _long(), 2));
        vm.warp(uint256(book.orderTiming(oid).executionDeadline) + 1);
        router.expireOrder(oid);
        uint64 windowOid = _commitAs(ATTACKER, _openReq("w2", _long(), 2));
        require(book.orderTiming(windowOid).executionWindowSeconds == 2, "2s window rejected");
    }

    function test_attack_applyRouterConfigAfterOracle_acceptedBasket() public {
        _publish(1.5e8);
        require(engine.lastMarkPrice() != 0, "oracle/config path left mark at zero");
    }

    function test_attack_executeClose_traderClaimBalance() public {
        // strategy:filled_position — Close/margin probes need a live filled position, not an empty book.
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
        // strategy:unsafe_price_sweep — Liquidation cleanup only voids a queued open if the live position is actually unsafe. Sweep marks until isLiquidatableAt, do not print 1.5x.
        _openThinFilled(ATTACKER, _long(), 60); lastCommitId = _commitAs(ATTACKER, _openReqAt("q", _long(), 60, 1_000e18, 100e6)); _sweepUntilLiquidatable(ATTACKER);
        _snapshotLiqReserve(ATTACKER);
        address[] memory accounts = new address[](1);
        accounts[0] = ATTACKER;
        uint256 liqMark = engine.lastMarkPrice();
        if (liqMark == 0) liqMark = 1.5e8;
        router.executeLiquidationBatch(accounts, _mockPythUpdateData(liqMark));
        require(
            clearinghouse.liquidationReserveAssets(ATTACKER) != snapshotLiqReserve,
            "liquidation reserve path was a no-op"
        );
    }

    function test_attack_applyOpen_liquidationReserve() public {
        // strategy:reserve_open — Open-path liquidation-reserve probes need a live filled account to reprice the bucket.
        _openFilled(ATTACKER, _long(), 60);
        _snapshotLiqReserve(ATTACKER);
        uint64 oid = _commitAs(ATTACKER, _openReq("g", _long(), 60));
        try router.executeOrder(oid, _mockPythUpdateData(1e8)) {} catch {}
        require(
            clearinghouse.liquidationReserveAssets(ATTACKER) != snapshotLiqReserve,
            "liquidation reserve path was a no-op"
        );
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
        // strategy:price_print_then_mutate — Delayed-order optionality is after the fill price is public. Commit, publish, then snapshot free and mutate. Liquidation uses unsafe_price_sweep instead of a fixed mark.
        _openFilled(ATTACKER, _long(), 60); lastCommitId = _commitAs(ATTACKER, _openReq("q", _long(), 60)); _publish(1.5e8);
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
        // strategy:price_print_then_mutate — Delayed-order optionality is after the fill price is public. Commit, publish, then snapshot free and mutate. Liquidation uses unsafe_price_sweep instead of a fixed mark.
        _openFilled(ATTACKER, _long(), 60); lastCommitId = _commitAs(ATTACKER, _openReq("q", _long(), 60)); _publish(1.5e8);
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
        // strategy:receipt_open — NAV/sharePrice tests need a reclaimable receipt in flight. Open first so the outsider epoch is priced against that receipt.
        _openFilled(ATTACKER, _long(), 60);
        // strategy:epoch_advance — settle/epoch reverts with no matured head (NoLpEpochProgress). Queue a pending deposit and warp to its epoch before the mutator.
        _queueDeposit(VICTIM, 10_000e6); _warpToDepositEpoch();
        _snapshotTreasury();
        _settleLpEpochForTest();
        require(
            clearinghouse.balanceAssets(engine.protocolTreasury()) != snapshotTreasury,
            "protocol treasury path was a no-op"
        );
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
        // strategy:filled_position — Close/margin probes need a live filled position, not an empty book.
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
