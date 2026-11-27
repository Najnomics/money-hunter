"""Regression tests for matcher, Slither rc/json-out, and undocumented cap."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from adapters.evm import ADAPTER
from tools._shared import entry_token
from tools.phase3_divergence import (
    SLITHER_RAN_CODES,
    Surface,
    UNDOCUMENTED_CAP,
    UNMAPPED_KINDS,
    _build_command,
    _match_surfaces,
    _parse_slither,
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

    def test_empty_entry_matches_nothing(self):
        surfaces = [Surface(file="src/A.sol", line=1, name="deposit", kind="function", language="solidity")]
        self.assertEqual(_match_surfaces("", surfaces), [])

    def test_contract_disambiguates_duplicate_names(self):
        surfaces = [
            Surface(file="src/Vault.sol", line=10, name="deposit", kind="function", language="solidity", entry=True),
            Surface(file="src/Router.sol", line=20, name="deposit", kind="function", language="solidity", entry=True),
        ]
        hits = _match_surfaces("Vault.deposit(uint256)", surfaces)
        self.assertEqual([h.file for h in hits], ["src/Vault.sol"])

    def test_slither_255_is_ran(self):
        self.assertIn(255, SLITHER_RAN_CODES)
        self.assertGreaterEqual(UNDOCUMENTED_CAP, 200)
        self.assertIn("unmapped_critical_flow", UNMAPPED_KINDS)

    def test_slither_command_writes_json_file_not_stdout(self):
        slither = ADAPTER.static_tools[0]
        self.assertIn("{json_out}", slither.args)
        command, reason, _cwd = _build_command(
            slither, ["/tmp/src"], None, json_out=Path("/tmp/sweep/slither-1.json")
        )
        self.assertIsNone(reason)
        self.assertIn("--json", command)
        self.assertIn("/tmp/sweep/slither-1.json", command)
        self.assertNotIn("-", command[command.index("--json") + 1 :])

    def test_parse_slither_reads_detectors_payload(self):
        payload = json.dumps(
            {
                "results": {
                    "detectors": [
                        {
                            "check": "reentrancy-eth",
                            "impact": "High",
                            "description": "Reentrancy in withdraw",
                            "elements": [
                                {
                                    "source_mapping": {
                                        "filename_relative": "src/Vault.sol",
                                        "lines": [88],
                                    }
                                }
                            ],
                        }
                    ]
                }
            }
        )
        findings = _parse_slither(payload, None, 10)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["rule"], "reentrancy-eth")
        self.assertEqual(findings[0]["file"], "src/Vault.sol")
        self.assertEqual(findings[0]["line"], 88)
        self.assertEqual(_parse_slither("not-json", None, 10), [])


if __name__ == "__main__":
    unittest.main()
