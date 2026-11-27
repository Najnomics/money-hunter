"""Cartesian mutator × value-var self-check."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from schemas.phase4 import NeverGeneratedInput
from tests.helpers import make_ctx
from tools.hypothesis_seed import hyp_touches_pair
from tools.phase4_specialists import never_generated_check

never_generated_check = never_generated_check.handler


class NeverGeneratedTests(unittest.TestCase):
    def test_generates_missing_pairs_and_skips_covered(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            ctx.state.write_section(
                2,
                "state_vocab",
                {"states": [{"var": "sharePrice"}, {"var": "totalSupply"}]},
            )
            ctx.state.write_section(
                3,
                "ast_map",
                {
                    "surfaces": [
                        {"file": "src/Vault.sol", "line": 10, "name": "deposit", "kind": "function", "entry": True},
                        {"file": "src/Vault.sol", "line": 40, "name": "redeem", "kind": "function", "entry": True},
                        {"file": "src/Vault.sol", "line": 80, "name": "previewDeposit", "kind": "function", "entry": True},
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
                            "divergence_id": "DIV-SEED-0001",
                            "lens": "dimensional",
                            "statement": "deposit can inflate sharePrice",
                            "falsifiable_prediction": "Call deposit and measure sharePrice.",
                            "sink": "sharePrice",
                            "evidence": ["pair:deposit::sharePrice"],
                        }
                    ]
                },
            )
            out = never_generated_check(ctx, NeverGeneratedInput())
            # previewDeposit is a getter and must not appear.
            generated_blob = " ".join(
                f"{h.statement} {h.falsifiable_prediction} {' '.join(h.evidence)}" for h in out.hypotheses
            )
            self.assertNotIn("previewDeposit", generated_blob)
            # deposit x sharePrice already touched.
            for hyp in out.hypotheses:
                self.assertFalse(hyp_touches_pair(hyp, "deposit", "sharePrice"))
            # redeem x totalSupply must be generated.
            self.assertTrue(
                any(hyp_touches_pair(h, "redeem", "totalSupply") for h in out.hypotheses),
                msg=[h.statement for h in out.hypotheses],
            )
            self.assertGreaterEqual(out.pairs_generated, 1)
            self.assertGreaterEqual(out.pairs_total, 3)  # 2 mutators × 2 vars minus getters

    def test_mentions_requires_both_tokens(self):
        hyp = {
            "statement": "deposit moves cash",
            "falsifiable_prediction": "measure cash",
            "sink": "cash",
            "evidence": [],
        }
        self.assertTrue(hyp_touches_pair(hyp, "deposit", "cash"))
        self.assertFalse(hyp_touches_pair(hyp, "redeem", "cash"))
        self.assertFalse(hyp_touches_pair(hyp, "deposit", "sharePrice"))


if __name__ == "__main__":
    unittest.main()
