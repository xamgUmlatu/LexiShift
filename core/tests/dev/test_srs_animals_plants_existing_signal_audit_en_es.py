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
                top_n=10,
                generated_at="2026-05-17T00:00:00+00:00",
            )

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["row_count"], 7)
            findings = {row["code"] for row in report["findings"]}
            self.assertIn("animal_evidence_found", findings)
            self.assertIn("plants_nature_evidence_found", findings)

            families = {row["family"]: row for row in report["families"]}
            animals = families["animals"]
            plants = families["plants_nature"]
            animal_candidates = _candidate_by_lemma(animals)
            plant_candidates = _candidate_by_lemma(plants)

            self.assertEqual(set(animal_candidates), {"coral", "pajaro", "perro"})
            self.assertEqual(set(plant_candidates), {"coral", "flor", "sauce"})
            self.assertNotIn("pasear", animal_candidates)
            self.assertNotIn("mesa", animal_candidates)
            self.assertNotIn("mesa", plant_candidates)

            self.assertEqual(animal_candidates["coral"]["confidence_band"], "high")
            self.assertEqual(plant_candidates["coral"]["confidence_band"], "high")
            self.assertEqual(animal_candidates["pajaro"]["confidence_band"], "review")
            self.assertTrue(animal_candidates["pajaro"]["review_required"])

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
            "entry_ord INTEGER, headword_lc TEXT, translation TEXT, "
            "raw_glosses_json TEXT, tags_json TEXT, topics_json TEXT, categories_json TEXT)"
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
            ],
        )
        conn.executemany(
            "INSERT INTO sense_glosses "
            "(entry_ord, headword_lc, translation, raw_glosses_json, tags_json, "
            "topics_json, categories_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (1, "perro", "dog", "[]", "[]", "[]", "[]"),
                (2, "coral", "coral", '["(zoology) coral"]', "[]", '["zoology"]', "[]"),
                (2, "coral", "coral", '["(botany) coral tree"]', "[]", '["botany"]', "[]"),
                (3, "flor", "flower", "[]", "[]", "[]", "[]"),
                (
                    4,
                    "mesa",
                    "table",
                    "[]",
                    "[]",
                    '["natural-sciences", "biology"]',
                    '["es:Biology"]',
                ),
                (5, "pasear", "to walk", '["to ride on an animal"]', "[]", "[]", "[]"),
                (6, "pajaro", "bird", "[]", "[]", "[]", "[]"),
                (7, "sauce", "willow", "[]", "[]", "[]", "[]"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
