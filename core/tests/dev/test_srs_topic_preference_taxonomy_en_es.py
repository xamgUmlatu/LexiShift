from __future__ import annotations

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
)


class SrsTopicPreferenceTaxonomyTests(unittest.TestCase):
    def test_validates_animals_nature_mapping_and_measures_current_coverage(self) -> None:
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
            self.assertIn("animals_nature_seed_labels_present", findings)
            self.assertIn("excluded_labels_not_mapped_positive", findings)
            family_by_id = {row["family"]: row for row in report["coverage"]["families"]}
            animals = family_by_id["animals_nature"]
            self.assertEqual(animals["row_count"], 3)
            top_labels = {row["label"]: row["count"] for row in animals["top_source_labels"]}
            self.assertEqual(top_labels["animals"], 1)
            self.assertEqual(top_labels["zoology"], 1)
            self.assertEqual(top_labels["botany"], 1)
            self.assertEqual(family_by_id["sat_toefl_exam_prep"]["row_count"], 0)

            markdown = render_markdown(report)
            self.assertIn("Animals/Nature Samples", markdown)
            self.assertIn("animals_nature", markdown)

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
                        "target_family": "animals_nature",
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
            "target_family": "animals_nature",
            "weight": 0.95,
            "confidence": 0.9,
            "policy": "trusted_direct_animal_label",
        },
        {
            "source_channel": "sense_topics",
            "source_label": "zoology",
            "target_family": "animals_nature",
            "weight": 0.85,
            "confidence": 0.85,
            "policy": "trusted_animal_science_label",
        },
        {
            "source_channel": "sense_topics",
            "source_label": "botany",
            "target_family": "animals_nature",
            "weight": 0.55,
            "confidence": 0.7,
            "policy": "trusted_nature_label_not_animal_specific",
        },
    ]
    if extra_mapping:
        mappings.append(extra_mapping)
    import json

    return json.dumps(
        {
            "schema_version": 1,
            "families": [
                {"id": "animals_nature", "readiness_state": "p0_enrichment"},
                {"id": "sat_toefl_exam_prep", "readiness_state": "legal_source_gated"},
            ],
            "source_label_mappings": mappings,
            "excluded_source_labels": [
                {
                    "source_label": "natural_sciences",
                    "reason": "too broad to substitute for animals/nature preference",
                }
            ],
        }
    )


if __name__ == "__main__":
    unittest.main()
