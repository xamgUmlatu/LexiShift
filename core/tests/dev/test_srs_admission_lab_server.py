from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "dev"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_admission_lab_server import (  # noqa: E402
    LabConfig,
    build_lab_response,
    build_profile_context,
)


def _create_frequency_db(path: Path) -> Path:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE frequency (
                lemma TEXT,
                core_rank REAL,
                pmw REAL,
                pos TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO frequency (
                lemma,
                core_rank,
                pmw,
                pos
            ) VALUES (?, ?, ?, ?)
            """,
            (
                ("alpha", 1.0, 100.0, "n"),
                ("beta", 2.0, 98.0, "n"),
                ("gamma", 3.0, 96.0, "n"),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return path


def _create_overlay(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "ok",
                "overlay_id": "unit_animals_plants_overlay",
                "overlay_policy": {
                    "promotion_state": "poc_candidate_not_product_overlay",
                },
                "summary": {"row_count": 2},
                "rows": [
                    {
                        "lemma": "beta",
                        "language_pair": "en-es",
                        "topic": "animals",
                        "membership": 1.0,
                        "review_id": "unit-animal",
                        "confidence_label": "strong",
                    },
                    {
                        "lemma": "gamma",
                        "language_pair": "en-es",
                        "topic": "plants_nature",
                        "membership": 1.0,
                        "review_id": "unit-plant",
                        "confidence_label": "strong",
                    },
                    {
                        "lemma": "perro",
                        "language_pair": "en-es",
                        "topic": "animals",
                        "membership": 1.0,
                        "review_id": "unit-animal-missing-from-seed",
                        "confidence_label": "strong",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def _create_zipf_bridge(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "full_source_target_pairs": [
                    {
                        "source": "bird",
                        "target": "ave",
                        "target_zipf_frequency_es": 4.12,
                    },
                    {
                        "source": "cat",
                        "target": "gato",
                        "target_zipf_frequency_es": 4.62,
                    },
                    {
                        "source": "dog",
                        "target": "perro",
                        "target_zipf_frequency_es": 4.90,
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def _create_kaikki_forward_db(path: Path) -> Path:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE entry_meta (headword_lc TEXT, pos TEXT)")
        conn.executemany(
            "INSERT INTO entry_meta (headword_lc, pos) VALUES (?, ?)",
            (
                ("ave", "noun"),
                ("gato", "noun"),
                ("perro", "noun"),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return path


class TestSrsAdmissionLabServer(unittest.TestCase):
    def test_build_profile_context_from_lab_controls(self) -> None:
        context = build_profile_context(
            {
                "interests": ["animals", "plants_nature"],
                "topic_weights": {"animals": 0.35, "finance": 2.0, "empty": 0},
                "proficiency_estimate": 0.62,
                "challenge_target": 0.58,
                "challenge_spread": 0.15,
            }
        )

        self.assertEqual(context["interests"], ["animals", "plants_nature"])
        self.assertEqual(context["topic_weights"], {"animals": 0.35, "finance": 1.0})
        self.assertEqual(context["proficiency"], {"estimated_value": 0.62})
        self.assertEqual(
            context["difficulty_preferences"],
            {
                "target_challenge_center": 0.58,
                "target_challenge_spread": 0.15,
            },
        )

    def test_build_profile_context_can_use_raw_json_override(self) -> None:
        context = build_profile_context(
            {
                "use_profile_context": True,
                "profile_context": {
                    "topic_weights": {"animals": 0.25},
                    "proficiency": {"estimated_value": 0.7},
                },
                "interests": ["finance"],
            }
        )

        self.assertEqual(
            context,
            {
                "topic_weights": {"animals": 0.25},
                "proficiency": {"estimated_value": 0.7},
            },
        )

    def test_build_lab_response_compares_preference_against_neutral(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frequency_db = _create_frequency_db(root / "freq.sqlite")
            overlay_path = _create_overlay(root / "overlay.json")

            response = build_lab_response(
                {
                    "pair": "en-es",
                    "interests": ["animals"],
                    "set_top_n": 3,
                    "initial_active_count": 3,
                    "preview_count": 3,
                    "preview_sampling_mode": "ranked",
                    "proficiency_estimate": 0.45,
                    "challenge_target": 0.45,
                    "challenge_spread": 0.2,
                },
                config=LabConfig(
                    frequency_db=frequency_db,
                    overlay_source_path=overlay_path,
                    augment_with_zipf_bridge=False,
                    set_top_n=3,
                    initial_active_count=3,
                    preview_count=3,
                    preview_sampling_mode="ranked",
                ),
            )

        self.assertTrue(response["ok"])
        self.assertEqual(response["neutral"]["top_lemmas"][0], "alpha")
        self.assertEqual(response["preference"]["top_lemmas"][0], "beta")
        self.assertEqual(response["preference"]["admitted_words"][0]["difficulty_estimate"], 0.004)
        self.assertEqual(response["preference"]["admitted_words"][0]["pos_raw"], "n")
        self.assertEqual(response["preference"]["admitted_words"][0]["pos_canonical"], "noun")
        self.assertEqual(
            response["preference"]["admitted_words"][0]["pos_matched_rule"],
            "freq-es-cde_compact:n",
        )
        self.assertEqual(response["preference"]["admitted_words"][0]["proficiency_fit"], 1.0)
        self.assertLess(response["preference"]["admitted_words"][0]["readiness_multiplier"], 0.20)
        self.assertEqual(
            response["preference"]["admitted_words"][0]["penalties"],
            ["readiness_gate"],
        )
        self.assertEqual(response["preference"]["topic_mover_count"], 1)
        self.assertEqual(
            response["preference"]["profile_topic_overlay"]["application_status"],
            "applied",
        )
        self.assertAlmostEqual(response["preference"]["topic_mover_share"], 1 / 3, places=3)
        topic_depth = response["preference"]["topic_depth_by_level"]
        self.assertEqual(topic_depth["version"], "profile_topic_depth_v1")
        self.assertEqual(topic_depth["topics"][0]["topic"], "animals")
        self.assertEqual(topic_depth["topics"][0]["candidate_count"], 1)
        self.assertEqual(
            response["preference"]["profile_topic_overlay"]["unmatched_eligible_lemma_sample"],
            ["perro"],
        )
        self.assertEqual(
            response["comparison"]["changed_or_new"][0],
            {
                "lemma": "beta",
                "preference_position": 1,
                "neutral_position": 2,
            },
        )

    def test_zipf_bridge_augmentation_adds_overlay_lemmas_missing_from_seed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frequency_db = _create_frequency_db(root / "freq.sqlite")
            overlay_path = _create_overlay(root / "overlay.json")
            zipf_bridge = _create_zipf_bridge(root / "zipf_bridge.json")
            kaikki_db = _create_kaikki_forward_db(root / "kaikki.sqlite")

            response = build_lab_response(
                {
                    "pair": "en-es",
                    "interests": ["animals"],
                    "set_top_n": 10,
                    "initial_active_count": 5,
                    "preview_count": 5,
                    "preview_sampling_mode": "ranked",
                    "proficiency_estimate": 0.25,
                    "challenge_target": 0.25,
                    "challenge_spread": 0.2,
                },
                config=LabConfig(
                    frequency_db=frequency_db,
                    overlay_source_path=overlay_path,
                    augment_with_zipf_bridge=True,
                    zipf_bridge_path=zipf_bridge,
                    kaikki_forward_db=kaikki_db,
                    set_top_n=10,
                    initial_active_count=5,
                    preview_count=5,
                    preview_sampling_mode="ranked",
                ),
            )

        augmentation = response["source"]["source_augmentation"]
        self.assertEqual(augmentation["status"], "applied")
        self.assertIn("perro", augmentation["added_lemma_sample"])
        self.assertEqual(augmentation["example_zipf_ranks"]["perro"]["rank"], 1)
        self.assertIn("perro", response["preference"]["top_lemmas"])
        self.assertIn("gato", response["preference"]["top_lemmas"])
        self.assertEqual(
            response["preference"]["profile_topic_overlay"]["unmatched_eligible_lemma_sample"],
            [],
        )


if __name__ == "__main__":
    unittest.main()
