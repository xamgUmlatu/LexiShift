from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.resources.dict_loaders import load_jmdict_glosses_and_script_forms  # noqa: E402
from lexishift_core.resources.japanese_script import kana_to_romaji  # noqa: E402
from lexishift_core.rulegen.pairs.ja_en import (  # noqa: E402
    JaEnRulegenConfig,
    generate_ja_en_results,
)


def _write_sample_jmdict(path: Path) -> None:
    payload = (
        "<JMdict>"
        "<entry>"
        "<k_ele><keb>猫</keb></k_ele>"
        "<r_ele><reb>ねこ</reb></r_ele>"
        "<sense><gloss xml:lang='eng'>cat</gloss></sense>"
        "</entry>"
        "</JMdict>"
    )
    path.write_text(payload, encoding="utf-8")


class TestJapaneseScriptForms(unittest.TestCase):
    def test_kana_to_romaji_transliterates_hiragana_and_katakana(self) -> None:
        self.assertEqual(kana_to_romaji("ねこ"), "neko")
        self.assertEqual(kana_to_romaji("キャット"), "kyatto")

    def test_jmdict_loader_extracts_script_forms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "JMdict_e"
            _write_sample_jmdict(path)
            mapping, forms = load_jmdict_glosses_and_script_forms(path)

        self.assertIn("cat", mapping["猫"])
        self.assertIn("cat", mapping["ねこ"])
        self.assertEqual(forms["猫"]["kanji"], "猫")
        self.assertEqual(forms["猫"]["kana"], "ねこ")
        self.assertEqual(forms["猫"]["romaji"], "neko")
        self.assertEqual(forms["ねこ"]["kanji"], "猫")

    def test_ja_en_rulegen_metadata_includes_script_forms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "JMdict_e"
            _write_sample_jmdict(path)
            results = generate_ja_en_results(
                ("猫",),
                config=JaEnRulegenConfig(
                    jmdict_path=path,
                    include_variants=False,
                ),
            )

        self.assertGreater(len(results), 0)
        metadata = results[0].rule.metadata
        self.assertIsNotNone(metadata)
        self.assertIsNotNone(metadata.script_forms)
        self.assertEqual(metadata.script_forms["kanji"], "猫")
        self.assertEqual(metadata.script_forms["kana"], "ねこ")
        self.assertEqual(metadata.script_forms["romaji"], "neko")


if __name__ == "__main__":
    unittest.main()
