from __future__ import annotations

import csv
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from semantic_veto_srs_source_stack_audit_en_es import (  # noqa: E402
    audit_spalex_csv,
    build_source_stack_audit_report,
    render_source_stack_markdown,
)


class SemanticVetoSrsSourceStackAuditTests(unittest.TestCase):
    def test_spalex_csv_audit_measures_frequency_prevalence_and_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "word_info.csv"
            _write_spalex_csv(
                csv_path,
                [
                    ("que", 7.4, 2.1),
                    ("casa", 6.0, 1.7),
                    ("medicina", 4.5, 1.1),
                    ("cardiaco", 3.7, 0.9),
                    ("term-ignored", 3.1, 0.2),
                ],
            )

            audit = audit_spalex_csv(csv_path, target_sizes=(3, 5))

            self.assertEqual(audit["status"], "ok")
            self.assertEqual(audit["row_count"], 5)
            self.assertEqual(audit["clean_distinct_spelling_count"], 4)
            self.assertEqual(audit["column_coverage"]["zipf"]["share"], 1.0)
            readiness = {row["target_size"]: row for row in audit["target_readiness"]}
            self.assertTrue(readiness[3]["reaches_target"])
            self.assertFalse(readiness[5]["reaches_target"])
            self.assertEqual(audit["top_20_by_zipf"][:2], ["que", "casa"])

    def test_combined_stack_keeps_cde_seed_before_spalex_expansion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            csv_path = tmp_path / "word_info.csv"
            current_db = tmp_path / "freq-es-cde.sqlite"
            forward_db = tmp_path / "wiktionary-es-en.sqlite"
            reverse_db = tmp_path / "wiktionary-en-es.sqlite"
            _write_spalex_csv(
                csv_path,
                [
                    ("que", 7.4, 2.1),
                    ("casa", 6.0, 1.7),
                    ("medicina", 4.5, 1.1),
                    ("cardiaco", 3.7, 0.9),
                    ("legal", 3.1, 0.2),
                ],
            )
            _write_current_frequency_db(current_db, [("el", "l"), ("de", "e"), ("casa", "n")])
            _write_kaikki_forward_db(
                forward_db,
                {
                    "el": ("det", []),
                    "de": ("prep", []),
                    "casa": ("noun", []),
                    "que": ("conj", []),
                    "medicina": ("noun", ["medicine", "sciences"]),
                    "cardiaco": ("adj", ["medicine"]),
                },
            )
            _write_kaikki_reverse_db(reverse_db, ["el", "de", "casa", "que", "medicina"])

            report = build_source_stack_audit_report(
                spalex_csv=csv_path,
                current_frequency_db=current_db,
                kaikki_forward_db=forward_db,
                kaikki_reverse_db=reverse_db,
                target_sizes=(5,),
                generated_at="2026-05-17T00:00:00+00:00",
            )

            stack = report["combined_stack"]
            self.assertEqual(stack["cde_missing_from_spalex_count"], 2)
            readiness = stack["target_readiness"][0]
            self.assertEqual(readiness["baseline_rows"], 3)
            self.assertEqual(readiness["spalex_added_rows"], 2)
            self.assertEqual(readiness["pos_mapped_from_cde_or_kaikki_count"], 5)
            self.assertEqual(readiness["explicit_topic_count"], 1)
            self.assertEqual(readiness["medicine_signal_count"], 1)
            self.assertIn(
                "SPALEX_NOT_STANDALONE_REPLACEMENT",
                {finding["code"] for finding in report["findings"]},
            )
            markdown = render_source_stack_markdown(report)
            self.assertIn("freq-es-cde`: keep as the current seed/baseline", markdown)

    def test_missing_spalex_input_marks_report_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            current_db = tmp_path / "freq-es-cde.sqlite"
            forward_db = tmp_path / "wiktionary-es-en.sqlite"
            reverse_db = tmp_path / "wiktionary-en-es.sqlite"
            _write_current_frequency_db(current_db, [("el", "l")])
            _write_kaikki_forward_db(forward_db, {"el": ("det", [])})
            _write_kaikki_reverse_db(reverse_db, ["el"])

            report = build_source_stack_audit_report(
                spalex_csv=tmp_path / "missing.csv",
                current_frequency_db=current_db,
                kaikki_forward_db=forward_db,
                kaikki_reverse_db=reverse_db,
                target_sizes=(1,),
            )

            self.assertEqual(report["summary"]["status"], "error")
            self.assertIn("SPALEX_UNAVAILABLE", {finding["code"] for finding in report["findings"]})


def _write_spalex_csv(path: Path, rows: list[tuple[str, float, float]]) -> None:
    fieldnames = [
        "spelling",
        "count_total",
        "percent_total",
        "prevalence_total",
        "count_nts",
        "percent_nts",
        "prevalence_nts",
        "count_ntl",
        "percent_ntl",
        "prevalence_ntl",
        "freq",
        "zipf",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for spelling, zipf, prevalence in rows:
            writer.writerow(
                {
                    "spelling": spelling,
                    "count_total": 200,
                    "percent_total": 95,
                    "prevalence_total": prevalence,
                    "count_nts": 100,
                    "percent_nts": 95,
                    "prevalence_nts": prevalence,
                    "count_ntl": 100,
                    "percent_ntl": 95,
                    "prevalence_ntl": prevalence,
                    "freq": 100.0,
                    "zipf": zipf,
                }
            )


def _write_current_frequency_db(path: Path, rows: list[tuple[str, str]]) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE frequency (id REAL, freq REAL, lemma TEXT, pos TEXT)")
        conn.executemany(
            "INSERT INTO frequency (id, freq, lemma, pos) VALUES (?, ?, ?, ?)",
            [(index + 1, 1000.0 - index, lemma, pos) for index, (lemma, pos) in enumerate(rows)],
        )
        conn.commit()
    finally:
        conn.close()


def _write_kaikki_forward_db(path: Path, rows: dict[str, tuple[str, list[str]]]) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE entries ("
            "headword TEXT, headword_lc TEXT, translation TEXT, translation_lc TEXT, "
            "rank INTEGER, pos TEXT, entry_ord INTEGER, gloss_ord INTEGER)"
        )
        conn.execute(
            "CREATE TABLE entry_meta ("
            "entry_ord INTEGER, headword TEXT, headword_lc TEXT, lang TEXT, lang_code TEXT, "
            "pos TEXT, pos_title TEXT, categories_json TEXT, forms_json TEXT, sounds_json TEXT, "
            "synonyms_json TEXT, tags_json TEXT, etymology_text TEXT)"
        )
        conn.execute(
            "CREATE TABLE sense_glosses ("
            "entry_ord INTEGER, sense_ord INTEGER, gloss_ord INTEGER, headword TEXT, "
            "headword_lc TEXT, translation TEXT, translation_lc TEXT, pos TEXT, "
            "raw_glosses_json TEXT, tags_json TEXT, topics_json TEXT, categories_json TEXT, "
            "form_of_json TEXT, alt_of_json TEXT)"
        )
        for index, (lemma, (pos, topics)) in enumerate(rows.items(), 1):
            topics_json = "[" + ",".join(f'"{topic}"' for topic in topics) + "]"
            conn.execute(
                "INSERT INTO entries VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (lemma, lemma, f"{lemma} gloss", f"{lemma} gloss", index, pos, index, 1),
            )
            conn.execute(
                "INSERT INTO entry_meta VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (index, lemma, lemma, "Spanish", "es", pos, pos, "[]", "[]", "[]", "[]", "[]", ""),
            )
            conn.execute(
                "INSERT INTO sense_glosses VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    index,
                    1,
                    1,
                    lemma,
                    lemma,
                    f"{lemma} gloss",
                    f"{lemma} gloss",
                    pos,
                    "[]",
                    "[]",
                    topics_json,
                    "[]",
                    "[]",
                    "[]",
                ),
            )
        conn.execute("CREATE TABLE meta (key TEXT, value TEXT)")
        conn.execute("INSERT INTO meta VALUES ('metadata', '{\"source_provider\":\"test\"}')")
        conn.commit()
    finally:
        conn.close()


def _write_kaikki_reverse_db(path: Path, spanish_targets: list[str]) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE entries ("
            "headword TEXT, headword_lc TEXT, translation TEXT, translation_lc TEXT, "
            "rank INTEGER, pos TEXT, entry_ord INTEGER, gloss_ord INTEGER)"
        )
        for index, target in enumerate(spanish_targets, 1):
            conn.execute(
                "INSERT INTO entries VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (f"en-{target}", f"en-{target}", target, target, index, "noun", index, 1),
            )
        conn.execute("CREATE TABLE meta (key TEXT, value TEXT)")
        conn.execute("INSERT INTO meta VALUES ('metadata', '{\"source_provider\":\"test\"}')")
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
