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
from lexishift_core.rulegen.generation import (  # noqa: E402
    PosMatchScoringConfig,
    RuleScoreWeights,
    RuleScoringConfig,
)
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

    def test_en_es_requires_freedict_es_en_path(self) -> None:
        with self.assertRaises(ValueError):
            run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-es",
                    targets=("casa",),
                    language_pair="en-es",
                    freedict_de_en_path=None,
                )
            )

    def test_en_es_dispatches_to_freedict_generator(self) -> None:
        with patch(
            "lexishift_core.rulegen.adapters.generate_en_es_results",
            return_value=[
                SimpleNamespace(
                    rule=VocabRule(source_phrase="house", replacement="casa")
                )
            ],
        ) as generate:
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-es",
                    targets=("casa",),
                    language_pair="en-es",
                    freedict_de_en_path=Path("/tmp/spa-eng.tei"),
                )
            )
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].source_phrase, "house")
        self.assertEqual(rules[0].replacement, "casa")
        generate.assert_called_once()

    def test_en_es_dispatches_scoring_and_rule_caps(self) -> None:
        scoring = RuleScoringConfig(
            weights=RuleScoreWeights(pos_match=0.35),
            pos_match=PosMatchScoringConfig(enabled=False),
        )
        with patch(
            "lexishift_core.rulegen.adapters.generate_en_es_results",
            return_value=[
                SimpleNamespace(
                    rule=VocabRule(source_phrase="house", replacement="casa")
                )
            ],
        ) as generate:
            run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-es",
                    targets=("casa",),
                    language_pair="en-es",
                    freedict_de_en_path=Path("/tmp/spa-eng.tei"),
                    max_rules_per_target=5,
                    semantic_demotion_scale=0.4,
                    scoring=scoring,
                )
            )
        generate.assert_called_once()
        args, kwargs = generate.call_args
        _ = args
        self.assertEqual(kwargs["config"].max_rules_per_target, 5)
        self.assertAlmostEqual(kwargs["config"].semantic_demotion_scale, 0.4, places=6)
        self.assertAlmostEqual(kwargs["config"].scoring.weights.pos_match, 0.35, places=6)
        self.assertFalse(kwargs["config"].scoring.pos_match.enabled)

    def test_en_es_adapter_generates_rules_from_freedict_tei(self) -> None:
        tei_payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>casa</orth></form>
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
            path = Path(tmp) / "spa-eng.tei"
            path.write_text(tei_payload, encoding="utf-8")
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-es",
                    targets=("casa",),
                    language_pair="en-es",
                    freedict_de_en_path=path,
                )
            )
        sources = sorted({rule.source_phrase for rule in rules})
        self.assertIn("house", sources)
        self.assertIn("home", sources)
        self.assertTrue(all(rule.replacement == "casa" for rule in rules))

    def test_en_es_adapter_generates_plural_pair_with_canonical_target(self) -> None:
        tei_payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>hora</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="en">hour</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spa-eng.tei"
            path.write_text(tei_payload, encoding="utf-8")
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-es",
                    targets=("hora",),
                    language_pair="en-es",
                    freedict_de_en_path=path,
                )
            )

        by_source = {rule.source_phrase: rule for rule in rules}
        self.assertIn("hour", by_source)
        self.assertIn("hours", by_source)
        self.assertEqual(by_source["hour"].replacement, "hora")
        self.assertEqual(by_source["hours"].replacement, "hora")
        hours_metadata = by_source["hours"].metadata
        self.assertIsNotNone(hours_metadata)
        self.assertIsNotNone(hours_metadata.morphology)
        self.assertEqual(hours_metadata.morphology.get("source_form"), "plural")
        self.assertEqual(hours_metadata.morphology.get("target_surface"), "horas")
        self.assertEqual(hours_metadata.morphology.get("target_lemma"), "hora")

    def test_en_es_adapter_caps_total_rules_per_target_after_variants(self) -> None:
        tei_payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>hora</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="en">hour</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spa-eng.tei"
            path.write_text(tei_payload, encoding="utf-8")
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-es",
                    targets=("hora",),
                    language_pair="en-es",
                    freedict_de_en_path=path,
                    include_variants=True,
                    max_rules_per_target=1,
                )
            )

        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].source_phrase, "hour")

    def test_en_es_adapter_sanitizes_gloss_noise_before_rulegen(self) -> None:
        tei_payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>hora</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="en">hour (noun).</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spa-eng.tei"
            path.write_text(tei_payload, encoding="utf-8")
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-es",
                    targets=("hora",),
                    language_pair="en-es",
                    freedict_de_en_path=path,
                    include_variants=False,
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["hour"])
        self.assertEqual(rules[0].replacement, "hora")

    def test_en_es_adapter_caps_to_top_three_by_dictionary_order(self) -> None:
        tei_payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>casa</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="en">house</quote></cit>
          <cit type="trans"><quote xml:lang="en">home</quote></cit>
          <cit type="trans"><quote xml:lang="en">dwelling</quote></cit>
          <cit type="trans"><quote xml:lang="en">residence</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spa-eng.tei"
            path.write_text(tei_payload, encoding="utf-8")
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-es",
                    targets=("casa",),
                    language_pair="en-es",
                    freedict_de_en_path=path,
                    include_variants=False,
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["house", "home", "dwelling"])
        self.assertTrue(all(rule.replacement == "casa" for rule in rules))

    def test_en_es_adapter_demotes_generic_gloss_terms_for_top_k(self) -> None:
        tei_payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>casa</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="en">appearing</quote></cit>
          <cit type="trans"><quote xml:lang="en">looking</quote></cit>
          <cit type="trans"><quote xml:lang="en">house</quote></cit>
          <cit type="trans"><quote xml:lang="en">home</quote></cit>
          <cit type="trans"><quote xml:lang="en">dwelling</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spa-eng.tei"
            path.write_text(tei_payload, encoding="utf-8")
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-es",
                    targets=("casa",),
                    language_pair="en-es",
                    freedict_de_en_path=path,
                    include_variants=False,
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["house", "home", "dwelling"])
        self.assertTrue(all(rule.replacement == "casa" for rule in rules))

    def test_en_ja_adapter_caps_to_top_three_by_dictionary_order(self) -> None:
        jmdict_payload = (
            "<JMdict>"
            "<entry>"
            "<k_ele><keb>時</keb></k_ele>"
            "<r_ele><reb>とき</reb></r_ele>"
            "<sense>"
            "<gloss xml:lang='eng'>time</gloss>"
            "<gloss xml:lang='eng'>occasion</gloss>"
            "<gloss xml:lang='eng'>moment</gloss>"
            "<gloss xml:lang='eng'>period</gloss>"
            "</sense>"
            "</entry>"
            "</JMdict>"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "JMdict_e"
            path.write_text(jmdict_payload, encoding="utf-8")
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-ja",
                    targets=("時",),
                    language_pair="en-ja",
                    jmdict_path=path,
                    include_variants=False,
                    word_packages_by_target={
                        "時": {
                            "version": 1,
                            "language_tag": "ja",
                            "surface": "時",
                            "reading": "とき",
                            "script_forms": {"kanji": "時", "kana": "とき", "romaji": "toki"},
                            "source": {"provider": "freq-ja-bccwj"},
                        }
                    },
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["time", "occasion", "moment"])
        self.assertTrue(all(rule.replacement == "時" for rule in rules))

    def test_en_ja_adapter_does_not_emit_context_free_verb_inflections(self) -> None:
        jmdict_payload = (
            "<JMdict>"
            "<entry>"
            "<k_ele><keb>時</keb></k_ele>"
            "<r_ele><reb>とき</reb></r_ele>"
            "<sense>"
            "<gloss xml:lang='eng'>time</gloss>"
            "<gloss xml:lang='eng'>hour</gloss>"
            "</sense>"
            "</entry>"
            "</JMdict>"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "JMdict_e"
            path.write_text(jmdict_payload, encoding="utf-8")
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-ja",
                    targets=("時",),
                    language_pair="en-ja",
                    jmdict_path=path,
                    include_variants=True,
                    word_packages_by_target={
                        "時": {
                            "version": 1,
                            "language_tag": "ja",
                            "surface": "時",
                            "reading": "とき",
                            "script_forms": {"kanji": "時", "kana": "とき", "romaji": "toki"},
                            "source": {"provider": "freq-ja-bccwj"},
                        }
                    },
                )
            )
        sources = {rule.source_phrase for rule in rules}
        self.assertIn("time", sources)
        self.assertIn("hour", sources)
        self.assertNotIn("timed", sources)
        self.assertNotIn("timing", sources)
        self.assertFalse(any(source.endswith("ed") or source.endswith("ing") for source in sources))

    def test_en_ja_adapter_demotes_generic_gloss_terms_for_top_k(self) -> None:
        jmdict_payload = (
            "<JMdict>"
            "<entry>"
            "<k_ele><keb>様</keb></k_ele>"
            "<r_ele><reb>よう</reb></r_ele>"
            "<sense>"
            "<gloss xml:lang='eng'>appearing</gloss>"
            "<gloss xml:lang='eng'>looking</gloss>"
            "<gloss xml:lang='eng'>form</gloss>"
            "<gloss xml:lang='eng'>style</gloss>"
            "<gloss xml:lang='eng'>design</gloss>"
            "</sense>"
            "</entry>"
            "</JMdict>"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "JMdict_e"
            path.write_text(jmdict_payload, encoding="utf-8")
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-ja",
                    targets=("様",),
                    language_pair="en-ja",
                    jmdict_path=path,
                    include_variants=False,
                    word_packages_by_target={
                        "様": {
                            "version": 1,
                            "language_tag": "ja",
                            "surface": "様",
                            "reading": "よう",
                            "script_forms": {"kanji": "様", "kana": "よう", "romaji": "you"},
                            "source": {"provider": "freq-ja-bccwj"},
                        }
                    },
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["form", "style", "design"])

    def test_en_de_adapter_demotes_generic_gloss_terms_for_top_k(self) -> None:
        tei_payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>haus</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="en">appearing</quote></cit>
          <cit type="trans"><quote xml:lang="en">looking</quote></cit>
          <cit type="trans"><quote xml:lang="en">house</quote></cit>
          <cit type="trans"><quote xml:lang="en">home</quote></cit>
          <cit type="trans"><quote xml:lang="en">dwelling</quote></cit>
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
                    targets=("haus",),
                    language_pair="en-de",
                    freedict_de_en_path=path,
                    include_variants=False,
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["house", "home", "dwelling"])
        self.assertTrue(all(rule.replacement == "haus" for rule in rules))

    def test_es_en_adapter_generates_rules_from_freedict_tei(self) -> None:
        tei_payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>house</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="es">casa</quote></cit>
          <cit type="trans"><quote xml:lang="es">hogar</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "eng-spa.tei"
            path.write_text(tei_payload, encoding="utf-8")
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="es-en",
                    targets=("house",),
                    language_pair="es-en",
                    freedict_de_en_path=path,
                )
            )
        sources = sorted({rule.source_phrase for rule in rules})
        self.assertIn("casa", sources)
        self.assertIn("hogar", sources)
        self.assertTrue(all(rule.replacement == "house" for rule in rules))

    def test_es_en_adapter_demotes_generic_gloss_terms_for_top_k(self) -> None:
        tei_payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>house</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="es">tipo</quote></cit>
          <cit type="trans"><quote xml:lang="es">clase</quote></cit>
          <cit type="trans"><quote xml:lang="es">casa</quote></cit>
          <cit type="trans"><quote xml:lang="es">hogar</quote></cit>
          <cit type="trans"><quote xml:lang="es">vivienda</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "eng-spa.tei"
            path.write_text(tei_payload, encoding="utf-8")
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="es-en",
                    targets=("house",),
                    language_pair="es-en",
                    freedict_de_en_path=path,
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["casa", "hogar", "vivienda"])
        self.assertTrue(all(rule.replacement == "house" for rule in rules))


if __name__ == "__main__":
    unittest.main()
