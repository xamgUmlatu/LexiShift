from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CORE_ROOT = os.path.join(PROJECT_ROOT, "core")
for path in (PROJECT_ROOT, CORE_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from lexishift_core.pos.ud_ancora import (  # noqa: E402
    DEFAULT_PACK_ID,
    build_ud_ancora_pos_overlay,
)


class TestBuildUdAncoraPosOverlayEs(unittest.TestCase):
    def test_builds_majority_upos_overlay_with_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "es_ancora-ud-mini.conllu"
            source.write_text(
                "\n".join(
                    [
                        "# sent_id = 1",
                        "1\tEl\tel\tDET\t_\t_\t2\tdet\t_\t_",
                        "2\tgato\tgato\tNOUN\t_\t_\t3\tnsubj\t_\t_",
                        "3\tcorre\tcorrer\tVERB\t_\t_\t0\troot\t_\t_",
                        "",
                        "# sent_id = 2",
                        "1\tUna\tuno\tDET\t_\t_\t2\tdet\t_\t_",
                        "2\tcasa\tcasa\tNOUN\t_\t_\t0\troot\t_\t_",
                        "",
                        "# sent_id = 3",
                        "1\tGato\tgato\tPROPN\t_\t_\t0\troot\t_\t_",
                        "2\trápido\trápido\tADJ\t_\t_\t1\tamod\t_\t_",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            pack_root = root / DEFAULT_PACK_ID

            metadata = build_ud_ancora_pos_overlay(
                source_paths=(source,),
                output_sqlite=pack_root / "main.sqlite",
                overwrite=True,
                write_sidecars=True,
            )

            self.assertEqual(metadata["row_count"], 6)
            self.assertTrue((pack_root / "main.sqlite").exists())
            self.assertTrue((pack_root / "manifest.json").exists())
            self.assertTrue((pack_root / "provenance.json").exists())
            self.assertTrue((pack_root / "metadata.json").exists())

            with sqlite3.connect(pack_root / "main.sqlite") as conn:
                row = conn.execute(
                    """
                    SELECT raw_pos, pos_canonical, pos_bucket, confidence, source_count,
                           total_count, pos_counts_json
                    FROM pos_overlay
                    WHERE lemma = 'gato'
                    """
                ).fetchone()
                meta_value = conn.execute(
                    "SELECT value FROM meta WHERE key = 'metadata'"
                ).fetchone()[0]

            self.assertEqual(row[0], "NOUN")
            self.assertEqual(row[1], "noun")
            self.assertEqual(row[2], "noun")
            self.assertAlmostEqual(float(row[3]), 0.5)
            self.assertEqual(int(row[4]), 1)
            self.assertEqual(int(row[5]), 2)
            self.assertEqual(json.loads(row[6]), {"NOUN": 1, "PROPN": 1})
            self.assertEqual(json.loads(meta_value)["license"], "CC BY 4.0")

            with sqlite3.connect(pack_root / "main.sqlite") as conn:
                una_row = conn.execute(
                    "SELECT raw_pos, pos_canonical FROM pos_overlay WHERE lemma = 'una'"
                ).fetchone()
            self.assertEqual(una_row, ("DET", "determiner"))


if __name__ == "__main__":
    unittest.main()
