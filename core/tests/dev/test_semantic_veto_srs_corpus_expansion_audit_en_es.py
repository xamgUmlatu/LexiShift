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

from semantic_veto_srs_corpus_expansion_audit_en_es import (  # noqa: E402
    audit_frequency_candidate,
    build_corpus_expansion_audit_report,
    render_corpus_expansion_markdown,
)


class SemanticVetoSrsCorpusExpansionAuditTests(unittest.TestCase):
    def test_candidate_audit_measures_size_ordering_pos_and_topics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "candidate.sqlite"
            _write_frequency_db(db_path, row_count=6000, include_topics=True)

            audit = audit_frequency_candidate(
                path=db_path,
                label="expanded_candidate",
                target_sizes=(2000, 5000, 10000),
            )

            self.assertEqual(audit["status"], "ok")
            self.assertEqual(audit["unique_lemma_count"], 6000)
            self.assertEqual(audit["resolved_columns"]["lemma"], "lemma")
            self.assertEqual(audit["resolved_columns"]["rank"], "rank")
            self.assertEqual(audit["resolved_columns"]["frequency"], "freq")
            self.assertEqual(audit["resolved_columns"]["pos"], "pos")
            self.assertEqual(audit["column_coverage"]["pos_nonempty_share"], 1.0)
            self.assertGreater(audit["column_coverage"]["topic_row_share"], 0.0)
            readiness = {row["target_size"]: row for row in audit["target_readiness"]}
            self.assertTrue(readiness[5000]["reaches_target"])
            self.assertFalse(readiness[10000]["reaches_target"])
            self.assertNotIn("below_5000_distinct_lemmas", audit["issues"])
            self.assertNotIn("missing_or_empty_pos_column", audit["issues"])

    def test_report_keeps_topic_absence_visible_without_blocking_general_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "current.sqlite"
            _write_frequency_db(db_path, row_count=2000, include_topics=False)

            report = build_corpus_expansion_audit_report(
                candidate_dbs=[db_path],
                target_sizes=(2000, 5000, 10000),
                generated_at="2026-05-14T00:00:00+00:00",
            )

            summary = report["summary"]
            self.assertEqual(summary["status"], "review")
            self.assertEqual(summary["current_unique_lemma_count"], 2000)
            self.assertEqual(summary["candidate_reaching_5000"], False)
            self.assertIn(
                "no_candidate_has_topic_or_domain_rows",
                summary["expansion_blockers"],
            )
            markdown = render_corpus_expansion_markdown(report)
            self.assertIn("Candidate Source Research Matrix", markdown)
            self.assertIn("Do not start another paid semantic-veto generation wave", markdown)

    def test_missing_candidate_is_an_error(self) -> None:
        audit = audit_frequency_candidate(
            path=Path("/tmp/lexishift-missing-corpus-expansion.sqlite"),
            label="missing",
            target_sizes=(2000, 5000),
        )

        self.assertEqual(audit["status"], "error")
        self.assertIn("candidate_db_missing", audit["issues"])


def _write_frequency_db(path: Path, *, row_count: int, include_topics: bool) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE frequency (lemma TEXT, rank REAL, freq REAL, pos TEXT, topics TEXT)"
        )
        rows = []
        for index in range(1, row_count + 1):
            topics = "medicine,science" if include_topics and index % 3 == 0 else ""
            pos = "n" if index % 2 else "v"
            rows.append((f"lemma_{index}", index, float(row_count - index + 1), pos, topics))
        conn.executemany(
            "INSERT INTO frequency (lemma, rank, freq, pos, topics) VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        conn.execute("CREATE TABLE meta (key TEXT, value TEXT)")
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            ("metadata", '{"source": "synthetic", "row_count": %d}' % row_count),
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
