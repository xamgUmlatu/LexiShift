from __future__ import annotations

from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(CORE_ROOT), str(SCRIPTS_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_representative_target_family_construction_en_es import (  # noqa: E402
    build_representative_target_family_construction_report,
    render_representative_target_family_construction_markdown,
)


class SemanticVetoRepresentativeTargetFamilyConstructionTests(unittest.TestCase):
    def test_constructs_families_without_reselecting_sampled_triggers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            forward = tmp / "wiktionary-en-es.sqlite"
            reverse = tmp / "wiktionary-es-en.sqlite"
            freedict = tmp / "freedict-es-en.sqlite"
            _create_forward_db(forward)
            _create_reverse_db(reverse)
            _create_reverse_db(freedict)

            report = build_representative_target_family_construction_report(
                sample_payload=_sample_payload(),
                wiktionary_en_es_sqlite=forward,
                wiktionary_es_en_sqlite=reverse,
                freedict_es_en_sqlite=freedict,
                wordnet_index=None,
                generated_at="2026-05-06T00:00:00Z",
                queue_id="test_representative_target_family",
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["decision"],
            "representative_target_family_construction_queue_established",
        )
        summary = report["summary"]
        self.assertEqual(summary["attempted_sample_count"], 3)
        self.assertEqual(summary["source_ready_family_count"], 1)
        self.assertEqual(summary["weak_diagnostic_family_count"], 1)
        self.assertEqual(summary["blocked_count"], 1)
        self.assertEqual(summary["reason_counts"]["constructed_family"], 2)
        self.assertEqual(summary["reason_counts"]["missing_noun_or_verb_translation"], 1)

        attempts = {row["trigger"]: row for row in report["construction_attempts"]}
        self.assertEqual(
            attempts["leave"]["readiness_stage"],
            "source_supported_family_draft_needs_review",
        )
        self.assertEqual(attempts["leave"]["cell_id"], "rank=1-500::poly=high::pos=cross")
        self.assertEqual(
            attempts["home"]["readiness_stage"], "weak_family_draft_needs_source_support"
        )
        self.assertEqual(attempts["blue"]["readiness_stage"], "construction_blocked")
        self.assertEqual(len(report["draft_dataset"]["families"]), 1)
        self.assertEqual(len(report["construction_queue"]["rows"]), 3)
        self.assertTrue(report["e2e_checks"]["attempts_match_loaded_sample_rows"])
        self.assertTrue(report["e2e_checks"]["sample_rows_have_no_outcome_fields"])
        self.assertTrue(report["e2e_checks"]["no_llm_packets_emitted"])

        family = report["source_ready_families"][0]
        metadata = family["metadata"]["representative_heuristic_band_sample"]
        self.assertEqual(metadata["cell_id"], "rank=1-500::poly=high::pos=cross")

        markdown = render_representative_target_family_construction_markdown(report)
        self.assertIn("Representative Target-Family Construction", markdown)
        self.assertIn("Blocked rows remain part of the representative result", markdown)


def _sample_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "status": "ok",
        "decision": "representative_heuristic_band_sample_frozen",
        "sampled_rows": [
            _sample_row("leave", rank=100, senses=4, pos_count=2),
            _sample_row("home", rank=120, senses=4, pos_count=2),
            _sample_row("blue", rank=140, senses=4, pos_count=2),
        ],
    }


def _sample_row(trigger: str, *, rank: int, senses: int, pos_count: int) -> dict[str, object]:
    return {
        "trigger": trigger,
        "source_rank": rank,
        "source_frequency": 1000,
        "source_rank_band": "1-500",
        "wordnet_sense_count": senses,
        "polysemy_band": "high_10_plus",
        "wordnet_pos_count": pos_count,
        "pos_shape": "cross_pos_polysemy",
        "cell_id": "rank=1-500::poly=high::pos=cross",
        "sample_rank_in_cell": rank // 20,
        "cell_eligible_count": 3,
        "cell_sample_count": 3,
        "cell_sampling_weight": 1.0,
    }


def _create_forward_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE sense_glosses (
          entry_ord INTEGER NOT NULL,
          sense_ord INTEGER NOT NULL,
          gloss_ord INTEGER NOT NULL,
          headword TEXT NOT NULL,
          headword_lc TEXT NOT NULL,
          translation TEXT NOT NULL,
          translation_lc TEXT NOT NULL,
          pos TEXT,
          raw_glosses_json TEXT,
          tags_json TEXT,
          topics_json TEXT,
          categories_json TEXT,
          form_of_json TEXT,
          alt_of_json TEXT,
          PRIMARY KEY (entry_ord, sense_ord, gloss_ord)
        );
        CREATE TABLE translation_meta (
          entry_ord INTEGER NOT NULL,
          sense_ord INTEGER NOT NULL,
          gloss_ord INTEGER NOT NULL,
          sense_text TEXT,
          english_text TEXT,
          note_text TEXT,
          roman_text TEXT,
          tags_json TEXT,
          code TEXT,
          lang TEXT,
          lang_code TEXT,
          PRIMARY KEY (entry_ord, sense_ord, gloss_ord)
        );
        CREATE TABLE entries (
          headword TEXT NOT NULL,
          headword_lc TEXT NOT NULL,
          translation TEXT NOT NULL,
          translation_lc TEXT NOT NULL,
          rank INTEGER NOT NULL,
          pos TEXT,
          entry_ord INTEGER NOT NULL,
          gloss_ord INTEGER NOT NULL,
          PRIMARY KEY (headword_lc, translation_lc)
        );
        """
    )
    sense_rows = [
        (1, 1, 1, "leave", "leave", "permiso", "permiso", "noun", '["permission"]'),
        (2, 1, 1, "leave", "leave", "dejar", "dejar", "verb", '["to leave"]'),
        (3, 1, 1, "home", "home", "hogar", "hogar", "noun", '["dwelling"]'),
        (4, 1, 1, "home", "home", "en casa", "en casa", "adverb", '["at home"]'),
    ]
    conn.executemany(
        """
        INSERT INTO sense_glosses
        (entry_ord, sense_ord, gloss_ord, headword, headword_lc, translation,
         translation_lc, pos, raw_glosses_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        sense_rows,
    )
    conn.executemany(
        """
        INSERT INTO translation_meta
        (entry_ord, sense_ord, gloss_ord, sense_text)
        VALUES (?, ?, ?, ?)
        """,
        [
            (1, 1, 1, "permission"),
            (2, 1, 1, "to leave"),
            (3, 1, 1, "dwelling"),
            (4, 1, 1, "at home"),
        ],
    )
    conn.executemany(
        """
        INSERT INTO entries
        (headword, headword_lc, translation, translation_lc, rank, pos, entry_ord, gloss_ord)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("leave", "leave", "permiso", "permiso", 1, "noun", 1, 1),
            ("leave", "leave", "dejar", "dejar", 2, "verb", 2, 1),
            ("home", "home", "hogar", "hogar", 1, "noun", 3, 1),
            ("home", "home", "en casa", "en casa", 2, "adverb", 4, 1),
        ],
    )
    conn.commit()
    conn.close()


def _create_reverse_db(path: Path) -> None:
    conn = sqlite3.connect(path)
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
          gloss_ord INTEGER NOT NULL,
          PRIMARY KEY (headword_lc, translation_lc)
        )
        """
    )
    conn.executemany(
        """
        INSERT INTO entries
        (headword, headword_lc, translation, translation_lc, rank, pos, entry_ord, gloss_ord)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("permiso", "permiso", "leave", "leave", 1, "noun", 1, 1),
            ("dejar", "dejar", "leave", "leave", 1, "verb", 2, 1),
        ],
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    unittest.main()
