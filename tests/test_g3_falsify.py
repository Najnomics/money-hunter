"""G3 tests must call real Plether and not pass on random pairs or patched code."""
from __future__ import annotations

import unittest
from pathlib import Path

from tools.g3_harness import run_distinguishing

ROOT = Path(__file__).resolve().parent.parent
TARGETS = ROOT / "harness" / "g3_plether" / "test" / "ApexG3Targets.t.sol"


class G3FalsifyTests(unittest.TestCase):
    def test_97591_and_99136_call_real_plether(self):
        src = TARGETS.read_text(encoding="utf-8")
        self.assertIn("import {BasePerpTest}", src)
        self.assertIn("router.commitOrder", src)
        self.assertIn("router.expireOrder", src)
        self.assertIn("juniorVault.convertToAssets", src)
        self.assertIn("juniorVault.convertToShares", src)
        self.assertIn("_settleLpEpochForTest", src)
        self.assertNotIn("nav = nav + vpiRebateReserve", src)
        self.assertNotIn("binding = false", src)

    def test_random_pairs_are_inconclusive(self):
        pairs = (
            ("deposit", "totalSupply"),
            ("finalizePoolConfig", "highWaterMark"),
            ("approve", "sharePrice"),
            ("harvest", "vpiRebateReserve"),
        )
        for fn, var in pairs:
            with self.subTest(fn=fn, var=var):
                result = run_distinguishing(family="share-supply-overflow", function=fn, var=var)
                self.assertFalse(result["ok"])
                self.assertTrue(result.get("inconclusive"), msg=result)


if __name__ == "__main__":
    unittest.main()
