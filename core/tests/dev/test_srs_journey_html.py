from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_journey_html import render_html  # noqa: E402


class TestSrsJourneyHtml(unittest.TestCase):
    def test_render_html_includes_playback_controls_and_state_panels(self) -> None:
        html = render_html(
            {
                "generated_at": "2026-03-21T00:00:00+00:00",
                "scenario": {
                    "id": "en-ja_core_journey_v1",
                    "name": "en-ja_core_journey_v1",
                    "pair": "en-ja",
                    "lane": "deterministic_core_journey",
                    "contract_mode": "observe_current_behavior",
                },
                "initialize": {
                    "bootstrap_audit": {
                        "candidate_count": 3,
                        "admitted_count": 2,
                        "admission_weight_sum": 2.7,
                        "stopwords_path": None,
                        "candidates": [
                            {
                                "seed_rank": 1,
                                "lemma": "alpha",
                                "cohort": "stable",
                                "selected": True,
                                "selected_order": 1,
                                "admission_weight": 1.0,
                                "admission_weight_share": 0.37,
                                "core_rank": 1.0,
                                "pos_bucket": "noun",
                                "word_package": {"reading": "alpha"},
                            }
                        ],
                    }
                },
                "signal_summary": {
                    "event_count": 8,
                    "event_types": {"feedback": 6, "exposure": 2},
                },
                "summary": {
                    "status": "WARN",
                    "pass_count": 4,
                    "warn_count": 1,
                    "fail_count": 0,
                },
                "phases": [
                    {
                        "label": "bootstrap_publish",
                        "now": "2026-03-21T09:00:00+00:00",
                        "counts": {"admitted": 2, "due": 2, "published": 2},
                        "sets": {
                            "admitted": ["alpha", "beta"],
                            "due": ["alpha", "beta"],
                            "published": ["alpha", "beta"],
                        },
                        "deltas": {
                            "admitted_in": ["alpha", "beta"],
                            "admitted_out": [],
                            "due_in": ["alpha", "beta"],
                            "due_out": [],
                            "published_in": ["alpha", "beta"],
                            "published_out": [],
                        },
                        "relationships": {
                            "published_not_due": [],
                            "published_not_admitted": [],
                            "due_not_published": [],
                        },
                        "events_applied": {
                            "feedback": [],
                            "exposure": [],
                            "counts": {"feedback": 0, "exposure": 0},
                        },
                        "refresh": {"requested": False, "payload": None, "audit": None},
                        "items": [
                            {
                                "lemma": "alpha",
                                "cohort": "stable",
                                "status": "new",
                                "confidence": 1.0,
                                "stability": None,
                                "difficulty": None,
                                "exposures": 0,
                                "next_due": None,
                                "due_rank": 1,
                                "in_due": True,
                                "in_published": True,
                                "recent_history": [],
                                "source_type": "initial",
                                "word_package": {"reading": "alpha", "pos_canonical": "noun"},
                            }
                        ],
                        "findings": [],
                    },
                    {
                        "label": "high_retention_growth",
                        "now": "2026-03-22T09:00:00+00:00",
                        "counts": {"admitted": 4, "due": 2, "published": 4},
                        "sets": {
                            "admitted": ["alpha", "beta", "delta", "epsilon"],
                            "due": ["delta", "epsilon"],
                            "published": ["alpha", "beta", "delta", "epsilon"],
                        },
                        "deltas": {
                            "admitted_in": ["delta", "epsilon"],
                            "admitted_out": [],
                            "due_in": ["delta", "epsilon"],
                            "due_out": ["alpha", "beta"],
                            "published_in": ["delta", "epsilon"],
                            "published_out": [],
                        },
                        "relationships": {
                            "published_not_due": ["alpha", "beta"],
                            "published_not_admitted": [],
                            "due_not_published": [],
                        },
                        "events_applied": {
                            "feedback": [
                                {
                                    "index": 1,
                                    "lemma": "alpha",
                                    "rating": "good",
                                    "cohort": "stable",
                                    "ts": "2026-03-22T09:00:00+00:00",
                                }
                            ],
                            "exposure": [],
                            "counts": {"feedback": 1, "exposure": 0},
                        },
                        "refresh": {
                            "requested": True,
                            "payload": {
                                "applied": True,
                                "admission_refresh": {
                                    "reason_code": "normal",
                                    "admission_budget": 2,
                                    "candidate_pool_size": 4,
                                    "due_pressure": 0.25,
                                    "feedback_window": {
                                        "retention_ratio": 1.0,
                                        "strain_ratio": 0.0,
                                    },
                                    "selected_lemmas": ["delta", "epsilon"],
                                },
                            },
                            "audit": {
                                "candidates": [
                                    {
                                        "seed_rank": 1,
                                        "lemma": "delta",
                                        "cohort": "frontier",
                                        "selected": True,
                                        "selected_order": 1,
                                        "eligible": True,
                                        "filtered_reason": None,
                                        "selector_score": 0.82,
                                        "selector_score_share": 0.52,
                                        "admission_weight": 0.82,
                                        "admission_weight_share": 0.31,
                                        "core_rank": 4.0,
                                        "pos_bucket": "noun",
                                        "word_package": {"reading": "delta"},
                                    }
                                ],
                            },
                        },
                        "items": [
                            {
                                "lemma": "delta",
                                "cohort": "frontier",
                                "status": "learning",
                                "confidence": 0.82,
                                "stability": 1.0,
                                "difficulty": 0.5,
                                "exposures": 0,
                                "next_due": "2026-03-23T09:00:00Z",
                                "due_rank": 1,
                                "in_due": True,
                                "in_published": True,
                                "recent_history": [
                                    {"ts": "2026-03-22T09:00:00+00:00", "rating": "good"}
                                ],
                                "source_type": "frequency",
                                "word_package": {"reading": "delta", "pos_canonical": "noun"},
                            }
                        ],
                        "findings": [
                            {
                                "level": "PASS",
                                "code": "SRS_JOURNEY_HIGH_RETENTION_ADMITS",
                                "message": "High-retention phase admitted new frontier items.",
                                "details": "admitted=4",
                            }
                        ],
                    },
                ],
                "findings": [
                    {
                        "level": "WARN",
                        "phase": "high_retention_growth",
                        "code": "SRS_JOURNEY_PUBLICATION_SCOPE_OBSERVED",
                        "message": "Published set is broader than the due subset in the current journey run.",
                        "details": "phase=high_retention_growth admitted=4 due=2 published=4",
                    }
                ],
            }
        )
        self.assertIn("SRS Journey Pedagogical Review", html)
        self.assertIn("playback-toggle", html)
        self.assertIn("Profile State", html)
        self.assertIn("Admission Review", html)
        self.assertIn("Full report JSON", html)
        self.assertIn("selected_lemmas", html)
        self.assertIn("bootstrap_audit", html)
        self.assertIn("phase-range", html)


if __name__ == "__main__":
    unittest.main()
