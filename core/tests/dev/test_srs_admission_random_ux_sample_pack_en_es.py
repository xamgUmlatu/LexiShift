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

from srs_admission_random_ux_sample_pack_en_es import build_report  # noqa: E402


def _create_frequency_db(path: Path) -> Path:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE frequency (
                lemma TEXT,
                core_rank REAL,
                pmw REAL,
                pos TEXT,
                profile_topics TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO frequency (
                lemma,
                core_rank,
                pmw,
                pos,
                profile_topics
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                ("alpha", 1.0, 100.0, "n", None),
                ("beta", 2.0, 98.0, "n", None),
                ("gamma", 3.0, 96.0, "n", None),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return path


def _lemma(index: int) -> str:
    letters = []
    value = index
    while True:
        letters.append(chr(ord("a") + (value % 26)))
        value //= 26
        if value == 0:
            break
    return "palabra" + "".join(reversed(letters))


def _create_large_frequency_db(path: Path, *, count: int) -> Path:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE frequency (
                lemma TEXT,
                core_rank REAL,
                pmw REAL,
                pos TEXT,
                profile_topics TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO frequency (
                lemma,
                core_rank,
                pmw,
                pos,
                profile_topics
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                (_lemma(index), float(index + 1), float(1000 - index), "n", None)
                for index in range(count)
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return path


def _create_overlay(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "ok",
                "overlay_id": "unit_en_es_overlay",
                "overlay_policy": {"promotion_state": "reviewed_overlay_candidate_not_default"},
                "rows": [
                    {
                        "lemma": "beta",
                        "language_pair": "en-es",
                        "topic": "animals",
                        "membership": 1.0,
                        "confidence_label": "strong",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _create_large_overlay(path: Path, *, count: int) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "ok",
                "overlay_id": "unit_en_es_large_overlay",
                "overlay_policy": {"promotion_state": "reviewed_overlay_candidate_not_default"},
                "rows": [
                    {
                        "lemma": _lemma(index),
                        "language_pair": "en-es",
                        "topic": "animals",
                        "membership": 1.0,
                        "confidence_label": "strong",
                    }
                    for index in range(count)
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _create_corrected_csv(path: Path) -> Path:
    path.write_text(
        "\n".join(
            (
                "rank,lemma,reading,score,band,candidate_state,correction_types,"
                "display_form,admission_override,topic_stretch_allowed,"
                "manual_correction_active",
                "1,alpha,,0.100000,0.10-0.15,normal_vocab,,,,True,",
                "2,beta,,0.440000,0.40-0.45,normal_vocab,,,,True,",
                "3,gamma,,0.500000,0.50-0.55,normal_vocab,,,,True,",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _create_large_corrected_csv(path: Path, *, count: int) -> Path:
    lines = [
        "rank,lemma,reading,score,band,candidate_state,correction_types,"
        "display_form,admission_override,topic_stretch_allowed,"
        "manual_correction_active"
    ]
    for index in range(count):
        score = 0.20 + min(0.60, index / 1000)
        lines.append(f"{index + 1},{_lemma(index)},,{score:.6f},0.20-0.80,normal_vocab,,,,True,")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _create_config(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "defaults": {
                    "set_top_n": 3,
                    "initial_active_count": 3,
                    "preview_count": 3,
                    "preview_sampling_mode": "reserved_topic_lane",
                },
                "scenarios": [
                    {
                        "name": "animals_p45",
                        "description": "Animals preference.",
                        "proficiency": 0.45,
                        "topic_weights": {"animals": 1.0},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


class TestSrsAdmissionRandomUxSamplePackEnEs(unittest.TestCase):
    def test_build_report_uses_corrected_en_es_ranking_and_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_report(
                config_json=_create_config(root / "config.json"),
                pair="en-es",
                frequency_db=_create_frequency_db(root / "freq.sqlite"),
                overlay_source_path=_create_overlay(root / "overlay.json"),
                corrected_ranking_csv=_create_corrected_csv(root / "corrected.csv"),
                taxonomy_json=None,
                scenario_filter=(),
                set_top_n=3,
                initial_active_count=3,
                preview_count=3,
                preview_sampling_mode="reserved_topic_lane",
                draw_count=1,
                random_seed=123,
                markdown_word_limit_per_draw=3,
            )

        self.assertEqual(report["summary"]["status"], "PASS")
        scenario = report["scenarios"][0]
        self.assertGreater(scenario["aggregate"]["topic_mover_total"], 0)
        words = scenario["draws"][0]["admitted_words"]
        beta = next(row for row in words if row["lemma"] == "beta")
        self.assertEqual(beta["topic_affinity_source"], "topic_hint:animals")
        self.assertAlmostEqual(beta["corrected_difficulty"], 0.44)
        self.assertAlmostEqual(beta["runtime_difficulty_estimate"], 0.44)

    def test_random_preview_keeps_profile_metadata_beyond_top_diagnostic_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            count = 220
            report = build_report(
                config_json=_create_config(root / "config.json"),
                pair="en-es",
                frequency_db=_create_large_frequency_db(root / "freq.sqlite", count=count),
                overlay_source_path=_create_large_overlay(root / "overlay.json", count=count),
                corrected_ranking_csv=_create_large_corrected_csv(
                    root / "corrected.csv",
                    count=count,
                ),
                taxonomy_json=None,
                scenario_filter=(),
                set_top_n=count,
                initial_active_count=count,
                preview_count=count,
                preview_sampling_mode="reserved_topic_lane",
                draw_count=1,
                random_seed=123,
                markdown_word_limit_per_draw=3,
            )

        words = report["scenarios"][0]["draws"][0]["admitted_words"]
        tail = next(row for row in words if row["lemma"] == _lemma(215))
        self.assertEqual(tail["topic_affinity_source"], "topic_hint:animals")
        self.assertIsNotNone(tail["runtime_difficulty_estimate"])
        self.assertIsNotNone(tail["reranked_rank"])


if __name__ == "__main__":
    unittest.main()
