"""Regression tests for Plether recall bugs: entry matching and Slither rc."""

from __future__ import annotations

import unittest

from tools._shared import entry_token
from tools.phase3_divergence import (
    SLITHER_RAN_CODES,
    Surface,
    UNDOCUMENTED_CAP,
    _match_surfaces,
)


class EntryMatchTests(unittest.TestCase):
    def test_entry_token_strips_abi_types(self):
        self.assertEqual(entry_token("MarginClearinghouse.depositFor(address,uint256)"), "depositFor")
        self.assertEqual(entry_token("OrderRouter.executeOrder(uint64,bytes[])"), "executeOrder")
        self.assertEqual(entry_token("HousePool.settleLpEpoch(uint256,uint256)"), "settleLpEpoch")
        self.assertEqual(entry_token("GET /v1/withdraw"), "withdraw")

    def test_match_surfaces_does_not_use_argument_types(self):
        surfaces = [
            Surface(file="src/CfdClosePreview.sol", line=1, name="previewClose", kind="function", language="solidity"),
            Surface(
                file="src/MarginClearinghouse.sol",
                line=371,
                name="depositFor",
                kind="function",
                language="solidity",
                entry=True,
            ),
            Surface(file="src/MarginClearinghouse.sol", line=10, name="uint256", kind="function", language="solidity"),
        ]
        hits = _match_surfaces("MarginClearinghouse.depositFor(address,uint256)", surfaces)
        self.assertEqual([h.name for h in hits], ["depositFor"])
        self.assertTrue(hits[0].file.endswith("MarginClearinghouse.sol"))

    def test_commit_order_maps(self):
        surfaces = [
            Surface(
                file="src/OrderRouter.sol",
                line=88,
                name="commitOrder",
                kind="function",
                language="solidity",
                entry=True,
            ),
        ]
        self.assertTrue(_match_surfaces("OrderRouter.commitOrder(OrderV3Types.OrderRequest)", surfaces))

    def test_slither_255_is_ran(self):
        self.assertIn(255, SLITHER_RAN_CODES)
        self.assertGreaterEqual(UNDOCUMENTED_CAP, 200)


if __name__ == "__main__":
    unittest.main()
