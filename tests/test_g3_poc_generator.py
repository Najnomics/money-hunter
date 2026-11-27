"""Generic G3 PoC generator: strategies in, finding ids out."""
from __future__ import annotations

import unittest
from pathlib import Path

from tools.g3_poc_generator import render_file, render_test

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "tools" / "g3_poc_generator.py"


class G3PocGeneratorTests(unittest.TestCase):
    def test_settle_shareprice_emits_epoch_and_receipt_helpers(self):
        src = render_test("settleLpEpoch", "sharePrice", "refundable-receipt-in-nav")
        self.assertIn("function test_attack_settleLpEpoch_sharePrice", src)
        self.assertIn("_queueDeposit", src)
        self.assertIn("_warpToDepositEpoch", src)
        self.assertIn("_openFilled", src)
        self.assertIn("_snapshotNav", src)
        self.assertIn("snapshotVictim", src)
        self.assertIn("incumbent assets ignored reclaimable receipt", src)
        self.assertLess(src.index("_openFilled"), src.index("_queueDeposit"))
        self.assertLess(src.index("_warpToDepositEpoch"), src.index("_snapshotNav"))

    def test_assign_unassigned_emits_residual_seed(self):
        src = render_test("assignUnassignedAssets", "unassignedAssets", "hwm-recap-accounting")
        self.assertIn("_seedUnownedResidual", src)
        self.assertIn("pool.assignUnassignedAssets", src)
        self.assertNotIn("pool.accountExcess", src)

    def test_rebate_var_asserts_reserve_not_junior_nav(self):
        src = render_test("executeClose", "vpiRebateReserve", "refundable-receipt-in-nav")
        self.assertIn("_snapshotRebate(ATTACKER)", src)
        self.assertIn("_rebateOf(ATTACKER)", src)
        self.assertNotIn("snapshotVictim", src)
        src_w = render_test("withdraw", "vpiRebateReserve", "refundable-receipt-in-nav")
        self.assertIn("_openFilled(ATTACKER, _short()", src_w)
        self.assertIn("_snapshotRebate(ATTACKER)", src_w)
        self.assertIn("_snapshotNav()", src_w)
        self.assertIn("snapshotVictim", src_w)
        src_o = render_test("executeOpen", "vpiRebateReserve", "refundable-receipt-in-nav")
        self.assertIn("_openFilled(VICTIM, _long()", src_o)
        self.assertIn("_short()", src_o)

    def test_execute_order_accepted_basket_requires_executed(self):
        src = render_test("executeOrder", "acceptedBasket", "oracle-staleness-calendar-watermark")
        self.assertIn("LifecycleStatus.Executed", src)
        self.assertIn("execute after oracle/config print failed", src)

    def test_execute_order_freesettlement_executes_the_pending_head(self):
        src = render_test("executeOrder", "freeSettlement", "delayed-order-optionality")
        self.assertIn("_commitAs", src)
        self.assertIn("executeOrder(router.nextExecuteId()", src)
        self.assertIn("LifecycleStatus.Executed", src)
        self.assertNotIn("executeOrder(lastCommitId", src)
        self.assertNotIn('_openReq("x"', src)

    def test_execute_liquidation_without_pending_print_uses_valid_try_catch(self):
        src = render_test("adverseLiquidationPrice", "acceptedBasket", "oracle-staleness-calendar-watermark")
        self.assertIn("try router.executeLiquidationBatch", src)
        self.assertNotIn("1.5e8)); {}", src)
        self.assertIn("try router.executeLiquidationBatch(accounts, _mockPythUpdateData(1.5e8)) {} catch {}", src)

    def test_execute_liquidation_delayed_order_targets_the_pending_account(self):
        src = render_test("executeLiquidationBatch", "freeSettlement", "delayed-order-optionality")
        self.assertIn("accounts[0] = ATTACKER", src)
        self.assertNotIn("accounts[0] = VICTIM", src)
        self.assertNotIn("try router.executeLiquidationBatch", src)
        self.assertIn("_sweepUntilLiquidatable", src)
        self.assertIn("_openThinFilled", src)
        self.assertIn("nextExecuteId", src)
        self.assertIn("liqMark", src)

    def test_execute_liquidation_reserve_asserts_bucket_move(self):
        src = render_test(
            "executeLiquidationBatch", "liquidationReserve", "delayed-order-optionality"
        )
        self.assertIn("_snapshotLiqReserve", src)
        self.assertIn("liquidation reserve path was a no-op", src)
        self.assertIn("_sweepUntilLiquidatable", src)
        self.assertNotIn('revert("no distinguishing assertion for this pair")', src)

    def test_settle_trader_claim_emits_claim_seed_and_pending_print(self):
        src = render_test("settleTraderClaim", "freeSettlement", "delayed-order-optionality")
        self.assertIn("_seedTraderClaim", src)
        self.assertIn("engine.settleTraderClaim(ATTACKER)", src)
        self.assertNotIn("try engine.settleTraderClaim", src)
        self.assertNotIn("_openFilled", src)
        self.assertIn("claim/free path was a no-op", src)

    def test_hwm_reconcile_emits_second_pass_and_hwm_snapshot(self):
        src = render_test("reconcile", "highWaterMark", "hwm-recap-accounting")
        self.assertIn("_seedPendingRecap", src)
        self.assertIn("_snapshotHwm", src)
        self.assertIn("seniorHighWaterMark() != snapshotHwm", src)
        self.assertGreaterEqual(src.count("_settleLpEpochForTest()"), 2)
        self.assertGreaterEqual(src.count("_warpToDepositEpoch"), 2)
        snap = src.index("_snapshotHwm")
        self.assertNotIn("_queueDeposit", src[snap:])

    def test_execute_open_degraded_closes_the_counterparty(self):
        src = render_test("executeOpen", "degradedMode", "false-emergency-mode")
        self.assertIn("_openFilled(VICTIM, _short()", src)
        self.assertIn("_closeFilled(VICTIM)", src)
        self.assertIn("_thinPool()", src)
        self.assertIn("_openAtFirstLegalMark", src)

    def test_settle_unassigned_does_not_queue_after_residual(self):
        src = render_test("settleLpEpoch", "unassignedAssets", "hwm-recap-accounting")
        self.assertGreaterEqual(src.count("_warpToDepositEpoch"), 2)
        residual = src.index("_seedUnownedResidual")
        self.assertNotIn("_queueDeposit", src[residual:])
        self.assertIn("_trySettleLpEpoch()", src)
        self.assertNotIn("try _settleLpEpochForTest()", src)

    def test_addmargin_emits_free_snapshot_and_price_print(self):
        src = render_test("addMargin", "freeSettlement", "delayed-order-optionality")
        self.assertIn("_snapshotFree", src)
        self.assertIn("_publish", src)
        self.assertIn("engine.addMargin", src)

    def test_execute_close_emits_hedge_and_price_move(self):
        src = render_test("executeClose", "degradedMode", "false-emergency-mode")
        self.assertIn("_openFilled(ATTACKER", src)
        self.assertIn("_openFilled(VICTIM", src)
        self.assertIn("_thinPool", src)
        self.assertIn("_thinPoolTo(10_000e6)", src)
        self.assertIn("_publish(1.5e8)", src)
        self.assertIn("_closeFilled", src)
        self.assertIn("degradedMode", src)

    def test_generator_source_has_no_finding_ids(self):
        src = GEN.read_text(encoding="utf-8")
        for finding in ("97591", "98209", "98854", "97590", "99136", "97906"):
            self.assertNotIn(finding, src)

    def test_render_file_dedupes_same_pair(self):
        src = render_file(
            [
                ("settleLpEpoch", "sharePrice", "refundable-receipt-in-nav"),
                ("settleLpEpoch", "sharePrice", "refundable-receipt-in-nav"),
            ]
        )
        self.assertEqual(src.count("function test_attack_settleLpEpoch_sharePrice"), 1)

    def test_blind_catalog_is_named_open_plus_pair_only(self):
        from tools.g3_harness import NAMED_OPEN_IDS, VERIFIED_IDS
        from tools.g3_poc_generator import blind_items

        named, pair_only = blind_items()
        remaining_named = [i for i in NAMED_OPEN_IDS if i not in VERIFIED_IDS]
        self.assertEqual(len(named), len(NAMED_OPEN_IDS))
        self.assertEqual(len(remaining_named), 11)
        self.assertEqual(len(pair_only), 25)
        self.assertEqual(len(VERIFIED_IDS), 32)
        src = GEN.read_text(encoding="utf-8")
        self.assertNotIn("findings/plether-key", src)


if __name__ == "__main__":
    unittest.main()
