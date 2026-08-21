from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_topic_preference_taxonomy_en_es import (  # noqa: E402
    build_report,
    render_markdown,
    validate_taxonomy,
)


class SrsTopicPreferenceTaxonomyTests(unittest.TestCase):
    def test_validates_animals_and_plants_mapping_and_measures_current_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            taxonomy = root / "taxonomy.json"
            frequency_db = root / "freq.sqlite"
            kaikki_db = root / "kaikki.sqlite"
            taxonomy.write_text(_taxonomy_json(), encoding="utf-8")
            _write_frequency_db(frequency_db)
            _write_kaikki_db(kaikki_db)

            report = build_report(
                taxonomy_path=taxonomy,
                frequency_db=frequency_db,
                kaikki_forward_db=kaikki_db,
                top_n=10,
                generated_at="2026-05-17T00:00:00+00:00",
            )

            self.assertEqual(report["status"], "ok")
            findings = {row["code"]: row for row in report["findings"]}
            self.assertIn("preference_ids_append_only", findings)
            self.assertIn("family_axis_metadata_valid", findings)
            self.assertIn("animals_seed_labels_present", findings)
            self.assertIn("plants_nature_seed_labels_present", findings)
            self.assertIn("excluded_labels_not_mapped_positive", findings)
            self.assertIn("exam_prep_target_english_scoped", findings)
            self.assertIn("family_mvp_picker_visibility_valid", findings)
            family_by_id = {row["family"]: row for row in report["coverage"]["families"]}
            animals = family_by_id["animals"]
            self.assertEqual(animals["row_count"], 2)
            top_labels = {row["label"]: row["count"] for row in animals["top_source_labels"]}
            self.assertEqual(top_labels["animals"], 1)
            self.assertEqual(top_labels["zoology"], 1)
            plants = family_by_id["plants_nature"]
            self.assertEqual(plants["row_count"], 1)
            plant_labels = {row["label"]: row["count"] for row in plants["top_source_labels"]}
            self.assertEqual(plant_labels["botany"], 1)
            self.assertEqual(family_by_id["sat_toefl_exam_prep"]["row_count"], 0)

            markdown = render_markdown(report)
            self.assertIn("Animals Samples", markdown)
            self.assertIn("Plants/Nature Samples", markdown)
            self.assertIn("plants_nature", markdown)

    def test_rejects_broad_excluded_label_as_positive_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            taxonomy = root / "taxonomy.json"
            frequency_db = root / "freq.sqlite"
            kaikki_db = root / "kaikki.sqlite"
            taxonomy.write_text(
                _taxonomy_json(
                    extra_mapping={
                        "source_channel": "sense_topics",
                        "source_label": "natural_sciences",
                        "target_family": "animals",
                        "weight": 0.4,
                        "confidence": 0.4,
                        "policy": "bad_broad_mapping",
                    }
                ),
                encoding="utf-8",
            )
            _write_frequency_db(frequency_db)
            _write_kaikki_db(kaikki_db)

            report = build_report(
                taxonomy_path=taxonomy,
                frequency_db=frequency_db,
                kaikki_forward_db=kaikki_db,
                top_n=10,
                generated_at="2026-05-17T00:00:00+00:00",
            )

            self.assertEqual(report["status"], "review")
            self.assertIn(
                "excluded_labels_mapped_positive",
                report["summary"]["issues"],
            )

    def test_repo_taxonomy_declares_registers_and_safe_expansion_contract(self) -> None:
        taxonomy_path = (
            REPO_ROOT / "docs" / "test_inputs" / "srs_topic_preference_taxonomy_en_es.json"
        )
        taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))

        findings = {row["code"]: row for row in validate_taxonomy(taxonomy)}
        self.assertEqual(findings["preference_ids_append_only"]["level"], "PASS")
        self.assertEqual(findings["family_axis_metadata_valid"]["level"], "PASS")
        self.assertEqual(findings["family_mvp_picker_visibility_valid"]["level"], "PASS")
        self.assertEqual(findings["exam_prep_legal_gated"]["level"], "PASS")
        self.assertEqual(findings["exam_prep_target_english_scoped"]["level"], "PASS")

        family_by_id = {row["id"]: row for row in taxonomy["families"]}
        self.assertEqual(family_by_id["casual_slang_register"]["axis"], "register")
        self.assertEqual(family_by_id["formal_professional_register"]["axis"], "register")
        self.assertEqual(
            family_by_id["casual_slang_register"]["readiness_state"],
            "review_only",
        )
        self.assertEqual(
            family_by_id["formal_professional_register"]["ux_group"],
            "interests_style",
        )
        self.assertEqual(
            family_by_id["sat_toefl_exam_prep"]["pair_scope"],
            "target_language:en",
        )
        visible_ids = [
            family["id"]
            for family in taxonomy["families"]
            if family["mvp_picker_visibility"] == "strict_mvp_visible"
        ]
        for promoted_family in (
            "animals",
            "food_cooking",
            "plants_nature",
            "shopping_money",
            "work_office",
            "science_math",
            "computing_internet",
            "travel_places_transport",
            "hobbies_crafts",
        ):
            self.assertIn(promoted_family, visible_ids)
            self.assertEqual(
                family_by_id[promoted_family]["mvp_picker_visibility"],
                "strict_mvp_visible",
            )
        for hidden_family in (
            "anime_manga_pop_culture",
            "sat_toefl_exam_prep",
            "casual_slang_register",
            "formal_professional_register",
        ):
            self.assertNotIn(hidden_family, visible_ids)
        mapped_pairs = {
            (row["source_label"], row["target_family"])
            for row in taxonomy["source_label_mappings"]
            if row["source_channel"] == "sense_topics"
        }
        self.assertIn(("food", "food_cooking"), mapped_pairs)
        self.assertIn(("cooking", "food_cooking"), mapped_pairs)


def _write_frequency_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE frequency (id REAL, pmw REAL, lemma TEXT)")
        conn.executemany(
            "INSERT INTO frequency (id, pmw, lemma) VALUES (?, ?, ?)",
            [
                (1, 100.0, "perro"),
                (2, 90.0, "coral"),
                (3, 80.0, "flor"),
                (4, 70.0, "mesa"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def _write_kaikki_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE sense_glosses ("
            "headword_lc TEXT, topics_json TEXT, tags_json TEXT, categories_json TEXT)"
        )
        conn.executemany(
            "INSERT INTO sense_glosses "
            "(headword_lc, topics_json, tags_json, categories_json) VALUES (?, ?, ?, ?)",
            [
                ("perro", '["animals"]', "[]", "[]"),
                ("coral", '["zoology"]', "[]", "[]"),
                ("flor", '["botany"]', "[]", "[]"),
                ("mesa", '["natural sciences"]', "[]", "[]"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def _taxonomy_json(*, extra_mapping: dict[str, object] | None = None) -> str:
    mappings = [
        {
            "source_channel": "sense_topics",
            "source_label": "animals",
            "target_family": "animals",
            "weight": 0.95,
            "confidence": 0.9,
            "policy": "trusted_direct_animal_label",
        },
        {
            "source_channel": "sense_topics",
            "source_label": "zoology",
            "target_family": "animals",
            "weight": 0.85,
            "confidence": 0.85,
            "policy": "trusted_animal_science_label",
        },
        {
            "source_channel": "sense_topics",
            "source_label": "botany",
            "target_family": "plants_nature",
            "weight": 0.9,
            "confidence": 0.9,
            "policy": "trusted_direct_plant_label",
        },
    ]
    if extra_mapping:
        mappings.append(extra_mapping)
    import json

    return json.dumps(
        {
            "schema_version": 1,
            "lifecycle_policy": {
                "preference_ids_are_append_only": True,
            },
            "families": [
                {
                    "id": "animals",
                    "readiness_state": "p0_enrichment",
                    "axis": "topic",
                    "ux_group": "interests_style",
                    "pair_scope": "all_supported_pairs",
                    "mvp_picker_visibility": "strict_mvp_visible",
                },
                {
                    "id": "plants_nature",
                    "readiness_state": "p0_enrichment",
                    "axis": "topic",
                    "ux_group": "interests_style",
                    "pair_scope": "all_supported_pairs",
                    "mvp_picker_visibility": "future_beta_hidden",
                },
                {
                    "id": "sat_toefl_exam_prep",
                    "readiness_state": "legal_source_gated",
                    "axis": "topic",
                    "ux_group": "interests_style",
                    "pair_scope": "target_language:en",
                    "mvp_picker_visibility": "legal_source_gated_hidden",
                },
            ],
            "source_label_mappings": mappings,
            "excluded_source_labels": [
                {
                    "source_label": "natural_sciences",
                    "target_family": "animals",
                    "reason": "too broad to substitute for animals preference",
                }
            ],
        }
    )


if __name__ == "__main__":
    unittest.main()
