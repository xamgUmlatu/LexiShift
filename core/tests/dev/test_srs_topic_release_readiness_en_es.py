from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_topic_release_readiness_en_es import build_report, render_markdown  # noqa: E402


class SrsTopicReleaseReadinessTests(unittest.TestCase):
    def test_classifies_source_overlay_register_and_blocked_topics(self) -> None:
        report = build_report(
            taxonomy_payload=_taxonomy_payload(),
            depth_audit_payload=_depth_audit_payload(),
            overlay_payloads=[_overlay_payload()],
            frontier_label="unit_10k",
            generated_at="2026-05-19T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "ok")
        rows = {row["family"]: row for row in report["topics"]}
        self.assertEqual(rows["science_technology"]["release_status"], "release_candidate")
        self.assertEqual(rows["science_technology"]["recommended_visibility"], "default_visible")

        self.assertEqual(
            rows["medicine_health"]["release_status"],
            "release_candidate_limited_depth",
        )
        self.assertEqual(
            rows["food_cooking"]["release_status"],
            "limited_release_candidate",
        )
        self.assertEqual(rows["food_cooking"]["effective_candidate_count"], 91)
        self.assertEqual(rows["food_cooking"]["effective_candidate_source"], "reviewed_overlay")
        self.assertEqual(rows["food_cooking"]["reviewed_overlay_candidate_count"], 91)

        self.assertEqual(rows["animals"]["release_status"], "beta_limited_candidate")
        self.assertEqual(
            rows["casual_slang_register"]["release_status"],
            "register_release_candidate_policy_review",
        )
        self.assertEqual(rows["hobbies_crafts"]["release_status"], "blocked_source_required")
        self.assertEqual(
            rows["sat_toefl_exam_prep"]["release_status"],
            "blocked_legal_source_required",
        )

        self.assertIn("some_topics_blocked", report["summary"]["warnings"])
        self.assertEqual(report["summary"]["default_visible_count"], 1)
        self.assertGreaterEqual(report["summary"]["limited_visible_count"], 3)

    def test_markdown_includes_release_gate_and_matrix(self) -> None:
        report = build_report(
            taxonomy_payload=_taxonomy_payload(),
            depth_audit_payload=_depth_audit_payload(),
            overlay_payloads=[_overlay_payload()],
            frontier_label="unit_10k",
            generated_at="2026-05-19T00:00:00+00:00",
        )

        markdown = render_markdown(report)

        self.assertIn("SRS Topic Release Readiness", markdown)
        self.assertIn("Release Gate", markdown)
        self.assertIn("food_cooking", markdown)
        self.assertIn("limited_release_candidate", markdown)
        self.assertIn("blocked_legal_source_required", markdown)

    def test_source_precision_review_updates_release_candidate_next_work(self) -> None:
        report = build_report(
            taxonomy_payload=_taxonomy_payload(),
            depth_audit_payload=_depth_audit_payload(),
            overlay_payloads=[_overlay_payload()],
            source_precision_payload=_source_precision_payload(),
            frontier_label="unit_10k",
            generated_at="2026-05-19T00:00:00+00:00",
        )

        rows = {row["family"]: row for row in report["topics"]}
        science = rows["science_technology"]

        self.assertEqual(science["source_precision_review"]["reviewed_count"], 4)
        self.assertEqual(
            science["next_work"][0],
            "tighten source-label guards before default promotion",
        )
        self.assertIn("source_precision_guards_needed", report["summary"]["warnings"])

        markdown = render_markdown(report)
        self.assertIn("Source Precision Review", markdown)
        self.assertIn("Families needing guard review", markdown)


def _taxonomy_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "families": [
            _family("science_technology", "Science & Technology", "source_ready"),
            _family("medicine_health", "Medicine & Health", "source_ready"),
            _family("food_cooking", "Food & Cooking", "p0_enrichment"),
            _family("animals", "Animals", "p0_enrichment"),
            _family("hobbies_crafts", "Hobbies & Crafts", "p0_enrichment"),
            _family("sat_toefl_exam_prep", "SAT & TOEFL Prep", "legal_source_gated"),
            _family(
                "casual_slang_register",
                "Casual & Slang",
                "review_only",
                axis="register",
            ),
        ],
    }


def _family(
    family_id: str,
    display_name: str,
    readiness_state: str,
    *,
    axis: str = "topic",
) -> dict[str, object]:
    return {
        "id": family_id,
        "display_name": display_name,
        "axis": axis,
        "product_priority": "p0",
        "readiness_state": readiness_state,
        "data_strategy": "unit",
    }


def _depth_audit_payload() -> dict[str, object]:
    return {
        "frontiers": [
            {
                "label": "unit_10k",
                "exists": True,
                "seed_count": 10000,
                "unique_lemma_count": 10000,
                "families": [
                    _depth("science_technology", 140, 4),
                    _depth("medicine_health", 130, 2),
                    _depth("food_cooking", 17, 2),
                    _depth("animals", 35, 1),
                    _depth("hobbies_crafts", 0, 0),
                    _depth("sat_toefl_exam_prep", 0, 0),
                    _depth(
                        "casual_slang_register",
                        0,
                        0,
                        axis="register",
                        review_only_count=160,
                    ),
                ],
            }
        ]
    }


def _depth(
    family_id: str,
    trusted_count: int,
    band_count: int,
    *,
    axis: str = "topic",
    review_only_count: int = 0,
) -> dict[str, object]:
    return {
        "family": family_id,
        "axis": axis,
        "trusted_candidate_count": trusted_count,
        "trusted_nonempty_band_count": band_count,
        "trusted_max_difficulty": 0.61 if band_count >= 3 else 0.31 if band_count else None,
        "review_only_candidate_count": review_only_count,
        "coverage_posture": "unit",
    }


def _overlay_payload() -> dict[str, object]:
    return {
        "status": "ok",
        "overlay_id": "unit_food_overlay",
        "rows": [
            {
                "language_pair": "en-es",
                "lemma": f"food-{index}",
                "topic": "food_cooking",
                "membership": 1.0,
                "confidence_label": "strong",
            }
            for index in range(91)
        ]
        + [
            {
                "language_pair": "en-es",
                "lemma": "food-light",
                "topic": "food_cooking",
                "membership": 0.65,
                "confidence_label": "light",
            }
        ],
    }


def _source_precision_payload() -> dict[str, object]:
    return {
        "decision": "srs_source_topic_precision_review_ready",
        "label_result": {
            "labels_state": "agent_labeled_pending_user_approval",
        },
        "summary": {
            "count": 4,
            "accepted_count": 2,
            "accepted_rate": 0.5,
            "rejected_count": 2,
            "rejected_rate": 0.5,
            "pending_count": 0,
        },
        "precision_by_family": [
            {
                "label": "science_technology",
                "count": 4,
                "accepted_count": 2,
                "accepted_rate": 0.5,
                "strong_count": 1,
                "light_count": 1,
                "rejected_count": 2,
                "rejected_rate": 0.5,
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
