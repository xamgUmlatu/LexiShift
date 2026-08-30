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

from srs_topic_todosloscorpus_source_audit_en_es import (  # noqa: E402
    build_report,
    render_markdown,
)


class SrsTopicTodosLosCorpusSourceAuditEnEsTests(unittest.TestCase):
    def test_audits_registered_promoted_and_candidate_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_root = root / "sources"
            frequency = root / "frequency.sqlite"
            registry = root / "registry.json"
            _write_frequency_db(frequency, ("abeja", "sangre", "cera", "historia"))
            _write_json(
                source_root / "data/animals/common.json",
                {"description": "historia", "animals": [{"name": "abeja"}]},
            )
            _write_json(
                source_root / "data/materials/abridged-body-fluids.json",
                {"description": "body fluids", "fluids": [{"name": "sangre"}, {"name": "cera"}]},
            )
            _write_json(
                source_root / "data/books/academic_subjects.json",
                {"description": "subjects", "subjects": [{"name": "historia"}]},
            )
            _write_json(
                registry,
                {
                    "schema_version": 1,
                    "sources": [
                        {
                            "id": "animals",
                            "provider": "Lingwars/todosloscorpus",
                            "license": "CC0",
                            "source_url": (
                                "https://raw.githubusercontent.com/Lingwars/todosloscorpus/"
                                "main/data/animals/common.json"
                            ),
                            "ingest_state": "direct_runtime",
                            "target_family": "animals",
                            "notes": "Already reviewed animals.",
                        }
                    ],
                },
            )

            report = build_report(
                registry_json=registry,
                frequency_db=frequency,
                source_root=source_root,
                source_paths=(
                    "data/animals/common.json",
                    "data/materials/abridged-body-fluids.json",
                    "data/books/academic_subjects.json",
                ),
                generated_at="2026-07-06T00:00:00+00:00",
            )

        self.assertEqual(report["status"], "ok")
        rows = {row["source_path"]: row for row in report["rows"]}
        self.assertEqual(
            rows["data/animals/common.json"]["recommendation"], "already_direct_runtime"
        )
        self.assertEqual(
            rows["data/materials/abridged-body-fluids.json"]["recommendation"],
            "promote_direct_runtime",
        )
        self.assertEqual(
            rows["data/materials/abridged-body-fluids.json"]["exclude_lemmas"],
            ["cera"],
        )
        self.assertEqual(
            rows["data/books/academic_subjects.json"]["recommendation"],
            "candidate_not_runtime",
        )
        self.assertEqual(report["summary"]["promotion_candidate_count"], 1)
        self.assertEqual(report["summary"]["candidate_only_count"], 1)
        markdown = render_markdown(report)
        self.assertIn("Source Matrix", markdown)
        self.assertIn("abridged-body-fluids", markdown)


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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
