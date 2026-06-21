from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.helper.use_cases.seed_cache import (  # noqa: E402
    get_srs_seed_frontier_cache_status,
    pairs_for_seed_resource_pack_id,
    prepare_srs_seed_frontier_cache,
    prepare_srs_seed_frontier_caches_for_pack,
)


def _build_freq_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE frequency (lemma TEXT, core_rank REAL, pmw REAL)")
    conn.executemany(
        "INSERT INTO frequency (lemma, core_rank, pmw) VALUES (?, ?, ?)",
        [
            ("alpha", 1, 100.0),
            ("beta", 2, 90.0),
            ("gamma", 3, 80.0),
        ],
    )
    conn.commit()
    conn.close()


class TestSeedCacheUseCase(unittest.TestCase):
    def test_pairs_for_seed_resource_pack_id_uses_pair_capabilities(self) -> None:
        self.assertEqual(
            pairs_for_seed_resource_pack_id("freq-ja-bccwj"),
            ("en-ja", "ja-ja"),
        )
        self.assertEqual(pairs_for_seed_resource_pack_id("jmdict-ja-en"), ("en-ja",))
        self.assertEqual(pairs_for_seed_resource_pack_id("kanjivg-ja"), ("en-ja", "ja-ja"))
        self.assertEqual(
            pairs_for_seed_resource_pack_id("jlpt-tanos-vocab-ja"),
            ("en-ja", "ja-ja"),
        )
        self.assertEqual(
            pairs_for_seed_resource_pack_id("sbsjapanese1-ja"),
            ("en-ja", "ja-ja"),
        )
        self.assertIn("en-es", pairs_for_seed_resource_pack_id("pos-es-ud-ancora-v1"))

    def test_seed_cache_status_blocks_when_pair_companion_resource_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            _build_freq_db(paths.frequency_packs_dir / "freq-ja-bccwj.sqlite")

            payload = get_srs_seed_frontier_cache_status(paths, pair="en-ja")

            self.assertFalse(payload["ok"])
            self.assertEqual(payload["status"], "blocked")
            self.assertEqual(payload["reason"], "missing_jmdict")

    def test_prepare_seed_cache_for_pair_writes_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            _build_freq_db(paths.frequency_packs_dir / "freq-de-default.sqlite")

            payload = prepare_srs_seed_frontier_cache(paths, pair="en-de")

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["status"], "ready")
            self.assertEqual(payload["seed_count"], 3)
            self.assertTrue(Path(str(payload["cache_path"])).is_file())

    def test_prepare_seed_cache_for_pack_allows_partial_warmup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            _build_freq_db(paths.frequency_packs_dir / "freq-ja-bccwj.sqlite")

            payload = prepare_srs_seed_frontier_caches_for_pack(
                paths,
                pack_id="freq-ja-bccwj",
            )

            self.assertEqual(payload["pairs"], ["en-ja", "ja-ja"])
            self.assertEqual(payload["prepared_count"], 1)
            self.assertEqual(payload["blocked_count"], 1)
            by_pair = {result["pair"]: result for result in payload["results"]}
            self.assertEqual(by_pair["en-ja"]["reason"], "missing_jmdict")
            self.assertEqual(by_pair["ja-ja"]["status"], "ready")


if __name__ == "__main__":
    unittest.main()
