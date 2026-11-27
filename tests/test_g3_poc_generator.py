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
        self.assertIn("navBefore", src)
        self.assertIn("NAV ignored reclaimable receipt", src)

    def test_assign_unassigned_emits_residual_seed(self):
        src = render_test("assignUnassignedAssets", "unassignedAssets", "hwm-recap-accounting")
        self.assertIn("_seedUnownedResidual", src)
        self.assertIn("pool.assignUnassignedAssets", src)
        self.assertNotIn("pool.accountExcess", src)

    def test_addmargin_emits_free_snapshot_and_price_print(self):
        src = render_test("addMargin", "freeSettlement", "delayed-order-optionality")
        self.assertIn("_snapshotFree", src)
        self.assertIn("_publish", src)
        self.assertIn("engine.addMargin", src)

    def test_execute_close_emits_hedge_and_price_move(self):
        src = render_test("executeClose", "degradedMode", "false-emergency-mode")
        self.assertIn("_openFilled(ATTACKER", src)
        self.assertIn("_openFilled(VICTIM", src)
        self.assertIn("_publish(1.015e8)", src)
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


if __name__ == "__main__":
    unittest.main()
