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

from lexishift_core.resources.dict_loaders import FreedictGlossRecord  # noqa: E402
from lexishift_core.replacement.core import VocabRule  # noqa: E402
from lexishift_core.rulegen.generation import (  # noqa: E402
    PosMatchScoringConfig,
    RuleScoreWeights,
    RuleScoringConfig,
)
from lexishift_core.rulegen.pairs.en_es import EnEsCompiledResources  # noqa: E402
from lexishift_core.rulegen.ranking import ReverseCheckScoringConfig  # noqa: E402
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

    def test_en_ja_dispatches_to_en_ja_generator(self) -> None:
        with patch(
            "lexishift_core.rulegen.adapters.generate_en_ja_results",
            return_value=[SimpleNamespace(rule=VocabRule(source_phrase="word", replacement="語"))],
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
                SimpleNamespace(rule=VocabRule(source_phrase="house", replacement="Haus"))
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
                SimpleNamespace(rule=VocabRule(source_phrase="house", replacement="casa"))
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

    def test_en_es_dispatches_wiktionary_source_metadata_for_kaikki_sqlite(self) -> None:
        with patch(
            "lexishift_core.rulegen.adapters.generate_en_es_results",
            return_value=[
                SimpleNamespace(rule=VocabRule(source_phrase="house", replacement="casa"))
            ],
        ) as generate:
            run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-es",
                    targets=("casa",),
                    language_pair="en-es",
                    freedict_de_en_path=Path("/tmp/wiktionary-es-en.sqlite"),
                )
            )
        generate.assert_called_once()
        args, kwargs = generate.call_args
        _ = args
        self.assertEqual(kwargs["config"].source_dict_id, "wiktionary_es_en")
        self.assertEqual(kwargs["config"].dictionary_pos_source_profile, "wiktionary")

    def test_en_es_dispatches_wiktionary_reverse_metadata_for_kaikki_sqlite(self) -> None:
        with patch(
            "lexishift_core.rulegen.adapters.generate_en_es_results",
            return_value=[
                SimpleNamespace(rule=VocabRule(source_phrase="house", replacement="casa"))
            ],
        ) as generate:
            run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-es",
                    targets=("casa",),
                    language_pair="en-es",
                    freedict_de_en_path=Path("/tmp/wiktionary-es-en.sqlite"),
                    freedict_reverse_path=Path("/tmp/wiktionary-en-es.sqlite"),
                )
            )
        generate.assert_called_once()
        args, kwargs = generate.call_args
        _ = args
        self.assertEqual(kwargs["config"].reverse_source_dict_id, "wiktionary_en_es")

    def test_en_es_dispatches_scoring_and_rule_caps(self) -> None:
        scoring = RuleScoringConfig(
            weights=RuleScoreWeights(pos_match=0.35),
            pos_match=PosMatchScoringConfig(enabled=False),
        )
        reverse_check = ReverseCheckScoringConfig(
            enabled=True,
            match_bonus=0.25,
            near_bonus=0.12,
            near_rank_max=1,
            miss_penalty=0.22,
            exact_hit_specificity_bonus=0.14,
        )
        with patch(
            "lexishift_core.rulegen.adapters.generate_en_es_results",
            return_value=[
                SimpleNamespace(rule=VocabRule(source_phrase="house", replacement="casa"))
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
                    reverse_check=reverse_check,
                    kaikki_policy_live_demotion=True,
                    kaikki_policy_risk_families=("math_geometry", "government_law"),
                    kaikki_policy_late_sense_penalty=0.16,
                )
            )
        generate.assert_called_once()
        args, kwargs = generate.call_args
        _ = args
        self.assertEqual(kwargs["config"].max_rules_per_target, 5)
        self.assertAlmostEqual(kwargs["config"].semantic_demotion_scale, 0.4, places=6)
        self.assertAlmostEqual(kwargs["config"].scoring.weights.pos_match, 0.35, places=6)
        self.assertFalse(kwargs["config"].scoring.pos_match.enabled)
        self.assertTrue(kwargs["config"].reverse_check.enabled)
        self.assertAlmostEqual(kwargs["config"].reverse_check.match_bonus, 0.25, places=6)
        self.assertAlmostEqual(kwargs["config"].reverse_check.near_bonus, 0.12, places=6)
        self.assertEqual(kwargs["config"].reverse_check.near_rank_max, 1)
        self.assertAlmostEqual(kwargs["config"].reverse_check.miss_penalty, 0.22, places=6)
        self.assertAlmostEqual(
            kwargs["config"].reverse_check.exact_hit_specificity_bonus,
            0.14,
            places=6,
        )
        self.assertTrue(kwargs["config"].kaikki_policy.enable_live_demotion)
        self.assertEqual(
            kwargs["config"].kaikki_policy.risk_families,
            ("math_geometry", "government_law"),
        )
        self.assertAlmostEqual(
            kwargs["config"].kaikki_policy.late_sense_clean_earlier_competition_penalty,
            0.16,
            places=6,
        )

    def test_en_es_dispatches_preloaded_gloss_records(self) -> None:
        forward_records = {"casa": [FreedictGlossRecord(translation="house", pos_raw="noun")]}
        reverse_records = {"house": [FreedictGlossRecord(translation="casa", pos_raw="noun")]}
        with patch(
            "lexishift_core.rulegen.adapters.generate_en_es_results",
            return_value=[
                SimpleNamespace(rule=VocabRule(source_phrase="house", replacement="casa"))
            ],
        ) as generate:
            run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-es",
                    targets=("casa",),
                    language_pair="en-es",
                    freedict_de_en_path=Path("/tmp/wiktionary-es-en.sqlite"),
                    freedict_reverse_path=Path("/tmp/wiktionary-en-es.sqlite"),
                    gloss_records_by_target=forward_records,
                    reverse_gloss_records_by_source=reverse_records,
                )
            )
        generate.assert_called_once()
        args, kwargs = generate.call_args
        _ = args
        self.assertIs(kwargs["config"].gloss_records_by_target, forward_records)
        self.assertIs(kwargs["config"].reverse_gloss_records_by_source, reverse_records)

    def test_en_es_dispatches_compiled_resources(self) -> None:
        compiled_resources = EnEsCompiledResources(
            records_by_target={"casa": [FreedictGlossRecord(translation="house", pos_raw="noun")]},
            reverse_records_by_source={
                "house": [FreedictGlossRecord(translation="casa", pos_raw="noun")]
            },
        )
        with patch(
            "lexishift_core.rulegen.adapters.generate_en_es_results",
            return_value=[
                SimpleNamespace(rule=VocabRule(source_phrase="house", replacement="casa"))
            ],
        ) as generate:
            run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-es",
                    targets=("casa",),
                    language_pair="en-es",
                    freedict_de_en_path=Path("/tmp/wiktionary-es-en.sqlite"),
                    compiled_pair_context=compiled_resources,
                )
            )
        generate.assert_called_once()
        _, kwargs = generate.call_args
        self.assertIs(kwargs["config"].compiled_resources, compiled_resources)

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
                    word_packages_by_target={
                        "hora": {
                            "version": 1,
                            "pos_canonical": "noun",
                        }
                    },
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

    def test_en_es_adapter_skips_plural_target_surface_for_non_noun_targets(self) -> None:
        tei_payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>mostrar</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="en">show</quote></cit>
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
                    targets=("mostrar",),
                    language_pair="en-es",
                    freedict_de_en_path=path,
                    include_variants=True,
                    word_packages_by_target={
                        "mostrar": {
                            "version": 1,
                            "pos_canonical": "verb",
                        }
                    },
                )
            )

        by_source = {rule.source_phrase: rule for rule in rules}
        self.assertIn("show", by_source)
        self.assertNotIn("shows", by_source)

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

    def test_en_es_adapter_strips_infinitive_marker_before_single_word_filter(self) -> None:
        tei_payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>hacer</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="en">to admire</quote></cit>
          <cit type="trans"><quote xml:lang="en">to carry out</quote></cit>
          <cit type="trans"><quote xml:lang="en">to value</quote></cit>
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
                    targets=("hacer",),
                    language_pair="en-es",
                    freedict_de_en_path=path,
                    include_variants=False,
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["admire", "value"])
        self.assertTrue(all(rule.replacement == "hacer" for rule in rules))

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

    def test_en_ja_adapter_strips_infinitive_marker_before_single_word_filter(self) -> None:
        jmdict_payload = (
            "<JMdict>"
            "<entry>"
            "<k_ele><keb>為る</keb></k_ele>"
            "<r_ele><reb>する</reb></r_ele>"
            "<sense>"
            "<gloss xml:lang='eng'>to admire</gloss>"
            "<gloss xml:lang='eng'>to carry out</gloss>"
            "<gloss xml:lang='eng'>to value</gloss>"
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
                    targets=("為る",),
                    language_pair="en-ja",
                    jmdict_path=path,
                    include_variants=False,
                    word_packages_by_target={
                        "為る": {
                            "version": 1,
                            "language_tag": "ja",
                            "surface": "為る",
                            "reading": "する",
                            "script_forms": {"kanji": "為る", "kana": "する", "romaji": "suru"},
                            "source": {"provider": "freq-ja-bccwj"},
                        }
                    },
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["admire", "value"])
        self.assertTrue(all(rule.replacement == "為る" for rule in rules))

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

    def test_en_de_adapter_strips_infinitive_marker_before_single_word_filter(self) -> None:
        tei_payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>machen</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="en">to admire</quote></cit>
          <cit type="trans"><quote xml:lang="en">to carry out</quote></cit>
          <cit type="trans"><quote xml:lang="en">to value</quote></cit>
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
                    targets=("machen",),
                    language_pair="en-de",
                    freedict_de_en_path=path,
                    include_variants=False,
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["admire", "value"])
        self.assertTrue(all(rule.replacement == "machen" for rule in rules))

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

    def test_es_en_dispatches_reverse_check_config(self) -> None:
        reverse_check = ReverseCheckScoringConfig(
            enabled=True,
            match_bonus=0.21,
            near_bonus=0.11,
            near_rank_max=2,
            miss_penalty=0.18,
        )
        with patch(
            "lexishift_core.rulegen.adapters.generate_es_en_results",
            return_value=[
                SimpleNamespace(rule=VocabRule(source_phrase="casa", replacement="house"))
            ],
        ) as generate:
            run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="es-en",
                    targets=("house",),
                    language_pair="es-en",
                    freedict_de_en_path=Path("/tmp/eng-spa.tei"),
                    reverse_check=reverse_check,
                )
            )
        generate.assert_called_once()
        args, kwargs = generate.call_args
        _ = args
        self.assertTrue(kwargs["config"].reverse_check.enabled)
        self.assertAlmostEqual(kwargs["config"].reverse_check.match_bonus, 0.21, places=6)
        self.assertAlmostEqual(kwargs["config"].reverse_check.near_bonus, 0.11, places=6)
        self.assertEqual(kwargs["config"].reverse_check.near_rank_max, 2)
        self.assertAlmostEqual(kwargs["config"].reverse_check.miss_penalty, 0.18, places=6)

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
