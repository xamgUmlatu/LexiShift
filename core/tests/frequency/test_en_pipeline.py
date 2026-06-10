from __future__ import annotations

import io
import os
import sqlite3
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.frequency.en.pipeline import run_en_frequency_pipeline  # noqa: E402


class TestEnglishFrequencyPipeline(unittest.TestCase):
    def test_builds_english_leipzig_frequency_pack_from_local_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "eng_news_2025_1M.tar.gz"
            _write_leipzig_words_archive(
                archive,
                "eng_news_2025_1M/eng_news_2025_1M-words.txt",
                "1\ttimes\t10\n2\tschool\t8\n3\twindow\t4\n",
            )
            output = root / "frequency_packs" / "freq-en-leipzig-default" / "main.sqlite"
            captured: dict[str, Path] = {}

            result = run_en_frequency_pipeline(
                output_sqlite=output,
                language_packs_dir=root / "language_packs",
                corpus_url=archive.as_uri(),
                min_lemma_count=1,
                source_bundle_component_paths_cb=lambda paths: captured.update(paths),
            )

            self.assertEqual(result.output_path.resolve(), output.resolve())
            self.assertIn("eng_news_2025_1M.tar.gz", captured)
            with sqlite3.connect(output) as conn:
                rows = conn.execute(
                    "select lemma, core_rank from frequency order by core_rank"
                ).fetchall()
            self.assertEqual(rows[:3], [("time", 1.0), ("school", 2.0), ("window", 3.0)])


def _write_leipzig_words_archive(archive_path: Path, member_name: str, payload: str) -> None:
    data = payload.encode("utf-8")
    with tarfile.open(archive_path, "w:gz") as archive:
        info = tarfile.TarInfo(member_name)
        info.size = len(data)
        archive.addfile(info, io.BytesIO(data))


if __name__ == "__main__":
    unittest.main()
