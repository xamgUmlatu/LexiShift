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

from semantic_veto_llm_data_priority_target_family_construction_en_es import (  # noqa: E402
    build_target_family_construction_report,
    render_target_family_construction_markdown,
)


class SemanticVetoLlmDataPriorityTargetFamilyConstructionTests(unittest.TestCase):
    def test_constructs_only_top_inventory_rows_and_separates_source_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            forward = tmp / "wiktionary-en-es.sqlite"
            reverse = tmp / "wiktionary-es-en.sqlite"
            freedict = tmp / "freedict-es-en.sqlite"
            _create_forward_db(forward)
            _create_reverse_db(reverse)
            _create_reverse_db(freedict)

            report = build_target_family_construction_report(
                bridge_payload=_bridge_payload(),
                inventory_payload=_inventory_payload(),
                wiktionary_en_es_sqlite=forward,
                wiktionary_es_en_sqlite=reverse,
                freedict_es_en_sqlite=freedict,
                wordnet_index=None,
                generated_at="2026-05-06T00:00:00Z",
                queue_id="test_target_family_queue",
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "target_family_construction_queue_established")
        summary = report["summary"]
        self.assertEqual(summary["attempted_inventory_only_count"], 3)
        self.assertEqual(summary["source_ready_family_count"], 1)
        self.assertEqual(summary["weak_diagnostic_family_count"], 1)
        self.assertEqual(summary["blocked_count"], 1)

        attempts = {row["trigger"]: row for row in report["construction_attempts"]}
        self.assertEqual(
            attempts["leave"]["readiness_stage"],
            "source_supported_family_draft_needs_review",
        )
        self.assertEqual(attempts["leave"]["active"]["target_lemma"], "permiso")
        self.assertEqual(
            attempts["home"]["readiness_stage"], "weak_family_draft_needs_source_support"
        )
        self.assertEqual(attempts["blue"]["readiness_stage"], "construction_blocked")
        self.assertNotIn("even", attempts)
        self.assertNotIn("out", attempts)

        self.assertEqual(len(report["draft_dataset"]["families"]), 1)
        self.assertEqual(len(report["construction_queue"]["rows"]), 3)
        self.assertTrue(report["e2e_checks"]["no_llm_packets_emitted"])
        self.assertTrue(report["e2e_checks"]["weak_rows_not_marked_source_ready"])

        markdown = render_target_family_construction_markdown(report)
        self.assertIn("Target-Family Construction", markdown)
        self.assertIn("source-ready family drafts: `1`", markdown.lower())


def _bridge_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "decision": "llm_data_priority_inventory_bridge_established",
        "priority_rows": [
            {
                "trigger": "even",
                "candidate_id": "candidate:even",
                "priority_rank": 1,
                "readiness_stage": "trigger_target_pair_scored",
                "in_top_n": True,
                "inventory_source_need": 0.9,
                "llm_packet_from_scored_pairs": {"phrase_rows": 4},
            },
            {
                "trigger": "leave",
                "candidate_id": "candidate:leave",
                "priority_rank": 2,
                "readiness_stage": "needs_translation_target_shadow_family",
                "in_top_n": True,
                "inventory_source_need": 0.8,
            },
            {
                "trigger": "home",
                "candidate_id": "candidate:home",
                "priority_rank": 3,
                "readiness_stage": "needs_translation_target_shadow_family",
                "in_top_n": True,
                "inventory_source_need": 0.7,
            },
            {
                "trigger": "blue",
                "candidate_id": "candidate:blue",
                "priority_rank": 4,
                "readiness_stage": "needs_translation_target_shadow_family",
                "in_top_n": True,
                "inventory_source_need": 0.6,
            },
            {
                "trigger": "out",
                "candidate_id": "candidate:out",
                "priority_rank": 5,
                "readiness_stage": "needs_translation_target_shadow_family",
                "in_top_n": False,
                "inventory_source_need": 0.5,
            },
        ],
    }


def _inventory_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "inventory_id": "semantic_non_v10_inventory_candidates_en_es",
        "pair": "en-es",
        "candidates": [
            _candidate("leave", sense_count=4),
            _candidate("home", sense_count=4),
            _candidate("blue", sense_count=4),
            _candidate("out", sense_count=4),
        ],
    }


def _candidate(trigger: str, *, sense_count: int) -> dict[str, object]:
    return {
        "candidate_id": f"candidate:{trigger}",
        "trigger": trigger,
        "score": 10.0,
        "complexity_band": "test",
        "sense_count": sense_count,
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
