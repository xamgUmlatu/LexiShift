from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_source_topic_precision_review_en_es import build_report, render_markdown  # noqa: E402


class SrsSourceTopicPrecisionReviewTests(unittest.TestCase):
    def test_builds_labeled_packet_for_default_release_topics_only(self) -> None:
        report = build_report(
            depth_audit_payload=_depth_audit_payload(),
            release_readiness_payload=_release_readiness_payload(),
            labels_payload=_labels_payload(),
            frontier_label="unit_10k",
            release_statuses=("release_candidate",),
            max_rows_per_family=3,
            generated_at="2026-05-19T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["count"], 3)
        self.assertEqual(report["summary"]["accepted_count"], 2)
        self.assertEqual(report["summary"]["rejected_count"], 1)
        self.assertEqual(report["summary"]["family_count"], 1)
        self.assertEqual(report["label_result"]["missing_review_ids"], [])
        self.assertEqual(report["label_result"]["unknown_review_ids"], [])
        self.assertEqual(report["label_result"]["invalid_decisions"], [])

        rows = report["review_queue"]
        self.assertEqual([row["family"] for row in rows], ["science_technology"] * 3)
        self.assertEqual(rows[0]["review_id"], "srs-src-topic-001")
        self.assertEqual(rows[1]["source_labels"], ["games"])
        self.assertEqual(rows[1]["manual_review"]["decision"], "reject_wrong_topic")
        self.assertEqual(report["rejected_rows"][0]["lemma"], "center")
        self.assertIn("source_false_positive_classes_present", report["summary"]["warnings"])

    def test_invalid_label_decision_fails_cleanly(self) -> None:
        labels = _labels_payload()
        labels["labels"][0]["decision"] = "accept_typo"

        report = build_report(
            depth_audit_payload=_depth_audit_payload(),
            release_readiness_payload=_release_readiness_payload(),
            labels_payload=labels,
            frontier_label="unit_10k",
            release_statuses=("release_candidate",),
            max_rows_per_family=3,
            generated_at="2026-05-19T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["label_result"]["invalid_decisions"], ["accept_typo"])
        self.assertIn("manual_labels_invalid", report["summary"]["issues"])

    def test_stale_review_ids_fall_back_to_family_lemma_labels(self) -> None:
        labels = _labels_payload()
        labels["labels"][0]["review_id"] = "retired-review-id"

        report = build_report(
            depth_audit_payload=_depth_audit_payload(),
            release_readiness_payload=_release_readiness_payload(),
            labels_payload=labels,
            frontier_label="unit_10k",
            release_statuses=("release_candidate",),
            max_rows_per_family=3,
            generated_at="2026-05-19T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["label_result"]["missing_review_ids"], [])
        first_review = report["review_queue"][0]["manual_review"]
        self.assertEqual(first_review["decision"], "accept_strong_topic")
        self.assertEqual(first_review["label_match"], "family_lemma")

    def test_markdown_surfaces_rejected_rows(self) -> None:
        report = build_report(
            depth_audit_payload=_depth_audit_payload(),
            release_readiness_payload=_release_readiness_payload(),
            labels_payload=_labels_payload(),
            frontier_label="unit_10k",
            release_statuses=("release_candidate",),
            max_rows_per_family=3,
            generated_at="2026-05-19T00:00:00+00:00",
        )

        markdown = render_markdown(report)

        self.assertIn("Source Topic Precision Review", markdown)
        self.assertIn("Rejected Rows", markdown)
        self.assertIn("center", markdown)
        self.assertIn("Notable Source Labels", markdown)


def _release_readiness_payload() -> dict[str, object]:
    return {
        "topics": [
            {
                "axis": "topic",
                "family": "science_technology",
                "release_status": "release_candidate",
            },
            {
                "axis": "topic",
                "family": "medicine_health",
                "release_status": "release_candidate_limited_depth",
            },
            {
                "axis": "register",
                "family": "casual_slang_register",
                "release_status": "register_release_candidate_policy_review",
            },
        ]
    }


def _depth_audit_payload() -> dict[str, object]:
    return {
        "frontiers": [
            {
                "label": "unit_10k",
                "exists": True,
                "families": [
                    {
                        "family": "science_technology",
                        "trusted_top_examples": [
                            {
                                "lemma": "controlador",
                                "difficulty": 0.2,
                                "source_labels": ["computing", "engineering"],
                            }
                        ],
                        "trusted_bands": [
                            {
                                "band": "0.60-0.80",
                                "examples": [
                                    {
                                        "lemma": "center",
                                        "difficulty": 0.62,
                                        "source_label": "games",
                                    }
                                ],
                            }
                        ],
                        "trusted_hardest_examples": [
                            {
                                "lemma": "venus",
                                "difficulty": 0.66,
                                "source_labels": ["sciences"],
                            }
                        ],
                    },
                    {
                        "family": "medicine_health",
                        "trusted_top_examples": [
                            {"lemma": "doctor", "difficulty": 0.1, "source_labels": ["medicine"]}
                        ],
                    },
                ],
            }
        ]
    }


def _labels_payload() -> dict[str, object]:
    return {
        "review_id": "unit-source-topic-review",
        "state": "agent_labeled_pending_user_approval",
        "reviewer": "codex",
        "reviewed_at": "2026-05-19",
        "labels": [
            {
                "review_id": "srs-src-topic-001",
                "family": "science_technology",
                "lemma": "controlador",
                "decision": "accept_strong_topic",
                "notes": "Direct technical noun.",
            },
            {
                "review_id": "srs-src-topic-002",
                "family": "science_technology",
                "lemma": "center",
                "decision": "reject_wrong_topic",
                "notes": "English artifact, not a Spanish topic lemma.",
            },
            {
                "review_id": "srs-src-topic-003",
                "family": "science_technology",
                "lemma": "venus",
                "decision": "accept_light_topic",
                "notes": "Useful topic term, but proper-noun handling needs policy review.",
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
