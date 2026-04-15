from __future__ import annotations

import gzip
import json
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
from lexishift_core.resources.kaikki_sqlite import convert_kaikki_glosses_to_sqlite  # noqa: E402
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
    build_en_es_rulegen_config,
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

    def test_en_ja_requires_translation_dictionary_path(self) -> None:
        with self.assertRaises(ValueError):
            run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-ja",
                    targets=("語",),
                    language_pair="en-ja",
                    jmdict_path=None,
                    translation_dict_path=None,
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
                    translation_dict_path=Path("/tmp/JMdict_e"),
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

    def test_en_ja_dispatches_wiktionary_source_metadata_for_kaikki_sqlite(self) -> None:
        with patch(
            "lexishift_core.rulegen.adapters.generate_en_ja_results",
            return_value=[SimpleNamespace(rule=VocabRule(source_phrase="house", replacement="家"))],
        ) as generate:
            run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-ja",
                    targets=("家",),
                    language_pair="en-ja",
                    translation_dict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                )
            )
        generate.assert_called_once()
        _, kwargs = generate.call_args
        self.assertEqual(kwargs["config"].source_dict_id, "wiktionary_ja_en")
        self.assertEqual(kwargs["config"].dictionary_pos_source_profile, "wiktionary")

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
                    kaikki_policy_risk_family_demotions=(
                        ("communication_network", 0.33),
                        ("music", 0.41),
                    ),
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
        self.assertEqual(
            kwargs["config"].kaikki_policy.risk_family_demotions,
            (("communication_network", 0.33), ("music", 0.41)),
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

    def test_build_en_es_rulegen_config_preserves_request_metadata(self) -> None:
        compiled_resources = EnEsCompiledResources(
            records_by_target={"casa": [FreedictGlossRecord(translation="house", pos_raw="noun")]},
        )
        request = RulegenAdapterRequest(
            pair="en-es",
            targets=("casa",),
            language_pair="en-es",
            freedict_de_en_path=Path("/tmp/wiktionary-es-en.sqlite"),
            freedict_reverse_path=Path("/tmp/wiktionary-en-es.sqlite"),
            compiled_pair_context=compiled_resources,
            kaikki_policy_live_demotion=True,
            kaikki_policy_risk_families=("math_geometry",),
            kaikki_policy_risk_family_demotions=(("music", 0.45),),
            kaikki_policy_late_sense_penalty=0.12,
        )

        config = build_en_es_rulegen_config(request)

        self.assertEqual(config.source_dict_id, "wiktionary_es_en")
        self.assertEqual(config.reverse_source_dict_id, "wiktionary_en_es")
        self.assertEqual(config.dictionary_pos_source_profile, "wiktionary")
        self.assertIs(config.compiled_resources, compiled_resources)
        self.assertTrue(config.kaikki_policy.enable_live_demotion)
        self.assertEqual(config.kaikki_policy.risk_families, ("math_geometry",))
        self.assertEqual(config.kaikki_policy.risk_family_demotions, (("music", 0.45),))
        self.assertAlmostEqual(
            config.kaikki_policy.late_sense_clean_earlier_competition_penalty,
            0.12,
            places=6,
        )

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

    def test_en_ja_adapter_generates_rules_from_kaikki_sqlite(self) -> None:
        records = [
            {
                "word": "家",
                "lang": "Japanese",
                "lang_code": "ja",
                "pos": "noun",
                "senses": [
                    {"glosses": ["house", "home"]},
                ],
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "raw-wiktextract-data-ja-en.jsonl.gz"
            output_path = Path(tmp) / "wiktionary-ja-en.sqlite"
            with gzip.open(input_path, "wt", encoding="utf-8") as handle:
                for record in records:
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            convert_kaikki_glosses_to_sqlite(
                input_path,
                output_path,
                source_lang_code="ja",
                gloss_language="en",
                source_provider="wiktionary-ja-en",
                source_dump="enwiktionary",
                overwrite=True,
            )
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-ja",
                    targets=("家",),
                    language_pair="en-ja",
                    jmdict_path=output_path,
                    include_variants=False,
                    word_packages_by_target={
                        "家": {
                            "version": 1,
                            "language_tag": "ja",
                            "surface": "家",
                            "reading": "いえ",
                            "script_forms": {"kanji": "家", "kana": "いえ", "romaji": "ie"},
                            "source": {"provider": "freq-ja-bccwj"},
                        }
                    },
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["house", "home"])
        self.assertTrue(all(rule.replacement == "家" for rule in rules))

    def test_en_ja_adapter_normalizes_kaikki_gloss_fragments_into_single_word_rules(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("家", "学生", "言葉", "先生", "様"),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                gloss_records_by_target={
                    "家": [FreedictGlossRecord(translation="a house", pos_raw="noun")],
                    "学生": [
                        FreedictGlossRecord(
                            translation="a student (usually of a university, sometimes of a high school)",
                            pos_raw="noun",
                        )
                    ],
                    "言葉": [FreedictGlossRecord(translation="a word, a term", pos_raw="noun")],
                    "先生": [
                        FreedictGlossRecord(
                            translation="a teacher or a professor",
                            pos_raw="noun",
                        )
                    ],
                    "様": [
                        FreedictGlossRecord(
                            translation="certain form or way",
                            pos_raw="noun",
                        )
                    ],
                },
                word_packages_by_target={
                    "家": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "家",
                        "reading": "いえ",
                        "script_forms": {"kanji": "家", "kana": "いえ", "romaji": "ie"},
                        "source": {"provider": "freq-ja-bccwj"},
                    },
                    "学生": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "学生",
                        "reading": "がくせい",
                        "script_forms": {"kanji": "学生", "kana": "がくせい", "romaji": "gakusei"},
                        "source": {"provider": "freq-ja-bccwj"},
                    },
                    "言葉": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "言葉",
                        "reading": "ことば",
                        "script_forms": {"kanji": "言葉", "kana": "ことば", "romaji": "kotoba"},
                        "source": {"provider": "freq-ja-bccwj"},
                    },
                    "先生": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "先生",
                        "reading": "せんせい",
                        "script_forms": {"kanji": "先生", "kana": "せんせい", "romaji": "sensei"},
                        "source": {"provider": "freq-ja-bccwj"},
                    },
                    "様": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "様",
                        "reading": "よう",
                        "script_forms": {"kanji": "様", "kana": "よう", "romaji": "you"},
                        "source": {"provider": "freq-ja-bccwj"},
                    },
                },
            )
        )
        rules_by_target = {
            target: [rule.source_phrase for rule in rules if rule.replacement == target]
            for target in ("家", "学生", "言葉", "先生", "様")
        }
        self.assertEqual(rules_by_target["家"], ["house"])
        self.assertEqual(rules_by_target["学生"], ["student"])
        self.assertEqual(rules_by_target["言葉"], ["word", "term"])
        self.assertEqual(rules_by_target["先生"], ["teacher", "professor"])
        self.assertEqual(rules_by_target["様"], ["form", "way"])

    def test_en_ja_adapter_demotes_non_primary_honorific_glosses_when_teacher_terms_exist(
        self,
    ) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("先生",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=2,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "先生": [
                        FreedictGlossRecord(translation="an elder", pos_raw="noun"),
                        FreedictGlossRecord(translation="a scholar", pos_raw="noun"),
                        FreedictGlossRecord(
                            translation="a teacher or a professor",
                            pos_raw="noun",
                        ),
                    ]
                },
                word_packages_by_target={
                    "先生": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "先生",
                        "reading": "せんせい",
                        "script_forms": {"kanji": "先生", "kana": "せんせい", "romaji": "sensei"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["teacher"])

    def test_en_ja_adapter_prefers_kaikki_rows_with_matching_readings(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("道",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                gloss_records_by_target={
                    "道": [
                        FreedictGlossRecord(
                            translation="road; way (みち)",
                            pos_raw="noun",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "道",
                                        "ruby": ["['道', 'みち']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                        FreedictGlossRecord(
                            translation="to speak (いう)",
                            pos_raw="verb",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "道",
                                        "ruby": ["['道', 'いう']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                    ]
                },
                word_packages_by_target={
                    "道": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "道",
                        "reading": "みち",
                        "script_forms": {"kanji": "道", "kana": "みち", "romaji": "michi"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["road", "way"])

    def test_en_ja_adapter_combines_split_ruby_segments_for_matching_readings(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("上手",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=2,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "上手": [
                        FreedictGlossRecord(
                            translation="skillful, dexterous",
                            pos_raw="adj",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "上手 ^-na",
                                        "ruby": ["['上', 'じょう']", "['手', 'ず']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                        FreedictGlossRecord(
                            translation="superior, better",
                            pos_raw="adj",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "上手 ^-na",
                                        "ruby": ["['上', 'うわ']", "['手', 'て']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                    ]
                },
                word_packages_by_target={
                    "上手": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "上手",
                        "reading": "うわて",
                        "script_forms": {"kanji": "上手", "kana": "うわて", "romaji": "uwate"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["superior"])

    def test_en_ja_adapter_drops_unresolved_character_glosses_when_reading_matches_content(
        self,
    ) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("上",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=2,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "上": [
                        FreedictGlossRecord(translation="earlier", pos_raw="character"),
                        FreedictGlossRecord(
                            translation="the above",
                            pos_raw="noun",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "上 ^",
                                        "ruby": ["['上', 'うえ']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                        FreedictGlossRecord(
                            translation="the top",
                            pos_raw="noun",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "上 ^",
                                        "ruby": ["['上', 'うえ']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                    ]
                },
                word_packages_by_target={
                    "上": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "上",
                        "reading": "うえ",
                        "script_forms": {"kanji": "上", "kana": "うえ", "romaji": "ue"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["above"])

    def test_en_ja_adapter_recovers_presence_for_hitoke(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("人気",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=1,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "人気": [
                        FreedictGlossRecord(
                            translation="popularity",
                            pos_raw="noun",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "人気",
                                        "ruby": ["['人', 'にん']", "['気', 'き']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                        FreedictGlossRecord(
                            translation="presence of people",
                            pos_raw="noun",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "人気",
                                        "ruby": ["['人', 'ひと']", "['気', 'け']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                    ]
                },
                word_packages_by_target={
                    "人気": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "人気",
                        "reading": "ひとけ",
                        "script_forms": {"kanji": "人気", "kana": "ひとけ", "romaji": "hitoke"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["presence"])

    def test_en_ja_adapter_splits_five_part_adjective_lists_for_heta(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("下手",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=1,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "下手": [
                        FreedictGlossRecord(
                            translation="unskilled, bad at, poor at, weak at, incompetent",
                            pos_raw="adj",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "下手",
                                        "ruby": ["['下手', 'へた']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                        FreedictGlossRecord(
                            translation="superficial, halfhearted, half-assed, careless",
                            pos_raw="adj",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "下手",
                                        "ruby": ["['下手', 'へた']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                    ]
                },
                word_packages_by_target={
                    "下手": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "下手",
                        "reading": "へた",
                        "script_forms": {"kanji": "下手", "kana": "へた", "romaji": "heta"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["unskilled"])

    def test_en_ja_adapter_recovers_spicy_from_spicy_hot_gloss(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("辛い",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=1,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "辛い": [
                        FreedictGlossRecord(
                            translation="spicy hot, salty, bitter, not sweet, harsh",
                            pos_raw="adj",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "辛い",
                                        "ruby": ["['辛', 'から']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                        FreedictGlossRecord(
                            translation="painful",
                            pos_raw="adj",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "辛い",
                                        "ruby": ["['辛', 'つら']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                    ]
                },
                word_packages_by_target={
                    "辛い": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "辛い",
                        "reading": "からい",
                        "script_forms": {"kanji": "辛い", "kana": "からい", "romaji": "karai"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["spicy"])

    def test_en_ja_adapter_handles_kaikki_family_competition_for_new_benchmark_cases(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("場合", "事業", "国", "気", "話", "全て", "県"),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=True,
                max_definitions_per_target=1,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "場合": [
                        FreedictGlossRecord(translation="if, when", pos_raw="noun"),
                        FreedictGlossRecord(
                            translation="case, occasion, circumstances, situation",
                            pos_raw="noun",
                        ),
                    ],
                    "事業": [
                        FreedictGlossRecord(translation="project, work", pos_raw="noun"),
                        FreedictGlossRecord(
                            translation="an enterprise, a business",
                            pos_raw="noun",
                        ),
                    ],
                    "国": [
                        FreedictGlossRecord(translation="a land, a large place", pos_raw="noun"),
                        FreedictGlossRecord(
                            translation="a country in general, a region",
                            pos_raw="noun",
                        ),
                        FreedictGlossRecord(
                            translation="a country as in a nation, a state",
                            pos_raw="noun",
                        ),
                        FreedictGlossRecord(
                            translation="the office of emperor, the crown; affairs of state",
                            pos_raw="noun",
                        ),
                        FreedictGlossRecord(
                            translation="one's birthplace, where one is from, one's home",
                            pos_raw="noun",
                        ),
                    ],
                    "気": [
                        FreedictGlossRecord(translation="breath", pos_raw="character"),
                        FreedictGlossRecord(translation="gas", pos_raw="character"),
                        FreedictGlossRecord(translation="atmosphere", pos_raw="character"),
                        FreedictGlossRecord(translation="spirit", pos_raw="character"),
                        FreedictGlossRecord(translation="feeling, mood", pos_raw="character"),
                        FreedictGlossRecord(translation="spirit, mood", pos_raw="noun"),
                        FreedictGlossRecord(
                            translation="inclination, will, mood, urge",
                            pos_raw="noun",
                        ),
                        FreedictGlossRecord(translation="qi", pos_raw="noun"),
                        FreedictGlossRecord(translation="chi", pos_raw="noun"),
                        FreedictGlossRecord(translation="ki", pos_raw="noun"),
                    ],
                    "話": [
                        FreedictGlossRecord(
                            translation="talk, conversation",
                            pos_raw="character",
                        ),
                        FreedictGlossRecord(
                            translation="talking; speaking; speech; conversation",
                            pos_raw="noun",
                        ),
                        FreedictGlossRecord(
                            translation="story; tale; narrative",
                            pos_raw="noun",
                        ),
                        FreedictGlossRecord(
                            translation="a topic; a subject; that which is spoken about",
                            pos_raw="noun",
                        ),
                    ],
                    "全て": [
                        FreedictGlossRecord(
                            translation="entirely, completely; all",
                            pos_raw="adv",
                        ),
                        FreedictGlossRecord(
                            translation="in general, approximately",
                            pos_raw="adv",
                        ),
                        FreedictGlossRecord(
                            translation="everything, all",
                            pos_raw="noun",
                        ),
                    ],
                    "県": [
                        FreedictGlossRecord(
                            translation=(
                                "a type of administrative district, including 43 of the 47 "
                                "prefectures of modern Japan, Chinese counties, French "
                                "departments, etc."
                            ),
                            pos_raw="noun",
                        ),
                    ],
                },
                word_packages_by_target={
                    "場合": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "場合",
                        "reading": "ばあい",
                        "script_forms": {"kanji": "場合", "kana": "ばあい", "romaji": "baai"},
                        "source": {"provider": "freq-ja-bccwj"},
                    },
                    "事業": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "事業",
                        "reading": "じぎょう",
                        "script_forms": {"kanji": "事業", "kana": "じぎょう", "romaji": "jigyou"},
                        "source": {"provider": "freq-ja-bccwj"},
                    },
                    "国": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "国",
                        "reading": "くに",
                        "script_forms": {"kanji": "国", "kana": "くに", "romaji": "kuni"},
                        "source": {"provider": "freq-ja-bccwj"},
                    },
                    "気": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "気",
                        "reading": "き",
                        "script_forms": {"kanji": "気", "kana": "き", "romaji": "ki"},
                        "source": {"provider": "freq-ja-bccwj"},
                    },
                    "話": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "話",
                        "reading": "はなし",
                        "script_forms": {"kanji": "話", "kana": "はなし", "romaji": "hanashi"},
                        "source": {"provider": "freq-ja-bccwj"},
                    },
                    "全て": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "全て",
                        "reading": "すべて",
                        "script_forms": {"kanji": "全て", "kana": "すべて", "romaji": "subete"},
                        "source": {"provider": "freq-ja-bccwj"},
                    },
                    "県": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "県",
                        "reading": "けん",
                        "script_forms": {"kanji": "県", "kana": "けん", "romaji": "ken"},
                        "source": {"provider": "freq-ja-bccwj"},
                    },
                },
            )
        )
        by_target = {rule.replacement: rule.source_phrase for rule in rules}
        self.assertEqual(by_target["場合"], "case")
        self.assertIn(by_target["事業"], {"business", "enterprise"})
        self.assertEqual(by_target["国"], "country")
        self.assertEqual(by_target["気"], "spirit")
        self.assertIn(by_target["話"], {"conversation", "talk"})
        self.assertEqual(by_target["全て"], "all")
        self.assertEqual(by_target["県"], "prefecture")

    def test_en_ja_adapter_resolves_kana_target_via_matching_reading_index(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("まだ",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=1,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "未だ": [
                        FreedictGlossRecord(
                            translation="not yet, still not, never yet",
                            pos_raw="adv",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "未だ",
                                        "ruby": ["['未', 'ま']", "['だ', 'だ']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                        FreedictGlossRecord(
                            translation="still, continuing to the present",
                            pos_raw="adv",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "未だ",
                                        "ruby": ["['未', 'ま']", "['だ', 'だ']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                    ]
                },
                word_packages_by_target={
                    "まだ": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "まだ",
                        "reading": "まだ",
                        "script_forms": {"kana": "まだ", "romaji": "mada"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["still"])

    def test_en_ja_adapter_resolves_kana_target_via_matching_romaji_alias(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("まだ",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=1,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "未だ": [
                        FreedictGlossRecord(
                            translation="yet, still",
                            pos_raw="adv",
                            metadata={
                                "entry_forms": [
                                    {"form": "未だ", "tags": ["canonical"]},
                                    {"form": "mada", "tags": ["romanization"]},
                                ]
                            },
                        ),
                    ]
                },
                word_packages_by_target={
                    "まだ": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "まだ",
                        "reading": "まだ",
                        "script_forms": {"kana": "まだ", "romaji": "mada"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["yet"])

    def test_en_ja_adapter_recovers_ability_head_for_dekiru(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("できる",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=1,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "できる": [
                        FreedictGlossRecord(
                            translation="to be able to do",
                            pos_raw="verb",
                        )
                    ]
                },
                word_packages_by_target={
                    "できる": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "できる",
                        "reading": "できる",
                        "script_forms": {"kana": "できる", "romaji": "dekiru"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["able"])

    def test_en_ja_adapter_recovers_quantity_head_for_ooi(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("多い",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=1,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "多い": [
                        FreedictGlossRecord(
                            translation=(
                                "there are many, there is much, there are numerous, "
                                "there is an abundance"
                            ),
                            pos_raw="adj",
                        )
                    ]
                },
                word_packages_by_target={
                    "多い": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "多い",
                        "reading": "おおい",
                        "script_forms": {"kanji": "多い", "kana": "おおい", "romaji": "ooi"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["many"])

    def test_en_ja_adapter_demotes_inaudible_when_quiet_state_terms_exist(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("静か",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=2,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "静か": [
                        FreedictGlossRecord(translation="inaudible, quiet, silent", pos_raw="adj"),
                        FreedictGlossRecord(translation="calm, tranquil", pos_raw="adj"),
                    ]
                },
                word_packages_by_target={
                    "静か": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "静か",
                        "reading": "しずか",
                        "script_forms": {"kanji": "静か", "kana": "しずか", "romaji": "shizuka"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["quiet"])

    def test_en_ja_adapter_demotes_shape_senses_when_immediacy_adverbs_exist(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("すぐ",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=2,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "すぐ": [
                        FreedictGlossRecord(translation="straight, not bent", pos_raw="adj"),
                        FreedictGlossRecord(
                            translation="soon, immediately, right away", pos_raw="adv"
                        ),
                    ]
                },
                word_packages_by_target={
                    "すぐ": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "すぐ",
                        "reading": "すぐ",
                        "script_forms": {"kana": "すぐ", "romaji": "sugu"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["soon"])

    def test_en_ja_adapter_prefers_practical_evaluatives_over_structural_competitors(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("結構",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=2,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "結構": [
                        FreedictGlossRecord(
                            translation="assembly, composition, plan, scheme",
                            pos_raw="noun",
                        ),
                        FreedictGlossRecord(
                            translation="splendid, wonderful",
                            pos_raw="adj",
                        ),
                        FreedictGlossRecord(
                            translation="fine, sufficient, tolerable",
                            pos_raw="adj",
                        ),
                    ]
                },
                word_packages_by_target={
                    "結構": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "結構",
                        "reading": "けっこう",
                        "script_forms": {"kanji": "結構", "kana": "けっこう", "romaji": "kekkou"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["fine"])

    def test_en_ja_adapter_recovers_day_head_for_ichinichi(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("一日",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=2,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "一日": [
                        FreedictGlossRecord(translation="one day, 24 hours", pos_raw="noun"),
                        FreedictGlossRecord(
                            translation="the daytime, the period from dawn until dusk",
                            pos_raw="noun",
                        ),
                    ]
                },
                word_packages_by_target={
                    "一日": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "一日",
                        "reading": "いちにち",
                        "script_forms": {
                            "kanji": "一日",
                            "kana": "いちにち",
                            "romaji": "ichinichi",
                        },
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["day"])

    def test_en_ja_adapter_demotes_categorical_adverbs_when_certainty_terms_exist(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("必ず",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=2,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "必ず": [
                        FreedictGlossRecord(
                            translation="absolutely, categorically, certainly, definitely, surely",
                            pos_raw="adv",
                        ),
                        FreedictGlossRecord(
                            translation="inevitably, invariably, without fail, necessarily, always",
                            pos_raw="adv",
                        ),
                    ]
                },
                word_packages_by_target={
                    "必ず": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "必ず",
                        "reading": "かならず",
                        "script_forms": {"kanji": "必ず", "kana": "かならず", "romaji": "kanarazu"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["certainly"])

    def test_en_ja_adapter_demotes_direction_noise_when_kata_has_way_senses(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("方",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=1,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "方": [
                        FreedictGlossRecord(translation="direction", pos_raw="character"),
                        FreedictGlossRecord(translation="alternative", pos_raw="character"),
                        FreedictGlossRecord(translation="square", pos_raw="character"),
                        FreedictGlossRecord(
                            translation="way, method",
                            pos_raw="suffix",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "方",
                                        "ruby": ["['方', 'かた']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                    ]
                },
                word_packages_by_target={
                    "方": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "方",
                        "reading": "かた",
                        "script_forms": {"kanji": "方", "kana": "かた", "romaji": "kata"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["way"])

    def test_en_ja_adapter_keeps_japanese_script_unresolved_kaikki_variants(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("様",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                gloss_records_by_target={
                    "様": [
                        FreedictGlossRecord(
                            translation="certain form or way",
                            pos_raw="character",
                            metadata={"entry_forms": [{"form": "樣", "tags": ["kyūjitai"]}]},
                        ),
                        FreedictGlossRecord(
                            translation="way, style, appearance",
                            pos_raw="noun",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "様",
                                        "ruby": ["['様', 'よう']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                        FreedictGlossRecord(
                            translation="noise",
                            pos_raw="noun",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "Second grade kyōiku kanji",
                                        "tags": ["romanization"],
                                    }
                                ]
                            },
                        ),
                    ]
                },
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
        self.assertEqual([rule.source_phrase for rule in rules], ["form", "way", "style"])

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

    def test_en_ja_adapter_falls_back_to_kana_kaikki_entries_for_kanji_targets(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("飲む", "分かる"),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=3,
                max_rules_per_target=2,
                gloss_records_by_target={
                    "のむ": [
                        FreedictGlossRecord(
                            translation="飲む, 呑む: to drink, to gulp, to swallow; to eat (soup)",
                            pos_raw="verb",
                            metadata={
                                "entry_forms": [
                                    {"form": "のむ transitive godan", "tags": ["canonical"]},
                                    {"form": "飲む", "tags": ["alternative", "kanji"]},
                                    {"form": "呑む", "tags": ["alternative", "kanji"]},
                                ]
                            },
                        )
                    ],
                    "わかる": [
                        FreedictGlossRecord(
                            translation=(
                                "分かる, 判る: to understand, to comprehend, to grasp, to know"
                            ),
                            pos_raw="verb",
                            metadata={
                                "entry_forms": [
                                    {"form": "わかる intransitive godan", "tags": ["canonical"]},
                                    {"form": "分かる", "tags": ["alternative", "kanji"]},
                                    {"form": "判る", "tags": ["alternative", "kanji"]},
                                ]
                            },
                        )
                    ],
                },
                word_packages_by_target={
                    "飲む": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "飲む",
                        "reading": "のむ",
                        "script_forms": {"kanji": "飲む", "kana": "のむ", "romaji": "nomu"},
                        "source": {"provider": "freq-ja-bccwj"},
                    },
                    "分かる": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "分かる",
                        "reading": "わかる",
                        "script_forms": {"kanji": "分かる", "kana": "わかる", "romaji": "wakaru"},
                        "source": {"provider": "freq-ja-bccwj"},
                    },
                },
            )
        )
        rules_by_target = {
            target: [rule.source_phrase for rule in rules if rule.replacement == target]
            for target in ("飲む", "分かる")
        }
        self.assertEqual(rules_by_target["飲む"], ["drink", "gulp"])
        self.assertEqual(rules_by_target["分かる"], ["understand", "comprehend"])

    def test_en_ja_adapter_prefers_lexical_book_over_counter_noise(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("本",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=1,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "本": [
                        FreedictGlossRecord(
                            translation=(
                                "long cylindrical things such as glasses of drink, "
                                "pairs of jeans, pens or trains and buses"
                            ),
                            pos_raw="counter",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "本",
                                        "ruby": ["['本', 'ほん']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                        FreedictGlossRecord(
                            translation="a book",
                            pos_raw="noun",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "本",
                                        "ruby": ["['本', 'ほん']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                        FreedictGlossRecord(
                            translation="original, actual, base",
                            pos_raw="prefix",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "本",
                                        "ruby": ["['本', 'ほん']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                    ]
                },
                word_packages_by_target={
                    "本": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "本",
                        "reading": "ほん",
                        "script_forms": {"kanji": "本", "kana": "ほん", "romaji": "hon"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["book"])

    def test_en_ja_adapter_avoids_structural_character_noise_when_lexical_sense_exists(
        self,
    ) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("犬",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=2,
                max_rules_per_target=2,
                gloss_records_by_target={
                    "犬": [
                        FreedictGlossRecord(
                            translation="the dog radical (いぬ)",
                            pos_raw="character",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "犬",
                                        "ruby": ["['犬', 'いぬ']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                        FreedictGlossRecord(
                            translation="a dog",
                            pos_raw="character",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "First grade kyōiku kanji",
                                        "tags": ["romanization"],
                                    }
                                ]
                            },
                        ),
                        FreedictGlossRecord(
                            translation="dog, canine",
                            pos_raw="noun",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "犬",
                                        "ruby": ["['犬', 'いぬ']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                    ]
                },
                word_packages_by_target={
                    "犬": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "犬",
                        "reading": "いぬ",
                        "script_forms": {"kanji": "犬", "kana": "いぬ", "romaji": "inu"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["dog", "canine"])

    def test_en_ja_adapter_keeps_plain_character_gloss_when_it_is_the_best_lexical_match(
        self,
    ) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("雪",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=1,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "雪": [
                        FreedictGlossRecord(
                            translation="snow",
                            pos_raw="character",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "Second grade kyōiku kanji",
                                        "tags": ["romanization"],
                                    }
                                ]
                            },
                        ),
                        FreedictGlossRecord(
                            translation="white hair",
                            pos_raw="noun",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "雪",
                                        "ruby": ["['雪', 'ゆき']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                        FreedictGlossRecord(
                            translation="a female given name",
                            pos_raw="name",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "雪",
                                        "ruby": ["['雪', 'ゆき']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        ),
                    ]
                },
                word_packages_by_target={
                    "雪": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "雪",
                        "reading": "ゆき",
                        "script_forms": {"kanji": "雪", "kana": "ゆき", "romaji": "yuki"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["snow"])

    def test_en_ja_adapter_recovers_safe_single_word_verb_heads(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("売る",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=1,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "売る": [
                        FreedictGlossRecord(
                            translation="to sell something (to agree to transfer goods)",
                            pos_raw="verb",
                        ),
                        FreedictGlossRecord(translation="to betray", pos_raw="verb"),
                        FreedictGlossRecord(translation="to agitate", pos_raw="verb"),
                    ]
                },
                word_packages_by_target={
                    "売る": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "売る",
                        "reading": "うる",
                        "script_forms": {"kanji": "売る", "kana": "うる", "romaji": "uru"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["sell"])

    def test_en_ja_adapter_recovers_color_value_from_color_noun_phrase(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("白",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=1,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "白": [
                        FreedictGlossRecord(translation="the color white", pos_raw="noun"),
                        FreedictGlossRecord(translation="innocence", pos_raw="noun"),
                    ]
                },
                word_packages_by_target={
                    "白": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "白",
                        "reading": "しろ",
                        "script_forms": {"kanji": "白", "kana": "しろ", "romaji": "shiro"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["white"])

    def test_en_ja_adapter_recovers_train_from_safe_transport_head_phrase(self) -> None:
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-ja",
                targets=("電車",),
                language_pair="en-ja",
                jmdict_path=Path("/tmp/wiktionary-ja-en.sqlite"),
                include_variants=False,
                max_definitions_per_target=1,
                max_rules_per_target=1,
                gloss_records_by_target={
                    "電車": [
                        FreedictGlossRecord(
                            translation="an electric multiple unit train",
                            pos_raw="noun",
                            metadata={
                                "entry_forms": [
                                    {
                                        "form": "電車",
                                        "ruby": ["['電', 'でん']", "['車', 'しゃ']"],
                                        "tags": ["canonical"],
                                    }
                                ]
                            },
                        )
                    ]
                },
                word_packages_by_target={
                    "電車": {
                        "version": 1,
                        "language_tag": "ja",
                        "surface": "電車",
                        "reading": "でんしゃ",
                        "script_forms": {"kanji": "電車", "kana": "でんしゃ", "romaji": "densha"},
                        "source": {"provider": "freq-ja-bccwj"},
                    }
                },
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["train"])

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
