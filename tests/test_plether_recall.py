"""Regression: replay every Blind2 miss against the hardened gates.

Each case uses the real kill language or cartesian locus from
`origin/cursor/plether-blind2` SCORE.md / LEDGER.md. Passing here means that
exact drop no longer closes or omits the finding.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime import ToolError
from schemas.phase4 import NeverGeneratedInput, SeedResearchInput
from schemas.phase5 import RecordExperimentInput
from schemas.phase6 import CheckResult, CoverageInput, DisproofCheck, DisproveInput
from tests.helpers import make_ctx
from tests.plether_misses import MISSES, by_bucket, by_id
from tools.gate_policy import infer_experiment_class, is_freeze_value_flow
from tools.hypothesis_seed import hyp_touches_pair, is_public_mutator, list_value_vars
from tools.phase4_specialists import never_generated_check, seed_from_research
from tools.phase5_sandbox import record_experiment
from tools.phase6_validate import coverage_check, disprove_finding

never_generated_check = never_generated_check.handler
seed_from_research = seed_from_research.handler
record_experiment = record_experiment.handler
disprove_finding = disprove_finding.handler
coverage_check = coverage_check.handler


def _write_hyp(ctx, **fields) -> dict:
    hyp = {
        "id": fields.pop("id", "H-0001"),
        "divergence_id": "DIV-0001",
        "lens": fields.pop("lens", "battery:vault"),
        "statement": fields.pop("statement", "Share supply overflow can freeze convertToShares."),
        "falsifiable_prediction": fields.pop(
            "falsifiable_prediction",
            "Attacker mints until convertToShares reverts and deposits freeze.",
        ),
        "sink": fields.pop("sink", "totalSupply"),
        "evidence": fields.pop("evidence", ["[DEDUCED] family:share-supply-overflow"]),
        "status": "open",
        "family": fields.pop("family", None),
        "variant": fields.pop("variant", None),
    }
    hyp.update(fields)
    ctx.state.write_section(4, "dimensional", {"hypotheses": [hyp]})
    return hyp


def _log(root: Path, text: str) -> Path:
    path = root / ".apex" / "experiments" / "out.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _seed_pair(ctx, function: str, var: str) -> None:
    ctx.state.write_section(2, "state_vocab", {"states": [{"var": var}]})
    ctx.state.write_section(
        3,
        "ast_map",
        {
            "surfaces": [
                {
                    "file": "src/Target.sol",
                    "line": 40,
                    "name": function,
                    "kind": "function",
                    "entry": True,
                }
            ]
        },
    )


class CatalogSanityTests(unittest.TestCase):
    def test_catalog_matches_blind2_score_shape(self):
        self.assertEqual(len(MISSES), 63)
        self.assertEqual(len(by_bucket("KILLED")), 20)
        self.assertEqual(len(by_bucket("PAIR-ONLY")), 42)
        self.assertEqual(len(by_bucket("NEVER_GENERATED")), 1)
        self.assertEqual(
            [m.id for m in MISSES if m.sev == "C" and m.bucket == "KILLED"],
            ["97591", "97906", "98172", "99075", "98209", "98854"],
        )
        self.assertEqual(by_id("97628").sev, "H")
        self.assertEqual(by_id("97590").sev, "H")
        self.assertEqual(by_id("99136").bucket, "NEVER_GENERATED")


class KilledOverflowG4Tests(unittest.TestCase):
    """Fixes 11+18: replay H-0002 'supply unreachable' / astronomical language."""

    def test_killed_overflow_g4_survives(self):
        for miss in (by_id("98172"), by_id("99075"), by_id("97628")):
            with self.subTest(id=miss.id):
                with tempfile.TemporaryDirectory() as tmp:
                    ctx = make_ctx(Path(tmp))
                    self.assertTrue(is_freeze_value_flow({"family": miss.family, "statement": miss.kill_text}))
                    _write_hyp(
                        ctx,
                        family=miss.family,
                        statement=miss.root_cause,
                        sink=miss.var,
                        variant=None,
                    )
                    out = disprove_finding(
                        ctx,
                        DisproveInput(
                            hypothesis_id="H-0001",
                            checks=[
                                DisproofCheck(
                                    name="system-constraint",
                                    question="Does a cap make the impact unreachable?",
                                    result=CheckResult.BLOCKS,
                                    evidence=miss.kill_text,
                                )
                            ],
                        ),
                    )
                    item = out.items[0]
                    self.assertNotEqual(item.verdict, "disproved", msg=miss.id)
                    self.assertEqual(item.blocking_checks, [])
                    self.assertIn("freeze", item.rationale.lower())

    def test_99075_variant_kill_does_not_close_family(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            _write_hyp(
                ctx,
                family="share-supply-overflow",
                statement="Fee-share mint can freeze settlement for everyone.",
                falsifiable_prediction="A tiny fee mint near the offset limit locks redemptions.",
            )
            out = disprove_finding(
                ctx,
                DisproveInput(
                    hypothesis_id="H-0001",
                    variant="quoteDepositFromState",
                    checks=[
                        DisproofCheck(
                            name="auth-middleware",
                            question="Does auth block this mutator?",
                            result=CheckResult.BLOCKS,
                            evidence="onlyAdmin; unprivileged call is denied on this mutator.",
                        )
                    ],
                ),
            )
            self.assertEqual(out.items[0].verdict, "disproved-variant")
            self.assertEqual(out.items[0].scope, "variant")


class KilledG3StallTests(unittest.TestCase):
    """Fixes 12+17: real stall logs cannot pass/kill and are not coverage."""

    def test_killed_g3_stall_is_not_a_pass_or_kill(self):
        stalls = [m for m in by_bucket("KILLED") if m.drop_gate == "G3"]
        self.assertGreaterEqual(len(stalls), 12)
        for miss in stalls:
            with self.subTest(id=miss.id):
                klass = infer_experiment_class(observation=miss.kill_text, command="forge test")
                self.assertIn(klass, {"happy-path", "code-fact"}, msg=f"{miss.id}: {klass} for {miss.kill_text!r}")
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    ctx = make_ctx(root)
                    _write_hyp(
                        ctx,
                        family=miss.family,
                        statement=miss.root_cause,
                        sink=miss.var,
                    )
                    log = _log(root, miss.kill_text)
                    with self.assertRaises(ToolError) as raised:
                        record_experiment(
                            ctx,
                            RecordExperimentInput(
                                hypothesis_id="H-0001",
                                command="forge test --match-test test_roundtrip",
                                observation=miss.kill_text,
                                verdict="refuted",
                                output_path=str(log),
                            ),
                        )
                    self.assertIn("distinguishing", str(raised.exception).lower())
                    # Recording as inconclusive still does not count as tested.
                    recorded = record_experiment(
                        ctx,
                        RecordExperimentInput(
                            hypothesis_id="H-0001",
                            command="forge test --match-test test_roundtrip",
                            observation=miss.kill_text,
                            verdict="inconclusive",
                            output_path=str(log),
                        ),
                    )
                    ctx.state.append_items(
                        5, "experiments", [recorded.items[0].model_dump(mode="json")]
                    )
                    cov = coverage_check(ctx, CoverageInput())
                    self.assertTrue(
                        any(g.id == "GAP-DISTINGUISHING-H-0001" for g in cov.gaps),
                        msg=[g.id for g in cov.gaps],
                    )
                    self.assertTrue(
                        any(g.id == "GAP-HYP-H-0001" for g in cov.gaps),
                        msg="happy-path analog must not count as a distinguishing experiment",
                    )


class KilledFamilyVariantTests(unittest.TestCase):
    """Fix 13: 97591 mint-to-pool kill is not VPI-in-NAV."""

    def test_killed_family_variant_stays_live(self):
        miss = by_id("97591")
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            _write_hyp(
                ctx,
                family=miss.family,
                statement="Share price includes reclaimable receipts or VPI marks.",
            )
            out = disprove_finding(
                ctx,
                DisproveInput(
                    hypothesis_id="H-0001",
                    checks=[
                        DisproofCheck(
                            name="system-constraint",
                            question="Does min(raw, accounted) exclude mint-to-pool?",
                            result=CheckResult.BLOCKS,
                            evidence=miss.kill_text,
                        )
                    ],
                ),
            )
            self.assertEqual(out.items[0].verdict, "needs-variant")
            out2 = disprove_finding(
                ctx,
                DisproveInput(
                    hypothesis_id="H-0001",
                    variant="mint-to-pool",
                    checks=[
                        DisproofCheck(
                            name="system-constraint",
                            question="mint-to-pool analog",
                            result=CheckResult.BLOCKS,
                            evidence=miss.kill_text + " onlyAdmin.",
                        )
                    ],
                ),
            )
            self.assertEqual(out2.items[0].verdict, "disproved-variant")
            ctx.state.append_items(6, "disproofs", [out2.items[0].model_dump(mode="json")])
            cov = coverage_check(ctx, CoverageInput())
            self.assertTrue(any(g.id == "GAP-VARIANT-H-0001" for g in cov.gaps))
            # Cartesian still names the VPI-in-NAV pair as its own variant.
            _seed_pair(ctx, miss.function, miss.var)
            filled = never_generated_check(ctx, NeverGeneratedInput(max_generate=40, max_queue=8))
            self.assertTrue(
                any(hyp_touches_pair(h, miss.function, miss.var) for h in filled.hypotheses),
                msg=[h.statement for h in filled.hypotheses],
            )


class KilledPdfG2Tests(unittest.TestCase):
    """Fix 15: 98961 HWM excerpt is this pin, not 'wrong protocol'."""

    def test_killed_pdf_wrong_protocol_blocked(self):
        miss = by_id("98961")
        excerpt = (
            "Dust Senior redemption removes too much high-water-mark (HWM over-reduction) "
            "on this pin's recapitalization rounding."
        )
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            ctx.state.write_section(
                3,
                "ast_map",
                {
                    "surfaces": [
                        {
                            "file": "src/HousePool.sol",
                            "line": 90,
                            "name": miss.function,
                            "kind": "function",
                            "entry": True,
                        }
                    ]
                },
            )
            ctx.state.write_section(
                1,
                "audits",
                {
                    "past_findings": [
                        {
                            "title": "HWM over-reduction on dust Senior redemption",
                            "source": "audits/past.pdf",
                            "excerpt": excerpt,
                            "dedupe_key": "audit:hwm-rounding-98961",
                        }
                    ]
                },
            )
            seeded = seed_from_research(
                ctx, SeedResearchInput(fill_never_generated=False, include_families=False)
            )
            audit_hyps = [h for h in seeded.hypotheses if h.lens == "past-audit"]
            self.assertTrue(audit_hyps, msg=seeded.hypotheses)
            evidence = " ".join(audit_hyps[0].evidence)
            self.assertIn(f"mapped-surface:{miss.function}", evidence)
            ctx.state.write_section(
                4,
                "research_seeds",
                {"hypotheses": [h.model_dump(mode="json") for h in audit_hyps]},
            )
            out = disprove_finding(
                ctx,
                DisproveInput(
                    hypothesis_id=audit_hyps[0].id,
                    checks=[
                        DisproofCheck(
                            name="wrong-target",
                            question="Is this the wrong protocol?",
                            result=CheckResult.BLOCKS,
                            evidence=miss.kill_text,
                        )
                    ],
                ),
            )
            self.assertNotEqual(out.items[0].verdict, "disproved")
            self.assertIn("in-scope", out.items[0].rationale.lower())


class PairOnlyAndNeverGeneratedTests(unittest.TestCase):
    """Fixes 14+16: every pair-only locus is named and G3-queued; 99136 is generated."""

    def test_pair_only_is_named_and_queued(self):
        for miss in by_bucket("PAIR-ONLY"):
            with self.subTest(id=miss.id):
                self.assertTrue(
                    is_public_mutator({"name": miss.function, "kind": "function", "entry": True}),
                    msg=f"{miss.id} mutator {miss.function} dropped from cartesian",
                )
                with tempfile.TemporaryDirectory() as tmp:
                    ctx = make_ctx(Path(tmp))
                    _seed_pair(ctx, miss.function, miss.var)
                    out = never_generated_check(
                        ctx, NeverGeneratedInput(max_generate=80, max_queue=50)
                    )
                    self.assertTrue(
                        any(hyp_touches_pair(h, miss.function, miss.var) for h in out.hypotheses),
                        msg=f"{miss.id} {miss.function}::{miss.var} not named; "
                        f"{[h.title for h in out.hypotheses]}",
                    )
                    queued = {f"{row['function']}::{row['var']}" for row in out.g3_queue}
                    self.assertIn(
                        f"{miss.function}::{miss.var}",
                        queued,
                        msg=f"{miss.id} not G3-queued; queued={sorted(queued)}",
                    )

    def test_never_generated_execution_window(self):
        miss = by_id("99136")
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            # Vocab is already long and omits executionWindow — the Blind2 shape.
            ctx.state.write_section(
                2,
                "state_vocab",
                {
                    "states": [
                        {"var": name}
                        for name in (
                            "sharePrice",
                            "totalSupply",
                            "totalAssets",
                            "freeSettlement",
                            "acceptedBasket",
                            "unassignedAssets",
                            "highWaterMark",
                            "vpiRebateReserve",
                            "pnlPledgeAssets",
                            "seniorPrincipal",
                            "traderClaimBalance",
                            "degradedMode",
                            "liquidationReserve",
                            "protocolTreasury",
                            "currentExecutionConfigHash",
                            "accountedAssets",
                            "rawAssets",
                            "juniorPrincipal",
                            "fundedRedeemAssets",
                            "balanceAssets",
                            "depositClaimEscrowShares",
                            "pendingRedeemEscrowShares",
                            "executionBountyAssets",
                            "reservedSeniorDepositAssets",
                            "lpEpochSettlementPaused",
                        )
                    ]
                },
            )
            ctx.state.write_section(
                3,
                "ast_map",
                {
                    "surfaces": [
                        {
                            "file": "src/OrderRouter.sol",
                            "line": 10,
                            "name": miss.function,
                            "kind": "function",
                            "entry": True,
                        }
                    ]
                },
            )
            vars_ = list_value_vars(ctx)
            self.assertIn("executionWindow", vars_, msg=vars_)
            out = never_generated_check(ctx, NeverGeneratedInput(max_generate=80, max_queue=50))
            self.assertTrue(
                any(hyp_touches_pair(h, miss.function, miss.var) for h in out.hypotheses),
                msg=[h.title for h in out.hypotheses],
            )
            queued = {f"{row['function']}::{row['var']}" for row in out.g3_queue}
            self.assertIn(f"{miss.function}::{miss.var}", queued, msg=sorted(queued))


if __name__ == "__main__":
    unittest.main()
