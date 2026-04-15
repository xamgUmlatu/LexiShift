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
    _should_suppress_fragment_reverse_miss,
    generate_en_es_results,
)
from lexishift_core.rulegen.pairs.en_es_support import (  # noqa: E402
    _expand_en_es_gloss_variants,
)


class TestKaikkiRecordViews(unittest.TestCase):
    def test_build_kaikki_record_views_exposes_marker_text_and_relations(self) -> None:
        views = build_kaikki_record_views(
            {
                "entry_tags": ["Demonstrative", "Common"],
                "entry_categories": ["Spanish Determiners"],
                "sense_tags": ["Mexico", "informal", "vulgar"],
                "sense_topics": ["Government", "Communication"],
                "sense_categories": ["es:Government", "Spanish vulgarities"],
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
        self.assertIn("sense_tag:vulgar", views["combined_prefixed_markers"])
        self.assertEqual(
            views["family_fields"]["government_law"],
            ("sense_topic:government", "sense_category:es:government"),
        )
        self.assertIn("sense_tag:vulgar", views["family_fields"]["register_region"])
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

    def test_build_kaikki_record_views_exposes_new_domain_families(self) -> None:
        views = build_kaikki_record_views(
            {
                "sense_topics": ["Music", "Chemistry", "Mechanics"],
                "sense_categories": ["es:Biology", "es:Computing"],
            }
        )

        combined = views.get("combined_families", ())
        self.assertIn("music", combined)
        self.assertIn("chemistry", combined)
        self.assertIn("mechanics_tools", combined)
        self.assertIn("biology", combined)
        self.assertIn("computing", combined)

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

    def test_live_kaikki_policy_demotion_respects_family_override_values(self) -> None:
        results = generate_en_es_results(
            ["batería"],
            config=EnEsRulegenConfig(
                freedict_es_en_path=Path("/tmp/unused"),
                gloss_records_by_target={
                    "batería": [
                        FreedictGlossRecord(
                            translation="drummer",
                            pos_raw="noun",
                            metadata={
                                "sense_topics": ["music"],
                            },
                        ),
                        FreedictGlossRecord(
                            translation="battery",
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
                    risk_families=("music",),
                    risk_family_demotions=(("music", 0.47),),
                ),
            ),
        )

        by_source = {
            result.candidate.source_phrase: result.candidate.metadata for result in results
        }
        drummer_metadata = by_source["drummer"]
        self.assertAlmostEqual(drummer_metadata["semantic_demotion"], 0.47, places=6)
        self.assertEqual(
            drummer_metadata["semantic_demotion_reason"],
            "kaikki_policy:music",
        )
        shadow = drummer_metadata["kaikki_policy_shadow"]
        self.assertTrue(bool(shadow["live_demotion_applied"]))
        self.assertAlmostEqual(shadow["live_demotion_value"], 0.47, places=6)
        self.assertEqual(shadow["live_demotion_reasons"], ("kaikki_policy:music",))

    def test_long_nominal_gloss_recovers_bare_head_candidate(self) -> None:
        results = generate_en_es_results(
            ["batería"],
            config=EnEsRulegenConfig(
                freedict_es_en_path=Path("/tmp/unused"),
                gloss_records_by_target={
                    "batería": [
                        FreedictGlossRecord(
                            translation="large and rechargeable battery",
                            pos_raw="noun",
                            metadata={
                                "entry_ord": 0,
                                "sense_ord": 0,
                                "gloss_ord": 0,
                            },
                        ),
                        FreedictGlossRecord(
                            translation="drum kit, drum set",
                            pos_raw="noun",
                            metadata={
                                "entry_ord": 0,
                                "sense_ord": 1,
                                "gloss_ord": 0,
                                "sense_topics": ["music"],
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
        self.assertIn("battery", by_source)
        gloss_provenance = by_source["battery"]["gloss_provenance"]
        self.assertEqual(
            gloss_provenance["fragment_source_text"],
            "large and rechargeable battery",
        )
        self.assertEqual(gloss_provenance["fragment_strategy"], "nominal_head")
        self.assertIn(
            "extract_nominal_head",
            gloss_provenance["normalization_operations"],
        )

    def test_short_nominal_compounds_do_not_collapse_to_generic_tail(self) -> None:
        variants = _expand_en_es_gloss_variants("drum kit", pos_raw="noun")
        emitted = {text for text, _metadata in variants}
        self.assertIn("drum kit", emitted)
        self.assertNotIn("kit", emitted)

    def test_comma_separated_noun_lists_do_not_emit_nominal_head_tail(self) -> None:
        variants = _expand_en_es_gloss_variants(
            "sight, scene, picture, spectacle, image (an event that leaves an impact)",
            pos_raw="noun",
        )
        emitted = {text for text, _metadata in variants}
        self.assertIn("sight, scene, picture, spectacle, image", emitted)
        self.assertNotIn("image", emitted)

    def test_explanatory_noun_gloss_emits_leading_alias(self) -> None:
        variants = _expand_en_es_gloss_variants(
            "picture, painting or other work of art, especially one in a frame",
            pos_raw="noun",
        )
        metadata_by_text = {text: metadata for text, metadata in variants}
        self.assertIn(
            "picture, painting or other work of art, especially one in a frame", metadata_by_text
        )
        self.assertIn("picture", metadata_by_text)
        self.assertEqual(
            metadata_by_text["picture"]["gloss_fragment_strategy"],
            "leading_alias",
        )
        self.assertIn(
            "extract_leading_alias",
            metadata_by_text["picture"]["gloss_fragment_operations"],
        )

    def test_cuadro_art_gloss_surfaces_picture_candidate(self) -> None:
        results = generate_en_es_results(
            ["cuadro"],
            config=EnEsRulegenConfig(
                freedict_es_en_path=Path("/tmp/unused"),
                gloss_records_by_target={
                    "cuadro": [
                        FreedictGlossRecord(
                            translation="square (a polygon with four straight sides of equal length and four right angles)",
                            pos_raw="noun",
                            metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 0},
                        ),
                        FreedictGlossRecord(
                            translation="rectangle (any quadrilateral having opposing sides parallel and four right angles)",
                            pos_raw="noun",
                            metadata={"entry_ord": 0, "sense_ord": 1, "gloss_ord": 0},
                        ),
                        FreedictGlossRecord(
                            translation="picture, painting or other work of art, especially one in a frame",
                            pos_raw="noun",
                            metadata={"entry_ord": 0, "sense_ord": 2, "gloss_ord": 0},
                        ),
                    ]
                },
                include_variants=False,
                max_definitions_per_target=None,
                source_dict_id="wiktionary_es_en",
                dictionary_pos_source_profile="wiktionary",
            ),
        )

        metadata_by_source = {
            result.candidate.source_phrase: result.candidate.metadata for result in results
        }
        self.assertIn("picture", metadata_by_source)
        self.assertEqual(
            metadata_by_source["picture"]["gloss_provenance"]["fragment_strategy"],
            "leading_alias",
        )
        self.assertFalse(bool(metadata_by_source["picture"]["reverse_check_supported"]))
        self.assertFalse(bool(metadata_by_source["picture"]["reverse_check_hit"]))

    def test_only_heuristic_fragment_strategies_suppress_reverse_miss(self) -> None:
        self.assertFalse(
            _should_suppress_fragment_reverse_miss(
                gloss_provenance={"fragment_strategy": "top_level_comma"},
                reverse_rank=None,
            )
        )
        self.assertTrue(
            _should_suppress_fragment_reverse_miss(
                gloss_provenance={"fragment_strategy": "leading_alias"},
                reverse_rank=None,
            )
        )

    def test_provenance_penalty_demotes_late_sense_with_clean_earlier_competition(self) -> None:
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
                                "entry_ord": 50,
                                "sense_ord": 0,
                                "gloss_ord": 0,
                            },
                        ),
                        FreedictGlossRecord(
                            translation="to table (a proposal)",
                            pos_raw="verb",
                            metadata={
                                "entry_ord": 50,
                                "sense_ord": 1,
                                "gloss_ord": 0,
                                "sense_topics": ["government"],
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
                    enable_live_demotion=False,
                    late_sense_clean_earlier_competition_penalty=0.18,
                    risk_families=("government_law",),
                ),
            ),
        )

        by_source = {
            result.candidate.source_phrase: result.candidate.metadata for result in results
        }
        table_metadata = by_source["table"]
        self.assertAlmostEqual(table_metadata["semantic_demotion"], 0.18, places=6)
        self.assertEqual(
            table_metadata["semantic_demotion_reason"],
            "kaikki_provenance:late_sense_clean_earlier_competition",
        )
        shadow = table_metadata["kaikki_policy_shadow"]
        self.assertTrue(bool(shadow["provenance_demotion_applied"]))
        self.assertAlmostEqual(shadow["provenance_demotion_value"], 0.18, places=6)
        self.assertEqual(
            shadow["provenance_demotion_reasons"],
            ("kaikki_provenance:late_sense_clean_earlier_competition",),
        )


if __name__ == "__main__":
    unittest.main()
