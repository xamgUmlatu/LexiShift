from __future__ import annotations

from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.pack_artifact_metrics import (  # noqa: E402
    sqlite_artifact_metrics_for_pack,
)


class TestPackArtifactMetrics(unittest.TestCase):
    def test_frequency_sqlite_metrics_include_rows_lemmas_pos_and_topics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "frequency.sqlite"
            with sqlite3.connect(db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE frequency (
                        lemma TEXT,
                        freq REAL,
                        pos TEXT,
                        topics_json TEXT
                    );
                    """
                )
                conn.executemany(
                    "INSERT INTO frequency (lemma, freq, pos, topics_json) VALUES (?, ?, ?, ?);",
                    [
                        ("gato", 100.0, "n", '["animals"]'),
                        ("gato", 50.0, "", ""),
                        ("perro", 25.0, "n", None),
                    ],
                )
                conn.commit()

            metrics = sqlite_artifact_metrics_for_pack(
                pack_kind="frequency",
                artifact_path=db_path,
            )

        self.assertEqual(
            metrics,
            {
                "row_count": 3,
                "distinct_lemma_count": 2,
                "pos_rows": 2,
                "topic_domain_rows": 1,
            },
        )

    def test_non_frequency_or_unreadable_artifacts_do_not_invent_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_path = Path(tmp) / "not-sqlite.sqlite"
            bad_path.write_text("not sqlite", encoding="utf-8")

            self.assertEqual(
                sqlite_artifact_metrics_for_pack(pack_kind="embedding", artifact_path=bad_path),
                {},
            )
            self.assertEqual(
                sqlite_artifact_metrics_for_pack(pack_kind="frequency", artifact_path=bad_path),
                {},
            )


if __name__ == "__main__":
    unittest.main()
