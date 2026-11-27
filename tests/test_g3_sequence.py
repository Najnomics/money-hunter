"""Generic G3 sequences for the four pin-FAIL root causes. No finding-specific PoCs."""
from __future__ import annotations

import unittest
from pathlib import Path

from tools.g3_sequence import STRATEGIES, select_strategies, setup_block

ROOT = Path(__file__).resolve().parent.parent


class SequenceSelectionTests(unittest.TestCase):
    def test_settle_shareprice_needs_epoch_and_receipt_open(self):
        # Root cause: settleLpEpoch reverted NoLpEpochProgress with no matured head,
        # and NAV could not move without a reclaimable receipt in flight.
        chosen = select_strategies("settleLpEpoch", "sharePrice", "refundable-receipt-in-nav")
        self.assertIn("epoch_advance", chosen)
        self.assertIn("receipt_open", chosen)
        src = setup_block("settleLpEpoch", "sharePrice", "refundable-receipt-in-nav")
        self.assertIn("_queueDeposit", src)
        self.assertIn("_warpToDepositEpoch", src)
        self.assertIn("_openFilled", src)
        self.assertLess(src.index("_openFilled"), src.index("_queueDeposit"))

    def test_settle_unassigned_seeds_unowned_residual(self):
        chosen = select_strategies("settleLpEpoch", "unassignedAssets", "hwm-recap-accounting")
        self.assertIn("unowned_residual", chosen)
        src = setup_block("settleLpEpoch", "unassignedAssets", "hwm-recap-accounting")
        self.assertIn("_seedUnownedResidual", src)
        self.assertIn("_warpToDepositEpoch", src)
        self.assertLess(src.index("_seedUnownedResidual"), src.index("_warpToDepositEpoch"))

    def test_assign_unassigned_needs_unowned_residual_not_account_excess(self):
        # Root cause: mint-to-pool + accountExcess left unassigned=0.
        chosen = select_strategies("assignUnassignedAssets", "unassignedAssets", "hwm-recap-accounting")
        self.assertIn("unowned_residual", chosen)
        src = setup_block("assignUnassignedAssets", "unassignedAssets", "hwm-recap-accounting")
        self.assertIn("_seedUnownedResidual", src)
        self.assertNotIn("pool.accountExcess", src)

    def test_withdraw_rebate_holds_a_skew_reducing_open(self):
        chosen = select_strategies("withdraw", "vpiRebateReserve", "refundable-receipt-in-nav")
        self.assertIn("rebate_held", chosen)
        self.assertIn("pending_close", chosen)
        self.assertNotIn("filled_position", chosen)
        src = setup_block("withdraw", "vpiRebateReserve", "refundable-receipt-in-nav")
        self.assertIn("_openFilled(VICTIM", src)
        self.assertIn("_openFilled(ATTACKER, _short()", src)
        self.assertIn("_commitClose(ATTACKER)", src)
        self.assertLess(src.index("_openFilled(ATTACKER, _short()"), src.index("_commitClose"))

    def test_execute_open_rebate_seeds_opposite_skew(self):
        chosen = select_strategies("executeOpen", "vpiRebateReserve", "refundable-receipt-in-nav")
        self.assertIn("skew_seed", chosen)
        src = setup_block("executeOpen", "vpiRebateReserve", "refundable-receipt-in-nav")
        self.assertIn("_openFilled(VICTIM, _long()", src)

    def test_evaluate_open_freesettlement_prints_then_snapshots(self):
        chosen = select_strategies("evaluateOpen", "freeSettlement", "delayed-order-optionality")
        self.assertIn("locked_vs_free", chosen)
        self.assertIn("price_print_then_mutate", chosen)
        src = setup_block("evaluateOpen", "freeSettlement", "delayed-order-optionality")
        self.assertIn("_snapshotFree", src)
        self.assertIn("_publish", src)
        self.assertLess(src.index("_publish"), src.index("_snapshotFree"))

    def test_addmargin_freesettlement_snapshots_free_after_price_print(self):
        # Root cause: total balance still included committed margin.
        chosen = select_strategies("addMargin", "freeSettlement", "delayed-order-optionality")
        self.assertIn("locked_vs_free", chosen)
        self.assertIn("price_print_then_mutate", chosen)
        src = setup_block("addMargin", "freeSettlement", "delayed-order-optionality")
        self.assertIn("_snapshotFree", src)
        self.assertIn("_publish", src)
        self.assertLess(src.index("_publish"), src.index("_snapshotFree"))

    def test_execute_close_degraded_needs_two_actors_and_price_move(self):
        # Root cause: single-leg close at the seed price did not latch degradedMode.
        chosen = select_strategies("executeClose", "degradedMode", "false-emergency-mode")
        self.assertIn("thin_pool", chosen)
        self.assertIn("multi_actor_hedge", chosen)
        self.assertIn("oracle_price_move", chosen)
        self.assertIn("drain_cash", chosen)
        src = setup_block("executeClose", "degradedMode", "false-emergency-mode")
        self.assertIn("_thinPool", src)
        self.assertIn("_thinPoolTo(10_000e6)", src)
        self.assertIn("_openFilled(ATTACKER", src)
        self.assertIn("_openFilled(VICTIM", src)
        self.assertIn("_publish(1.5e8)", src)
        self.assertLess(src.index("_thinPool"), src.index("_openFilled"))
        self.assertLess(src.index("_openFilled"), src.index("_thinPoolTo"))

    def test_random_deposit_total_supply_is_not_a_hedge_sequence(self):
        chosen = select_strategies("deposit", "totalSupply", "")
        self.assertNotIn("multi_actor_hedge", chosen)
        self.assertNotIn("oracle_price_move", chosen)

    def test_sequence_helper_can_snapshot_rebate_reserve(self):
        src = (ROOT / "harness" / "g3_plether" / "test" / "G3Sequence.sol").read_text(encoding="utf-8")
        self.assertIn("vpiRebateReserveAssets", src)
        self.assertIn("_snapshotRebate", src)
        self.assertNotIn("97591", src)

    def test_close_helper_uses_live_mark_not_hardcoded_shock(self):
        src = (ROOT / "harness" / "g3_plether" / "test" / "G3Sequence.sol").read_text(encoding="utf-8")
        close = src.split("function _closeFilled", 1)[1]
        self.assertIn("lastMarkPrice", close)
        self.assertIn("_commitClose(who)", close)
        self.assertIn("function _commitClose", src)
        self.assertIn("engine.positions(who)", src)
        self.assertNotIn("_mockPythUpdateData(1.5e8)", close)

    def test_strategy_module_has_no_finding_ids(self):
        src = (ROOT / "tools" / "g3_sequence.py").read_text(encoding="utf-8")
        for finding in ("97591", "98209", "98854", "97590", "99136"):
            self.assertNotIn(finding, src)

    def test_every_strategy_has_a_why(self):
        self.assertGreaterEqual(len(STRATEGIES), 13)
        for strat in STRATEGIES:
            self.assertTrue(strat.why.strip())


if __name__ == "__main__":
    unittest.main()
