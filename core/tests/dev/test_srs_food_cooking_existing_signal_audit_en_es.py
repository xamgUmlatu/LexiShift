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

from srs_food_cooking_existing_signal_audit_en_es import (  # noqa: E402
    build_report,
    evidence_from_rows,
    load_food_policy,
    render_markdown,
)


class SrsFoodCookingExistingSignalAuditTests(unittest.TestCase):
    def test_confidence_audit_finds_food_without_mutating_sources(self) -> None:
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
                generated_at="2026-05-19T00:00:00+00:00",
            )

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["row_count"], 7)
            findings = {row["code"] for row in report["findings"]}
            self.assertIn("food_cooking_evidence_found", findings)
            self.assertIn("food_cooking_overlap_allowed", findings)

            family = report["family"]
            candidates = _candidate_by_lemma(family)
            self.assertLessEqual({"pan", "caldo", "manzana", "ave"}, set(candidates))
            self.assertNotIn("mesa", candidates)
            self.assertNotIn("rosa", candidates)

            self.assertEqual(candidates["pan"]["best_tier"], "B")
            self.assertEqual(candidates["pan"]["confidence_band"], "high")
            self.assertEqual(candidates["caldo"]["best_tier"], "C")
            self.assertIn(candidates["caldo"]["confidence_band"], {"medium", "high"})
            self.assertTrue(candidates["caldo"]["review_required"])
            self.assertEqual(candidates["manzana"]["best_tier"], "B")
            self.assertTrue(candidates["ave"]["review_required"])

            markdown = render_markdown(report)
            self.assertIn("Food/Cooking Existing Signal Audit", markdown)
            self.assertIn("food_cooking_evidence_found", markdown)
            self.assertIn("food/cooking can intentionally overlap", str(report["limitations"]))

    def test_policy_skips_reviewed_false_positive_signals(self) -> None:
        policy = load_food_policy()

        blocked_examples = {
            "anaranjado": [
                _row("noun", "orange (the colour of the fruit of an orange tree)", ["es:Colors"])
            ],
            "limonero": [_row("noun", "lemon, lemon tree", [], entry_categories=["es:Trees"])],
            "cha": [_row("noun", "tea", ["Spanish terms with historical senses"])],
            "claudia": [_row("noun", "greengage", ["es:Fruits"])],
            "cocobolo": [_row("noun", "cocobolo", ["es:Legumes"])],
            "loco": [
                _row("adj", "crazy", [], entry_categories=["es:Seafood", "es:Legumes"]),
                _row("noun", "person", [], raw_glosses=["fruit"]),
            ],
            "morena": [_row("noun", "moray", ["es:Fish"])],
        }
        for lemma, rows in blocked_examples.items():
            with self.subTest(lemma=lemma):
                self.assertEqual(evidence_from_rows(lemma, rows, policy), [])

        accepted = evidence_from_rows("arroz", [_row("noun", "rice", ["es:Foods"])], policy)
        self.assertTrue(accepted)
        self.assertEqual(accepted[0].source_label, "foods")


def _candidate_by_lemma(family: dict[str, object] | object) -> dict[str, dict[str, object]]:
    if not isinstance(family, dict):
        return {}
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
                (1, 100.0, "pan"),
                (2, 90.0, "caldo"),
                (3, 80.0, "manzana"),
                (4, 70.0, "ave"),
                (5, 60.0, "mesa"),
                (6, 50.0, "rosa"),
                (7, 40.0, "pintar"),
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
                (1, "pan", "[]", "[]"),
                (2, "caldo", "[]", '["es:Soups"]'),
                (3, "manzana", "[]", '["es:Fruits"]'),
                (4, "ave", "[]", '["es:Meats", "es:Animals"]'),
                (5, "mesa", "[]", "[]"),
                (6, "rosa", "[]", '["es:Flowers"]'),
                (7, "pintar", "[]", "[]"),
            ],
        )
        conn.executemany(
            "INSERT INTO sense_glosses "
            "(entry_ord, sense_ord, gloss_ord, headword_lc, pos, translation, "
            "raw_glosses_json, tags_json, topics_json, categories_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (1, 0, 0, "pan", "noun", "bread", "[]", "[]", "[]", "[]"),
                (2, 0, 0, "caldo", "noun", "broth", "[]", "[]", "[]", '["es:Soups"]'),
                (
                    3,
                    0,
                    0,
                    "manzana",
                    "noun",
                    "apple",
                    "[]",
                    "[]",
                    "[]",
                    '["es:Fruits"]',
                ),
                (4, 0, 0, "ave", "noun", "bird", "[]", "[]", "[]", '["es:Meats"]'),
                (5, 0, 0, "mesa", "noun", "table", "[]", "[]", "[]", "[]"),
                (6, 0, 0, "rosa", "noun", "rose", "[]", "[]", "[]", '["es:Flowers"]'),
                (
                    7,
                    0,
                    0,
                    "pintar",
                    "verb",
                    "to paint",
                    '["to paint food on a sign"]',
                    "[]",
                    "[]",
                    "[]",
                ),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def _row(
    pos: str,
    translation: str,
    sense_categories: list[str],
    *,
    entry_categories: list[str] | None = None,
    raw_glosses: list[str] | None = None,
) -> dict[str, object]:
    return {
        "pos": pos,
        "translation": translation,
        "raw_glosses": raw_glosses or [],
        "topics": [],
        "sense_tags": [],
        "sense_categories": sense_categories,
        "entry_tags": [],
        "entry_categories": entry_categories or [],
        "sense_index": 0,
    }


if __name__ == "__main__":
    unittest.main()
