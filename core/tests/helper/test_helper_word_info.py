from __future__ import annotations

from datetime import datetime, timezone
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Iterable
from unittest.mock import patch

CORE_ROOT = Path(__file__).resolve().parents[2]
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.use_cases import word_info as word_info_module  # noqa: E402
from lexishift_core.helper.use_cases.word_info_senses import (  # noqa: E402
    _jmdict_structured_notes,
)
from lexishift_core.helper.engine import lookup_word_info  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.persistence.storage import VocabDataset, save_vocab_dataset  # noqa: E402
from lexishift_core.replacement.core import VocabRule  # noqa: E402
from lexishift_core.srs import SrsItem, SrsStore, save_srs_store  # noqa: E402
from lexishift_core.srs.time import format_ts  # noqa: E402


NOW = datetime(2026, 6, 2, 12, 0, tzinfo=timezone.utc)


def _write_translation_pack(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE entries (
                headword TEXT,
                headword_lc TEXT,
                translation TEXT,
                pos TEXT,
                rank INTEGER
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO entries (headword, headword_lc, translation, pos, rank)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                ("perro", "perro", "dog", "noun", 1),
                ("perro", "perro", "hound", "noun", 2),
                ("gato", "gato", "cat", "noun", 1),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _write_auxiliary_translation_pack(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute(
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
                examples_json TEXT,
                tags_json TEXT,
                topics_json TEXT,
                categories_json TEXT,
                form_of_json TEXT,
                alt_of_json TEXT,
                PRIMARY KEY (entry_ord, sense_ord, gloss_ord)
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO sense_glosses (
                entry_ord, sense_ord, gloss_ord, headword, headword_lc,
                translation, translation_lc, pos, raw_glosses_json,
                examples_json, tags_json, topics_json, categories_json,
                form_of_json, alt_of_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (
                    1,
                    1,
                    1,
                    "perro",
                    "perro",
                    "dog",
                    "dog",
                    "noun",
                    json.dumps(["dog (the species Canis familiaris)"]),
                    json.dumps(
                        [
                            {
                                "text": "perro callejero",
                                "translation": "stray dog",
                                "type": "example",
                            }
                        ]
                    ),
                    json.dumps(["masculine"]),
                    "",
                    "",
                    "",
                    "",
                ),
                (
                    1,
                    2,
                    1,
                    "perro",
                    "perro",
                    "restricted insult",
                    "restricted insult",
                    "noun",
                    json.dumps(["(slang) restricted insult"]),
                    "",
                    json.dumps(["slang"]),
                    "",
                    "",
                    "",
                    "",
                ),
                (
                    1,
                    3,
                    1,
                    "perro",
                    "perro",
                    "hound (dog used for hunting (animal))",
                    "hound",
                    "noun",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ),
                (
                    2,
                    0,
                    0,
                    "perro",
                    "perro",
                    "doggy",
                    "doggy",
                    "adj",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _word_package(surface: str, *, provider: str = "freq-es-cde") -> dict[str, object]:
    return {
        "version": 1,
        "language_tag": "es",
        "surface": surface,
        "reading": surface,
        "script_forms": {"surface": surface},
        "source": {"provider": provider},
        "pos": "noun",
        "pos_canonical": "noun",
    }


def _japanese_word_package(surface: str, reading: str) -> dict[str, object]:
    return {
        "version": 1,
        "language_tag": "ja",
        "surface": surface,
        "reading": reading,
        "script_forms": {"kanji": surface, "kana": reading},
        "source": {"provider": "jmdict"},
        "pos": "noun",
        "pos_canonical": "noun",
    }


def _write_jmdict_sense_sample(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """
<JMdict>
  <entry>
    <k_ele><keb>斎</keb></k_ele>
    <r_ele><reb>とき</reb></r_ele>
    <sense>
      <pos>noun</pos>
      <gloss>meals exchanged by parishioners and priests</gloss>
    </sense>
  </entry>
  <entry>
    <k_ele><keb>時</keb></k_ele>
    <k_ele><keb>刻</keb></k_ele>
    <k_ele><keb>秋</keb></k_ele>
    <r_ele><reb>とき</reb><re_restr>時</re_restr></r_ele>
    <r_ele><reb>じ</reb><re_restr>時</re_restr></r_ele>
    <sense>
      <stagr>とき</stagr>
      <pos>noun</pos>
      <s_inf>刻 signifies a time of day; 秋 signifies an important time</s_inf>
      <gloss>time</gloss>
      <gloss>hour</gloss>
      <gloss>moment</gloss>
    </sense>
    <sense>
      <stagk>時</stagk>
      <stagr>とき</stagr>
      <pos>noun</pos>
      <pos>adverb</pos>
      <gloss>occasion</gloss>
      <gloss>case</gloss>
    </sense>
    <sense>
      <stagr>じ</stagr>
      <pos>noun</pos>
      <gloss>clock hour</gloss>
      <gloss>o'clock</gloss>
    </sense>
  </entry>
  <entry>
    <r_ele><reb>ブラシ</reb><re_nokanji /></r_ele>
    <sense>
      <pos>noun</pos>
      <gloss>brush</gloss>
    </sense>
  </entry>
</JMdict>
""".strip(),
        encoding="utf-8",
    )


def _all_strings(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, dict):
        for key, inner_value in value.items():
            yield str(key)
            yield from _all_strings(inner_value)
        return
    if isinstance(value, (list, tuple)):
        for inner_value in value:
            yield from _all_strings(inner_value)


class TestHelperWordInfo(unittest.TestCase):
    def test_pos_payload_preserves_raw_label_and_prefers_stable_canonical(self) -> None:
        payload = word_info_module._pos_payload(
            (
                {
                    "pos": "動詞-一般",
                    "pos_raw": "動詞-一般",
                },
                {
                    "pos": "動詞-一般",
                    "pos_raw": "動詞-一般",
                    "pos_canonical": "verb",
                },
            ),
            (),
        )

        self.assertEqual(payload["canonical"], "verb")
        self.assertEqual(payload["label"], "動詞-一般")
        self.assertEqual(payload["raw"], "動詞-一般")
        self.assertEqual(payload["source"], "word_package")

    def test_jmdict_structures_only_exact_notes_for_known_written_forms(self) -> None:
        source_text = "刻 signifies a time of day; 秋 signifies an important time"
        self.assertEqual(
            _jmdict_structured_notes(
                (source_text,),
                entry_written_forms=("時", "刻", "秋"),
            ),
            [
                {
                    "kind": "orthography_variants",
                    "source_text": source_text,
                    "items": [
                        {"written_form": "刻", "text": "a time of day"},
                        {"written_form": "秋", "text": "an important time"},
                    ],
                }
            ],
        )
        for note, written_forms in (
            (source_text, ("時", "刻")),
            ("刻 signifies a time of day; also used poetically", ("時", "刻")),
            ("刻 signifies a time of day", ("時", "刻")),
        ):
            with self.subTest(note=note, written_forms=written_forms):
                self.assertEqual(
                    _jmdict_structured_notes(
                        (note,),
                        entry_written_forms=written_forms,
                    ),
                    [],
                )

    def test_lookup_word_info_merges_srs_rules_and_translation_glosses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            _write_translation_pack(paths.language_packs_dir / "wiktionary-es-en.sqlite")
            word_package = _word_package("perro")
            word_package["source"]["artifact_path"] = str(
                paths.language_packs_dir / "wiktionary-es-en.sqlite"
            )
            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-es:perro",
                            lemma="perro",
                            language_pair="en-es",
                            source_type="initial_set",
                            admitted_at=format_ts(NOW),
                            next_due=None,
                            exposures=2,
                            word_package=word_package,
                        ),
                    ),
                    version=2,
                ),
                paths.srs_store_path_for("default"),
            )
            save_vocab_dataset(
                VocabDataset(
                    rules=(
                        VocabRule(source_phrase="dog", replacement="perro"),
                        VocabRule(source_phrase="hound", replacement="perro"),
                    ),
                ),
                paths.ruleset_path("en-es", profile_id="default"),
            )

            result = lookup_word_info(
                paths,
                pair="en-es",
                profile_id="default",
                lemma="perro",
                display="Perro",
                origin="srs",
                source_phrase="dog",
            )

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["source_language"], "en")
            self.assertEqual(result["target_language"], "es")
            self.assertEqual(result["display"], "Perro")
            self.assertEqual(result["pos"]["canonical"], "noun")
            self.assertEqual(
                [gloss["text"] for gloss in result["glosses"]],
                ["dog", "hound"],
            )
            self.assertEqual(result["glosses"][0]["source_kind"], "installed_translation_pack")
            self.assertEqual(result["dictionary"]["pack_id"], "wiktionary_es_en")
            self.assertEqual(result["dictionary"]["provider"], "wiktionary")
            self.assertEqual(result["dictionary_match"]["surface"], "perro")
            self.assertEqual(result["dictionary_match"]["quality"], "exact_surface")
            self.assertEqual(result["source_phrases"], ["dog", "hound"])
            self.assertEqual(result["rule_summary"]["rule_count"], 2)
            self.assertTrue(result["srs"]["present"])
            self.assertEqual(result["srs"]["exposures"], 2)
            self.assertIn("srs_store", result["diagnostics"]["resolution_sources"])
            self.assertIn("published_ruleset", result["diagnostics"]["resolution_sources"])
            self.assertIn("installed_lexical_pack", result["diagnostics"]["resolution_sources"])
            self.assertEqual(result["diagnostics"]["missing_resources"], [])
            self.assertEqual(result["external_links"][0]["label"], "Wiktionary")
            self.assertNotIn("artifact_path", result["word_package"]["source"])

            leaked = [text for text in _all_strings(result) if str(Path(tmp)) in text]
            self.assertEqual(leaked, [])

    def test_lookup_word_info_returns_auxiliary_sense_details_and_examples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            _write_auxiliary_translation_pack(
                paths.language_packs_dir / "wiktionary-es-en" / "main.sqlite"
            )

            result = lookup_word_info(
                paths,
                pair="en-es",
                profile_id="default",
                lemma="perro",
                display="perro",
            )

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["diagnostics"]["missing_resources"], [])
            self.assertEqual(result["glosses"][0]["text"], "dog")
            self.assertEqual(
                result["glosses"][0]["details"],
                ["dog (the species Canis familiaris)"],
            )
            self.assertEqual(
                result["glosses"][0]["examples"],
                [{"text": "perro callejero", "translation": "stray dog"}],
            )
            self.assertEqual(result["glosses"][1]["text"], "hound")
            self.assertEqual(result["glosses"][1]["details"], ["dog used for hunting (animal)"])
            self.assertEqual(
                [[gloss["text"] for gloss in sense["glosses"]] for sense in result["senses"]],
                [["dog"], ["hound"]],
            )
            self.assertEqual(
                result["senses"][0]["examples"],
                [{"text": "perro callejero", "translation": "stray dog"}],
            )
            self.assertNotIn(
                "restricted insult",
                [gloss["text"] for gloss in result["glosses"]],
            )
            self.assertNotIn("doggy", [gloss["text"] for gloss in result["glosses"]])
            self.assertEqual(result["glosses"][0]["source"], "wiktionary_es_en")

            leaked = [text for text in _all_strings(result) if str(Path(tmp)) in text]
            self.assertEqual(leaked, [])

    def test_lookup_word_info_gracefully_reports_missing_local_gloss_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))

            result = lookup_word_info(
                paths,
                pair="en-es",
                profile_id="default",
                lemma="perro",
                display="perro",
            )

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["glosses"], [])
            self.assertEqual(result["srs"], {"present": False})
            self.assertEqual(
                result["diagnostics"]["provider_status"],
                "missing_translation_pack",
            )
            self.assertEqual(
                result["diagnostics"]["missing_resources"][0]["type"],
                "translation_pack",
            )

            leaked = [text for text in _all_strings(result) if str(Path(tmp)) in text]
            self.assertEqual(leaked, [])

    def test_jmdict_word_info_reuses_process_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            jmdict_path = paths.language_packs_dir / "jmdict-ja-en" / "JMdict_e"
            jmdict_path.parent.mkdir(parents=True, exist_ok=True)
            jmdict_path.write_text("<JMdict />", encoding="utf-8")
            word_info_module._load_jmdict_definition_data_cached.cache_clear()
            calls: list[tuple[Path, tuple[str, ...]]] = []

            def fake_loader(
                path: Path,
                lookup_candidates: tuple[str, ...],
                *,
                index_path: Path | None = None,
            ) -> tuple[dict[str, list[object]], dict[str, list[str]]]:
                self.assertIsNotNone(index_path)
                calls.append((path, lookup_candidates))
                return (
                    {},
                    {
                        "会社": ["company"],
                    },
                )

            with patch.object(
                word_info_module,
                "load_jmdict_definition_records_for_terms",
                fake_loader,
            ):
                first = lookup_word_info(
                    paths,
                    pair="en-ja",
                    profile_id="default",
                    lemma="会社",
                    display="会社",
                )
                second = lookup_word_info(
                    paths,
                    pair="en-ja",
                    profile_id="default",
                    lemma="会社",
                    display="会社",
                )

            self.assertEqual([gloss["text"] for gloss in first["glosses"]], ["company"])
            self.assertEqual([gloss["text"] for gloss in second["glosses"]], ["company"])
            self.assertEqual(calls, [(jmdict_path, ("会社",))])

    def test_jmdict_word_info_matches_exact_surface_and_reading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            jmdict_path = paths.language_packs_dir / "jmdict-ja-en" / "JMdict_e"
            _write_jmdict_sense_sample(jmdict_path)
            word_info_module._load_jmdict_definition_data_cached.cache_clear()

            result = lookup_word_info(
                paths,
                pair="en-ja",
                profile_id="default",
                lemma="時",
                display="時",
                word_package=_japanese_word_package("時", "とき"),
            )

        self.assertEqual(
            [gloss["text"] for gloss in result["glosses"]],
            ["time", "hour", "moment", "occasion", "case"],
        )
        self.assertEqual(
            [[gloss["text"] for gloss in sense["glosses"]] for sense in result["senses"]],
            [
                ["time", "hour", "moment"],
                ["occasion", "case"],
            ],
        )
        self.assertEqual(
            result["senses"][0]["details"],
            ["刻 signifies a time of day; 秋 signifies an important time"],
        )
        self.assertEqual(
            result["senses"][0]["structured_notes"],
            [
                {
                    "kind": "orthography_variants",
                    "source_text": "刻 signifies a time of day; 秋 signifies an important time",
                    "items": [
                        {"written_form": "刻", "text": "a time of day"},
                        {"written_form": "秋", "text": "an important time"},
                    ],
                }
            ],
        )
        self.assertEqual(
            result["senses"][1]["restrictions"],
            {"written_forms": ["時"], "readings": ["とき"]},
        )
        self.assertEqual(result["dictionary"]["pack_id"], "jmdict-ja-en")
        self.assertEqual(result["dictionary"]["provider"], "edrdg")
        self.assertEqual(
            result["dictionary_match"],
            {
                "surface": "時",
                "reading": "とき",
                "quality": "exact_surface_reading",
            },
        )

    def test_jmdict_word_info_keeps_same_surface_readings_separate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            jmdict_path = paths.language_packs_dir / "jmdict-ja-en" / "JMdict_e"
            _write_jmdict_sense_sample(jmdict_path)
            word_info_module._load_jmdict_definition_data_cached.cache_clear()

            result = lookup_word_info(
                paths,
                pair="en-ja",
                profile_id="default",
                lemma="時",
                display="時",
                word_package=_japanese_word_package("時", "じ"),
            )

        self.assertEqual(
            [gloss["text"] for gloss in result["glosses"]],
            ["clock hour", "o'clock"],
        )
        self.assertEqual(
            [[gloss["text"] for gloss in sense["glosses"]] for sense in result["senses"]],
            [["clock hour", "o'clock"]],
        )
        self.assertEqual(result["dictionary_match"]["reading"], "じ")

    def test_request_word_package_does_not_attach_different_reading_srs_item(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            jmdict_path = paths.language_packs_dir / "jmdict-ja-en" / "JMdict_e"
            _write_jmdict_sense_sample(jmdict_path)
            word_info_module._load_jmdict_definition_data_cached.cache_clear()
            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-ja:時:toki",
                            lemma="時",
                            language_pair="en-ja",
                            source_type="initial_set",
                            admitted_at=format_ts(NOW),
                            next_due=None,
                            exposures=4,
                            word_package=_japanese_word_package("時", "とき"),
                        ),
                    ),
                    version=2,
                ),
                paths.srs_store_path_for("default"),
            )

            result = lookup_word_info(
                paths,
                pair="en-ja",
                profile_id="default",
                lemma="時",
                display="時",
                word_package=_japanese_word_package("時", "じ"),
            )

        self.assertEqual(result["word_package"]["reading"], "じ")
        self.assertEqual(result["srs"], {"present": False})
        self.assertEqual(
            [gloss["text"] for gloss in result["glosses"]],
            ["clock hour", "o'clock"],
        )

    def test_jmdict_word_info_matches_katakana_headword_to_normalized_reading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            jmdict_path = paths.language_packs_dir / "jmdict-ja-en" / "JMdict_e"
            _write_jmdict_sense_sample(jmdict_path)
            word_info_module._load_jmdict_definition_data_cached.cache_clear()

            result = lookup_word_info(
                paths,
                pair="en-ja",
                profile_id="default",
                lemma="ブラシ",
                display="ブラシ",
                word_package={
                    "version": 1,
                    "language_tag": "ja",
                    "surface": "ブラシ",
                    "reading": "ぶらし",
                    "script_forms": {"kana": "ブラシ"},
                    "source": {"provider": "jmdict"},
                },
            )

        self.assertEqual([gloss["text"] for gloss in result["glosses"]], ["brush"])
        self.assertEqual(result["dictionary_match"]["quality"], "exact_surface_reading")


if __name__ == "__main__":
    unittest.main()
