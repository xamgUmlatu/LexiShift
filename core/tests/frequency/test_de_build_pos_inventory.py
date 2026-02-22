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

from lexishift_core.frequency.de.build import build_de_frequency_sqlite  # noqa: E402


class TestDeBuildPosInventory(unittest.TestCase):
    def test_build_de_frequency_records_pos_inventory_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            input_path = workspace / "deu_news_2023_1M-words.txt"
            pos_lexicon_path = workspace / "de-pos-compact.tsv"
            output_path = workspace / "freq-de-default.sqlite"

            input_path.write_text(
                "\n".join(
                    (
                        "1\tKatze\t5",
                        "2\tlaufen\t3",
                        "3\txwort\t2",
                    )
                ),
                encoding="utf-8",
            )
            pos_lexicon_path.write_text(
                "\n".join(
                    (
                        "katze\tSUB",
                        "laufen\tVVFIN",
                        "xwort\tZZTOP",
                    )
                ),
                encoding="utf-8",
            )

            result = build_de_frequency_sqlite(
                input_path=input_path,
                output_path=output_path,
                min_count=1,
                min_lemma_count=1,
                min_lemma_length=2,
                disable_lexicon_whitelist=True,
                language_packs_dir=workspace / "language_packs",
                pos_lexicon_path=pos_lexicon_path,
                pos_format="generic_compact",
                no_lemmatize=True,
                overwrite=True,
            )

            self.assertEqual(result.pos_inventory["rows_with_pos"], 3)
            self.assertEqual(result.pos_inventory["rows_without_pos"], 0)
            self.assertEqual(result.pos_inventory["pos_inventory_size"], 3)
            self.assertEqual(result.pos_inventory["unknown_pos_inventory_size"], 1)
            self.assertEqual(
                result.pos_inventory["unknown_pos_inventory_top"],
                [{"tag": "ZZTOP", "count": 1}],
            )

            with sqlite3.connect(output_path) as conn:
                row = conn.execute("SELECT value FROM meta WHERE key='metadata'").fetchone()
            self.assertIsNotNone(row)
            payload = json.loads(str(row[0]))
            pos_inventory = payload.get("pos_inventory")
            self.assertIsInstance(pos_inventory, dict)
            self.assertEqual(pos_inventory["unknown_pos_inventory_size"], 1)
            self.assertEqual(pos_inventory["pos_source_provider"], "freq-de-default")


if __name__ == "__main__":
    unittest.main()
