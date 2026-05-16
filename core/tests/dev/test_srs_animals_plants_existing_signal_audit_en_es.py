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

from srs_animals_plants_existing_signal_audit_en_es import (  # noqa: E402
    build_report,
    render_markdown,
)


class SrsAnimalsPlantsExistingSignalAuditTests(unittest.TestCase):
    def test_confidence_audit_splits_animals_from_plants_and_blocks_broad_hits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frequency_db = root / "freq.sqlite"
            kaikki_db = root / "kaikki.sqlite"
            _write_frequency_db(frequency_db)
            _write_kaikki_db(kaikki_db)

            report = build_report(
                frequency_db=frequency_db,
                kaikki_forward_db=kaikki_db,
                top_n=20,
                generated_at="2026-05-17T00:00:00+00:00",
            )

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["row_count"], 11)
            findings = {row["code"] for row in report["findings"]}
            self.assertIn("animal_evidence_found", findings)
            self.assertIn("plants_nature_evidence_found", findings)

            families = {row["family"]: row for row in report["families"]}
            animals = families["animals"]
            plants = families["plants_nature"]
            animal_candidates = _candidate_by_lemma(animals)
            plant_candidates = _candidate_by_lemma(plants)

            self.assertLessEqual(
                {"broma", "coral", "pajaro", "perro", "rana"}, set(animal_candidates)
            )
            self.assertLessEqual({"coral", "flor", "sauce", "trigo"}, set(plant_candidates))
            self.assertNotIn("pasear", animal_candidates)
            self.assertNotIn("carne", animal_candidates)
            self.assertNotIn("mesa", animal_candidates)
            self.assertNotIn("mesa", plant_candidates)

            self.assertEqual(animal_candidates["coral"]["confidence_band"], "high")
            self.assertEqual(plant_candidates["coral"]["confidence_band"], "review")
            self.assertTrue(plant_candidates["coral"]["review_required"])
            self.assertEqual(plant_candidates["flor"]["confidence_band"], "high")
            self.assertEqual(animal_candidates["pajaro"]["best_tier"], "B")
            self.assertEqual(animal_candidates["pajaro"]["confidence_band"], "high")
            self.assertFalse(animal_candidates["pajaro"]["review_required"])
            self.assertEqual(animal_candidates["broma"]["confidence_band"], "review")
            self.assertTrue(animal_candidates["broma"]["review_required"])
            self.assertEqual(plant_candidates["trigo"]["best_tier"], "B")
            self.assertEqual(plant_candidates["trigo"]["confidence_band"], "high")

            broad_only = {
                row["lemma"]: set(row["excluded_labels"]) for row in report["broad_exclusions"]
            }
            self.assertEqual(broad_only["mesa"], {"biology", "natural_sciences"})

            markdown = render_markdown(report)
            self.assertIn("max_evidence_score_v1", str(report["confidence_model"]))
            self.assertIn("Broad Exclusions Sample", markdown)
            self.assertIn("animals", markdown)
            self.assertIn("plants_nature", markdown)


def _candidate_by_lemma(family: dict[str, object]) -> dict[str, dict[str, object]]:
    rows = family["top_candidates"]
    return {
        str(row["lemma"]): row
        for row in (rows if isinstance(rows, list) else [])
        if isinstance(row, dict) and "lemma" in row
    }


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
                (5, 60.0, "pasear"),
                (6, 50.0, "pajaro"),
                (7, 40.0, "sauce"),
                (8, 30.0, "rana"),
                (9, 20.0, "trigo"),
                (10, 10.0, "carne"),
                (11, 9.0, "broma"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def _write_kaikki_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE entry_meta ("
            "entry_ord INTEGER, headword_lc TEXT, tags_json TEXT, categories_json TEXT)"
        )
        conn.execute(
            "CREATE TABLE sense_glosses ("
            "entry_ord INTEGER, sense_ord INTEGER, gloss_ord INTEGER, headword_lc TEXT, "
            "pos TEXT, translation TEXT, raw_glosses_json TEXT, tags_json TEXT, "
            "topics_json TEXT, categories_json TEXT)"
        )
        conn.executemany(
            "INSERT INTO entry_meta "
            "(entry_ord, headword_lc, tags_json, categories_json) VALUES (?, ?, ?, ?)",
            [
                (1, "perro", "[]", '["es:Dogs"]'),
                (2, "coral", "[]", "[]"),
                (3, "flor", "[]", '["es:Flowers"]'),
                (4, "mesa", "[]", "[]"),
                (5, "pasear", "[]", "[]"),
                (6, "pajaro", "[]", "[]"),
                (7, "sauce", "[]", '["es:Trees"]'),
                (8, "rana", "[]", '["es:Amphibians"]'),
                (9, "trigo", "[]", '["es:Grains"]'),
                (10, "carne", "[]", "[]"),
                (11, "broma", "[]", "[]"),
            ],
        )
        conn.executemany(
            "INSERT INTO sense_glosses "
            "(entry_ord, sense_ord, gloss_ord, headword_lc, pos, translation, "
            "raw_glosses_json, tags_json, topics_json, categories_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (1, 0, 0, "perro", "noun", "dog", "[]", "[]", "[]", "[]"),
                (
                    2,
                    0,
                    0,
                    "coral",
                    "noun",
                    "coral",
                    '["(zoology) coral"]',
                    "[]",
                    '["zoology"]',
                    "[]",
                ),
                (
                    2,
                    1,
                    0,
                    "coral",
                    "noun",
                    "coral",
                    '["(botany) coral tree"]',
                    "[]",
                    '["botany"]',
                    "[]",
                ),
                (3, 0, 0, "flor", "noun", "flower", "[]", "[]", "[]", "[]"),
                (
                    4,
                    0,
                    0,
                    "mesa",
                    "noun",
                    "table",
                    "[]",
                    "[]",
                    '["natural-sciences", "biology"]',
                    '["es:Biology"]',
                ),
                (
                    5,
                    0,
                    0,
                    "pasear",
                    "verb",
                    "to walk",
                    '["to ride on an animal"]',
                    "[]",
                    "[]",
                    "[]",
                ),
                (6, 0, 0, "pajaro", "noun", "bird", "[]", "[]", "[]", "[]"),
                (7, 0, 0, "sauce", "noun", "willow", "[]", "[]", "[]", "[]"),
                (8, 0, 0, "rana", "noun", "frog", "[]", "[]", "[]", "[]"),
                (9, 0, 0, "trigo", "noun", "wheat", "[]", "[]", "[]", "[]"),
                (
                    10,
                    0,
                    0,
                    "carne",
                    "noun",
                    "an animal's meat",
                    "[]",
                    "[]",
                    "[]",
                    "[]",
                ),
                (11, 0, 0, "broma", "noun", "joke", "[]", "[]", "[]", "[]"),
                (11, 1, 0, "broma", "noun", "dog", "[]", "[]", "[]", "[]"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
