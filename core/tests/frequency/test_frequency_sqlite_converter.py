from __future__ import annotations

import json
import os
import importlib.util
import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
LEXISHIFT_CORE_ROOT = Path(PROJECT_ROOT) / "lexishift_core"
POS_ROOT = LEXISHIFT_CORE_ROOT / "pos"
lexishift_core_pkg = sys.modules.get("lexishift_core")
if lexishift_core_pkg is None:
    lexishift_core_pkg = types.ModuleType("lexishift_core")
    lexishift_core_pkg.__path__ = [str(LEXISHIFT_CORE_ROOT)]  # type: ignore[attr-defined]
    sys.modules["lexishift_core"] = lexishift_core_pkg
pos_pkg = sys.modules.get("lexishift_core.pos")
if pos_pkg is None:
    pos_pkg = types.ModuleType("lexishift_core.pos")
    pos_pkg.__path__ = [str(POS_ROOT)]  # type: ignore[attr-defined]
    sys.modules["lexishift_core.pos"] = pos_pkg
POS_SPEC = importlib.util.spec_from_file_location(
    "lexishift_core.pos.normalization",
    POS_ROOT / "normalization.py",
)
if POS_SPEC is None or POS_SPEC.loader is None:
    raise RuntimeError(f"Unable to load POS normalization module from {POS_ROOT}")
POS_MODULE = importlib.util.module_from_spec(POS_SPEC)
sys.modules[POS_SPEC.name] = POS_MODULE
POS_SPEC.loader.exec_module(POS_MODULE)
SQLITE_MODULE_PATH = Path(PROJECT_ROOT) / "lexishift_core" / "frequency" / "sqlite.py"
SQLITE_SPEC = importlib.util.spec_from_file_location(
    "lexishift_frequency_sqlite", SQLITE_MODULE_PATH
)
if SQLITE_SPEC is None or SQLITE_SPEC.loader is None:
    raise RuntimeError(f"Unable to load frequency sqlite module: {SQLITE_MODULE_PATH}")
SQLITE_MODULE = importlib.util.module_from_spec(SQLITE_SPEC)
sys.modules[SQLITE_SPEC.name] = SQLITE_MODULE
SQLITE_SPEC.loader.exec_module(SQLITE_MODULE)

ParseConfig = SQLITE_MODULE.ParseConfig  # type: ignore[attr-defined]
PosInventoryConfig = SQLITE_MODULE.PosInventoryConfig  # type: ignore[attr-defined]
TopicEnrichmentConfig = SQLITE_MODULE.TopicEnrichmentConfig  # type: ignore[attr-defined]
convert_frequency_to_sqlite = SQLITE_MODULE.convert_frequency_to_sqlite  # type: ignore[attr-defined]


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

            conn = sqlite3.connect(output_path)
            try:
                row = conn.execute("SELECT value FROM meta WHERE key='metadata'").fetchone()
            finally:
                conn.close()
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

    def test_convert_frequency_can_enrich_topics_from_companion_sqlite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "freq.tsv"
            output_path = Path(tmp) / "freq.sqlite"
            topic_source_path = Path(tmp) / "wiktionary-es-en.sqlite"
            input_path.write_text(
                "\n".join(
                    (
                        "rank\tlemma\tpmw",
                        "1\tmovimiento\t100",
                        "2\thola\t50",
                    )
                ),
                encoding="utf-8",
            )
            conn = sqlite3.connect(topic_source_path)
            try:
                conn.execute(
                    "CREATE TABLE sense_glosses ("
                    "headword TEXT, headword_lc TEXT, topics_json TEXT)"
                )
                conn.executemany(
                    "INSERT INTO sense_glosses (headword, headword_lc, topics_json) "
                    "VALUES (?, ?, ?)",
                    [
                        ("movimiento", "movimiento", json.dumps(["banking", "music"])),
                        ("MOVIMIENTO", "movimiento", json.dumps(["business"])),
                    ],
                )
                conn.commit()
            finally:
                conn.close()

            metadata = convert_frequency_to_sqlite(
                input_path,
                output_path,
                overwrite=True,
                topic_enrichment=TopicEnrichmentConfig(
                    source_sqlite_path=topic_source_path,
                    source_provider="wiktionary-es-en",
                ),
            )

            self.assertTrue(metadata["topic_enrichment_applied"])
            self.assertEqual(metadata["topic_enrichment_source_provider"], "wiktionary-es-en")
            self.assertEqual(metadata["topic_enrichment_matched_lemma_count"], 1)

            conn = sqlite3.connect(output_path)
            try:
                row = conn.execute(
                    "SELECT sense_topics FROM frequency WHERE lemma = 'movimiento' LIMIT 1"
                ).fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(
                    json.loads(str(row[0])),
                    ["banking", "music", "business"],
                )
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
