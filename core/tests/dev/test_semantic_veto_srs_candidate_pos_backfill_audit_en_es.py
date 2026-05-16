from __future__ import annotations

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

from semantic_veto_srs_candidate_pos_backfill_audit_en_es import (  # noqa: E402
    build_candidate_pos_backfill_report,
    render_candidate_pos_backfill_markdown,
)


class SemanticVetoSrsCandidatePosBackfillAuditTests(unittest.TestCase):
    def test_backfill_report_measures_external_pos_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate_db = root / "candidate.sqlite"
            wiktionary_db = root / "wiktionary-es-en.sqlite"
            freedict_db = root / "freedict-es-en.sqlite"
            _write_candidate_db(
                candidate_db,
                ["casa", "correr", "azul", "rapido", "ambiguo", "missing"],
            )
            _write_wiktionary_db(
                wiktionary_db,
                entry_rows=[
                    ("casa", "noun"),
                    ("correr", "verb"),
                    ("azul", "adj"),
                    ("ambiguo", "noun"),
                ],
                sense_rows=[
                    ("ambiguo", "adj"),
                    ("fuera", "noun"),
                ],
            )
            _write_freedict_db(freedict_db, rows=[("rapido", "adverb")])

            report = build_candidate_pos_backfill_report(
                candidate_db=candidate_db,
                wiktionary_es_en_sqlite=wiktionary_db,
                freedict_es_en_sqlite=freedict_db,
                target_sizes=(3, 5, 6),
                generated_at="2026-05-16T00:00:00+00:00",
            )

            summary = report["summary"]
            self.assertEqual(summary["status"], "review")
            self.assertEqual(summary["candidate_unique_lemma_count"], 6)
            self.assertEqual(summary["any_pos_lemma_count"], 5)
            self.assertEqual(summary["mapped_pos_lemma_count"], 5)
            self.assertEqual(summary["weighted_lexical_bucket_lemma_count"], 4)
            self.assertEqual(summary["ambiguous_raw_pos_lemma_count"], 1)
            self.assertIn("candidate_pos_backfill_incomplete", summary["issues"])
            sources = {source["source_id"]: source for source in report["sources"]}
            self.assertEqual(sources["wiktionary_es_en"]["candidate_hit_count"], 4)
            self.assertEqual(sources["freedict_es_en"]["candidate_hit_count"], 1)
            readiness = {row["target_size"]: row for row in report["target_readiness"]}
            self.assertTrue(readiness[5]["mapped_pos_reaches_target"])
            self.assertFalse(readiness[5]["weighted_lexical_bucket_reaches_target"])
            self.assertFalse(readiness[6]["mapped_pos_reaches_target"])
            rank_bands = {row["rank_band_top_n"]: row for row in report["rank_band_coverage"]}
            self.assertEqual(rank_bands[3]["mapped_pos_lemma_count"], 3)
            self.assertEqual(rank_bands[6]["mapped_pos_lemma_count"], 5)
            scenarios = {row["scenario_id"]: row for row in report["filter_scenarios"]}
            self.assertEqual(scenarios["mapped_pos"]["kept_count"], 5)
            self.assertEqual(
                scenarios["mapped_pos_nonambiguous_surface_clean"]["kept_count"],
                4,
            )
            self.assertEqual(scenarios["confident_weighted_bucket"]["kept_count"], 4)
            markdown = render_candidate_pos_backfill_markdown(report)
            self.assertIn("Source Coverage", markdown)
            self.assertIn("Rank-Band Coverage", markdown)
            self.assertIn("Filter Scenarios", markdown)
            self.assertIn("no-mutation readiness audit", markdown)

    def test_missing_candidate_is_error_but_missing_source_is_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate_db = root / "candidate.sqlite"
            _write_candidate_db(candidate_db, ["uno"])

            report = build_candidate_pos_backfill_report(
                candidate_db=candidate_db,
                wiktionary_es_en_sqlite=root / "missing-wiktionary.sqlite",
                freedict_es_en_sqlite=root / "missing-freedict.sqlite",
                target_sizes=(1,),
                generated_at="2026-05-16T00:00:00+00:00",
            )

            self.assertEqual(report["summary"]["status"], "review")
            self.assertIn("no_external_pos_backfill_available", report["summary"]["issues"])
            self.assertTrue(all(source["status"] == "review" for source in report["sources"]))

        missing_report = build_candidate_pos_backfill_report(
            candidate_db=Path("/tmp/lexishift-missing-pos-backfill.sqlite"),
            wiktionary_es_en_sqlite=None,
            freedict_es_en_sqlite=None,
            target_sizes=(1,),
            generated_at="2026-05-16T00:00:00+00:00",
        )
        self.assertEqual(missing_report["summary"]["status"], "error")
        self.assertIn("candidate_db_missing", missing_report["summary"]["issues"])


def _write_candidate_db(path: Path, lemmas: list[str]) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE frequency (lemma TEXT, rank INTEGER, freq REAL)")
        conn.executemany(
            "INSERT INTO frequency (lemma, rank, freq) VALUES (?, ?, ?)",
            [
                (lemma, index, float(len(lemmas) - index + 1))
                for index, lemma in enumerate(lemmas, start=1)
            ],
        )
        conn.commit()
    finally:
        conn.close()


def _write_wiktionary_db(
    path: Path,
    *,
    entry_rows: list[tuple[str, str]],
    sense_rows: list[tuple[str, str]],
) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE entry_meta (headword_lc TEXT, pos TEXT)")
        conn.execute("CREATE TABLE sense_glosses (headword_lc TEXT, pos TEXT)")
        conn.executemany("INSERT INTO entry_meta (headword_lc, pos) VALUES (?, ?)", entry_rows)
        conn.executemany("INSERT INTO sense_glosses (headword_lc, pos) VALUES (?, ?)", sense_rows)
        conn.commit()
    finally:
        conn.close()


def _write_freedict_db(path: Path, *, rows: list[tuple[str, str]]) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE entries (headword_lc TEXT, pos TEXT)")
        conn.executemany("INSERT INTO entries (headword_lc, pos) VALUES (?, ?)", rows)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
