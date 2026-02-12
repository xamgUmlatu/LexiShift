from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.replacement.core import VocabRule  # noqa: E402
from lexishift_core.rulegen.adapters import (  # noqa: E402
    RulegenAdapterRequest,
    run_rules_with_adapter,
)


class TestRulegenAdapters(unittest.TestCase):
    def test_returns_empty_rules_for_pair_without_rulegen_mode(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="de-en",
                targets=("house",),
                language_pair="de-en",
            )
        )
        self.assertEqual(rules, [])

    def test_en_ja_requires_jmdict_path(self) -> None:
        with self.assertRaises(ValueError):
            run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-ja",
                    targets=("語",),
                    language_pair="en-ja",
                    jmdict_path=None,
                )
            )

    def test_en_ja_dispatches_to_ja_en_generator(self) -> None:
        with patch(
            "lexishift_core.rulegen.adapters.generate_ja_en_results",
            return_value=[
                SimpleNamespace(
                    rule=VocabRule(source_phrase="word", replacement="語")
                )
            ],
        ) as generate:
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-ja",
                    targets=("語",),
                    language_pair="en-ja",
                    jmdict_path=Path("/tmp/JMdict_e"),
                    word_packages_by_target={
                        "語": {
                            "version": 1,
                            "language_tag": "ja",
                            "surface": "語",
                            "reading": "ご",
                            "script_forms": {"kanji": "語", "kana": "ご", "romaji": "go"},
                            "source": {"provider": "freq-ja-bccwj"},
                        }
                    },
                )
            )
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].source_phrase, "word")
        self.assertEqual(rules[0].replacement, "語")
        generate.assert_called_once()
        args, kwargs = generate.call_args
        self.assertIn("config", kwargs)
        self.assertEqual(
            kwargs["config"].word_packages_by_target["語"]["reading"],
            "ご",
        )

    def test_en_de_requires_freedict_de_en_path(self) -> None:
        with self.assertRaises(ValueError):
            run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Haus",),
                    language_pair="en-de",
                    freedict_de_en_path=None,
                )
            )

    def test_en_de_dispatches_to_freedict_generator(self) -> None:
        with patch(
            "lexishift_core.rulegen.adapters.generate_en_de_results",
            return_value=[
                SimpleNamespace(
                    rule=VocabRule(source_phrase="house", replacement="Haus")
                )
            ],
        ) as generate:
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Haus",),
                    language_pair="en-de",
                    freedict_de_en_path=Path("/tmp/deu-eng.tei"),
                )
            )
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].source_phrase, "house")
        self.assertEqual(rules[0].replacement, "Haus")
        generate.assert_called_once()

    def test_en_de_adapter_generates_rules_from_freedict_tei(self) -> None:
        tei_payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>Haus</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="en">house</quote></cit>
          <cit type="trans"><quote xml:lang="en">home</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deu-eng.tei"
            path.write_text(tei_payload, encoding="utf-8")
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Haus",),
                    language_pair="en-de",
                    freedict_de_en_path=path,
                )
            )
        sources = sorted({rule.source_phrase for rule in rules})
        self.assertIn("house", sources)
        self.assertIn("home", sources)
        self.assertTrue(all(rule.replacement == "Haus" for rule in rules))


if __name__ == "__main__":
    unittest.main()
