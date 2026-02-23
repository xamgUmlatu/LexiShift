from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

CORE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if CORE_ROOT not in sys.path:
    sys.path.insert(0, CORE_ROOT)

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_TESTING_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPTS_TESTING_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_TESTING_DIR))

from pos_inventory_audit import build_pos_inventory_report  # noqa: E402


def _write_frequency_db_with_metadata(path: Path, metadata: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE frequency (lemma TEXT, core_rank REAL, pmw REAL, pos TEXT);")
        conn.execute("INSERT INTO frequency (lemma, core_rank, pmw, pos) VALUES ('alpha', 1, 10, 'n');")
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);")
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?);",
            ("metadata", json.dumps(metadata, sort_keys=True)),
        )
        conn.commit()


class TestPosInventoryAudit(unittest.TestCase):
    def test_audit_reads_generic_pos_inventory_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frequency_dir = root / "frequency_packs"
            db_path = frequency_dir / "freq-en-coca.sqlite"
            _write_frequency_db_with_metadata(
                db_path,
                {
                    "row_count": 1,
                    "rows_with_pos": 1,
                    "rows_without_pos": 0,
                    "pos_inventory_size": 2,
                    "unknown_pos_inventory_size": 1,
                    "pos_source_provider": "freq-en-coca",
                    "pos_mapping_profile": "compact-latin",
                    "pos_columns_resolved": ["pos"],
                    "unknown_pos_inventory_top": [{"tag": "u", "count": 1}],
                },
            )

            report = build_pos_inventory_report(data_root=root, top_unknown=5)
            by_name = {row.filename: row for row in report.rows}
            self.assertIn("freq-en-coca.sqlite", by_name)
            row = by_name["freq-en-coca.sqlite"]
            self.assertEqual(row.status, "ok")
            self.assertEqual(row.rows_with_pos, 1)
            self.assertEqual(row.unknown_pos_inventory_size, 1)
            self.assertEqual(row.pos_mapping_profile, "compact-latin")

    def test_audit_reads_nested_de_pos_inventory_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frequency_dir = root / "frequency_packs"
            db_path = frequency_dir / "freq-de-default.sqlite"
            _write_frequency_db_with_metadata(
                db_path,
                {
                    "row_count": 1,
                    "pos_inventory": {
                        "rows_with_pos": 1,
                        "rows_without_pos": 0,
                        "pos_inventory_size": 3,
                        "unknown_pos_inventory_size": 1,
                        "pos_source_provider": "freq-de-default",
                        "pos_mapping_profile": "freq-de-default",
                        "pos_columns_resolved": ["pos"],
                        "unknown_pos_inventory_top": [{"tag": "ZZTOP", "count": 1}],
                    },
                },
            )

            report = build_pos_inventory_report(data_root=root, top_unknown=5)
            by_name = {row.filename: row for row in report.rows}
            self.assertIn("freq-de-default.sqlite", by_name)
            row = by_name["freq-de-default.sqlite"]
            self.assertEqual(row.status, "ok")
            self.assertEqual(row.rows_with_pos, 1)
            self.assertEqual(row.unknown_pos_inventory_size, 1)
            self.assertEqual(row.pos_source_provider, "freq-de-default")


if __name__ == "__main__":
    unittest.main()
