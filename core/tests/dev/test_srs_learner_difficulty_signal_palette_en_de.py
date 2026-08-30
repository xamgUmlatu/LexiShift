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

from srs_learner_difficulty_signal_palette_en_de import build_report, render_markdown  # noqa: E402


class SrsLearnerDifficultySignalPaletteEnDeTests(unittest.TestCase):
    def test_build_report_combines_frequency_translation_reverse_and_topics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frequency_db = root / "freq-de.sqlite"
            translation_db = root / "freedict-de-en.sqlite"
            reverse_translation_db = root / "freedict-en-de.sqlite"
            english_frequency_db = root / "freq-en.sqlite"
            topic_overlay = root / "topic-overlay.json"
            learner_source = root / "learner-source.json"
            wiktionary_metadata = root / "wiktionary-metadata.json"
            external_source = root / "external-source.json"
            _write_frequency_db(
                frequency_db,
                rows=(
                    ("haus", 1.0, 1000.0, "SUB:NOM:SIN:NEU"),
                    ("computer", 2.0, 800.0, "SUB:NOM:SIN:MAS"),
                    ("spielen", 3.0, 700.0, "VER:INF:NON"),
                ),
            )
            _write_translation_db(
                translation_db,
                rows=(
                    ("haus", "house", 1, "n"),
                    ("computer", "computer", 1, "n"),
                    ("spielen", "play", 1, "v"),
                ),
            )
            _write_translation_db(
                reverse_translation_db,
                rows=(
                    ("house", "haus", 1, "n"),
                    ("computer", "computer", 1, "n"),
                    ("play", "spielen", 1, "v"),
                ),
            )
            _write_frequency_db(
                english_frequency_db,
                rows=(
                    ("house", 10.0, 500.0, ""),
                    ("computer", 20.0, 300.0, ""),
                    ("play", 30.0, 250.0, ""),
                ),
            )
            _write_json(
                topic_overlay,
                {
                    "status": "ok",
                    "overlay_id": "unit",
                    "summary": {},
                    "rows": [
                        {
                            "language_pair": "en-de",
                            "lemma": "computer",
                            "topic": "computing_internet",
                            "membership": 1.0,
                        },
                        {
                            "language_pair": "en-de",
                            "lemma": "spielen",
                            "topic": "games",
                            "membership": 1.0,
                        },
                    ],
                },
            )
            _write_json(
                learner_source,
                {
                    "status": "ok",
                    "decision": "en_de_learner_sources_ready",
                    "source_summary": {
                        "sources": [
                            {
                                "source_id": "openlingo_mit_german_dictionary",
                                "decision": "included_sidecar",
                            },
                            {
                                "source_id": "odenet_basiswortschatz",
                                "decision": "included_sidecar",
                            },
                        ]
                    },
                    "source_overlay": {
                        "haus": {
                            "term": "haus",
                            "source_ids": ["openlingo_mit_german_dictionary"],
                            "source_count": 1,
                            "evidence_count": 1,
                            "learner_core_score": 0.08,
                            "confidence": 0.82,
                            "levels": ["A1"],
                            "min_level": "A1",
                            "hit_evidence": [
                                {
                                    "source_id": "openlingo_mit_german_dictionary",
                                    "score": 0.08,
                                    "confidence": 0.82,
                                    "evidence": "cefr_like_dictionary_entry",
                                }
                            ],
                        },
                        "computer": {
                            "term": "computer",
                            "source_ids": ["odenet_basiswortschatz"],
                            "source_count": 1,
                            "evidence_count": 1,
                            "learner_core_score": 0.18,
                            "confidence": 0.55,
                            "levels": [],
                            "min_level": None,
                            "hit_evidence": [
                                {
                                    "source_id": "odenet_basiswortschatz",
                                    "score": 0.18,
                                    "confidence": 0.55,
                                    "evidence": "basiswortschatz_entry:n",
                                }
                            ],
                        },
                    },
                },
            )
            _write_json(
                wiktionary_metadata,
                {
                    "status": "ok",
                    "decision": "en_de_wiktionary_metadata_ready",
                    "summary": {
                        "metadata_coverage_count": 2,
                        "marked_usage_count": 1,
                        "rare_dated_count": 1,
                        "form_or_alt_of_count": 1,
                        "multi_sense_count": 1,
                    },
                    "wiktionary_metadata_by_lemma": {
                        "haus": {
                            "lemma": "haus",
                            "entry_count": 1,
                            "sense_count": 2,
                            "gloss_count": 2,
                            "pos_values": ["noun"],
                            "pos_count": 1,
                            "topic_count": 0,
                            "region_tag_count": 0,
                            "form_of_count": 0,
                            "alt_of_count": 0,
                            "marked_usage_flag": False,
                            "rare_dated_flag": False,
                            "colloquial_flag": False,
                            "sensitive_flag": False,
                        },
                        "spielen": {
                            "lemma": "spielen",
                            "entry_count": 2,
                            "sense_count": 4,
                            "gloss_count": 4,
                            "pos_values": ["noun", "verb"],
                            "pos_count": 2,
                            "topic_count": 1,
                            "region_tag_count": 0,
                            "form_of_count": 1,
                            "alt_of_count": 0,
                            "marked_usage_flag": True,
                            "marked_terms": ["rare"],
                            "rare_dated_flag": True,
                            "colloquial_flag": False,
                            "sensitive_flag": False,
                        },
                    },
                },
            )
            _write_json(
                external_source,
                {
                    "status": "ok",
                    "decision": "en_de_external_difficulty_sources_ready",
                    "source_summary": {
                        "overlay_term_count": 2,
                        "source_hit_count": 3,
                        "sources": [
                            {
                                "source_id": "wordfreq_de_multi_source",
                                "decision": "included_sidecar",
                            },
                            {
                                "source_id": "klexikon_child_encyclopedia_titles",
                                "decision": "included_sidecar",
                            },
                        ],
                    },
                    "external_source_by_lemma": {
                        "haus": {
                            "term": "haus",
                            "source_ids": [
                                "wordfreq_de_multi_source",
                                "klexikon_child_encyclopedia_titles",
                            ],
                            "source_count": 2,
                            "evidence_count": 2,
                            "confidence": 0.94,
                            "modern_source_known": True,
                            "modern_frequency_score": 0.72,
                            "child_source_known": True,
                            "archive_source_known": False,
                            "archive_attestation_score": 0.0,
                            "wordfreq_known": True,
                            "wordfreq_zipf": 5.41,
                            "wordfreq_commonness_score": 0.72,
                            "opensubtitles_known": False,
                            "opensubtitles_frequency_score": 0.0,
                            "klexikon_title_known": True,
                        },
                        "computer": {
                            "term": "computer",
                            "source_ids": ["olastor_opensubtitles_cistem"],
                            "source_count": 1,
                            "evidence_count": 1,
                            "confidence": 0.5,
                            "modern_source_known": True,
                            "modern_frequency_score": 0.44,
                            "child_source_known": False,
                            "archive_source_known": False,
                            "archive_attestation_score": 0.0,
                            "wordfreq_known": False,
                            "wordfreq_commonness_score": 0.0,
                            "opensubtitles_known": True,
                            "opensubtitles_frequency_score": 0.44,
                            "opensubtitles_rank": 22,
                            "klexikon_title_known": False,
                        },
                    },
                },
            )

            report = build_report(
                frequency_db=frequency_db,
                translation_db=translation_db,
                reverse_translation_db=reverse_translation_db,
                english_frequency_db=english_frequency_db,
                topic_overlay_json=topic_overlay,
                learner_source_json=learner_source,
                wiktionary_metadata_json=wiktionary_metadata,
                external_source_json=external_source,
                top_n=10,
                include_rows=True,
                generated_at="2026-07-06T00:00:00+00:00",
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["row_count"], 3)
        self.assertEqual(report["summary"]["rows_with_translations"], 3)
        self.assertEqual(report["summary"]["rows_with_reverse_support"], 3)
        self.assertEqual(report["summary"]["rows_with_topic_overlay"], 2)
        self.assertEqual(report["summary"]["rows_with_learner_source"], 2)
        self.assertEqual(report["summary"]["rows_with_wiktionary_metadata"], 2)
        self.assertEqual(report["summary"]["rows_with_wiktionary_marked_usage"], 1)
        self.assertEqual(report["summary"]["rows_with_wiktionary_form_variant"], 1)
        self.assertEqual(report["summary"]["rows_with_external_source"], 2)
        self.assertEqual(report["summary"]["rows_with_external_modern_source"], 2)
        self.assertEqual(report["summary"]["rows_with_external_child_source"], 1)
        self.assertEqual(
            report["summary"]["topic_counts"],
            {"computing_internet": 1, "games": 1},
        )
        self.assertEqual(
            report["summary"]["learner_source_counts"],
            {"odenet_basiswortschatz": 1, "openlingo_mit_german_dictionary": 1},
        )
        rows = {row["lemma"]: row for row in report["signal_rows"]}
        self.assertEqual(rows["computer"]["topics"], ["computing_internet"])
        self.assertGreater(rows["computer"]["english_translation_similarity_ease"], 0.9)
        self.assertEqual(rows["computer"]["learner_source_known"], 1.0)
        self.assertEqual(rows["computer"]["odenet_basis_learner_source_known"], 1.0)
        self.assertEqual(rows["computer"]["odenet_basis_learner_core_score"], 0.18)
        self.assertFalse(rows["computer"]["learner_source_context"]["broad_source_known"])
        self.assertEqual(rows["computer"]["external_source_known"], 1.0)
        self.assertEqual(rows["computer"]["opensubtitles_cistem_known"], 1.0)
        self.assertEqual(rows["computer"]["opensubtitles_cistem_rank"], 22)
        self.assertEqual(rows["spielen"]["pos_bucket"], "verb")
        self.assertEqual(rows["spielen"]["wiktionary_metadata_known"], 1.0)
        self.assertEqual(rows["spielen"]["wiktionary_marked_usage_flag"], 1.0)
        self.assertEqual(rows["spielen"]["wiktionary_rare_dated_flag"], 1.0)
        self.assertEqual(rows["spielen"]["wiktionary_form_variant_count"], 1)
        self.assertEqual(rows["haus"]["learner_core_score"], 0.08)
        self.assertEqual(rows["haus"]["wiktionary_sense_count"], 2)
        self.assertGreater(rows["haus"]["wiktionary_sense_count_score"], 0.0)
        self.assertEqual(rows["haus"]["learner_source_known"], 1.0)
        self.assertEqual(rows["haus"]["openlingo_learner_source_known"], 1.0)
        self.assertEqual(rows["haus"]["openlingo_learner_core_score"], 0.08)
        self.assertEqual(rows["haus"]["goethe_stem_learner_source_known"], 0.0)
        self.assertEqual(rows["haus"]["odenet_basis_learner_source_known"], 0.0)
        self.assertTrue(rows["haus"]["learner_source_context"]["broad_source_known"])
        self.assertEqual(rows["haus"]["external_child_source_known"], 1.0)
        self.assertEqual(rows["haus"]["wordfreq_de_known"], 1.0)
        self.assertAlmostEqual(rows["haus"]["wordfreq_de_zipf"], 5.41)
        self.assertEqual(rows["haus"]["klexikon_title_known"], 1.0)
        markdown = render_markdown(report)
        self.assertIn("en-de Learner Difficulty Signal Palette", markdown)
        self.assertIn("computing_internet", markdown)
        self.assertIn("Learner-source counts", markdown)
        self.assertIn("External-source counts", markdown)


def _write_frequency_db(
    path: Path,
    *,
    rows: tuple[tuple[str, float, float, str], ...],
) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE frequency (
                lemma TEXT NOT NULL,
                core_rank REAL,
                pmw REAL,
                pos TEXT
            )
            """
        )
        conn.executemany(
            "INSERT INTO frequency (lemma, core_rank, pmw, pos) VALUES (?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def _write_translation_db(
    path: Path,
    *,
    rows: tuple[tuple[str, str, int, str], ...],
) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE entries (
                headword TEXT NOT NULL,
                headword_lc TEXT NOT NULL,
                translation TEXT NOT NULL,
                translation_lc TEXT NOT NULL,
                rank INTEGER NOT NULL,
                pos TEXT,
                entry_ord INTEGER NOT NULL,
                gloss_ord INTEGER NOT NULL
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO entries (
                headword,
                headword_lc,
                translation,
                translation_lc,
                rank,
                pos,
                entry_ord,
                gloss_ord
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (headword, headword, translation, translation, rank, pos, rank, 0)
                for headword, translation, rank, pos in rows
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
