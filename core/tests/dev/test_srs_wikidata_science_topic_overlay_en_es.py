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

from srs_wikidata_science_topic_overlay_en_es import build_report, render_markdown  # noqa: E402


class TestSrsWikidataScienceTopicOverlayEnEs(unittest.TestCase):
    def test_build_report_promotes_safe_elements_and_units(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frequency = root / "frequency.sqlite"
            fixture = root / "fixture.json"
            _write_frequency_db(
                frequency,
                ("oro", "radio", "oxígeno", "kilómetro", "metro", "julio"),
            )
            _write_json(
                fixture,
                {
                    "element_rows": [
                        {
                            "label": "oro",
                            "qid": "Q897",
                            "description": "elemento químico con número atómico 79",
                        },
                        {
                            "label": "radio",
                            "qid": "Q1128",
                            "description": "elemento químico con número atómico 88",
                        },
                        {
                            "label": "oxígeno",
                            "qid": "Q629",
                            "description": "elemento químico",
                        },
                        {
                            "label": "ununseptio",
                            "qid": "Q1",
                            "description": "elemento químico hipotético",
                        },
                    ],
                    "unit_rows": [
                        {
                            "label": "kilómetro",
                            "qid": "Q828224",
                            "description": "unidad de longitud",
                        },
                        {
                            "label": "metro",
                            "qid": "Q11573",
                            "description": "unidad básica de medida de la longitud",
                        },
                    ],
                },
            )

            report = build_report(
                frequency_db=frequency,
                fixture_json=fixture,
                top_n=10000,
                generated_at="2026-07-06T00:00:00+00:00",
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["row_count"], 3)
        self.assertEqual(
            report["summary"]["counts_by_source"],
            {"wikidata_chemical_elements": 2, "wikidata_units_of_measure": 1},
        )
        rows_by_lemma = {str(row["lemma"]): row for row in report["rows"]}
        self.assertEqual(set(rows_by_lemma), {"kilómetro", "oro", "oxígeno"})
        self.assertEqual(rows_by_lemma["oro"]["topic"], "science_technology")
        self.assertEqual(rows_by_lemma["oro"]["confidence_label"], "strong")
        self.assertEqual(rows_by_lemma["oro"]["provenance"]["wikidata_qids"], ["Q897"])
        self.assertEqual(rows_by_lemma["kilómetro"]["facet_id"], "units_of_measure")
        skip_reasons = {
            (str(row["label"]).lower(), row["reason"]) for row in report["skipped_rows"]
        }
        self.assertIn(("radio", "excluded_homograph"), skip_reasons)
        self.assertIn(("metro", "excluded_homograph"), skip_reasons)
        self.assertIn(("ununseptio", "outside_frequency_frontier"), skip_reasons)
        markdown = render_markdown(report)
        self.assertIn("Wikidata Science Topic Overlay", markdown)
        self.assertIn("kilómetro", markdown)


def _write_frequency_db(path: Path, lemmas: tuple[str, ...]) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE frequency (
                lemma TEXT,
                source_rank REAL,
                pmw REAL,
                pos TEXT,
                pos_canonical TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO frequency (
                lemma,
                source_rank,
                pmw,
                pos,
                pos_canonical
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                (lemma, float(index + 1), float(100 - index), "n", "noun")
                for index, lemma in enumerate(lemmas)
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
