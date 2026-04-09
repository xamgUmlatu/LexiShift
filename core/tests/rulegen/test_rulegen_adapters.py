from __future__ import annotations

import os
import sqlite3
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
from lexishift_core.replacement.core import RuleMetadata, VocabRule  # noqa: E402
from lexishift_core.rulegen.generation import (  # noqa: E402
    RuleCandidate,
    PosMatchScoringConfig,
    RuleScoreWeights,
    RuleScoringConfig,
)
from lexishift_core.rulegen.pairs.en_de import (  # noqa: E402
    EnDeKaikkiPolicyConfig,
    EnDeRulegenConfig,
    generate_en_de_results,
)

try:  # noqa: E402
    from lexishift_core.rulegen.pairs.en_de import (
        EnDeCompiledResources,
        build_en_de_compiled_resources,
    )
except ImportError:  # pragma: no cover - branch-local capability seam
    EnDeCompiledResources = None
    build_en_de_compiled_resources = None
from lexishift_core.rulegen.pairs.en_es import EnEsCompiledResources  # noqa: E402
from lexishift_core.rulegen.ranking import ReverseCheckScoringConfig  # noqa: E402
from lexishift_core.rulegen.adapters import (  # noqa: E402
    RulegenAdapterRequest,
    build_en_es_rulegen_config,
    run_rules_with_adapter,
)
from lexishift_core.helper.translation_packs import TranslationPackRef  # noqa: E402

_EN_DE_CONFIG_FIELDS = EnDeRulegenConfig.__dataclass_fields__
_EN_DE_SUPPORTS_REPRESENTATIVE_PENALTY = "sense_representative_penalty" in _EN_DE_CONFIG_FIELDS
_EN_DE_SUPPORTS_DEFAULTNESS_COMPETITION = (
    "sense_defaultness_competition_penalty" in _EN_DE_CONFIG_FIELDS
)


class TestRulegenAdapters(unittest.TestCase):
    def test_en_es_adapter_derives_semantic_admission_from_sense_provenance(self) -> None:
        with patch(
            "lexishift_core.rulegen.adapters.generate_en_es_results",
            return_value=[
                SimpleNamespace(
                    candidate=RuleCandidate(
                        source_phrase="account",
                        replacement="cuenta",
                        language_pair="en-es",
                        source_dict="wiktionary_es_en",
                        metadata={
                            "sense_provenance": {
                                "entry_ord": 20,
                                "sense_ord": 1,
                                "gloss_ord": 0,
                            }
                        },
                    ),
                    rule=VocabRule(
                        source_phrase="account",
                        replacement="cuenta",
                        metadata=RuleMetadata(language_pair="en-es"),
                    ),
                    confidence=0.91,
                )
            ],
        ):
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-es",
                    targets=("cuenta",),
                    language_pair="en-es",
                    translation_dict_path=Path("/tmp/wiktionary-es-en.sqlite"),
                )
            )

        self.assertEqual(len(rules), 1)
        metadata = rules[0].metadata
        self.assertIsNotNone(metadata)
        assert metadata is not None
        self.assertEqual(metadata.semantic_admission["schema_version"], 1)
        self.assertEqual(metadata.semantic_admission["status"], "unavailable")
        self.assertEqual(
            metadata.semantic_admission["reason_code"],
            "missing_shadow_selection",
        )
        self.assertIn("sense_id", metadata.semantic_admission)
        self.assertIn("competition_set_id", metadata.semantic_admission)
        self.assertIn("trigger_id", metadata.semantic_admission)

    def test_de_en_adapter_derives_semantic_admission_from_freedict_gloss_index(self) -> None:
        with patch(
            "lexishift_core.rulegen.adapters.generate_de_en_results",
            return_value=[
                SimpleNamespace(
                    candidate=RuleCandidate(
                        source_phrase="Haus",
                        replacement="house",
                        language_pair="de-en",
                        source_dict="freedict_en_de",
                        metadata={"gloss_index": 2},
                    ),
                    rule=VocabRule(
                        source_phrase="Haus",
                        replacement="house",
                        metadata=RuleMetadata(language_pair="de-en"),
                    ),
                    confidence=0.91,
                )
            ],
        ):
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="de-en",
                    targets=("house",),
                    language_pair="de-en",
                    translation_dict_path=Path("/tmp/freedict-en-de.sqlite"),
                )
            )

        self.assertEqual(len(rules), 1)
        metadata = rules[0].metadata
        self.assertIsNotNone(metadata)
        assert metadata is not None
        self.assertEqual(metadata.semantic_admission["schema_version"], 1)
        self.assertEqual(metadata.semantic_admission["status"], "unavailable")
        self.assertEqual(
            metadata.semantic_admission["reason_code"],
            "missing_shadow_selection",
        )
        self.assertIn("sense_id", metadata.semantic_admission)
        self.assertIn("competition_set_id", metadata.semantic_admission)
        self.assertIn("trigger_id", metadata.semantic_admission)

    def test_en_ja_adapter_derives_semantic_admission_from_jmdict_entry_forms(self) -> None:
        with patch(
            "lexishift_core.rulegen.adapters.generate_en_ja_results",
            return_value=[
                SimpleNamespace(
                    candidate=RuleCandidate(
                        source_phrase="time",
                        replacement="時",
                        language_pair="en-ja",
                        source_dict="jmdict",
                        metadata={
                            "word_package": {
                                "version": 1,
                                "language_tag": "ja",
                                "surface": "時",
                                "reading": "とき",
                                "script_forms": {
                                    "kanji": "時",
                                    "kana": "とき",
                                    "romaji": "toki",
                                },
                            }
                        },
                    ),
                    rule=VocabRule(
                        source_phrase="time",
                        replacement="時",
                        metadata=RuleMetadata(language_pair="en-ja"),
                    ),
                    confidence=0.91,
                )
            ],
        ):
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-ja",
                    targets=("時",),
                    language_pair="en-ja",
                    jmdict_path=Path("/tmp/JMdict_e"),
                )
            )

        self.assertEqual(len(rules), 1)
        metadata = rules[0].metadata
        self.assertIsNotNone(metadata)
        assert metadata is not None
        self.assertEqual(metadata.semantic_admission["schema_version"], 1)
        self.assertEqual(metadata.semantic_admission["status"], "unavailable")
        self.assertEqual(
            metadata.semantic_admission["reason_code"],
            "missing_shadow_selection",
        )
        self.assertIn("sense_id", metadata.semantic_admission)
        self.assertIn("competition_set_id", metadata.semantic_admission)
        self.assertIn("trigger_id", metadata.semantic_admission)

    def test_es_en_adapter_derives_semantic_admission_from_freedict_gloss_index(self) -> None:
        with patch(
            "lexishift_core.rulegen.adapters.generate_es_en_results",
            return_value=[
                SimpleNamespace(
                    candidate=RuleCandidate(
                        source_phrase="casa",
                        replacement="house",
                        language_pair="es-en",
                        source_dict="freedict_en_es",
                        metadata={"gloss_index": 1},
                    ),
                    rule=VocabRule(
                        source_phrase="casa",
                        replacement="house",
                        metadata=RuleMetadata(language_pair="es-en"),
                    ),
                    confidence=0.91,
                )
            ],
        ):
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="es-en",
                    targets=("house",),
                    language_pair="es-en",
                    translation_dict_path=Path("/tmp/freedict-en-es.sqlite"),
                )
            )

        self.assertEqual(len(rules), 1)
        metadata = rules[0].metadata
        self.assertIsNotNone(metadata)
        assert metadata is not None
        self.assertEqual(metadata.semantic_admission["schema_version"], 1)
        self.assertEqual(metadata.semantic_admission["status"], "unavailable")
        self.assertEqual(
            metadata.semantic_admission["reason_code"],
            "missing_shadow_selection",
        )
        self.assertIn("sense_id", metadata.semantic_admission)
        self.assertIn("competition_set_id", metadata.semantic_admission)
        self.assertIn("trigger_id", metadata.semantic_admission)

    def test_de_en_requires_translation_dictionary_path(self) -> None:
        with self.assertRaises(ValueError):
            run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="de-en",
                    targets=("house",),
                    language_pair="de-en",
                )
            )

    def test_de_en_dispatches_to_freedict_generator(self) -> None:
        with patch(
            "lexishift_core.rulegen.adapters.generate_de_en_results",
            return_value=[
                SimpleNamespace(rule=VocabRule(source_phrase="Haus", replacement="house"))
            ],
        ) as generate:
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="de-en",
                    targets=("house",),
                    language_pair="de-en",
                    translation_dict_path=Path("/tmp/eng-deu.tei"),
                )
            )
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].source_phrase, "Haus")
        self.assertEqual(rules[0].replacement, "house")
        generate.assert_called_once()

    def test_de_en_adapter_generates_rules_from_freedict_tei(self) -> None:
        tei_payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>house</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="de">Haus</quote></cit>
          <cit type="trans"><quote xml:lang="de">Heim</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "eng-deu.tei"
            path.write_text(tei_payload, encoding="utf-8")
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="de-en",
                    targets=("house",),
                    language_pair="de-en",
                    translation_dict_path=path,
                )
            )
        sources = sorted({rule.source_phrase for rule in rules})
        self.assertIn("haus", sources)
        self.assertIn("heim", sources)
        self.assertTrue(all(rule.replacement == "house" for rule in rules))

    def test_de_en_adapter_allows_umlaut_source_candidates(self) -> None:
        tei_payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>girl</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="de">Mädchen</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "eng-deu.tei"
            path.write_text(tei_payload, encoding="utf-8")
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="de-en",
                    targets=("girl",),
                    language_pair="de-en",
                    translation_dict_path=path,
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["mädchen"])

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

    def test_en_de_requires_translation_dict_path(self) -> None:
        with self.assertRaises(ValueError):
            run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Haus",),
                    language_pair="en-de",
                    translation_dict_path=None,
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
                    translation_dict_path=Path("/tmp/deu-eng.tei"),
                )
            )
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].source_phrase, "house")
        self.assertEqual(rules[0].replacement, "Haus")
        generate.assert_called_once()

    def test_en_de_dispatches_with_generic_translation_dict_path(self) -> None:
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
                    translation_dict_path=Path("/tmp/deu-eng.tei"),
                )
            )
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].source_phrase, "house")
        self.assertEqual(rules[0].replacement, "Haus")
        generate.assert_called_once()

    def test_en_de_adapter_infers_wiktionary_profile_from_translation_path(self) -> None:
        with patch(
            "lexishift_core.rulegen.adapters.generate_en_de_results",
            return_value=[
                SimpleNamespace(rule=VocabRule(source_phrase="house", replacement="Haus"))
            ],
        ) as generate:
            run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Haus",),
                    language_pair="en-de",
                    translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                    kaikki_policy_register_demotion=True,
                    kaikki_policy_live_demotion=True,
                    kaikki_policy_risk_families=("government_law",),
                    kaikki_policy_late_sense_penalty=0.2,
                )
            )
        generate.assert_called_once()
        _, kwargs = generate.call_args
        config = kwargs["config"]
        self.assertEqual(config.source_dict_id, "wiktionary_de_en")
        self.assertEqual(config.dictionary_pos_source_profile, "wiktionary")
        self.assertTrue(config.kaikki_policy.enable_register_demotion)
        self.assertTrue(config.kaikki_policy.enable_live_demotion)
        self.assertEqual(config.kaikki_policy.risk_families, ("government_law",))
        self.assertAlmostEqual(
            config.kaikki_policy.late_sense_clean_earlier_competition_penalty,
            0.2,
            places=6,
        )

    def test_en_de_dispatches_reverse_check_and_reverse_metadata(self) -> None:
        reverse_check = ReverseCheckScoringConfig(
            enabled=True,
            match_bonus=0.23,
            near_bonus=0.11,
            near_rank_max=1,
            miss_penalty=0.19,
            exact_hit_specificity_bonus=0.13,
        )
        with patch(
            "lexishift_core.rulegen.adapters.generate_en_de_results",
            return_value=[
                SimpleNamespace(rule=VocabRule(source_phrase="house", replacement="Haus"))
            ],
        ) as generate:
            run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Haus",),
                    language_pair="en-de",
                    translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                    reverse_translation_dict_path=Path("/tmp/wiktionary-en-de.sqlite"),
                    reverse_check=reverse_check,
                )
            )
        generate.assert_called_once()
        _, kwargs = generate.call_args
        config = kwargs["config"]
        self.assertEqual(config.reverse_freedict_en_de_path, Path("/tmp/wiktionary-en-de.sqlite"))
        self.assertEqual(config.reverse_source_dict_id, "wiktionary_en_de")
        self.assertTrue(config.reverse_check.enabled)
        self.assertAlmostEqual(config.reverse_check.match_bonus, 0.23, places=6)
        self.assertAlmostEqual(config.reverse_check.near_bonus, 0.11, places=6)
        self.assertEqual(config.reverse_check.near_rank_max, 1)
        self.assertAlmostEqual(config.reverse_check.miss_penalty, 0.19, places=6)
        self.assertAlmostEqual(
            config.reverse_check.exact_hit_specificity_bonus,
            0.13,
            places=6,
        )

    def test_en_de_dispatches_compiled_resources(self) -> None:
        if EnDeCompiledResources is None:
            self.skipTest("en-de compiled resources are not available on this branch")
        compiled_resources = EnDeCompiledResources(
            records_by_target={"Haus": [FreedictGlossRecord(translation="house", pos_raw="noun")]},
            reverse_records_by_source={
                "house": [FreedictGlossRecord(translation="Haus", pos_raw="noun")]
            },
        )
        with patch(
            "lexishift_core.rulegen.adapters.generate_en_de_results",
            return_value=[
                SimpleNamespace(rule=VocabRule(source_phrase="house", replacement="Haus"))
            ],
        ) as generate:
            run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Haus",),
                    language_pair="en-de",
                    translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                    compiled_pair_context=compiled_resources,
                )
            )
        generate.assert_called_once()
        _, kwargs = generate.call_args
        self.assertIs(kwargs["config"].compiled_resources, compiled_resources)

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
                    translation_dict_path=path,
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
                    translation_dict_path=None,
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
                    translation_dict_path=Path("/tmp/spa-eng.tei"),
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
                    translation_dict_path=Path("/tmp/wiktionary-es-en.sqlite"),
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
                    translation_dict_path=Path("/tmp/wiktionary-es-en.sqlite"),
                    reverse_translation_dict_path=Path("/tmp/wiktionary-en-es.sqlite"),
                )
            )
        generate.assert_called_once()
        args, kwargs = generate.call_args
        _ = args
        self.assertEqual(kwargs["config"].reverse_source_dict_id, "wiktionary_en_es")

    def test_en_es_dispatches_with_generic_translation_paths(self) -> None:
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
                    translation_dict_path=Path("/tmp/wiktionary-es-en.sqlite"),
                    reverse_translation_dict_path=Path("/tmp/wiktionary-en-es.sqlite"),
                )
            )
        generate.assert_called_once()
        _, kwargs = generate.call_args
        self.assertEqual(kwargs["config"].source_dict_id, "wiktionary_es_en")
        self.assertEqual(kwargs["config"].reverse_source_dict_id, "wiktionary_en_es")

    def test_en_es_config_prefers_explicit_translation_pack_metadata(self) -> None:
        config = build_en_es_rulegen_config(
            RulegenAdapterRequest(
                pair="en-es",
                targets=("casa",),
                language_pair="en-es",
                translation_pack=TranslationPackRef(
                    pair="en-es",
                    direction="forward",
                    path=Path("/tmp/custom-es-en.sqlite"),
                    provider="wiktionary",
                    pack_id="wiktionary_es_en",
                    pos_source_profile="wiktionary",
                ),
                reverse_translation_pack=TranslationPackRef(
                    pair="en-es",
                    direction="reverse",
                    path=Path("/tmp/custom-en-es.sqlite"),
                    provider="wiktionary",
                    pack_id="wiktionary_en_es",
                    pos_source_profile="wiktionary",
                ),
            )
        )
        self.assertEqual(config.freedict_es_en_path, Path("/tmp/custom-es-en.sqlite"))
        self.assertEqual(config.reverse_freedict_en_es_path, Path("/tmp/custom-en-es.sqlite"))
        self.assertEqual(config.source_dict_id, "wiktionary_es_en")
        self.assertEqual(config.reverse_source_dict_id, "wiktionary_en_es")
        self.assertEqual(config.dictionary_pos_source_profile, "wiktionary")

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
                    translation_dict_path=Path("/tmp/spa-eng.tei"),
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
                    translation_dict_path=Path("/tmp/wiktionary-es-en.sqlite"),
                    reverse_translation_dict_path=Path("/tmp/wiktionary-en-es.sqlite"),
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
                    translation_dict_path=Path("/tmp/wiktionary-es-en.sqlite"),
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
            translation_dict_path=Path("/tmp/wiktionary-es-en.sqlite"),
            reverse_translation_dict_path=Path("/tmp/wiktionary-en-es.sqlite"),
            compiled_pair_context=compiled_resources,
            kaikki_policy_live_demotion=True,
            kaikki_policy_risk_families=("math_geometry",),
            kaikki_policy_late_sense_penalty=0.12,
        )

        config = build_en_es_rulegen_config(request)

        self.assertEqual(config.source_dict_id, "wiktionary_es_en")
        self.assertEqual(config.reverse_source_dict_id, "wiktionary_en_es")
        self.assertEqual(config.dictionary_pos_source_profile, "wiktionary")
        self.assertIs(config.compiled_resources, compiled_resources)
        self.assertTrue(config.kaikki_policy.enable_live_demotion)
        self.assertEqual(config.kaikki_policy.risk_families, ("math_geometry",))
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
                    translation_dict_path=path,
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
                    translation_dict_path=path,
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
                    translation_dict_path=path,
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
                    translation_dict_path=path,
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
                    translation_dict_path=path,
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
                    translation_dict_path=path,
                    include_variants=False,
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["house", "home", "dwelling"])
        self.assertTrue(all(rule.replacement == "casa" for rule in rules))

    def test_en_es_adapter_keeps_exact_gloss_terms_by_default(self) -> None:
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
                    translation_dict_path=path,
                    include_variants=False,
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["appearing", "looking", "house"])

    def test_en_es_adapter_demotes_generic_gloss_terms_for_top_k_when_enabled(self) -> None:
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
                    translation_dict_path=path,
                    include_variants=False,
                    enable_exact_gloss_demotions=True,
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
                    translation_dict_path=path,
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

    def test_en_ja_adapter_demotes_generic_gloss_terms_for_top_k_when_enabled(self) -> None:
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
                    enable_exact_gloss_demotions=True,
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

    def test_en_de_adapter_keeps_exact_gloss_terms_by_default(self) -> None:
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
                    translation_dict_path=path,
                    include_variants=False,
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["appearing", "looking", "house"])

    def test_en_de_adapter_demotes_generic_gloss_terms_for_top_k_when_enabled(self) -> None:
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
                    translation_dict_path=path,
                    include_variants=False,
                    enable_exact_gloss_demotions=True,
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["house", "home", "dwelling"])
        self.assertTrue(all(rule.replacement == "haus" for rule in rules))

    def test_en_de_adapter_splits_semicolon_kaikki_gloss_to_recover_single_word_candidate(
        self,
    ) -> None:
        records = {
            "Leben": [
                FreedictGlossRecord(
                    translation="life; being alive",
                    pos_raw="noun",
                    metadata={"sense_tags": ("feminine",)},
                )
            ]
        }
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-de",
                targets=("Leben",),
                language_pair="en-de",
                translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                gloss_records_by_target=records,
                include_variants=False,
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["life"])

    def test_en_de_adapter_splits_kaikki_comma_glosses_and_strips_articles(self) -> None:
        records = {
            "Weg": [
                FreedictGlossRecord(
                    translation="path, trail, track (usually for foot traffic)",
                    pos_raw="noun",
                    metadata={"sense_categories": ("German terms with usage examples",)},
                )
            ],
            "Stuhl": [
                FreedictGlossRecord(
                    translation="a chair (to sit on)",
                    pos_raw="noun",
                    metadata={},
                )
            ],
        }
        weg_rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-de",
                targets=("Weg",),
                language_pair="en-de",
                translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                gloss_records_by_target=records,
                include_variants=False,
            )
        )
        stuhl_rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-de",
                targets=("Stuhl",),
                language_pair="en-de",
                translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                gloss_records_by_target=records,
                include_variants=False,
            )
        )
        self.assertEqual([rule.source_phrase for rule in weg_rules], ["path", "trail", "track"])
        self.assertEqual([rule.source_phrase for rule in stuhl_rules], ["chair"])

    def test_en_de_adapter_extracts_colon_suffixes_and_drops_boilerplate_glosses(self) -> None:
        records = {
            "Ordentlich": [
                FreedictGlossRecord(
                    translation="in good condition: clean; neat; well-kept; developed",
                    pos_raw="adjective",
                    metadata={"sense_tags": ("predicative",)},
                )
            ],
            "Es": [
                FreedictGlossRecord(
                    translation=(
                        "Used to indicate that something exists (often with a certain property "
                        "and/or in a certain location). Usually translated as there is/are or "
                        "there exist(s)"
                    ),
                    pos_raw="particle",
                    metadata={"sense_topics": ("grammar",)},
                )
            ],
        }
        ordentlich_rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-de",
                targets=("Ordentlich",),
                language_pair="en-de",
                translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                gloss_records_by_target=records,
                include_variants=False,
                max_definitions_per_target=4,
            )
        )
        es_rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-de",
                targets=("Es",),
                language_pair="en-de",
                translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                gloss_records_by_target=records,
                include_variants=False,
            )
        )
        self.assertEqual(
            [rule.source_phrase for rule in ordentlich_rules],
            ["clean", "neat", "well-kept", "developed"],
        )
        self.assertEqual(es_rules, [])

    def test_en_de_adapter_splits_simple_slash_variants_and_strips_orphaned_delimiters(
        self,
    ) -> None:
        records = {
            "Polar": [
                FreedictGlossRecord(
                    translation="solid/liquid",
                    pos_raw="adjective",
                    metadata={},
                )
            ],
            "Fragt": [
                FreedictGlossRecord(
                    translation="(second-person singular present of fragen",
                    pos_raw="verb",
                    metadata={"sense_categories": ("German verb forms",)},
                )
            ],
        }
        polar_rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-de",
                targets=("Polar",),
                language_pair="en-de",
                translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                gloss_records_by_target=records,
                include_variants=False,
            )
        )
        fragt_rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-de",
                targets=("Fragt",),
                language_pair="en-de",
                translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                gloss_records_by_target=records,
                include_variants=False,
            )
        )
        self.assertEqual([rule.source_phrase for rule in polar_rules], ["solid", "liquid"])
        self.assertEqual(fragt_rules, [])

    def test_en_de_adapter_trims_head_qualifiers_for_word_and_mouth_glosses(self) -> None:
        records = {
            "Wort": [
                FreedictGlossRecord(
                    translation="word as an isolated unit",
                    pos_raw="noun",
                    metadata={"sense_raw_glosses": ("word as an isolated unit",)},
                ),
                FreedictGlossRecord(
                    translation="utterance, word with context",
                    pos_raw="noun",
                    metadata={"sense_raw_glosses": ("utterance, word with context",)},
                ),
            ],
            "Mund": [
                FreedictGlossRecord(
                    translation="mouth of a person",
                    pos_raw="noun",
                    metadata={},
                )
            ],
        }
        wort_rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-de",
                targets=("Wort",),
                language_pair="en-de",
                translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                gloss_records_by_target=records,
                include_variants=False,
            )
        )
        mund_rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-de",
                targets=("Mund",),
                language_pair="en-de",
                translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                gloss_records_by_target=records,
                include_variants=False,
            )
        )
        self.assertEqual([rule.source_phrase for rule in wort_rules], ["word", "utterance"])
        self.assertEqual([rule.source_phrase for rule in mund_rules], ["mouth"])

    def test_en_de_adapter_demotes_marked_kaikki_senses(self) -> None:
        records = {
            "Mund": [
                FreedictGlossRecord(
                    translation="hand",
                    pos_raw="noun",
                    metadata={"sense_tags": ("obsolete",)},
                ),
                FreedictGlossRecord(
                    translation="mouth of a person",
                    pos_raw="noun",
                    metadata={},
                ),
            ]
        }
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-de",
                targets=("Mund",),
                language_pair="en-de",
                translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                gloss_records_by_target=records,
                include_variants=False,
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["mouth", "hand"])

    def test_en_de_adapter_interleaves_kaikki_sense_groups_when_enabled(self) -> None:
        records = {
            "Zug": [
                FreedictGlossRecord(
                    translation="procession, train",
                    pos_raw="noun",
                    metadata={"entry_ord": 1027, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="pull",
                    pos_raw="noun",
                    metadata={"entry_ord": 1027, "sense_ord": 1, "gloss_ord": 0},
                ),
            ]
        }
        rules = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-de",
                targets=("Zug",),
                language_pair="en-de",
                translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                gloss_records_by_target=records,
                include_variants=False,
                max_definitions_per_target=2,
                interleave_definition_groups=True,
            )
        )
        self.assertEqual([rule.source_phrase for rule in rules], ["procession", "pull", "train"])

    def test_en_de_adapter_uses_source_frequency_prior_when_enabled(self) -> None:
        tei_payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>Haus</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="en">establishment</quote></cit>
          <cit type="trans"><quote xml:lang="en">institution</quote></cit>
          <cit type="trans"><quote xml:lang="en">house</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            path = base / "deu-eng.tei"
            path.write_text(tei_payload, encoding="utf-8")
            freq_db = base / "freq-en-coca.sqlite"
            conn = sqlite3.connect(freq_db)
            try:
                conn.execute("CREATE TABLE frequency (lemma TEXT, core_rank REAL, pmw REAL)")
                conn.executemany(
                    "INSERT INTO frequency (lemma, core_rank, pmw) VALUES (?, ?, ?)",
                    [
                        ("establishment", 800.0, 1.0),
                        ("institution", 700.0, 2.0),
                        ("house", 1.0, 1000.0),
                    ],
                )
                conn.commit()
            finally:
                conn.close()
            without_prior = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Haus",),
                    language_pair="en-de",
                    translation_dict_path=path,
                    include_variants=False,
                )
            )
            with_prior = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Haus",),
                    language_pair="en-de",
                    translation_dict_path=path,
                    include_variants=False,
                    scoring=RuleScoringConfig(weights=RuleScoreWeights(frequency_weight=1.0)),
                    enable_source_frequency_prior=True,
                    source_frequency_db_path=freq_db,
                )
            )
        self.assertEqual(
            [rule.source_phrase for rule in without_prior],
            ["establishment", "institution", "house"],
        )
        self.assertEqual(
            [rule.source_phrase for rule in with_prior],
            ["house", "establishment", "institution"],
        )

    def test_en_de_adapter_reverse_check_promotes_exact_reverse_hit(self) -> None:
        records = {
            "Grund": [
                FreedictGlossRecord(translation="motive", pos_raw="noun"),
                FreedictGlossRecord(translation="reason", pos_raw="noun"),
            ]
        }
        reverse_records = {
            "motive": [FreedictGlossRecord(translation="Beweggrund", pos_raw="noun")],
            "reason": [FreedictGlossRecord(translation="Grund", pos_raw="noun")],
        }
        without_reverse = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-de",
                targets=("Grund",),
                language_pair="en-de",
                translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                gloss_records_by_target=records,
                reverse_gloss_records_by_source=reverse_records,
                include_variants=False,
            )
        )
        with_reverse = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-de",
                targets=("Grund",),
                language_pair="en-de",
                translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                gloss_records_by_target=records,
                reverse_gloss_records_by_source=reverse_records,
                include_variants=False,
                reverse_check=ReverseCheckScoringConfig(
                    enabled=True,
                    match_bonus=0.6,
                    miss_penalty=0.6,
                ),
            )
        )
        self.assertEqual([rule.source_phrase for rule in without_reverse], ["motive", "reason"])
        self.assertEqual([rule.source_phrase for rule in with_reverse], ["reason", "motive"])

    def test_en_de_adapter_prefers_same_sense_representative_when_enabled(self) -> None:
        records = {
            "Zug": [
                FreedictGlossRecord(
                    translation="procession, train",
                    pos_raw="noun",
                    metadata={"entry_ord": 1027, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="pull",
                    pos_raw="noun",
                    metadata={"entry_ord": 1027, "sense_ord": 1, "gloss_ord": 0},
                ),
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            freq_db = base / "freq-en-coca.sqlite"
            conn = sqlite3.connect(freq_db)
            try:
                conn.execute("CREATE TABLE frequency (lemma TEXT, core_rank REAL, pmw REAL)")
                conn.executemany(
                    "INSERT INTO frequency (lemma, core_rank, pmw) VALUES (?, ?, ?)",
                    [
                        ("procession", 1000.0, 1.0),
                        ("train", 10.0, 700.0),
                        ("pull", 100.0, 100.0),
                    ],
                )
                conn.commit()
            finally:
                conn.close()
            without_selection = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Zug",),
                    language_pair="en-de",
                    translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                    gloss_records_by_target=records,
                    include_variants=False,
                    max_definitions_per_target=2,
                    enable_source_frequency_prior=True,
                    source_frequency_db_path=freq_db,
                    scoring=RuleScoringConfig(weights=RuleScoreWeights(frequency_weight=0.0)),
                )
            )
            with_selection = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Zug",),
                    language_pair="en-de",
                    translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                    gloss_records_by_target=records,
                    include_variants=False,
                    max_definitions_per_target=2,
                    enable_source_frequency_prior=True,
                    source_frequency_db_path=freq_db,
                    sense_representative_selection=True,
                    scoring=RuleScoringConfig(weights=RuleScoreWeights(frequency_weight=0.0)),
                )
            )
        self.assertEqual(
            [rule.source_phrase for rule in without_selection],
            ["procession", "train", "pull"],
        )
        self.assertEqual(
            [rule.source_phrase for rule in with_selection],
            ["train", "procession", "pull"],
        )

    def test_en_de_adapter_sense_representative_selection_keeps_direct_gloss_over_trimmed_head(
        self,
    ) -> None:
        records = {
            "Stimme": [
                FreedictGlossRecord(
                    translation="voice (speaking or singing), call of an animal",
                    pos_raw="noun",
                    metadata={"entry_ord": 6622, "sense_ord": 0, "gloss_ord": 0},
                ),
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            freq_db = base / "freq-en-coca.sqlite"
            conn = sqlite3.connect(freq_db)
            try:
                conn.execute("CREATE TABLE frequency (lemma TEXT, core_rank REAL, pmw REAL)")
                conn.executemany(
                    "INSERT INTO frequency (lemma, core_rank, pmw) VALUES (?, ?, ?)",
                    [
                        ("voice", 100.0, 10.0),
                        ("call", 10.0, 500.0),
                    ],
                )
                conn.commit()
            finally:
                conn.close()
            without_selection = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Stimme",),
                    language_pair="en-de",
                    translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                    gloss_records_by_target=records,
                    include_variants=False,
                    max_definitions_per_target=3,
                    max_rules_per_target=1,
                    enable_source_frequency_prior=True,
                    source_frequency_db_path=freq_db,
                )
            )
            with_selection = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Stimme",),
                    language_pair="en-de",
                    translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                    gloss_records_by_target=records,
                    include_variants=False,
                    max_definitions_per_target=3,
                    max_rules_per_target=1,
                    enable_source_frequency_prior=True,
                    source_frequency_db_path=freq_db,
                    sense_representative_selection=True,
                )
            )
        self.assertEqual([rule.source_phrase for rule in without_selection], ["voice"])
        self.assertEqual([rule.source_phrase for rule in with_selection], ["voice"])

    def test_en_de_adapter_demotes_earlier_candidate_when_cleaner_later_competition_exists(
        self,
    ) -> None:
        tei_payload = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <entry>
        <form><orth>Grund</orth></form>
        <sense>
          <cit type="trans"><quote xml:lang="en">motive</quote></cit>
          <cit type="trans"><quote xml:lang="en">motivation</quote></cit>
          <cit type="trans"><quote xml:lang="en">reason</quote></cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            path = base / "deu-eng.tei"
            path.write_text(tei_payload, encoding="utf-8")
            freq_db = base / "freq-en-coca.sqlite"
            conn = sqlite3.connect(freq_db)
            try:
                conn.execute("CREATE TABLE frequency (lemma TEXT, pmw REAL)")
                conn.executemany(
                    "INSERT INTO frequency (lemma, pmw) VALUES (?, ?)",
                    [
                        ("motive", 1.0),
                        ("motivation", 1.0),
                        ("reason", 1000.0),
                    ],
                )
                conn.commit()
            finally:
                conn.close()
            without_competition = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Grund",),
                    language_pair="en-de",
                    translation_dict_path=path,
                    include_variants=False,
                    scoring=RuleScoringConfig(weights=RuleScoreWeights(frequency_weight=0.0)),
                    enable_source_frequency_prior=True,
                    source_frequency_db_path=freq_db,
                )
            )
            with_competition = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Grund",),
                    language_pair="en-de",
                    translation_dict_path=path,
                    include_variants=False,
                    scoring=RuleScoringConfig(weights=RuleScoreWeights(frequency_weight=0.0)),
                    enable_source_frequency_prior=True,
                    source_frequency_db_path=freq_db,
                    cleaner_later_competition_penalty=0.8,
                )
            )
        self.assertEqual(
            [rule.source_phrase for rule in without_competition],
            ["motive", "motivation", "reason"],
        )
        self.assertEqual(
            [rule.source_phrase for rule in with_competition],
            ["reason", "motive", "motivation"],
        )

    @unittest.skipUnless(
        _EN_DE_SUPPORTS_REPRESENTATIVE_PENALTY,
        "Current branch en-de config does not expose representative-penalty tuning.",
    )
    def test_en_de_adapter_cleaner_later_competition_ignores_later_same_sense_non_representative(
        self,
    ) -> None:
        records = {
            "Stimme": [
                FreedictGlossRecord(
                    translation="voice (speaking or singing), call of an animal",
                    pos_raw="noun",
                    metadata={"entry_ord": 6622, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="vote",
                    pos_raw="noun",
                    metadata={"entry_ord": 6622, "sense_ord": 1, "gloss_ord": 0},
                ),
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            freq_db = base / "freq-en-coca.sqlite"
            conn = sqlite3.connect(freq_db)
            try:
                conn.execute("CREATE TABLE frequency (lemma TEXT, pmw REAL)")
                conn.executemany(
                    "INSERT INTO frequency (lemma, pmw) VALUES (?, ?)",
                    [
                        ("voice", 100.0),
                        ("call", 900.0),
                        ("vote", 50.0),
                    ],
                )
                conn.commit()
            finally:
                conn.close()
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Stimme",),
                    language_pair="en-de",
                    translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                    gloss_records_by_target=records,
                    include_variants=False,
                    max_definitions_per_target=3,
                    max_rules_per_target=1,
                    scoring=RuleScoringConfig(weights=RuleScoreWeights(frequency_weight=0.0)),
                    enable_source_frequency_prior=True,
                    source_frequency_db_path=freq_db,
                    sense_representative_selection=True,
                    cleaner_later_competition_penalty=0.8,
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["voice"])

    def test_en_de_adapter_cleaner_later_competition_uses_later_sense_representative(
        self,
    ) -> None:
        records = {
            "Grund": [
                FreedictGlossRecord(
                    translation="ground",
                    pos_raw="noun",
                    metadata={"entry_ord": 2884, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="reason",
                    pos_raw="noun",
                    metadata={"entry_ord": 2884, "sense_ord": 1, "gloss_ord": 0},
                ),
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            freq_db = base / "freq-en-coca.sqlite"
            conn = sqlite3.connect(freq_db)
            try:
                conn.execute("CREATE TABLE frequency (lemma TEXT, pmw REAL)")
                conn.executemany(
                    "INSERT INTO frequency (lemma, pmw) VALUES (?, ?)",
                    [
                        ("ground", 100.0),
                        ("reason", 800.0),
                        ("motive", 10.0),
                    ],
                )
                conn.commit()
            finally:
                conn.close()
            without_competition = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Grund",),
                    language_pair="en-de",
                    translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                    gloss_records_by_target=records,
                    include_variants=False,
                    max_definitions_per_target=3,
                    max_rules_per_target=1,
                    scoring=RuleScoringConfig(weights=RuleScoreWeights(frequency_weight=0.0)),
                    enable_source_frequency_prior=True,
                    source_frequency_db_path=freq_db,
                    sense_representative_selection=True,
                )
            )
            with_competition = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Grund",),
                    language_pair="en-de",
                    translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                    gloss_records_by_target=records,
                    include_variants=False,
                    max_definitions_per_target=3,
                    max_rules_per_target=1,
                    scoring=RuleScoringConfig(weights=RuleScoreWeights(frequency_weight=0.0)),
                    enable_source_frequency_prior=True,
                    source_frequency_db_path=freq_db,
                    sense_representative_selection=True,
                    cleaner_later_competition_penalty=0.8,
                )
            )
        self.assertEqual([rule.source_phrase for rule in without_competition], ["ground"])
        self.assertEqual([rule.source_phrase for rule in with_competition], ["reason"])

    @unittest.skipUnless(
        _EN_DE_SUPPORTS_DEFAULTNESS_COMPETITION,
        "Current branch en-de config does not expose defaultness-competition tuning.",
    )
    def test_en_de_adapter_sense_defaultness_competition_promotes_later_sense(
        self,
    ) -> None:
        records = {
            "Grund": [
                FreedictGlossRecord(
                    translation="ground, land",
                    pos_raw="noun",
                    metadata={"entry_ord": 2884, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="reason",
                    pos_raw="noun",
                    metadata={"entry_ord": 2884, "sense_ord": 1, "gloss_ord": 0},
                ),
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            freq_db = base / "freq-en-coca.sqlite"
            conn = sqlite3.connect(freq_db)
            try:
                conn.execute("CREATE TABLE frequency (lemma TEXT, pmw REAL)")
                conn.executemany(
                    "INSERT INTO frequency (lemma, pmw) VALUES (?, ?)",
                    [
                        ("ground", 120.0),
                        ("land", 110.0),
                        ("reason", 100000.0),
                    ],
                )
                conn.commit()
            finally:
                conn.close()
            without_defaultness = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Grund",),
                    language_pair="en-de",
                    translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                    gloss_records_by_target=records,
                    include_variants=False,
                    max_definitions_per_target=3,
                    max_rules_per_target=1,
                    scoring=RuleScoringConfig(weights=RuleScoreWeights(frequency_weight=0.0)),
                    enable_source_frequency_prior=True,
                    source_frequency_db_path=freq_db,
                    sense_representative_selection=True,
                )
            )
            with_defaultness = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Grund",),
                    language_pair="en-de",
                    translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                    gloss_records_by_target=records,
                    include_variants=False,
                    max_definitions_per_target=3,
                    max_rules_per_target=1,
                    scoring=RuleScoringConfig(weights=RuleScoreWeights(frequency_weight=0.0)),
                    enable_source_frequency_prior=True,
                    source_frequency_db_path=freq_db,
                    sense_representative_selection=True,
                    sense_defaultness_competition_penalty=0.8,
                )
            )
        self.assertEqual([rule.source_phrase for rule in without_defaultness], ["ground"])
        self.assertEqual([rule.source_phrase for rule in with_defaultness], ["reason"])

    @unittest.skipUnless(
        _EN_DE_SUPPORTS_DEFAULTNESS_COMPETITION,
        "Current branch en-de config does not expose defaultness-competition tuning.",
    )
    def test_en_de_adapter_sense_defaultness_competition_requires_sense_representatives(
        self,
    ) -> None:
        records = {
            "Grund": [
                FreedictGlossRecord(
                    translation="ground, land",
                    pos_raw="noun",
                    metadata={"entry_ord": 2884, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="reason, motive",
                    pos_raw="noun",
                    metadata={"entry_ord": 2884, "sense_ord": 1, "gloss_ord": 0},
                ),
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            freq_db = base / "freq-en-coca.sqlite"
            conn = sqlite3.connect(freq_db)
            try:
                conn.execute("CREATE TABLE frequency (lemma TEXT, pmw REAL)")
                conn.executemany(
                    "INSERT INTO frequency (lemma, pmw) VALUES (?, ?)",
                    [
                        ("ground", 120.0),
                        ("land", 110.0),
                        ("reason", 900.0),
                        ("motive", 10.0),
                    ],
                )
                conn.commit()
            finally:
                conn.close()
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Grund",),
                    language_pair="en-de",
                    translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                    gloss_records_by_target=records,
                    include_variants=False,
                    max_definitions_per_target=3,
                    max_rules_per_target=1,
                    scoring=RuleScoringConfig(weights=RuleScoreWeights(frequency_weight=0.0)),
                    enable_source_frequency_prior=True,
                    source_frequency_db_path=freq_db,
                    sense_defaultness_competition_penalty=0.8,
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["ground"])

    @unittest.skipUnless(
        _EN_DE_SUPPORTS_DEFAULTNESS_COMPETITION,
        "Current branch en-de config does not expose defaultness-competition tuning.",
    )
    def test_en_de_adapter_sense_defaultness_competition_promotes_cleaner_later_identity(
        self,
    ) -> None:
        records = {
            "Fall": [
                FreedictGlossRecord(
                    translation="fall, drop",
                    pos_raw="noun",
                    metadata={"entry_ord": 2723, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="case",
                    pos_raw="noun",
                    metadata={"entry_ord": 2723, "sense_ord": 1, "gloss_ord": 0},
                ),
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            freq_db = base / "freq-en-coca.sqlite"
            conn = sqlite3.connect(freq_db)
            try:
                conn.execute("CREATE TABLE frequency (lemma TEXT, pmw REAL)")
                conn.executemany(
                    "INSERT INTO frequency (lemma, pmw) VALUES (?, ?)",
                    [
                        ("fall", 120.0),
                        ("drop", 110.0),
                        ("case", 100000.0),
                    ],
                )
                conn.commit()
            finally:
                conn.close()
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Fall",),
                    language_pair="en-de",
                    translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                    gloss_records_by_target=records,
                    include_variants=False,
                    max_definitions_per_target=3,
                    max_rules_per_target=1,
                    scoring=RuleScoringConfig(weights=RuleScoreWeights(frequency_weight=0.0)),
                    enable_source_frequency_prior=True,
                    source_frequency_db_path=freq_db,
                    sense_representative_selection=True,
                    sense_defaultness_competition_penalty=0.8,
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["case"])

    @unittest.skipUnless(
        _EN_DE_SUPPORTS_DEFAULTNESS_COMPETITION,
        "Current branch en-de config does not expose defaultness-competition tuning.",
    )
    def test_en_de_adapter_sense_defaultness_competition_uses_frequency_when_provenance_ties(
        self,
    ) -> None:
        records = {
            "Grund": [
                FreedictGlossRecord(
                    translation="ground",
                    pos_raw="noun",
                    metadata={"entry_ord": 2884, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="reason",
                    pos_raw="noun",
                    metadata={"entry_ord": 2884, "sense_ord": 1, "gloss_ord": 0},
                ),
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            freq_db = base / "freq-en-coca.sqlite"
            conn = sqlite3.connect(freq_db)
            try:
                conn.execute("CREATE TABLE frequency (lemma TEXT, pmw REAL)")
                conn.executemany(
                    "INSERT INTO frequency (lemma, pmw) VALUES (?, ?)",
                    [
                        ("ground", 120.0),
                        ("reason", 900.0),
                    ],
                )
                conn.commit()
            finally:
                conn.close()
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Grund",),
                    language_pair="en-de",
                    translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                    gloss_records_by_target=records,
                    include_variants=False,
                    max_definitions_per_target=3,
                    max_rules_per_target=1,
                    scoring=RuleScoringConfig(weights=RuleScoreWeights(frequency_weight=0.0)),
                    enable_source_frequency_prior=True,
                    source_frequency_db_path=freq_db,
                    sense_representative_selection=True,
                    sense_defaultness_competition_penalty=0.8,
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["reason"])

    @unittest.skipUnless(
        _EN_DE_SUPPORTS_DEFAULTNESS_COMPETITION,
        "Current branch en-de config does not expose defaultness-competition tuning.",
    )
    def test_en_de_adapter_sense_defaultness_competition_blocks_parenthetical_later_gloss(
        self,
    ) -> None:
        records = {
            "Haus": [
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={"entry_ord": 27, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="home (in various phrases)",
                    pos_raw="noun",
                    metadata={"entry_ord": 27, "sense_ord": 1, "gloss_ord": 0},
                ),
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            freq_db = base / "freq-en-coca.sqlite"
            conn = sqlite3.connect(freq_db)
            try:
                conn.execute("CREATE TABLE frequency (lemma TEXT, pmw REAL)")
                conn.executemany(
                    "INSERT INTO frequency (lemma, pmw) VALUES (?, ?)",
                    [
                        ("house", 10.0),
                        ("home", 1000.0),
                    ],
                )
                conn.commit()
            finally:
                conn.close()
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Haus",),
                    language_pair="en-de",
                    translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                    gloss_records_by_target=records,
                    include_variants=False,
                    max_definitions_per_target=3,
                    max_rules_per_target=1,
                    scoring=RuleScoringConfig(weights=RuleScoreWeights(frequency_weight=0.0)),
                    enable_source_frequency_prior=True,
                    source_frequency_db_path=freq_db,
                    sense_representative_selection=True,
                    sense_defaultness_competition_penalty=1.0,
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["house"])

    @unittest.skipUnless(
        _EN_DE_SUPPORTS_DEFAULTNESS_COMPETITION,
        "Current branch en-de config does not expose defaultness-competition tuning.",
    )
    def test_en_de_adapter_sense_defaultness_competition_blocks_onomastic_later_sense(
        self,
    ) -> None:
        records = {
            "Freund": [
                FreedictGlossRecord(
                    translation="friend",
                    pos_raw="noun",
                    metadata={"entry_ord": 2050, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="a surname",
                    pos_raw="name",
                    metadata={
                        "entry_ord": 2051,
                        "sense_ord": 0,
                        "gloss_ord": 0,
                        "sense_tags": ("proper-noun", "surname"),
                        "sense_categories": ("German surnames",),
                    },
                ),
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            freq_db = base / "freq-en-coca.sqlite"
            conn = sqlite3.connect(freq_db)
            try:
                conn.execute("CREATE TABLE frequency (lemma TEXT, pmw REAL)")
                conn.executemany(
                    "INSERT INTO frequency (lemma, pmw) VALUES (?, ?)",
                    [
                        ("friend", 10.0),
                        ("surname", 1000.0),
                    ],
                )
                conn.commit()
            finally:
                conn.close()
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair="en-de",
                    targets=("Freund",),
                    language_pair="en-de",
                    translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                    gloss_records_by_target=records,
                    include_variants=False,
                    max_definitions_per_target=3,
                    max_rules_per_target=1,
                    scoring=RuleScoringConfig(weights=RuleScoreWeights(frequency_weight=0.0)),
                    enable_source_frequency_prior=True,
                    source_frequency_db_path=freq_db,
                    sense_representative_selection=True,
                    sense_defaultness_competition_penalty=1.0,
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["friend"])

    def test_en_de_adapter_uses_kaikki_policy_live_demotion_when_risky_family_present(
        self,
    ) -> None:
        risky_records = {
            "Haus": [
                FreedictGlossRecord(
                    translation="institution",
                    pos_raw="noun",
                    metadata={"sense_tags": ("abbreviation",)},
                ),
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={},
                ),
            ]
        }
        without_policy = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-de",
                targets=("Haus",),
                language_pair="en-de",
                translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                gloss_records_by_target=risky_records,
                include_variants=False,
            )
        )
        with_policy = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-de",
                targets=("Haus",),
                language_pair="en-de",
                translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                gloss_records_by_target=risky_records,
                include_variants=False,
                kaikki_policy_live_demotion=True,
                kaikki_policy_risk_families=("abbreviation_ellipsis_formof",),
            )
        )
        self.assertEqual(
            [rule.source_phrase for rule in without_policy],
            ["institution", "house"],
        )
        self.assertEqual(
            [rule.source_phrase for rule in with_policy],
            ["house", "institution"],
        )

    def test_en_de_results_mark_german_register_region_family_for_live_demotion(
        self,
    ) -> None:
        records = {
            "Kind": [
                FreedictGlossRecord(
                    translation="kid",
                    pos_raw="noun",
                    metadata={
                        "sense_tags": ("colloquial", "Southern-Germany"),
                        "sense_categories": ("German colloquialisms", "Regional German"),
                    },
                ),
                FreedictGlossRecord(
                    translation="child",
                    pos_raw="noun",
                    metadata={},
                ),
            ]
        }
        results = generate_en_de_results(
            ["Kind"],
            config=EnDeRulegenConfig(
                freedict_de_en_path=Path("/tmp/wiktionary-de-en.sqlite"),
                gloss_records_by_target=records,
                include_variants=False,
                max_definitions_per_target=None,
                kaikki_policy=EnDeKaikkiPolicyConfig(
                    enable_shadow_metadata=True,
                    enable_live_demotion=True,
                    risk_families=("register_region",),
                ),
            ),
        )
        by_source = {
            result.candidate.source_phrase: result.candidate.metadata for result in results
        }
        kid_metadata = by_source["kid"]
        self.assertEqual(kid_metadata["kaikki_family_names"], ("register_region",))
        self.assertAlmostEqual(kid_metadata["semantic_demotion"], 0.35, places=6)
        self.assertEqual(
            kid_metadata["semantic_demotion_reason"],
            "kaikki_policy:register_region",
        )
        shadow = kid_metadata["kaikki_policy_shadow"]
        self.assertEqual(shadow["risky_families"], ("register_region",))
        self.assertTrue(bool(shadow["live_demotion_applied"]))
        self.assertEqual(
            shadow["risk_family_sources"]["register_region"],
            (
                "sense_tag:colloquial",
                "sense_tag:southern-germany",
                "sense_category:german colloquialisms",
                "sense_category:regional german",
            ),
        )

    def test_en_de_compiled_resources_match_live_results_with_register_demotion(self) -> None:
        if build_en_de_compiled_resources is None:
            self.skipTest("en-de compiled resources are not available on this branch")
        records = {
            "Kind": [
                FreedictGlossRecord(
                    translation="kid",
                    pos_raw="noun",
                    metadata={"sense_tags": ("colloquial", "regional")},
                ),
                FreedictGlossRecord(
                    translation="child",
                    pos_raw="noun",
                    metadata={},
                ),
            ]
        }
        base_config = EnDeRulegenConfig(
            freedict_de_en_path=Path("/tmp/wiktionary-de-en.sqlite"),
            gloss_records_by_target=records,
            include_variants=False,
            max_definitions_per_target=None,
            kaikki_policy=EnDeKaikkiPolicyConfig(
                enable_shadow_metadata=True,
                enable_register_demotion=True,
            ),
        )
        compiled_resources = build_en_de_compiled_resources(
            targets=("Kind",),
            records_by_target=records,
            language_pair="en-de",
            source_dict="wiktionary_de_en",
            dictionary_pos_source_profile="wiktionary",
        )
        compiled_config = EnDeRulegenConfig(
            **{
                **base_config.__dict__,
                "compiled_resources": compiled_resources,
                "source_dict_id": "wiktionary_de_en",
                "dictionary_pos_source_profile": "wiktionary",
            }
        )

        live_results = generate_en_de_results(["Kind"], config=base_config)
        compiled_results = generate_en_de_results(["Kind"], config=compiled_config)

        self.assertEqual(
            [result.rule.source_phrase for result in compiled_results],
            [result.rule.source_phrase for result in live_results],
        )
        self.assertEqual(
            [result.confidence for result in compiled_results],
            [result.confidence for result in live_results],
        )
        compiled_by_source = {
            result.rule.source_phrase: result.candidate.metadata for result in compiled_results
        }
        self.assertAlmostEqual(
            float(compiled_by_source["kid"]["semantic_demotion"]),
            float(
                next(
                    result.candidate.metadata["semantic_demotion"]
                    for result in live_results
                    if result.rule.source_phrase == "kid"
                )
            ),
            places=6,
        )

    def test_en_de_adapter_uses_kaikki_register_demotion_when_register_markers_present(
        self,
    ) -> None:
        records = {
            "Kind": [
                FreedictGlossRecord(
                    translation="kid",
                    pos_raw="noun",
                    metadata={"sense_tags": ("colloquial", "regional")},
                ),
                FreedictGlossRecord(
                    translation="child",
                    pos_raw="noun",
                    metadata={},
                ),
            ]
        }
        without_policy = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-de",
                targets=("Kind",),
                language_pair="en-de",
                translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                gloss_records_by_target=records,
                include_variants=False,
            )
        )
        with_policy = run_rules_with_adapter(
            RulegenAdapterRequest(
                pair="en-de",
                targets=("Kind",),
                language_pair="en-de",
                translation_dict_path=Path("/tmp/wiktionary-de-en.sqlite"),
                gloss_records_by_target=records,
                include_variants=False,
                kaikki_policy_register_demotion=True,
            )
        )
        self.assertEqual([rule.source_phrase for rule in without_policy], ["kid", "child"])
        self.assertEqual([rule.source_phrase for rule in with_policy], ["child", "kid"])

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
                    translation_dict_path=path,
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
                    translation_dict_path=path,
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
                    translation_dict_path=Path("/tmp/eng-spa.tei"),
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

    def test_es_en_adapter_demotes_generic_gloss_terms_for_top_k_when_enabled(self) -> None:
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
                    translation_dict_path=path,
                    enable_exact_gloss_demotions=True,
                )
            )
        self.assertEqual([rule.source_phrase for rule in rules], ["casa", "hogar", "vivienda"])
        self.assertTrue(all(rule.replacement == "house" for rule in rules))


if __name__ == "__main__":
    unittest.main()
