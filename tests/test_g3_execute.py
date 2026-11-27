"""Fix 20/21: execute_queued_g3 requires execute=true; exact Plether tests only."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime import ToolError
from schemas.phase5 import ExecuteQueuedInput
from tests.helpers import make_ctx
from tools.g3_harness import CONTEST_PIN, NAMED_OPEN_IDS, pinned_head, require_contest_pin, run_distinguishing
from tools.phase5_sandbox import execute_queued_g3

execute_queued_g3 = execute_queued_g3.handler


class ExecuteQueuedG3Tests(unittest.TestCase):
    def test_execute_false_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            with self.assertRaises(ToolError):
                execute_queued_g3(ctx, ExecuteQueuedInput(execute=False))

    def test_contest_pin_is_immunefi_freeze(self):
        self.assertEqual(CONTEST_PIN, "a82d4fefb02768e5b3bddcc97dee371eee24fea8")
        self.assertEqual(pinned_head(), CONTEST_PIN)
        self.assertEqual(require_contest_pin(), CONTEST_PIN)

    def test_named_open_catalog_size(self):
        self.assertEqual(len(NAMED_OPEN_IDS), 38)
        self.assertEqual(len(set(NAMED_OPEN_IDS)), 38)

    def test_random_pair_without_exact_test_is_inconclusive(self):
        result = run_distinguishing(
            family="share-supply-overflow",
            function="deposit",
            var="totalSupply",
        )
        self.assertFalse(result["ok"])
        self.assertTrue(result.get("inconclusive"), msg=result)

    def test_family_fallback_does_not_pass_unrelated_pair(self):
        result = run_distinguishing(
            family="refundable-receipt-in-nav",
            function="finalizePoolConfig",
            var="highWaterMark",
        )
        self.assertFalse(result["ok"])
        self.assertTrue(result.get("inconclusive"), msg=result)


if __name__ == "__main__":
    unittest.main()
