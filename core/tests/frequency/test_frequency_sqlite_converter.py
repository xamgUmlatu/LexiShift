from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.frequency.sqlite import (  # noqa: E402
    ParseConfig,
    PosInventoryConfig,
    convert_frequency_to_sqlite,
)


class TestFrequencySqliteConverter(unittest.TestCase):
    def test_convert_frequency_records_pos_inventory_and_unknown_tags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "freq.tsv"
            output_path = Path(tmp) / "freq.sqlite"
            input_path.write_text(
                "\n".join(
                    (
                        "rank\tlemma\tpos\tpmw",
                        "1\tgato\tn\t100",
                        "2\traro\tx\t50",
                        "3\tsinpos\t\t20",
                    )
                ),
                encoding="utf-8",
            )

            metadata = convert_frequency_to_sqlite(
                input_path,
                output_path,
                config=ParseConfig(delimiter="\t", header_starts_with="rank", skip_prefixes=()),
                pos_inventory=PosInventoryConfig(
                    source_provider="freq-es-cde",
                    source_kind="frequency",
                    source_profile="freq-es-cde",
                    pos_columns=("pos",),
                ),
            )

            self.assertEqual(metadata["row_count"], 3)
            self.assertEqual(metadata["rows_with_pos"], 2)
            self.assertEqual(metadata["rows_without_pos"], 1)
            self.assertEqual(metadata["pos_inventory_size"], 2)
            self.assertEqual(metadata["unknown_pos_inventory_size"], 1)
            self.assertEqual(metadata["unknown_pos_inventory_top"], [{"tag": "x", "count": 1}])

            with sqlite3.connect(output_path) as conn:
                row = conn.execute("SELECT value FROM meta WHERE key='metadata'").fetchone()
            self.assertIsNotNone(row)
            payload = json.loads(str(row[0]))
            self.assertEqual(payload["unknown_pos_inventory_size"], 1)
            self.assertEqual(payload["pos_source_provider"], "freq-es-cde")

    def test_convert_frequency_without_pos_inventory_keeps_metadata_minimal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "freq.tsv"
            output_path = Path(tmp) / "freq.sqlite"
            input_path.write_text(
                "\n".join(
                    (
                        "rank\tlemma\tpmw",
                        "1\talpha\t10",
                        "2\tbeta\t5",
                    )
                ),
                encoding="utf-8",
            )

            metadata = convert_frequency_to_sqlite(input_path, output_path, overwrite=True)

            self.assertEqual(metadata["row_count"], 2)
            self.assertNotIn("rows_with_pos", metadata)
            self.assertNotIn("unknown_pos_inventory_size", metadata)


if __name__ == "__main__":
    unittest.main()
