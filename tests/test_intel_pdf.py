"""Bundled intel corpus, PDF past-audit ingest, and research seeding."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from schemas.phase1 import CheckIntelInput, ReviewAuditsInput
from schemas.phase4 import BatteryInput, SeedResearchInput
from tests.helpers import make_ctx, write_min_pdf
from tools.phase1_research import check_intel, review_past_audits
from tools.phase4_specialists import run_battery, seed_from_research

check_intel = check_intel.handler
review_past_audits = review_past_audits.handler
run_battery = run_battery.handler
seed_from_research = seed_from_research.handler
from tools.protocol_families import PROTOCOL_FAMILIES


class IntelPdfTests(unittest.TestCase):
    def test_check_intel_scans_bundled_patterns_without_external_corpus(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            out = check_intel(ctx, CheckIntelInput(keywords=["share price", "nav"]))
            self.assertGreater(out.found, 0)
            titles = " ".join(m.title.lower() for m in out.matches)
            self.assertIn("refundable", titles)
            self.assertTrue(any("intel-patterns" in n or "bundled" in n.lower() for n in out.notes))
            self.assertTrue(out.techniques)

    def test_review_past_audits_reads_pdf_headings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = make_ctx(root)
            audits = root / "audits"
            audits.mkdir()
            write_min_pdf(
                audits / "past.pdf",
                "# Critical Finding: Share price includes refundable fees",
            )
            out = review_past_audits(ctx, ReviewAuditsInput(paths=["audits"]))
            self.assertTrue(out.past_findings, msg=out.notes)
            self.assertTrue(any("refundable" in f.title.lower() for f in out.past_findings))
            self.assertTrue(any("PDF" in n or "pdf" in n for n in out.notes))

    def test_seed_from_research_emits_protocol_families(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            intel = check_intel(ctx, CheckIntelInput())
            ctx.state.write_section(1, "intel", intel.model_dump(mode="json"))
            out = seed_from_research(ctx, SeedResearchInput(fill_never_generated=False))
            family_ids = {h.family for h in out.hypotheses if h.family}
            for family in PROTOCOL_FAMILIES:
                self.assertIn(family.id, family_ids)
            self.assertTrue(any(d.get("id") == "DIV-SEED-0001" for d in ctx.state.divergences()))

    def test_default_vault_battery_includes_required_families(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_ctx(Path(tmp))
            out = run_battery(ctx, BatteryInput(battery="vault"))
            check_names = {c.name for item in out.items for c in item.checks}
            self.assertIn("share_price_excludes_reclaimable_receipts_and_fees", check_names)
            self.assertIn("share_supply_and_virtual_offset_cannot_overflow_to_freeze", check_names)
            self.assertIn("hwm_and_recap_do_not_reset_another_cohorts_claim", check_names)
            self.assertIn("queued_order_stays_binding_after_price_is_public", check_names)
            self.assertIn("oracle_rejects_stale_mixed_calendar_and_reset_watermarks", check_names)
            self.assertIn("emergency_mode_matches_cash_solvency_not_marked_gains", check_names)
            family_ids = {h.family for h in out.hypotheses}
            self.assertEqual(family_ids, {f.id for f in PROTOCOL_FAMILIES})
            blob = " ".join(h.statement.lower() for h in out.hypotheses)
            self.assertNotIn("plether", blob)
            self.assertNotIn("vpi", blob)
            self.assertNotIn("usdg", blob)
            self.assertNotIn("settlelpepoch", blob)


if __name__ == "__main__":
    unittest.main()
