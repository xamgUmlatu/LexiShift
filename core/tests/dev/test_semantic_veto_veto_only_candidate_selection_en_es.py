from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(CORE_ROOT), str(SCRIPTS_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_veto_only_candidate_selection_en_es import (  # noqa: E402
    build_veto_only_candidate_selection_report,
    render_veto_only_candidate_selection_markdown,
)


class SemanticVetoVetoOnlyCandidateSelectionTests(unittest.TestCase):
    def test_selects_candidate_that_passes_probe_and_validation(self) -> None:
        report = build_veto_only_candidate_selection_report(
            probe_report=_probe_report(),
            validation_report=_validation_report(),
            generated_at="2026-05-01T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "veto_only_shared_candidate_found")
        self.assertEqual(report["summary"]["passing_shared_count"], 1)
        self.assertEqual(report["e2e_checks"]["matched_parameter_rows"], 2)

        best = report["summary"]["best_candidate"]
        self.assertEqual(best["phrase_mode"], "shadow_or_phrase_score")
        self.assertTrue(best["passes_all_measured_lanes"])
        self.assertEqual(best["minimum_positive_allow_rate"], 0.85)
        self.assertEqual(best["minimum_negative_abstain_rate"], 0.7)

        markdown = render_veto_only_candidate_selection_markdown(report)
        self.assertIn("Candidate Selection", markdown)
        self.assertIn("shadow_or_phrase_score", markdown)

    def test_review_when_no_shared_parameter_passes(self) -> None:
        validation = _validation_report()
        validation["rows"][0]["target_status"] = "fail"
        report = build_veto_only_candidate_selection_report(
            probe_report=_probe_report(),
            validation_report=validation,
            generated_at="2026-05-01T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "veto_only_shared_candidate_not_found")
        self.assertEqual(report["summary"]["passing_shared_count"], 0)


def _probe_report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "ok",
        "decision": "veto_only_product_target_pass_found",
        "summary": {"row_count": 2, "target_pass_count": 1},
        "rows": [
            _row("shadow_or_phrase_score", 0.05, 0.0, 0.95, 0.8, 10.0, "pass"),
            _row("shadow_or_phrase", 0.02, 0.0, 0.8, 0.9, 9.0, "pass"),
        ],
    }


def _validation_report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "ok",
        "decision": "veto_only_validation_product_target_pass_found",
        "summary": {"row_count": 2, "target_pass_count": 1},
        "rows": [
            _row("shadow_or_phrase_score", 0.05, 0.0, 0.85, 0.7, 5.0, "pass"),
            _row("shadow_or_phrase", 0.02, 0.0, 0.65, 0.8, 4.0, "fail"),
        ],
    }


def _row(
    phrase_mode: str,
    shadow_lead: float,
    shadow_score: float,
    positive_allow: float,
    negative_abstain: float,
    utility: float,
    target_status: str,
) -> dict[str, object]:
    return {
        "config_id": "control_st_masked_all_margin_phrase_override",
        "phrase_mode": phrase_mode,
        "shadow_lead_min": shadow_lead,
        "shadow_score_min": shadow_score,
        "positive_allow_rate": positive_allow,
        "negative_abstain_rate": negative_abstain,
        "utility_score": utility,
        "target_status": target_status,
    }


if __name__ == "__main__":
    unittest.main()
