from __future__ import annotations

import os
import sys
import unittest
from types import SimpleNamespace

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.replacement.core import RuleMetadata, VocabRule  # noqa: E402
from lexishift_core.rulegen.generation import RuleCandidate  # noqa: E402
from lexishift_core.rulegen.semantic_publication import (  # noqa: E402
    annotate_results_with_semantic_admission,
    build_semantic_inventory_from_results,
    merge_semantic_publication_with_context_inventory,
    merge_semantic_publication_with_reference_inventory,
)


def _build_en_es_result(
    *,
    source_phrase: str,
    replacement: str,
    entry_ord: int,
    sense_ord: int,
) -> SimpleNamespace:
    return SimpleNamespace(
        candidate=RuleCandidate(
            source_phrase=source_phrase,
            replacement=replacement,
            language_pair="en-es",
            source_dict="wiktionary_es_en",
            metadata={
                "sense_provenance": {
                    "entry_ord": entry_ord,
                    "sense_ord": sense_ord,
                    "gloss_ord": 0,
                    "sense_raw_glosses": (f"{replacement} sense",),
                },
                "gloss_provenance": {
                    "raw_gloss_text": f"{source_phrase} -> {replacement}",
                    "fragment_emitted_text": source_phrase,
                },
            },
        ),
        rule=VocabRule(
            source_phrase=source_phrase,
            replacement=replacement,
            metadata=RuleMetadata(language_pair="en-es"),
        ),
        confidence=0.9,
    )


def _build_de_en_result(
    *,
    source_phrase: str,
    replacement: str,
    gloss_index: int,
) -> SimpleNamespace:
    return SimpleNamespace(
        candidate=RuleCandidate(
            source_phrase=source_phrase,
            replacement=replacement,
            language_pair="de-en",
            source_dict="freedict_en_de",
            metadata={"gloss_index": gloss_index},
        ),
        rule=VocabRule(
            source_phrase=source_phrase,
            replacement=replacement,
            metadata=RuleMetadata(language_pair="de-en"),
        ),
        confidence=0.9,
    )


class TestSemanticPublication(unittest.TestCase):
    def test_en_es_emitted_rule_siblings_promote_semantic_admission_to_ready(self) -> None:
        results = annotate_results_with_semantic_admission(
            (
                _build_en_es_result(
                    source_phrase="ball",
                    replacement="pelota",
                    entry_ord=20,
                    sense_ord=0,
                ),
                _build_en_es_result(
                    source_phrase="ball",
                    replacement="baile",
                    entry_ord=21,
                    sense_ord=0,
                ),
            )
        )

        self.assertEqual(len(results), 2)
        first = results[0].rule.metadata.semantic_admission
        second = results[1].rule.metadata.semantic_admission
        assert isinstance(first, dict)
        assert isinstance(second, dict)
        self.assertEqual(first["status"], "ready")
        self.assertEqual(second["status"], "ready")
        self.assertNotIn("reason_code", first)
        self.assertNotIn("reason_code", second)
        self.assertEqual(first["trigger_id"], second["trigger_id"])
        self.assertNotEqual(first["sense_id"], second["sense_id"])
        self.assertNotEqual(first["competition_set_id"], second["competition_set_id"])

    def test_build_semantic_inventory_publishes_ready_en_es_emitted_rule_sibling_competition_sets(
        self,
    ) -> None:
        results = (
            _build_en_es_result(
                source_phrase="ball",
                replacement="pelota",
                entry_ord=20,
                sense_ord=0,
            ),
            _build_en_es_result(
                source_phrase="ball",
                replacement="baile",
                entry_ord=21,
                sense_ord=0,
            ),
        )

        inventory = build_semantic_inventory_from_results(
            results=results,
            pair="en-es",
            profile_id="default",
            generated_at="2026-04-10T00:00:00Z",
        )

        self.assertEqual(
            inventory["capability"]["pointer_modes"],
            ["sense_provenance", "translation_gloss"],
        )
        self.assertEqual(inventory["capability"]["competition_mode"], "emitted_rule_siblings")
        self.assertEqual(len(inventory["triggers"]), 1)
        self.assertEqual(len(inventory["senses"]), 2)
        self.assertEqual(len(inventory["competition_sets"]), 2)
        competition_sets = list(inventory["competition_sets"].values())
        expected_sense_ids = set(inventory["senses"].keys())
        for record in competition_sets:
            self.assertEqual(record["status"], "ready")
            self.assertEqual(record["selection_mode"], "automatic")
            self.assertEqual(
                record["selection_policy_version"],
                "en_es_emitted_rule_siblings_v1",
            )
            self.assertIn(record["active_sense_id"], expected_sense_ids)
            self.assertEqual(len(record["shadow_sense_ids"]), 1)
            self.assertNotIn(record["active_sense_id"], record["shadow_sense_ids"])
            self.assertTrue(set(record["shadow_sense_ids"]).issubset(expected_sense_ids))

    def test_non_opted_in_pairs_keep_competition_sets_unavailable(self) -> None:
        results = annotate_results_with_semantic_admission(
            (
                _build_de_en_result(
                    source_phrase="Haus",
                    replacement="house",
                    gloss_index=0,
                ),
                _build_de_en_result(
                    source_phrase="Haus",
                    replacement="home",
                    gloss_index=1,
                ),
            )
        )

        for result in results:
            admission = result.rule.metadata.semantic_admission
            assert isinstance(admission, dict)
            self.assertEqual(admission["status"], "unavailable")
            self.assertEqual(admission["reason_code"], "missing_shadow_selection")

        inventory = build_semantic_inventory_from_results(
            results=results,
            pair="de-en",
            profile_id="default",
            generated_at="2026-04-10T00:00:00Z",
        )
        self.assertEqual(inventory["capability"]["pointer_modes"], ["translation_gloss"])
        self.assertEqual(len(inventory["senses"]), 2)
        for record in inventory["senses"].values():
            self.assertEqual(record["locator"]["locator_kind"], "translation_gloss")
        self.assertEqual(inventory["capability"]["competition_mode"], "not_published")
        for record in inventory["competition_sets"].values():
            self.assertEqual(record["status"], "unavailable")
            self.assertEqual(record["reason_code"], "missing_shadow_selection")

    def test_merge_semantic_publication_uses_ready_context_without_widening_ruleset(self) -> None:
        primary_results = (
            _build_en_es_result(
                source_phrase="ball",
                replacement="pelota",
                entry_ord=20,
                sense_ord=0,
            ),
        )
        context_results = (
            _build_en_es_result(
                source_phrase="ball",
                replacement="pelota",
                entry_ord=20,
                sense_ord=0,
            ),
            _build_en_es_result(
                source_phrase="ball",
                replacement="baile",
                entry_ord=21,
                sense_ord=0,
            ),
        )
        primary_inventory = build_semantic_inventory_from_results(
            results=primary_results,
            pair="en-es",
            profile_id="default",
            generated_at="2026-04-10T00:00:00Z",
        )
        context_inventory = build_semantic_inventory_from_results(
            results=context_results,
            pair="en-es",
            profile_id="default",
            generated_at="2026-04-10T00:00:00Z",
        )

        merged_rules, merged_inventory = merge_semantic_publication_with_context_inventory(
            rules=tuple(result.rule for result in primary_results),
            primary_inventory=primary_inventory,
            context_inventory=context_inventory,
        )

        self.assertEqual(len(merged_rules), 1)
        merged_admission = merged_rules[0].metadata.semantic_admission
        assert isinstance(merged_admission, dict)
        self.assertEqual(merged_admission["status"], "ready")
        self.assertNotIn("reason_code", merged_admission)
        self.assertEqual(len(merged_inventory["competition_sets"]), 1)
        merged_competition_set = next(iter(merged_inventory["competition_sets"].values()))
        self.assertEqual(merged_competition_set["status"], "ready")
        self.assertEqual(
            merged_competition_set["selection_policy_version"], "en_es_emitted_rule_siblings_v1"
        )
        self.assertEqual(len(merged_competition_set["shadow_sense_ids"]), 1)
        self.assertEqual(len(merged_inventory["senses"]), 2)

    def test_merge_reference_inventory_upgrades_matching_unavailable_rule_only(
        self,
    ) -> None:
        primary_results = annotate_results_with_semantic_admission(
            (
                _build_en_es_result(
                    source_phrase="light",
                    replacement="luz",
                    entry_ord=30,
                    sense_ord=0,
                ),
            )
        )
        primary_inventory = build_semantic_inventory_from_results(
            results=primary_results,
            pair="en-es",
            profile_id="default",
            generated_at="2026-04-10T00:00:00Z",
        )
        reference_inventory = {
            "schema_version": 1,
            "pair": "en-es",
            "profile_id": "semantic_pack_builder",
            "generated_at": "2026-04-09T00:00:00Z",
            "capability": {},
            "triggers": {
                "pack:trigger:light": {
                    "trigger_id": "pack:trigger:light",
                    "source_phrase": "light",
                }
            },
            "senses": {
                "pack:sense:luz": {
                    "sense_id": "pack:sense:luz",
                    "trigger_id": "pack:trigger:light",
                    "target_lemma": "luz",
                }
            },
            "competition_sets": {
                "pack:competition:light:luz": {
                    "competition_set_id": "pack:competition:light:luz",
                    "trigger_id": "pack:trigger:light",
                    "status": "ready",
                    "active_sense_id": "pack:sense:luz",
                    "shadow_sense_ids": [],
                }
            },
            "phrase_sets": {},
        }

        merged_rules, merged_inventory = merge_semantic_publication_with_reference_inventory(
            rules=tuple(result.rule for result in primary_results),
            primary_inventory=primary_inventory,
            reference_inventory=reference_inventory,
        )

        self.assertEqual(len(merged_rules), 1)
        merged_admission = merged_rules[0].metadata.semantic_admission
        assert isinstance(merged_admission, dict)
        self.assertEqual(merged_admission["status"], "ready")
        self.assertEqual(merged_admission["trigger_id"], "pack:trigger:light")
        self.assertEqual(merged_admission["sense_id"], "pack:sense:luz")
        self.assertEqual(
            merged_admission["competition_set_id"],
            "pack:competition:light:luz",
        )
        self.assertIn("pack:trigger:light", merged_inventory["triggers"])
        self.assertIn("pack:sense:luz", merged_inventory["senses"])
        self.assertIn("pack:competition:light:luz", merged_inventory["competition_sets"])

    def test_de_en_missing_gloss_index_reports_translation_gloss_reason_code(self) -> None:
        results = annotate_results_with_semantic_admission(
            (
                SimpleNamespace(
                    candidate=RuleCandidate(
                        source_phrase="Haus",
                        replacement="house",
                        language_pair="de-en",
                        source_dict="freedict_en_de",
                        metadata={},
                    ),
                    rule=VocabRule(
                        source_phrase="Haus",
                        replacement="house",
                        metadata=RuleMetadata(language_pair="de-en"),
                    ),
                    confidence=0.9,
                ),
            )
        )

        admission = results[0].rule.metadata.semantic_admission
        assert isinstance(admission, dict)
        self.assertEqual(admission["status"], "unavailable")
        self.assertEqual(
            admission["reason_code"],
            "missing_translation_gloss_locator",
        )
        self.assertNotIn("sense_id", admission)
        self.assertNotIn("competition_set_id", admission)


if __name__ == "__main__":
    unittest.main()
