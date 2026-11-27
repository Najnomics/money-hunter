"""Coverage must fail closed when a critical flow is unmapped."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from schemas.phase6 import CoverageInput
from tests.helpers import make_ctx
from tools.phase6_validate import coverage_check

coverage_check = coverage_check.handler


class CoverageFailClosedTests(unittest.TestCase):
    def test_unmapped_critical_flow_does_not_count_as_covered(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            ctx.state.write_section(
                2,
                "flows",
                {
                    "flows": [
                        {"id": "FLOW-1", "name": "deposit", "critical": True, "entry": "Vault.deposit(uint256)"},
                        {"id": "FLOW-2", "name": "preview", "critical": False, "entry": "Vault.previewDeposit(uint256)"},
                    ]
                },
            )
            ctx.state.write_section(
                3,
                "ast_map",
                {
                    "method": "regex",
                    "mapped_flows": {},
                    "surfaces": [],
                    "divergences": [
                        {
                            "id": "DIV-0001",
                            "kind": "unmapped_critical_flow",
                            "flow_id": "FLOW-1",
                            "expected": "entrypoint Vault.deposit",
                            "observed": "no matching implementation surface found",
                        }
                    ],
                },
            )
            out = coverage_check(ctx, CoverageInput())
            self.assertEqual(out.ratio, 0.0)
            self.assertEqual(out.confidence, "fail-closed")
            self.assertEqual(out.summary["fail_closed"], 1)
            self.assertEqual(out.summary["flows_covered"], 0)
            self.assertEqual(out.summary["unmapped_critical_flows"], 1)
            self.assertTrue(any(g.type == "unmapped_critical_flow" for g in out.gaps))
            self.assertTrue(out.notes and out.notes[0].startswith("FAIL-CLOSED"))

    def test_mapped_critical_flow_is_not_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            ctx.state.write_section(
                2,
                "flows",
                {"flows": [{"id": "FLOW-1", "name": "deposit", "critical": True}]},
            )
            ctx.state.write_section(
                3,
                "ast_map",
                {
                    "method": "tree-sitter",
                    "mapped_flows": {"FLOW-1": ["src/Vault.sol:10"]},
                    "surfaces": [{"file": "src/Vault.sol", "line": 10, "name": "deposit"}],
                    "divergences": [],
                },
            )
            ctx.state.write_section(
                4,
                "gap_fill",
                {"seeded_from": ["never-generated"], "uncovered": [], "hypotheses": []},
            )
            out = coverage_check(ctx, CoverageInput())
            self.assertEqual(out.ratio, 1.0)
            self.assertNotEqual(out.confidence, "fail-closed")
            self.assertEqual(out.summary["fail_closed"], 0)
            self.assertEqual(out.summary["unmapped_critical_flows"], 0)

    def test_never_generated_gap_when_self_check_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            ctx.state.write_section(2, "flows", {"flows": []})
            ctx.state.write_section(3, "ast_map", {"mapped_flows": {}, "surfaces": [], "divergences": []})
            out = coverage_check(ctx, CoverageInput())
            self.assertTrue(any(g.id == "GAP-NEVER-GENERATED" for g in out.gaps))


if __name__ == "__main__":
    unittest.main()
