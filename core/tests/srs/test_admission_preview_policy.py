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

from lexishift_core.helper.rulegen import SetInitializationConfig  # noqa: E402
from lexishift_core.helper.use_cases.admission_candidate_index import (  # noqa: E402
    try_preview_from_admission_candidate_index,
)
from lexishift_core.helper.use_cases.admission_preview import (  # noqa: E402
    ADMISSION_PREVIEW_ADVANCED_BOOTSTRAP_TOP_N,
    _resolve_admission_preview_bootstrap_top_n,
)
from lexishift_core.srs import SrsStore  # noqa: E402


class TestAdmissionPreviewBootstrapPolicy(unittest.TestCase):
    def test_nested_profile_proficiency_uses_advanced_preview_frontier(self) -> None:
        top_n, cap_applied = _resolve_admission_preview_bootstrap_top_n(
            bootstrap_top_n=None,
            profile_context={"proficiency": {"estimated_value": 0.75}},
        )

        self.assertEqual(top_n, ADMISSION_PREVIEW_ADVANCED_BOOTSTRAP_TOP_N)
        self.assertTrue(cap_applied)

    def test_admission_candidate_index_reuses_base_frontier_across_topic_overlays(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frequency_db = root / "freq.sqlite"
            _write_synthetic_frequency_db(frequency_db)
            config = SetInitializationConfig(
                frequency_db=frequency_db,
                top_n=10,
                initial_active_count=2,
                language_pair="en-es",
                require_jmdict=False,
                strategy="profile_bootstrap",
                profile_context={"proficiency": {"estimated_value": 0.5}},
            )

            first = try_preview_from_admission_candidate_index(
                SrsStore(items=(), version=2),
                config=config,
                profile_topic_overlay=None,
                index_cache_dir=root / "cache",
            )
            self.assertIsNotNone(first)
            assert first is not None
            first_report = first[1]
            first_index = first_report.profile_bootstrap_diagnostics["compiled_candidate_index"]
            self.assertEqual(first_index["build_status"], "built")

            topic_config = SetInitializationConfig(
                **{
                    **config.__dict__,
                    "profile_context": {
                        "proficiency": {"estimated_value": 0.5},
                        "interests": ["animals"],
                    },
                }
            )
            second = try_preview_from_admission_candidate_index(
                SrsStore(items=(), version=2),
                config=topic_config,
                profile_topic_overlay={
                    "overlay_id": "test-overlay",
                    "schema_version": 1,
                    "status": "ok",
                    "rows": [
                        {
                            "language_pair": "en-es",
                            "lemma": "word9",
                            "topic": "animals",
                            "membership": 1.0,
                        }
                    ],
                },
                index_cache_dir=root / "cache",
            )
            self.assertIsNotNone(second)
            assert second is not None
            second_report = second[1]
            second_index = second_report.profile_bootstrap_diagnostics["compiled_candidate_index"]
            self.assertEqual(second_index["build_status"], "ready")
            self.assertEqual(first_index["fingerprint"], second_index["fingerprint"])
            self.assertIn("animals", second_index["query"]["active_topics"])


def _write_synthetic_frequency_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE frequency (lemma TEXT, core_rank REAL, pmw REAL, pos TEXT)")
        conn.executemany(
            "INSERT INTO frequency (lemma, core_rank, pmw, pos) VALUES (?, ?, ?, ?)",
            [(f"word{index}", index, 1000.0 - index * 10.0, "NOUN") for index in range(1, 11)],
        )


if __name__ == "__main__":
    unittest.main()
