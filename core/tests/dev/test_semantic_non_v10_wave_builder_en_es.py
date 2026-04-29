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

from semantic_non_v10_wave_builder_en_es import (  # noqa: E402
    build_non_v10_wave_draft_report,
    render_non_v10_wave_draft_markdown,
)


class SemanticNonV10WaveBuilderTests(unittest.TestCase):
    def test_wave_builder_constructs_draft_active_shadow_families(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            forward = tmp / "wiktionary-en-es.sqlite"
            reverse = tmp / "wiktionary-es-en.sqlite"
            freedict = tmp / "freedict-es-en.sqlite"
            _create_forward_db(forward)
            _create_reverse_db(reverse, table_name="entries")
            _create_reverse_db(freedict, table_name="entries")

            report = build_non_v10_wave_draft_report(
                candidate_payload=_candidate_payload(),
                wiktionary_en_es_sqlite=forward,
                wiktionary_es_en_sqlite=reverse,
                freedict_es_en_sqlite=freedict,
                wave_id="source_non_v10_wave_test",
                wave_size=1,
                max_sense_count=20,
                generated_at="2026-04-28T00:00:00Z",
            )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "draft_wave_ready_for_source_linkage")
        self.assertEqual(report["summary"]["selected_family_count"], 1)
        family = report["selected_families"][0]
        self.assertEqual(family["trigger"], "leave")
        self.assertEqual(family["active"]["target_lemma"], "permiso")
        self.assertEqual(family["active"]["canonical_pos"], "noun")
        shadow_targets = [shadow["target_lemma"] for shadow in family["shadows"]]
        self.assertIn("dejar", shadow_targets)
        self.assertTrue(family["has_reverse_support"])
        self.assertTrue(family["has_freedict_support"])
        cases = report["draft_dataset"]["families"][0]["cases"]
        self.assertEqual(cases[0]["gold_winner"], family["active"]["sense_id"])
        self.assertIn("loader_only", cases[0]["slice_tags"])
        self.assertEqual(
            report["draft_queue"]["families"][0]["review_state"], "draft_needs_target_review"
        )

        markdown = render_non_v10_wave_draft_markdown(report)
        self.assertIn("Non-v10 Source Wave Draft", markdown)
        self.assertIn("permiso", markdown)

    def test_wave_builder_skips_missing_required_translation_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            forward = Path(tmp_dir) / "wiktionary-en-es.sqlite"
            _create_forward_db(forward, include_verb=False)

            report = build_non_v10_wave_draft_report(
                candidate_payload=_candidate_payload(),
                wiktionary_en_es_sqlite=forward,
                wave_id="source_non_v10_wave_test",
                wave_size=1,
                max_sense_count=20,
                generated_at="2026-04-28T00:00:00Z",
            )

        self.assertEqual(report["decision"], "draft_wave_blocked")
        self.assertEqual(report["summary"]["selected_family_count"], 0)
        self.assertEqual(
            report["skipped_candidates"][0]["reason"], "missing_noun_or_verb_translation"
        )

    def test_wave_builder_can_use_any_cross_pos_strategy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            forward = Path(tmp_dir) / "wiktionary-en-es.sqlite"
            _create_forward_db(forward, include_verb=False, include_adjective=True)

            report = build_non_v10_wave_draft_report(
                candidate_payload=_candidate_payload(),
                wiktionary_en_es_sqlite=forward,
                wave_id="source_non_v10_wave_test",
                wave_size=1,
                max_sense_count=20,
                require_translation_support=False,
                family_pos_strategy="any_cross_pos",
                generated_at="2026-04-28T00:00:00Z",
            )

        self.assertEqual(report["decision"], "draft_wave_ready_for_source_linkage")
        family = report["selected_families"][0]
        self.assertEqual(family["active"]["target_lemma"], "libre")
        self.assertEqual(family["active"]["canonical_pos"], "adjective")
        self.assertEqual(family["shadows"][0]["target_lemma"], "permiso")

    def test_wave_builder_skips_same_visible_active_and_shadow_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            forward = Path(tmp_dir) / "wiktionary-en-es.sqlite"
            _create_forward_db(forward, same_target_shadow=True, include_alternate_noun=False)

            report = build_non_v10_wave_draft_report(
                candidate_payload=_candidate_payload(),
                wiktionary_en_es_sqlite=forward,
                wave_id="source_non_v10_wave_test",
                wave_size=1,
                max_sense_count=20,
                require_translation_support=False,
                generated_at="2026-04-28T00:00:00Z",
            )

        self.assertEqual(report["decision"], "draft_wave_blocked")
        self.assertEqual(report["summary"]["selected_family_count"], 0)
        self.assertEqual(
            report["skipped_candidates"][0]["reason"],
            "missing_distinct_noun_or_verb_translation",
        )

    def test_wave_builder_records_same_visible_active_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            forward = Path(tmp_dir) / "wiktionary-en-es.sqlite"
            _create_forward_db(forward, include_adjective=True, same_visible_adjective=True)

            report = build_non_v10_wave_draft_report(
                candidate_payload=_candidate_payload(),
                wiktionary_en_es_sqlite=forward,
                wave_id="source_non_v10_wave_test",
                wave_size=1,
                max_sense_count=20,
                require_translation_support=False,
                generated_at="2026-04-28T00:00:00Z",
            )

        family = report["selected_families"][0]
        self.assertEqual(family["active"]["target_lemma"], "permiso")
        self.assertEqual(family["active_visible_target_alias_count"], 1)
        aliases = family["active"]["metadata"]["visible_target_aliases"]
        self.assertEqual(aliases[0]["canonical_pos"], "adjective")
        self.assertIn(
            "same-visible-target",
            family["active"]["evidence_views"]["all_evidence_text"],
        )


def _candidate_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "inventory_id": "semantic_non_v10_inventory_candidates_en_es",
        "candidates": [
            {
                "candidate_id": "en-es:wordnet-non-v10-candidate:leave",
                "trigger": "leave",
                "score": 16.1,
                "complexity_band": "broad",
                "sense_count": 17,
            }
        ],
    }


def _create_forward_db(
    path: Path,
    *,
    include_verb: bool = True,
    include_adjective: bool = False,
    same_target_shadow: bool = False,
    same_visible_adjective: bool = False,
    include_alternate_noun: bool = True,
) -> None:
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
    rows = [
        (1, 1, 1, "leave", "leave", "permiso", "permiso", "noun", '["permission to be absent"]')
    ]
    if include_alternate_noun:
        rows.append(
            (
                2,
                1,
                1,
                "leave",
                "leave",
                "licencia",
                "licencia",
                "noun",
                '["permission to be absent"]',
            )
        )
    if include_verb:
        verb_target = "permiso" if same_target_shadow else "dejar"
        rows.append(
            (
                3,
                1,
                1,
                "leave",
                "leave",
                verb_target,
                verb_target,
                "verb",
                '["to cause to remain"]',
            )
        )
    if include_adjective:
        adjective_target = "permiso" if same_visible_adjective else "libre"
        rows.append(
            (
                4,
                1,
                1,
                "leave",
                "leave",
                adjective_target,
                adjective_target,
                "adjective",
                '["not constrained"]',
            )
        )
    conn.executemany(
        """
        INSERT INTO sense_glosses
        (entry_ord, sense_ord, gloss_ord, headword, headword_lc, translation,
         translation_lc, pos, raw_glosses_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.executemany(
        """
        INSERT INTO translation_meta
        (entry_ord, sense_ord, gloss_ord, sense_text)
        VALUES (?, ?, ?, ?)
        """,
        [
            (1, 1, 1, "permission to be absent"),
            (2, 1, 1, "permission to be absent"),
            (3, 1, 1, "to cause to remain"),
            (4, 1, 1, "not constrained"),
        ],
    )
    verb_target = "permiso" if same_target_shadow else "dejar"
    entry_rows = [("leave", "leave", "permiso", "permiso", 1, "noun", 1, 1)]
    if include_alternate_noun:
        entry_rows.append(("leave", "leave", "licencia", "licencia", 2, "noun", 2, 1))
    if not same_target_shadow:
        entry_rows.append(("leave", "leave", verb_target, verb_target, 3, "verb", 3, 1))
    if include_adjective:
        adjective_target = "permiso" if same_visible_adjective else "libre"
        if not same_visible_adjective:
            entry_rows.append(
                ("leave", "leave", adjective_target, adjective_target, 4, "adjective", 4, 1)
            )
    conn.executemany(
        """
        INSERT INTO entries
        (headword, headword_lc, translation, translation_lc, rank, pos, entry_ord, gloss_ord)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        entry_rows,
    )
    conn.commit()
    conn.close()


def _create_reverse_db(path: Path, *, table_name: str) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        f"""
        CREATE TABLE {table_name} (
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
        f"""
        INSERT INTO {table_name}
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
