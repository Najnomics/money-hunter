"""Fix 20: execute_queued_g3 runs forge distinguishing attacks (execute=true)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime import ToolError
from schemas.phase5 import ExecuteQueuedInput
from schemas.phase6 import ReportInput
from tests.helpers import make_ctx
from tools.g3_harness import NAMED_OPEN_IDS, run_distinguishing
from tools.phase5_sandbox import execute_queued_g3
from tools.phase6_validate import generate_report

execute_queued_g3 = execute_queued_g3.handler
generate_report = generate_report.handler


class ExecuteQueuedG3Tests(unittest.TestCase):
    def test_execute_false_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            with self.assertRaises(ToolError):
                execute_queued_g3(ctx, ExecuteQueuedInput(execute=False))

    def test_overflow_forge_confirms_and_g4_verifies(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            ctx.state.write_section(
                2, "state_vocab", {"states": [{"var": "totalSupply"}, {"var": "sharePrice"}]}
            )
            ctx.state.write_section(
                3,
                "ast_map",
                {
                    "surfaces": [
                        {
                            "file": "src/Vault.sol",
                            "line": 10,
                            "name": "convertToShares",
                            "kind": "function",
                            "entry": True,
                        }
                    ]
                },
            )
            ctx.state.write_section(
                4,
                "dimensional",
                {
                    "hypotheses": [
                        {
                            "id": "H-0001",
                            "divergence_id": "DIV-0001",
                            "lens": "battery:vault",
                            "statement": "Share supply overflow freezes convertToShares.",
                            "falsifiable_prediction": "Near uint max, convertToShares reverts.",
                            "sink": "totalSupply",
                            "evidence": ["[DEDUCED] pair:convertToShares::totalSupply"],
                            "status": "open",
                            "family": "share-supply-overflow",
                            "variant": "convertToShares::totalSupply",
                            "title": "convertToShares x totalSupply",
                        }
                    ]
                },
            )
            ctx.state.write_section(
                3,
                "research_divs",
                {
                    "divergences": [
                        {
                            "id": "DIV-0001",
                            "kind": "research_seed",
                            "expected": "conversions work",
                            "observed": "overflow freeze",
                            "confidence": "low",
                            "status": "candidate",
                            "source_tool": "test",
                            "evidence": ["[DEDUCED] fixture"],
                        }
                    ]
                },
            )
            out = execute_queued_g3(
                ctx, ExecuteQueuedInput(execute=True, include_named_open=True, max_run=4)
            )
            self.assertTrue(out.items)
            self.assertTrue(any(i.verdict == "confirmed" for i in out.items), msg=out.items)
            self.assertTrue(all(i.status == "ran" for i in out.items))
            self.assertTrue(all(i.experiment_class == "distinguishing" for i in out.items))
            ctx.state.append_items(
                5, "experiments", [i.model_dump(mode="json") for i in out.items]
            )
            report = generate_report(ctx, ReportInput())
            self.assertGreaterEqual(report.summary.get("verified_findings", 0), 1)

    def test_named_open_catalog_size(self):
        self.assertEqual(len(NAMED_OPEN_IDS), 38)
        self.assertEqual(len(set(NAMED_OPEN_IDS)), 38)

    def test_99136_forge_pass(self):
        result = run_distinguishing(
            family="delayed-order-optionality",
            function="commitOrder",
            var="executionWindow",
        )
        self.assertTrue(result["ok"], msg=result.get("stdout") or result.get("stderr"))


if __name__ == "__main__":
    unittest.main()
