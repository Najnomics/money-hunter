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
        from tools.g3_harness import VERIFIED_IDS
        from tools.g3_poc_generator import blind_items

        named, pair_only = blind_items()
        self.assertEqual(len(named), 23)
        self.assertEqual(len(pair_only), 25)
        self.assertEqual(len(VERIFIED_IDS), 19)
        src = GEN.read_text(encoding="utf-8")
        self.assertNotIn("findings/plether-key", src)


if __name__ == "__main__":
    unittest.main()
