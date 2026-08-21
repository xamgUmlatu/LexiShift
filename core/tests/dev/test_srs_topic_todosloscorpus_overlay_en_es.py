from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_topic_todosloscorpus_overlay_en_es import build_report, render_markdown  # noqa: E402


class SrsTopicTodosLosCorpusOverlayEnEsTests(unittest.TestCase):
    def test_build_report_matches_static_cc0_sources_and_reports_unmatched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sources_root = root / "sources"
            sources_root.mkdir()
            registry = root / "registry.json"
            frequency = root / "frequency.sqlite"
            _write_frequency_db(
                frequency,
                ("abeja", "águila", "abeto", "guitarra", "sangre", "cera"),
            )
            _write_json(
                sources_root / "animals.json",
                {
                    "description": "abeto",
                    "animals": [{"name": "Abeja"}, {"name": "Águila"}, {"name": "Yak"}],
                },
            )
            _write_json(
                sources_root / "trees.json",
                {
                    "trees": [
                        {"name": "abeto", "number": "s"},
                        {"name": "abetos", "number": "p"},
                    ]
                },
            )
            _write_json(sources_root / "instruments.json", ["guitarra", "theremín"])
            _write_json(
                sources_root / "fluids.json",
                {"description": "body fluids", "fluids": [{"name": "sangre"}, {"name": "cera"}]},
            )
            _write_json(sources_root / "candidate.json", ["oficina"])
            _write_json(
                registry,
                {
                    "schema_version": 1,
                    "language_pair": "en-es",
                    "sources": [
                        {
                            "id": "animals",
                            "provider": "Lingwars/todosloscorpus",
                            "license": "CC0",
                            "source_url": "animals.json",
                            "ingest_state": "direct_runtime",
                            "target_family": "animals",
                            "membership": 1.0,
                            "confidence": 0.98,
                        },
                        {
                            "id": "trees",
                            "provider": "Lingwars/todosloscorpus",
                            "license": "CC0",
                            "source_url": "trees.json",
                            "ingest_state": "direct_runtime",
                            "target_family": "plants_nature",
                            "filters": {"number": "s"},
                        },
                        {
                            "id": "instruments",
                            "provider": "Lingwars/todosloscorpus",
                            "license": "CC0",
                            "source_url": "instruments.json",
                            "ingest_state": "direct_runtime",
                            "target_family": "music_media_entertainment",
                        },
                        {
                            "id": "body_fluids",
                            "provider": "Lingwars/todosloscorpus",
                            "license": "CC0",
                            "source_url": "fluids.json",
                            "ingest_state": "direct_runtime",
                            "target_family": "medicine_health",
                            "exclude_lemmas": ["cera"],
                        },
                        {
                            "id": "future_office",
                            "provider": "Lingwars/todosloscorpus",
                            "license": "CC0",
                            "source_url": "candidate.json",
                            "ingest_state": "candidate_not_runtime",
                            "target_family": "work_office",
                        },
                    ],
                },
            )

            report = build_report(
                registry_json=registry,
                frequency_db=frequency,
                source_root=sources_root,
                generated_at="2026-07-06T00:00:00+00:00",
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["row_count"], 5)
        self.assertEqual(report["summary"]["unique_lemma_count"], 5)
        self.assertEqual(report["summary"]["unmatched_entry_count"], 2)
        self.assertEqual(report["summary"]["filtered_entry_count"], 1)
        self.assertEqual(report["summary"]["skipped_source_count"], 1)
        self.assertEqual(
            report["summary"]["runtime_effective_counts_by_topic"],
            {
                "animals": 2,
                "medicine_health": 1,
                "music_media_entertainment": 1,
                "plants_nature": 1,
            },
        )
        self.assertFalse(any(row["lemma"] == "abetos" for row in report["rows"]))
        self.assertFalse(
            any(row["lemma"] == "abeto" and row["topic"] == "animals" for row in report["rows"])
        )
        self.assertFalse(any(row["lemma"] == "cera" for row in report["rows"]))
        row = next(item for item in report["rows"] if item["lemma"] == "abeja")
        self.assertEqual(row["source_channel"], "cc0_static_topic_list")
        self.assertEqual(row["confidence_label"], "strong")
        self.assertEqual(row["provenance"]["license"], "CC0")
        markdown = render_markdown(report)
        self.assertIn("Todos Los Corpus Topic Overlay", markdown)
        self.assertIn("future_office", markdown)

    def test_duplicate_rows_merge_source_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sources_root = root / "sources"
            sources_root.mkdir()
            registry = root / "registry.json"
            frequency = root / "frequency.sqlite"
            _write_frequency_db(frequency, ("abeja",))
            _write_json(sources_root / "a.json", ["abeja"])
            _write_json(sources_root / "b.json", [{"name": "abeja"}])
            _write_json(
                registry,
                {
                    "schema_version": 1,
                    "language_pair": "en-es",
                    "sources": [
                        {
                            "id": "animals_a",
                            "provider": "Lingwars/todosloscorpus",
                            "license": "CC0",
                            "source_url": "a.json",
                            "ingest_state": "direct_runtime",
                            "target_family": "animals",
                        },
                        {
                            "id": "animals_b",
                            "provider": "Lingwars/todosloscorpus",
                            "license": "CC0",
                            "source_url": "b.json",
                            "ingest_state": "direct_runtime",
                            "target_family": "animals",
                        },
                    ],
                },
            )

            report = build_report(
                registry_json=registry,
                frequency_db=frequency,
                source_root=sources_root,
                generated_at="2026-07-06T00:00:00+00:00",
            )

        self.assertEqual(report["summary"]["row_count"], 1)
        self.assertEqual(report["summary"]["duplicate_row_count"], 1)
        self.assertEqual(
            set(report["rows"][0]["provenance"]["source_ids"]),
            {"animals_a", "animals_b"},
        )


def _write_frequency_db(path: Path, lemmas: tuple[str, ...]) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE frequency (
                lemma TEXT,
                source_rank REAL,
                pmw REAL,
                pos TEXT,
                pos_canonical TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO frequency (
                lemma,
                source_rank,
                pmw,
                pos,
                pos_canonical
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                (lemma, float(index + 1), float(100 - index), "n", "noun")
                for index, lemma in enumerate(lemmas)
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
