from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.resources.dict_loaders import FreedictGlossRecord  # noqa: E402
from lexishift_core.rulegen.kaikki_views import build_kaikki_record_views  # noqa: E402
from lexishift_core.rulegen.pairs.en_es import (  # noqa: E402
    EnEsKaikkiPolicyConfig,
    EnEsRulegenConfig,
    generate_en_es_results,
)


class TestKaikkiRecordViews(unittest.TestCase):
    def test_build_kaikki_record_views_exposes_marker_text_and_relations(self) -> None:
        views = build_kaikki_record_views(
            {
                "entry_tags": ["Demonstrative", "Common"],
                "entry_categories": ["Spanish Determiners"],
                "sense_tags": ["Mexico", "informal"],
                "sense_topics": ["Government", "Communication"],
                "sense_categories": ["es:Government"],
                "translation_tags": ["Latin-America"],
                "entry_pos_title": "Determiner",
                "translation_sense_text": "greeting",
                "sense_form_of": [{"word": "presentar"}],
                "sense_alt_of": [{"word": "presentase"}],
            }
        )

        self.assertEqual(
            views["marker_fields"]["entry_tags"],
            ("demonstrative", "common"),
        )
        self.assertEqual(
            views["prefixed_marker_fields"]["sense_topics"],
            ("sense_topic:government", "sense_topic:communication"),
        )
        self.assertEqual(
            views["text_fields"]["entry_pos_title"],
            "determiner",
        )
        self.assertEqual(
            views["relation_fields"]["sense_form_of"],
            ("presentar",),
        )
        self.assertIn("sense_tag:informal", views["combined_prefixed_markers"])
        self.assertEqual(
            views["family_fields"]["government_law"],
            ("sense_topic:government", "sense_category:es:government"),
        )
        self.assertIn("register_region", views["combined_families"])
        self.assertIn("abbreviation_ellipsis_formof", views["combined_families"])

    def test_build_kaikki_record_views_keeps_domain_families_sense_scoped(self) -> None:
        views = build_kaikki_record_views(
            {
                "entry_categories": ["es:Law", "es:Mathematics"],
                "sense_topics": ["Communication"],
                "sense_categories": ["es:Communication"],
            }
        )

        self.assertNotIn("government_law", views.get("combined_families", ()))
        self.assertNotIn("math_geometry", views.get("combined_families", ()))
        self.assertIn("communication_network", views.get("combined_families", ()))


class TestRulegenEnEsKaikkiProvenance(unittest.TestCase):
    def test_generated_candidates_include_raw_and_normalized_kaikki_views(self) -> None:
        results = generate_en_es_results(
            ["presentar"],
            config=EnEsRulegenConfig(
                freedict_es_en_path=Path("/tmp/unused"),
                gloss_records_by_target={
                    "presentar": [
                        FreedictGlossRecord(
                            translation="to present, to submit",
                            pos_raw="verb",
                            metadata={
                                "entry_ord": 10,
                                "sense_ord": 0,
                                "gloss_ord": 0,
                                "entry_pos_title": "verb",
                                "entry_tags": ["common"],
                                "entry_categories": ["Spanish verbs"],
                                "sense_raw_glosses": ["to present, to submit"],
                                "sense_tags": ["transitive"],
                                "sense_topics": ["education"],
                                "sense_categories": ["Spanish terms with usage examples"],
                                "sense_form_of": [{"word": "presentar"}],
                            },
                        ),
                        FreedictGlossRecord(
                            translation="to introduce (someone), to acquaint",
                            pos_raw="verb",
                            metadata={
                                "entry_ord": 10,
                                "sense_ord": 1,
                                "gloss_ord": 0,
                                "entry_pos_title": "verb",
                                "entry_tags": ["common"],
                                "sense_raw_glosses": ["to introduce (someone), to acquaint"],
                                "sense_tags": ["transitive"],
                                "sense_topics": ["social"],
                                "sense_categories": ["Spanish terms with usage examples"],
                            },
                        ),
                    ]
                },
                include_variants=False,
                max_definitions_per_target=None,
                source_dict_id="wiktionary_es_en",
                dictionary_pos_source_profile="wiktionary",
            ),
        )

        by_source = {
            result.candidate.source_phrase: result.candidate.metadata for result in results
        }
        self.assertIn("introduce", by_source)
        metadata = by_source["introduce"]

        self.assertIn("dictionary_record", metadata)
        self.assertIn("dictionary_record_views", metadata)
        self.assertIn("gloss_provenance", metadata)
        self.assertIn("sense_provenance", metadata)
        self.assertIn("target_provenance", metadata)

        raw_record = metadata["dictionary_record"]
        self.assertEqual(raw_record["sense_topics"], ["social"])

        views = metadata["dictionary_record_views"]["kaikki"]
        self.assertEqual(views["marker_fields"]["entry_tags"], ("common",))
        self.assertEqual(views["marker_fields"]["sense_topics"], ("social",))
        self.assertEqual(
            views["prefixed_marker_fields"]["sense_categories"],
            ("sense_category:spanish terms with usage examples",),
        )

        gloss_provenance = metadata["gloss_provenance"]
        self.assertEqual(
            gloss_provenance["raw_gloss_text"],
            "to introduce (someone), to acquaint",
        )
        self.assertEqual(
            gloss_provenance["fragment_source_text"],
            "to introduce (someone)",
        )
        self.assertEqual(gloss_provenance["fragment_strategy"], "top_level_comma")
        self.assertTrue(bool(gloss_provenance["parenthetical_stripped"]))
        self.assertIn(
            "strip_inline_annotation",
            gloss_provenance["normalization_operations"],
        )

        sense_provenance = metadata["sense_provenance"]
        self.assertEqual(sense_provenance["entry_ord"], 10)
        self.assertEqual(sense_provenance["sense_ord"], 1)
        self.assertEqual(sense_provenance["pos_raw"], "verb")
        self.assertEqual(
            sense_provenance["sense_raw_glosses"],
            ("to introduce (someone), to acquaint",),
        )
        self.assertEqual(sense_provenance["dictionary_pos_canonical"], "verb")

        target_provenance = metadata["target_provenance"]
        self.assertEqual(target_provenance["target"], "presentar")
        self.assertEqual(target_provenance["candidate_total"], 4)
        self.assertEqual(target_provenance["sense_total"], 2)
        self.assertEqual(target_provenance["current_sense_candidate_count"], 2)
        self.assertEqual(target_provenance["earlier_sense_count"], 1)
        self.assertEqual(target_provenance["current_sense_ord"], 1)
        self.assertEqual(target_provenance["surviving_sense_ordinals"], (0, 1))

    def test_generated_candidates_include_kaikki_policy_shadow_metadata(self) -> None:
        results = generate_en_es_results(
            ["cuenta"],
            config=EnEsRulegenConfig(
                freedict_es_en_path=Path("/tmp/unused"),
                gloss_records_by_target={
                    "cuenta": [
                        FreedictGlossRecord(
                            translation="operation",
                            pos_raw="noun",
                            metadata={
                                "entry_ord": 20,
                                "sense_ord": 0,
                                "gloss_ord": 0,
                                "sense_topics": ["mathematics"],
                            },
                        ),
                        FreedictGlossRecord(
                            translation="account",
                            pos_raw="noun",
                            metadata={
                                "entry_ord": 20,
                                "sense_ord": 1,
                                "gloss_ord": 0,
                            },
                        ),
                    ]
                },
                include_variants=False,
                max_definitions_per_target=None,
                source_dict_id="wiktionary_es_en",
                dictionary_pos_source_profile="wiktionary",
            ),
        )

        by_source = {
            result.candidate.source_phrase: result.candidate.metadata for result in results
        }
        operation_shadow = by_source["operation"]["kaikki_policy_shadow"]
        account_shadow = by_source["account"]["kaikki_policy_shadow"]

        self.assertEqual(operation_shadow["mode"], "shadow")
        self.assertEqual(operation_shadow["families"], ("math_geometry",))
        self.assertEqual(operation_shadow["risky_families"], ("math_geometry",))
        self.assertTrue(bool(operation_shadow["clean_competition_present"]))
        self.assertTrue(bool(operation_shadow["would_demote"]))
        self.assertFalse(bool(operation_shadow["live_demotion_applied"]))
        self.assertEqual(
            operation_shadow["risk_family_sources"]["math_geometry"],
            ("sense_topic:mathematics",),
        )
        self.assertIn("risk_family:math_geometry", operation_shadow["reasons"])

        self.assertEqual(account_shadow["families"], ())
        self.assertEqual(account_shadow["risky_families"], ())
        self.assertFalse(bool(account_shadow["would_demote"]))

    def test_domain_family_shadow_ignores_entry_level_math_and_law_contamination(self) -> None:
        results = generate_en_es_results(
            ["cuenta"],
            config=EnEsRulegenConfig(
                freedict_es_en_path=Path("/tmp/unused"),
                gloss_records_by_target={
                    "cuenta": [
                        FreedictGlossRecord(
                            translation="operation",
                            pos_raw="noun",
                            metadata={
                                "entry_ord": 30,
                                "sense_ord": 0,
                                "gloss_ord": 0,
                                "entry_categories": ["es:Mathematics"],
                                "sense_topics": ["mathematics"],
                            },
                        ),
                        FreedictGlossRecord(
                            translation="account",
                            pos_raw="noun",
                            metadata={
                                "entry_ord": 30,
                                "sense_ord": 1,
                                "gloss_ord": 0,
                                "entry_categories": ["es:Mathematics", "es:Law"],
                                "sense_topics": ["computing"],
                            },
                        ),
                    ]
                },
                include_variants=False,
                max_definitions_per_target=None,
                source_dict_id="wiktionary_es_en",
                dictionary_pos_source_profile="wiktionary",
                kaikki_policy=EnEsKaikkiPolicyConfig(
                    enable_shadow_metadata=True,
                    enable_live_demotion=True,
                    risk_families=("math_geometry", "government_law"),
                ),
            ),
        )

        by_source = {
            result.candidate.source_phrase: result.candidate.metadata for result in results
        }
        operation_shadow = by_source["operation"]["kaikki_policy_shadow"]
        account_shadow = by_source["account"]["kaikki_policy_shadow"]
        account_families = by_source["account"]["dictionary_record_views"]["kaikki"][
            "combined_families"
        ]

        self.assertEqual(operation_shadow["risky_families"], ("math_geometry",))
        self.assertEqual(account_families, ("computing",))
        self.assertEqual(account_shadow["risky_families"], ())
        self.assertFalse(bool(account_shadow["would_demote"]))

    def test_live_kaikki_policy_demotion_uses_shadow_result(self) -> None:
        results = generate_en_es_results(
            ["cuenta"],
            config=EnEsRulegenConfig(
                freedict_es_en_path=Path("/tmp/unused"),
                gloss_records_by_target={
                    "cuenta": [
                        FreedictGlossRecord(
                            translation="operation",
                            pos_raw="noun",
                            metadata={
                                "sense_topics": ["mathematics"],
                            },
                        ),
                        FreedictGlossRecord(
                            translation="account",
                            pos_raw="noun",
                            metadata={},
                        ),
                    ]
                },
                include_variants=False,
                max_definitions_per_target=None,
                source_dict_id="wiktionary_es_en",
                dictionary_pos_source_profile="wiktionary",
                kaikki_policy=EnEsKaikkiPolicyConfig(
                    enable_shadow_metadata=True,
                    enable_live_demotion=True,
                    risk_families=("math_geometry",),
                ),
            ),
        )

        by_source = {
            result.candidate.source_phrase: result.candidate.metadata for result in results
        }
        operation_metadata = by_source["operation"]
        self.assertAlmostEqual(operation_metadata["semantic_demotion"], 0.30, places=6)
        self.assertEqual(
            operation_metadata["semantic_demotion_reason"],
            "kaikki_policy:math_geometry",
        )
        shadow = operation_metadata["kaikki_policy_shadow"]
        self.assertTrue(bool(shadow["live_demotion_applied"]))
        self.assertAlmostEqual(shadow["live_demotion_value"], 0.30, places=6)
        self.assertEqual(
            shadow["live_demotion_reasons"],
            ("kaikki_policy:math_geometry",),
        )


if __name__ == "__main__":
    unittest.main()
