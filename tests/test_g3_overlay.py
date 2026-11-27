"""Family overlays are token-selected, not finding-specific."""
from __future__ import annotations

import unittest
from pathlib import Path

from tools.g3_overlay import overlay_id

ROOT = Path(__file__).resolve().parent.parent


class OverlaySelectionTests(unittest.TestCase):
    def test_four_pin_pass_targets_get_distinct_family_overlays(self):
        self.assertEqual(
            overlay_id("settleLpEpoch", "sharePrice", "refundable-receipt-in-nav"),
            "zero_vpi",
        )
        self.assertEqual(
            overlay_id("assignUnassignedAssets", "unassignedAssets", "hwm-recap-accounting"),
            "assign_outstanding",
        )
        self.assertEqual(overlay_id("addMargin", "freeSettlement", "delayed-order-optionality"), "pending_order")
        self.assertEqual(overlay_id("executeClose", "degradedMode", "false-emergency-mode"), "margin_backing")

    def test_free_settlement_cousins_use_pending_order(self):
        # Overlay must distinguish withdraw/commit/assess/evaluate, not only addMargin.
        for fn in ("withdraw", "commitOrder", "assessCommittedOrder", "evaluateOpen"):
            self.assertEqual(
                overlay_id(fn, "freeSettlement", "delayed-order-optionality"),
                "pending_order",
            )

    def test_senior_principal_uses_assign_outstanding(self):
        self.assertEqual(
            overlay_id("settleLpEpoch", "seniorPrincipal", "hwm-recap-accounting"),
            "assign_outstanding",
        )

    def test_overflow_and_window_stay_on_score_b_overlays(self):
        self.assertEqual(overlay_id("convertToShares", "totalSupply", "share-supply-overflow"), "overflow_headroom")
        self.assertEqual(overlay_id("commitOrder", "executionWindow", "delayed-order-optionality"), "min_window")
        self.assertEqual(
            overlay_id("commitOrder", "minPublishTime", "oracle-staleness-calendar-watermark"),
            "first_tick",
        )

    def test_overlay_module_has_no_finding_ids(self):
        src = (ROOT / "tools" / "g3_overlay.py").read_text(encoding="utf-8")
        for finding in ("97591", "98209", "98854", "97590", "99136", "97906"):
            self.assertNotIn(finding, src)

    def test_pending_order_also_guards_withdraw_and_stacked_commit(self):
        src = (ROOT / "tools" / "g3_overlay.py").read_text(encoding="utf-8")
        self.assertIn("MarginClearinghouse.sol", src)
        self.assertIn("committedOrderMarginAssets[account] > 0", src)
        self.assertIn("router/OrderLiquidationBatchLogic.sol", src)
        self.assertIn("OrderRouter__SettlementFloorOrderPending(0)", src)


if __name__ == "__main__":
    unittest.main()
