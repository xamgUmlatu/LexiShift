from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
import zipfile


CORE_ROOT = Path(__file__).resolve().parents[2]
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.lookup_dictionary_settings import (  # noqa: E402
    LookupDictionarySettings,
    load_lookup_dictionary_settings,
    lookup_dictionary_pack_ids_for_pair,
    lookup_dictionary_source_ids_for_pair,
    save_lookup_dictionary_settings,
    with_lookup_dictionary_pack_ids,
    with_lookup_dictionary_source_ids,
    without_lookup_dictionary_pack,
)
from lexishift_core.helper.engine import lookup_word_info  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.helper.pack_provenance import (  # noqa: E402
    validate_pack_provenance_file,
)
from lexishift_core.helper.yomitan_lookup_dictionaries import (  # noqa: E402
    YomitanDictionaryImportError,
    import_yomitan_dictionary_zip,
    list_installed_lookup_dictionaries,
    lookup_yomitan_dictionary,
    remove_installed_lookup_dictionary,
)
from lexishift_core.helper.yomitan_dictionary_health import (  # noqa: E402
    inspect_installed_lookup_dictionary_health,
)
from lexishift_core.helper.yomitan_dictionary_inspection import (  # noqa: E402
    inspect_yomitan_dictionary_zip,
)


def _write_yomitan_zip(
    path: Path,
    *,
    format_number: int = 3,
    extra_members: dict[str, str] | None = None,
    terms: list[object] | None = None,
    title: str = "User-owned Japanese Dictionary",
) -> None:
    index = {
        "title": title,
        "revision": "2026.1",
        "format": format_number,
        "author": "Local user",
        "sourceLanguage": "ja",
        "targetLanguage": "ja",
    }
    default_terms = [
        [
            "時",
            "とき",
            "common",
            "n",
            10,
            ["time as a general concept\n① a point in time"],
            1,
            "frequent",
        ],
        ["時", "じ", "", "n", 5, ["hour; o'clock"], 2, ""],
        [
            "見る",
            "みる",
            "",
            "v1",
            8,
            [
                {
                    "type": "structured-content",
                    "content": [
                        {"tag": "div", "content": ["to see", {"tag": "br"}]},
                        {"tag": "ul", "content": [{"tag": "li", "content": "to observe"}]},
                    ],
                }
            ],
            3,
            "",
        ],
    ]
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("index.json", json.dumps(index, ensure_ascii=False))
        archive.writestr(
            "term_bank_1.json",
            json.dumps(terms if terms is not None else default_terms, ensure_ascii=False),
        )
        for name, value in dict(extra_members or {}).items():
            archive.writestr(name, value)


class TestYomitanLookupDictionaries(unittest.TestCase):
    def test_health_inspection_reports_healthy_without_scanning_dictionary_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "dictionary.zip"
            _write_yomitan_zip(source)
            imported = import_yomitan_dictionary_zip(
                source,
                dictionaries_dir=root / "dictionaries",
            )

            health = inspect_installed_lookup_dictionary_health(root / "dictionaries")

            self.assertEqual(len(health), 1)
            self.assertTrue(health[0].healthy)
            self.assertEqual(health[0].dictionary.pack_id, imported.dictionary.pack_id)
            self.assertGreater(health[0].disk_usage_bytes, 0)

    def test_health_inspection_reports_corrupt_and_missing_managed_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "dictionary.zip"
            dictionaries_dir = root / "dictionaries"
            _write_yomitan_zip(source)
            imported = import_yomitan_dictionary_zip(
                source,
                dictionaries_dir=dictionaries_dir,
            )
            imported.manifest_path.write_text("{not-json", encoding="utf-8")

            health = inspect_installed_lookup_dictionary_health(dictionaries_dir)

            self.assertEqual(health[0].status, "corrupt")
            self.assertEqual(health[0].reason, "manifest_invalid")
            self.assertEqual(list_installed_lookup_dictionaries(dictionaries_dir), ())

            imported.manifest_path.unlink()
            health = inspect_installed_lookup_dictionary_health(dictionaries_dir)
            self.assertEqual(health[0].status, "missing")
            self.assertEqual(health[0].reason, "manifest_missing")

    def test_reimport_of_same_zip_repairs_corrupt_sqlite_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "dictionary.zip"
            dictionaries_dir = root / "dictionaries"
            _write_yomitan_zip(source)
            imported = import_yomitan_dictionary_zip(
                source,
                dictionaries_dir=dictionaries_dir,
            )
            imported.artifact_path.write_bytes(b"not a sqlite database")
            self.assertEqual(
                inspect_installed_lookup_dictionary_health(dictionaries_dir)[0].status,
                "corrupt",
            )

            repaired = import_yomitan_dictionary_zip(
                source,
                dictionaries_dir=dictionaries_dir,
                expected_pack_id=imported.dictionary.pack_id,
            )

            self.assertEqual(repaired.dictionary.pack_id, imported.dictionary.pack_id)
            self.assertTrue(inspect_installed_lookup_dictionary_health(dictionaries_dir)[0].healthy)
            result = lookup_yomitan_dictionary(
                repaired.artifact_path,
                lookup_candidates=("時",),
                surface="時",
                reading="とき",
                sense_limit=4,
                gloss_limit=8,
            )
            self.assertIsNotNone(result)

    def test_repair_expectation_rejects_a_different_dictionary_before_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "dictionary.zip"
            _write_yomitan_zip(source, title="Different Dictionary")

            with self.assertRaisesRegex(
                YomitanDictionaryImportError,
                "not the same dictionary copy",
            ):
                import_yomitan_dictionary_zip(
                    source,
                    dictionaries_dir=root / "dictionaries",
                    expected_pack_id="yomitan-expected-deadbeef0000",
                )

            self.assertEqual(
                inspect_installed_lookup_dictionary_health(root / "dictionaries"),
                (),
            )

    def test_archive_inspection_validates_supported_term_dictionary_without_importing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "大辞林　第四版　画像無し (1).zip"
            _write_yomitan_zip(source)

            info = inspect_yomitan_dictionary_zip(source)

            self.assertEqual(info.path, source)
            self.assertEqual(info.title, "User-owned Japanese Dictionary")
            self.assertEqual(info.revision, "2026.1")
            self.assertEqual(info.format, 3)
            self.assertEqual(info.source_language, "ja")
            self.assertEqual(info.target_language, "ja")
            self.assertFalse((root / "lookup_dictionaries").exists())

            unrelated = root / "unrelated.zip"
            with zipfile.ZipFile(unrelated, "w") as archive:
                archive.writestr("notes.txt", "not a dictionary")
            with self.assertRaisesRegex(YomitanDictionaryImportError, "missing index.json"):
                inspect_yomitan_dictionary_zip(unrelated)

    def test_word_info_uses_selected_local_dictionary_then_falls_back_to_jmdict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            source = Path(tmp) / "dictionary.zip"
            _write_yomitan_zip(source)
            imported = import_yomitan_dictionary_zip(
                source,
                dictionaries_dir=paths.lookup_dictionary_packs_dir,
            )
            settings = with_lookup_dictionary_pack_ids(
                LookupDictionarySettings(),
                pair="en-ja",
                pack_ids=(imported.dictionary.pack_id,),
            )
            save_lookup_dictionary_settings(settings, paths.lookup_dictionary_settings_path)

            local_result = lookup_word_info(
                paths,
                pair="en-ja",
                profile_id="default",
                lemma="時",
                display="時",
                word_package={
                    "version": 1,
                    "language_tag": "ja",
                    "surface": "時",
                    "reading": "とき",
                    "script_forms": {"kanji": "時", "kana": "とき"},
                    "source": {"provider": "test"},
                },
            )
            self.assertEqual(local_result["dictionary"]["provider"], "yomitan")
            self.assertEqual(local_result["dictionary"]["title"], imported.dictionary.title)
            self.assertEqual(len(local_result["dictionary_results"]), 1)
            self.assertEqual(
                local_result["dictionary_results"][0]["source_id"],
                imported.dictionary.pack_id,
            )
            self.assertEqual(
                [gloss["text"] for gloss in local_result["glosses"]],
                ["time as a general concept\n① a point in time"],
            )

            jmdict_path = paths.language_packs_dir / "jmdict-ja-en" / "JMdict_e"
            jmdict_path.parent.mkdir(parents=True, exist_ok=True)
            jmdict_path.write_text(
                """
<JMdict>
  <entry>
    <k_ele><keb>会社</keb></k_ele>
    <r_ele><reb>かいしゃ</reb></r_ele>
    <sense><pos>noun</pos><gloss>company</gloss></sense>
  </entry>
</JMdict>
""".strip(),
                encoding="utf-8",
            )
            fallback_result = lookup_word_info(
                paths,
                pair="en-ja",
                profile_id="default",
                lemma="会社",
                display="会社",
                word_package={
                    "version": 1,
                    "language_tag": "ja",
                    "surface": "会社",
                    "reading": "かいしゃ",
                    "script_forms": {"kanji": "会社", "kana": "かいしゃ"},
                    "source": {"provider": "test"},
                },
            )
            self.assertEqual(fallback_result["dictionary"]["provider"], "edrdg")
            self.assertEqual(
                [entry["dictionary"]["title"] for entry in fallback_result["dictionary_results"]],
                ["JMdict"],
            )
            self.assertEqual(
                [gloss["text"] for gloss in fallback_result["glosses"]],
                ["company"],
            )

    def test_word_info_returns_every_match_in_configured_order_then_builtin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            first_source = Path(tmp) / "first.zip"
            second_source = Path(tmp) / "second.zip"
            _write_yomitan_zip(
                first_source,
                title="First Dictionary",
                terms=[["時", "とき", "", "n", 1, ["first definition"], 1, ""]],
            )
            _write_yomitan_zip(
                second_source,
                title="Second Dictionary",
                terms=[["時", "とき", "", "n", 1, ["second definition"], 1, ""]],
            )
            first = import_yomitan_dictionary_zip(
                first_source,
                dictionaries_dir=paths.lookup_dictionary_packs_dir,
            )
            second = import_yomitan_dictionary_zip(
                second_source,
                dictionaries_dir=paths.lookup_dictionary_packs_dir,
            )
            jmdict_path = paths.language_packs_dir / "jmdict-ja-en" / "JMdict_e"
            jmdict_path.parent.mkdir(parents=True, exist_ok=True)
            jmdict_path.write_text(
                """
<JMdict>
  <entry>
    <k_ele><keb>時</keb></k_ele>
    <r_ele><reb>とき</reb></r_ele>
    <sense><pos>noun</pos><gloss>built-in definition</gloss></sense>
  </entry>
</JMdict>
""".strip(),
                encoding="utf-8",
            )

            def lookup() -> dict[str, object]:
                return lookup_word_info(
                    paths,
                    pair="en-ja",
                    profile_id="default",
                    lemma="時",
                    display="時",
                    word_package={
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "時",
                        "reading": "とき",
                        "script_forms": {"kanji": "時", "kana": "とき"},
                        "source": {"provider": "test"},
                    },
                )

            settings = with_lookup_dictionary_pack_ids(
                LookupDictionarySettings(),
                pair="en-ja",
                pack_ids=(first.dictionary.pack_id, second.dictionary.pack_id),
            )
            save_lookup_dictionary_settings(settings, paths.lookup_dictionary_settings_path)
            first_result = lookup()
            self.assertEqual(first_result["dictionary"]["title"], "First Dictionary")
            self.assertEqual(first_result["glosses"][0]["text"], "first definition")
            self.assertEqual(
                [entry["dictionary"]["title"] for entry in first_result["dictionary_results"]],
                ["First Dictionary", "Second Dictionary", "JMdict"],
            )
            self.assertEqual(
                [entry["priority"] for entry in first_result["dictionary_results"]],
                [1, 2, 3],
            )
            self.assertEqual(
                [entry["glosses"][0]["text"] for entry in first_result["dictionary_results"]],
                ["first definition", "second definition", "built-in definition"],
            )

            reordered = with_lookup_dictionary_pack_ids(
                settings,
                pair="en-ja",
                pack_ids=(second.dictionary.pack_id, first.dictionary.pack_id),
            )
            save_lookup_dictionary_settings(reordered, paths.lookup_dictionary_settings_path)
            second_result = lookup()
            self.assertEqual(second_result["dictionary"]["title"], "Second Dictionary")
            self.assertEqual(second_result["glosses"][0]["text"], "second definition")
            self.assertEqual(
                [entry["dictionary"]["title"] for entry in second_result["dictionary_results"]],
                ["Second Dictionary", "First Dictionary", "JMdict"],
            )

            builtin_first = with_lookup_dictionary_source_ids(
                reordered,
                pair="en-ja",
                source_ids=(
                    "builtin:jmdict",
                    second.dictionary.pack_id,
                    first.dictionary.pack_id,
                ),
            )
            save_lookup_dictionary_settings(
                builtin_first,
                paths.lookup_dictionary_settings_path,
            )
            third_result = lookup()
            self.assertEqual(
                lookup_dictionary_source_ids_for_pair(
                    builtin_first,
                    "en-ja",
                    builtin_source_id="builtin:jmdict",
                ),
                (
                    "builtin:jmdict",
                    second.dictionary.pack_id,
                    first.dictionary.pack_id,
                ),
            )
            self.assertEqual(third_result["dictionary"]["title"], "JMdict")
            self.assertEqual(
                [entry["dictionary"]["title"] for entry in third_result["dictionary_results"]],
                ["JMdict", "Second Dictionary", "First Dictionary"],
            )

    def test_import_preserves_source_and_supports_reading_aware_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "user-dictionary.zip"
            dictionaries_dir = root / "lookup_dictionaries"
            _write_yomitan_zip(source)
            progress: list[tuple[int, int]] = []

            result = import_yomitan_dictionary_zip(
                source,
                dictionaries_dir=dictionaries_dir,
                progress=lambda current, total: progress.append((current, total)),
            )

            self.assertTrue(source.exists())
            self.assertTrue(result.artifact_path.exists())
            self.assertTrue(result.manifest_path.exists())
            self.assertEqual(validate_pack_provenance_file(result.provenance_path), ())
            self.assertEqual(result.dictionary.title, "User-owned Japanese Dictionary")
            self.assertEqual(result.dictionary.term_count, 3)
            self.assertEqual(progress, [(1, 1)])
            self.assertEqual(
                [item.pack_id for item in list_installed_lookup_dictionaries(dictionaries_dir)],
                [result.dictionary.pack_id],
            )

            lookup = lookup_yomitan_dictionary(
                result.artifact_path,
                lookup_candidates=("時",),
                surface="時",
                reading="とき",
                sense_limit=5,
                gloss_limit=5,
            )
            self.assertIsNotNone(lookup)
            assert lookup is not None
            self.assertEqual(lookup.dictionary["title"], "User-owned Japanese Dictionary")
            self.assertEqual(lookup.dictionary_match["quality"], "exact_surface_reading")
            self.assertEqual(lookup.dictionary_match["reading"], "とき")
            self.assertEqual(
                [gloss["text"] for gloss in lookup.glosses],
                ["time as a general concept\n① a point in time"],
            )
            self.assertNotIn("hour; o'clock", str(lookup.senses))

            kana_lookup = lookup_yomitan_dictionary(
                result.artifact_path,
                lookup_candidates=("とき",),
                surface="とき",
                reading="とき",
                sense_limit=5,
                gloss_limit=5,
            )
            self.assertIsNotNone(kana_lookup)
            assert kana_lookup is not None
            self.assertEqual(kana_lookup.dictionary_match["quality"], "exact_reading")
            self.assertEqual(kana_lookup.dictionary_match["surface"], "時")
            self.assertNotIn("hour; o'clock", str(kana_lookup.senses))

            structured_lookup = lookup_yomitan_dictionary(
                result.artifact_path,
                lookup_candidates=("見る",),
                surface="見る",
                reading="みる",
                sense_limit=5,
                gloss_limit=5,
            )
            self.assertIsNotNone(structured_lookup)
            assert structured_lookup is not None
            self.assertEqual(
                structured_lookup.glosses[0]["text"],
                "to see\n• to observe",
            )
            with sqlite3.connect(result.artifact_path) as conn:
                raw_glossary = conn.execute(
                    "SELECT glossary_json FROM terms WHERE expression = '見る'"
                ).fetchone()[0]
            self.assertIn('"structured-content"', raw_glossary)

    def test_structured_content_preserves_hierarchy_and_japanese_spacing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "structured.zip"
            dictionaries_dir = root / "lookup_dictionaries"
            _write_yomitan_zip(
                source,
                terms=[
                    [
                        "時",
                        "とき",
                        "",
                        "n",
                        1,
                        [
                            {
                                "type": "structured-content",
                                "content": [
                                    {
                                        "tag": "span",
                                        "data": {"name": "見出部"},
                                        "content": "とき【時】",
                                    },
                                    {
                                        "tag": "div",
                                        "data": {"name": "語義G"},
                                        "content": [
                                            {
                                                "tag": "span",
                                                "data": {"name": "語義Gnum"},
                                                "content": "①",
                                            },
                                            {
                                                "tag": "span",
                                                "data": {"name": "語釈"},
                                                "content": "ある時点。",
                                            },
                                            {
                                                "tag": "div",
                                                "data": {"name": "副義"},
                                                "content": [
                                                    {
                                                        "tag": "span",
                                                        "data": {"name": "副義num"},
                                                        "content": "㋐",
                                                    },
                                                    {
                                                        "tag": "span",
                                                        "data": {"name": "語釈"},
                                                        "content": "時刻。",
                                                    },
                                                ],
                                            },
                                            {
                                                "tag": "img",
                                                "title": "一",
                                                "path": "ignored.svg",
                                            },
                                        ],
                                    },
                                ],
                            }
                        ],
                        1,
                        "",
                    ],
                    [
                        "時",
                        "とき",
                        "",
                        "",
                        -1,
                        [
                            {
                                "type": "structured-content",
                                "content": {
                                    "tag": "a",
                                    "href": "?query=時を待つ&wildcards=off",
                                    "content": "時を待つ",
                                },
                            }
                        ],
                        1,
                        "",
                    ],
                ],
            )
            imported = import_yomitan_dictionary_zip(
                source,
                dictionaries_dir=dictionaries_dir,
            )
            lookup = lookup_yomitan_dictionary(
                imported.artifact_path,
                lookup_candidates=("時",),
                surface="時",
                reading="とき",
                sense_limit=5,
                gloss_limit=5,
            )
            self.assertIsNotNone(lookup)
            assert lookup is not None
            self.assertEqual(len(lookup.senses), 1)
            self.assertNotIn("とき 【 時 】", lookup.glosses[0]["text"])
            structured = lookup.senses[0].get("structured_content")
            self.assertIsInstance(structured, list)
            structured_json = json.dumps(structured, ensure_ascii=False)
            self.assertIn('"role": "sense"', structured_json)
            self.assertIn('"role": "subsense"', structured_json)
            self.assertIn('"type": "image-fallback"', structured_json)

    def test_large_glossaries_are_compressed_without_losing_lookup_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "compressed.zip"
            dictionaries_dir = root / "lookup_dictionaries"
            long_definition = "large structured definition " * 500
            _write_yomitan_zip(
                source,
                terms=[
                    [
                        "sample",
                        "sample",
                        "",
                        "",
                        1,
                        [{"type": "structured-content", "content": long_definition}],
                        1,
                        "",
                    ]
                ],
            )
            imported = import_yomitan_dictionary_zip(
                source,
                dictionaries_dir=dictionaries_dir,
            )
            with sqlite3.connect(imported.artifact_path) as conn:
                stored = conn.execute("SELECT glossary_json FROM terms").fetchone()[0]
            self.assertIsInstance(stored, bytes)
            self.assertTrue(stored.startswith(b"LSZ1"))
            lookup = lookup_yomitan_dictionary(
                imported.artifact_path,
                lookup_candidates=("sample",),
                surface="sample",
                reading="sample",
                sense_limit=5,
                gloss_limit=5,
            )
            self.assertIsNotNone(lookup)
            assert lookup is not None
            self.assertTrue(
                str(lookup.glosses[0]["text"]).startswith("large structured definition")
            )

    def test_reading_only_term_rows_are_imported_and_lookupable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "reading-only.zip"
            _write_yomitan_zip(
                source,
                terms=[
                    ["", "あて", "", "", -1, ["reading-only entry"], 1, ""],
                    ["", "", "", "", 0, ["unlookupable entry"], 2, ""],
                ],
            )
            imported = import_yomitan_dictionary_zip(
                source,
                dictionaries_dir=root / "lookup_dictionaries",
            )
            self.assertEqual(imported.dictionary.term_count, 1)
            with sqlite3.connect(imported.artifact_path) as conn:
                skipped = json.loads(
                    conn.execute(
                        "SELECT value_json FROM metadata WHERE key = 'skipped_term_count'"
                    ).fetchone()[0]
                )
            self.assertEqual(skipped, 1)
            lookup = lookup_yomitan_dictionary(
                imported.artifact_path,
                lookup_candidates=("あて",),
                surface="あて",
                reading="あて",
                sense_limit=5,
                gloss_limit=5,
            )
            self.assertIsNotNone(lookup)
            assert lookup is not None
            self.assertEqual(lookup.dictionary_match["surface"], "あて")
            self.assertEqual(lookup.glosses[0]["text"], "reading-only entry")

    def test_import_is_idempotent_for_same_archive_and_removal_is_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "dictionary.zip"
            dictionaries_dir = root / "lookup_dictionaries"
            _write_yomitan_zip(source)
            first = import_yomitan_dictionary_zip(source, dictionaries_dir=dictionaries_dir)
            second = import_yomitan_dictionary_zip(source, dictionaries_dir=dictionaries_dir)
            self.assertEqual(first.dictionary.pack_id, second.dictionary.pack_id)
            self.assertTrue(
                remove_installed_lookup_dictionary(dictionaries_dir, first.dictionary.pack_id)
            )
            self.assertFalse(first.artifact_path.exists())
            self.assertTrue(source.exists())
            with self.assertRaises(ValueError):
                remove_installed_lookup_dictionary(dictionaries_dir, "../outside")

    def test_import_rejects_unsupported_format_and_unsafe_archive_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dictionaries_dir = root / "lookup_dictionaries"
            old_format = root / "old.zip"
            _write_yomitan_zip(old_format, format_number=2)
            with self.assertRaisesRegex(YomitanDictionaryImportError, "format 2"):
                import_yomitan_dictionary_zip(old_format, dictionaries_dir=dictionaries_dir)

            unsafe = root / "unsafe.zip"
            _write_yomitan_zip(unsafe, extra_members={"../escape.txt": "no"})
            with self.assertRaisesRegex(YomitanDictionaryImportError, "unsafe file path"):
                import_yomitan_dictionary_zip(unsafe, dictionaries_dir=dictionaries_dir)

    def test_pair_settings_round_trip_and_remove_pack_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = Path(tmp) / "settings.json"
            settings = with_lookup_dictionary_pack_ids(
                LookupDictionarySettings(),
                pair="en-ja",
                pack_ids=("yomitan-local", "jmdict-ja-en", "yomitan-local"),
            )
            save_lookup_dictionary_settings(settings, settings_path)
            loaded = load_lookup_dictionary_settings(settings_path)
            self.assertEqual(
                lookup_dictionary_pack_ids_for_pair(loaded, "EN-JA"),
                ("yomitan-local", "jmdict-ja-en"),
            )
            removed = without_lookup_dictionary_pack(loaded, "yomitan-local")
            self.assertEqual(
                lookup_dictionary_pack_ids_for_pair(removed, "en-ja"),
                ("jmdict-ja-en",),
            )

    def test_same_dictionary_can_be_selected_for_multiple_language_pairs(self) -> None:
        settings = with_lookup_dictionary_pack_ids(
            LookupDictionarySettings(),
            pair="en-ja",
            pack_ids=("yomitan-daijirin",),
        )
        settings = with_lookup_dictionary_pack_ids(
            settings,
            pair="ja-ja",
            pack_ids=("yomitan-daijirin",),
        )
        self.assertEqual(
            lookup_dictionary_pack_ids_for_pair(settings, "en-ja"),
            ("yomitan-daijirin",),
        )
        self.assertEqual(
            lookup_dictionary_pack_ids_for_pair(settings, "ja-ja"),
            ("yomitan-daijirin",),
        )


if __name__ == "__main__":
    unittest.main()
