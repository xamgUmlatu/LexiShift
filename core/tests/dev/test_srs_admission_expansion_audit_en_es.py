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

from srs_admission_expansion_audit_en_es import build_report, render_markdown  # noqa: E402


class SrsAdmissionExpansionAuditTests(unittest.TestCase):
    def test_build_report_runs_candidate_pack_through_seed_and_profile_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "candidate.sqlite"
            _write_candidate_db(db_path)

            report = build_report(
                frequency_db=db_path,
                top_n=6,
                preview_limit=4,
                profile_top_n=4,
                profile_interests=("medicine",),
                generated_at="2026-05-17T00:00:00+00:00",
            )

            self.assertEqual(report["status"], "ok")
            seed = report["seed_admission"]
            self.assertEqual(seed["selected_count"], 6)
            self.assertEqual(seed["unique_lemma_count"], 6)
            self.assertEqual(seed["rank_column_counts"], {"id": 6})
            self.assertEqual(seed["pmw_column_counts"], {"pmw": 6})
            self.assertEqual(seed["pos_mapped_count"], 6)
            self.assertEqual(seed["topic_row_count"], 4)
            self.assertEqual(seed["admission_order_preview"][0]["lemma"], "salud")
            self.assertEqual(seed["rank_order_preview"][0]["lemma"], "el")

            scenario = report["profile_scenarios"][0]
            self.assertEqual(scenario["interest"], "medicine")
            self.assertEqual(scenario["status"], "eligible")
            self.assertGreaterEqual(scenario["top_rows_with_exact_interest"], 3)

            markdown = render_markdown(report)
            self.assertIn("SRS Admission Expansion Audit", markdown)
            self.assertIn("Profile Scenarios", markdown)

    def test_missing_candidate_db_marks_review(self) -> None:
        report = build_report(
            frequency_db=Path("/tmp/lexishift-missing-srs-admission-pack.sqlite"),
            top_n=3,
            profile_interests=("medicine",),
            generated_at="2026-05-17T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["summary"]["issues"], ["frequency_db_missing"])


def _write_candidate_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE frequency (id REAL, pmw REAL, lemma TEXT, pos TEXT, topics TEXT)"
        )
        conn.executemany(
            "INSERT INTO frequency (id, pmw, lemma, pos, topics) VALUES (?, ?, ?, ?, ?)",
            [
                (1, 600.0, "el", "d", ""),
                (2, 590.0, "de", "e", ""),
                (3, 580.0, "salud", "n", "medicine,health"),
                (4, 570.0, "clínica", "n", "medicine"),
                (5, 560.0, "diagnóstico", "n", "medicine"),
                (6, 550.0, "banco", "n", "finance"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
