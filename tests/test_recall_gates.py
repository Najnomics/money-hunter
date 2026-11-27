"""Fixes 11–15: freeze-is-impact G4, distinguishing G3, per-variant family kills,
public cartesian queue, excerpt→in-scope mapping before wrong-protocol kills.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime import ToolError
from schemas.phase4 import NeverGeneratedInput, SeedResearchInput
from schemas.phase5 import CartesianQueueInput, RecordExperimentInput
from schemas.phase6 import CheckResult, CoverageInput, DisproofCheck, DisproveInput
from tests.helpers import make_ctx
from tools.gate_policy import infer_experiment_class, is_freeze_value_flow
from tools.hypothesis_seed import (
    is_internal_helper,
    is_public_mutator,
    list_mutators,
    pair_rank,
)
from tools.phase4_specialists import never_generated_check, seed_from_research
from tools.phase5_sandbox import queue_cartesian_g3, record_experiment
from tools.phase6_validate import coverage_check, disprove_finding
from tools.scope_map import map_text_to_surfaces

never_generated_check = never_generated_check.handler
seed_from_research = seed_from_research.handler
record_experiment = record_experiment.handler
queue_cartesian_g3 = queue_cartesian_g3.handler
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


class FreezeIsImpactG4Tests(unittest.TestCase):
    def test_overflow_revert_is_not_unreachable_kill(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            _write_hyp(
                ctx,
                family="share-supply-overflow",
                statement="Mint near uint256 max freezes convertToShares so deposits cannot complete.",
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
                            evidence="Supply would overflow and revert; astronomical and unreachable.",
                        )
                    ],
                ),
            )
            self.assertEqual(out.items[0].verdict, "survives")
            self.assertEqual(out.items[0].blocking_checks, [])
            self.assertIn("freeze", out.items[0].rationale.lower())

    def test_non_freeze_unreachable_still_disproves(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            _write_hyp(
                ctx,
                family=None,
                statement="Only the admin can call pause.",
                falsifiable_prediction="Unprivileged pause reverts.",
                sink="paused",
                evidence=["[CODE] src/Vault.sol:10"],
            )
            out = disprove_finding(
                ctx,
                DisproveInput(
                    hypothesis_id="H-0001",
                    checks=[
                        DisproofCheck(
                            name="auth-middleware",
                            question="Does auth block the path?",
                            result=CheckResult.BLOCKS,
                            evidence="onlyAdmin; unprivileged call is unreachable.",
                        )
                    ],
                ),
            )
            self.assertEqual(out.items[0].verdict, "disproved")


class DistinguishingG3Tests(unittest.TestCase):
    def test_happy_path_is_not_a_g3_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = make_ctx(root)
            _write_hyp(ctx, family=None, statement="deposit then redeem round-trip")
            log = _log(root, "cap is live; solvent round-trip passed; assert True")
            with self.assertRaises(ToolError) as raised:
                record_experiment(
                    ctx,
                    RecordExperimentInput(
                        hypothesis_id="H-0001",
                        command="forge test --match-test test_roundtrip",
                        observation="happy path seeded fixture; cap is live",
                        verdict="confirmed",
                        output_path=str(log),
                        experiment_class="happy-path",
                    ),
                )
            self.assertIn("distinguishing", str(raised.exception).lower())

    def test_code_fact_is_not_a_g3_kill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = make_ctx(root)
            _write_hyp(ctx, family=None, statement="natspec says the cap is live")
            log = _log(root, "read the source; natspec says convertToShares reverts; no execution")
            with self.assertRaises(ToolError):
                record_experiment(
                    ctx,
                    RecordExperimentInput(
                        hypothesis_id="H-0001",
                        command="cat src/Vault.sol",
                        observation="code-fact: line 40 says the overflow check exists",
                        verdict="refuted",
                        output_path=str(log),
                    ),
                )

    def test_distinguishing_attack_can_confirm(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = make_ctx(root)
            _write_hyp(ctx, family=None, statement="attacker drains sharePrice at first-tick")
            log = _log(root, "vm.prank attacker; first-tick zero-state; second actor extracts")
            out = record_experiment(
                ctx,
                RecordExperimentInput(
                    hypothesis_id="H-0001",
                    command="forge test --match-test test_attack_deposit_sharePrice",
                    observation="attacker vm.prank adversarial first-tick; distinguishing",
                    verdict="confirmed",
                    output_path=str(log),
                    experiment_class="distinguishing",
                ),
            )
            self.assertEqual(out.items[0].verdict, "confirmed")
            self.assertEqual(out.items[0].experiment_class, "distinguishing")

    def test_unknown_class_is_inconclusive_not_a_kill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = make_ctx(root)
            _write_hyp(ctx, family=None, statement="maybe something")
            log = _log(root, "ran some test")
            out = record_experiment(
                ctx,
                RecordExperimentInput(
                    hypothesis_id="H-0001",
                    command="forge test",
                    observation="exit=0",
                    verdict="refuted",
                    output_path=str(log),
                ),
            )
            self.assertEqual(out.items[0].verdict, "inconclusive")
            self.assertEqual(out.items[0].experiment_class, "unknown")

    def test_infer_prefers_content_over_label(self):
        self.assertEqual(
            infer_experiment_class(
                declared="distinguishing",
                observation="code-fact natspec says the cap is live; no execution",
            ),
            "code-fact",
        )
        self.assertTrue(is_freeze_value_flow({"family": "share-supply-overflow"}))


class FamilyVariantG4Tests(unittest.TestCase):
    def test_family_kill_without_variant_is_not_a_family_kill(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            _write_hyp(
                ctx,
                family="delayed-order-optionality",
                statement="After the price is public a side door turns a committed order into an option.",
            )
            out = disprove_finding(
                ctx,
                DisproveInput(
                    hypothesis_id="H-0001",
                    checks=[
                        DisproofCheck(
                            name="auth-middleware",
                            question="Does auth block the path?",
                            result=CheckResult.BLOCKS,
                            evidence="only the keeper can call execute.",
                        )
                    ],
                ),
            )
            item = out.items[0]
            self.assertEqual(item.verdict, "needs-variant")
            self.assertEqual(item.scope, "family")
            self.assertNotEqual(item.verdict, "disproved")

    def test_family_kill_is_scoped_to_the_variant(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            _write_hyp(
                ctx,
                id="H-0001",
                family="delayed-order-optionality",
                statement="After the price is public a side door turns a committed order into an option.",
            )
            out = disprove_finding(
                ctx,
                DisproveInput(
                    hypothesis_id="H-0001",
                    variant="deposit",
                    checks=[
                        DisproofCheck(
                            name="auth-middleware",
                            question="Does auth block the path?",
                            result=CheckResult.BLOCKS,
                            evidence="deposit is admin-only on this pin.",
                        )
                    ],
                ),
            )
            item = out.items[0]
            self.assertEqual(item.verdict, "disproved-variant")
            self.assertEqual(item.scope, "variant")
            self.assertEqual(item.variant, "deposit")
            ctx.state.append_items(6, "disproofs", [item.model_dump(mode="json")])
            cov = coverage_check(ctx, CoverageInput())
            self.assertTrue(any(g.id == "GAP-VARIANT-H-0001" for g in cov.gaps), msg=cov.gaps)


class PublicCartesianQueueTests(unittest.TestCase):
    def test_drops_internal_and_constant_and_queues_distinguishing_g3(self):
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
                        {"file": "src/Vault.sol", "line": 70, "name": "_syncIndex", "kind": "function", "entry": False},
                        {"file": "src/Vault.sol", "line": 80, "name": "ENGINE", "kind": "function", "entry": True},
                        {"file": "src/Vault.sol", "line": 90, "name": "previewDeposit", "kind": "function", "entry": True},
                    ]
                },
            )
            names = {str(s.get("name")) for s in list_mutators(ctx)}
            self.assertEqual(names, {"deposit", "redeem"})
            self.assertFalse(is_public_mutator({"name": "_syncIndex", "kind": "function"}))
            self.assertFalse(is_public_mutator({"name": "ENGINE", "kind": "function", "entry": True}))
            out = never_generated_check(ctx, NeverGeneratedInput(max_queue=4))
            blob = " ".join(h.statement for h in out.hypotheses)
            self.assertNotIn("_syncIndex", blob)
            self.assertNotIn("ENGINE", blob)
            self.assertTrue(out.g3_queue)
            self.assertTrue(all(row["experiment_class"] == "distinguishing" for row in out.g3_queue))
            experiments = ctx.state.collect(5, "experiments")
            self.assertEqual(len(experiments), len(out.g3_queue))
            self.assertTrue(all(e.get("experiment_class") == "distinguishing" for e in experiments))
            self.assertTrue(all("attacker" in e.get("observation", "").lower() or "distinguishing" in e.get("observation", "").lower() for e in experiments))

    def test_public_entrypoint_outranks_settlement_internal(self):
        public = pair_rank(
            "commitOrder",
            "executionWindow",
            {"name": "commitOrder", "entry": True},
        )
        internal = pair_rank(
            "_applyLiquidationSettlementPlan",
            "sharePrice",
            {"name": "_applyLiquidationSettlementPlan", "entry": False},
        )
        settlement = pair_rank(
            "settlementApplyCarryAndMark",
            "sharePrice",
            {"name": "settlementApplyCarryAndMark", "entry": False},
        )
        self.assertTrue(is_internal_helper("_applyLiquidationSettlementPlan"))
        self.assertTrue(is_internal_helper("settlementApplyCarryAndMark"))
        self.assertFalse(is_internal_helper("commitOrder"))
        self.assertGreater(public, internal)
        self.assertGreater(public, settlement)

    def test_cartesian_action_does_not_execute(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            with self.assertRaises(ToolError):
                queue_cartesian_g3(ctx, CartesianQueueInput(execute=True))


class ExcerptScopeMapTests(unittest.TestCase):
    def test_maps_excerpt_to_in_scope_function_and_blocks_wrong_protocol_kill(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            ctx.state.write_section(
                3,
                "ast_map",
                {
                    "surfaces": [
                        {"file": "src/Vault.sol", "line": 10, "name": "deposit", "kind": "function", "entry": True},
                        {"file": "src/Vault.sol", "line": 40, "name": "redeem", "kind": "function", "entry": True},
                    ]
                },
            )
            ctx.state.write_section(
                1,
                "audits",
                {
                    "past_findings": [
                        {
                            "title": "Share price includes refundable fees on deposit",
                            "source": "audits/past.pdf",
                            "excerpt": "Calling deposit books a refundable receipt into sharePrice.",
                            "dedupe_key": "audit:share-price-fees",
                        }
                    ]
                },
            )
            hits = map_text_to_surfaces(ctx, "Calling deposit books a refundable receipt into sharePrice.")
            self.assertEqual([h["name"] for h in hits], ["deposit"])
            seeded = seed_from_research(ctx, SeedResearchInput(fill_never_generated=False, include_families=False))
            audit_hyps = [h for h in seeded.hypotheses if h.lens == "past-audit"]
            self.assertTrue(audit_hyps)
            evidence = " ".join(audit_hyps[0].evidence)
            self.assertIn("mapped-surface:deposit", evidence)
            self.assertIn("src/Vault.sol:10", evidence)
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
                            evidence="Wrong protocol; this analog does not apply here.",
                        )
                    ],
                ),
            )
            self.assertNotEqual(out.items[0].verdict, "disproved")
            self.assertIn("in-scope", out.items[0].rationale.lower())

    def test_unmapped_excerpt_may_take_wrong_protocol_kill(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            ctx.state.write_section(
                3,
                "ast_map",
                {
                    "surfaces": [
                        {"file": "src/Vault.sol", "line": 10, "name": "deposit", "kind": "function", "entry": True},
                    ]
                },
            )
            _write_hyp(
                ctx,
                family=None,
                statement="A disclosed analog from another product.",
                evidence=["[SEARCHED] intel other.md", "[DEDUCED] analog-unmapped: excerpt names no in-scope public function"],
            )
            out = disprove_finding(
                ctx,
                DisproveInput(
                    hypothesis_id="H-0001",
                    checks=[
                        DisproofCheck(
                            name="wrong-target",
                            question="Is this the wrong protocol?",
                            result=CheckResult.BLOCKS,
                            evidence="Wrong protocol; different product.",
                        )
                    ],
                ),
            )
            self.assertEqual(out.items[0].verdict, "disproved")


if __name__ == "__main__":
    unittest.main()
