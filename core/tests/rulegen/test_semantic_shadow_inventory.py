from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.resources.dict_loaders import TranslationGlossRecord  # noqa: E402
from lexishift_core.rulegen.semantic_shadow_inventory import (  # noqa: E402
    build_benchmark_shadow_targets,
    build_en_es_shadow_inventory,
    promote_shadow_candidates_for_policy,
)


def _record(
    *,
    translation: str,
    pos_raw: str = "noun",
    entry_ord: int | None = None,
    sense_ord: int | None = None,
    gloss_ord: int | None = None,
    sense_gloss: str = "",
) -> TranslationGlossRecord:
    metadata: dict[str, object] = {}
    if entry_ord is not None:
        metadata["entry_ord"] = entry_ord
    if sense_ord is not None:
        metadata["sense_ord"] = sense_ord
    if gloss_ord is not None:
        metadata["gloss_ord"] = gloss_ord
    if sense_gloss:
        metadata["sense_raw_glosses"] = (sense_gloss,)
    metadata["dictionary_pos_canonical"] = pos_raw
    return TranslationGlossRecord(
        translation=translation,
        pos_raw=pos_raw,
        metadata=metadata,
    )


class TestSemanticShadowInventory(unittest.TestCase):
    def test_build_benchmark_shadow_targets_groups_case_metadata_and_triggers(self) -> None:
        targets = build_benchmark_shadow_targets(
            (
                {
                    "case_id": "en-es:pelota:1",
                    "target": "pelota",
                    "tier": "hard",
                    "expected_top1_any": [" Ball "],
                    "expected_any": ["ball", "sphere"],
                },
                {
                    "case_id": "en-es:pelota:2",
                    "target": "pelota",
                    "tier": "review",
                    "expected_any": ["sphere", "orb"],
                },
                {
                    "case_id": "en-es:baile:1",
                    "target": "baile",
                    "tier": "hard",
                    "expected_any": ["dance ball"],
                },
            )
        )

        self.assertEqual([item.target for item in targets], ["baile", "pelota"])
        pelota = next(item for item in targets if item.target == "pelota")
        self.assertEqual(
            pelota.case_ids,
            ("en-es:pelota:1", "en-es:pelota:2"),
        )
        self.assertEqual(pelota.tiers, ("hard", "review"))
        self.assertEqual(pelota.reviewed_triggers, ("ball", "sphere", "orb"))

    def test_build_en_es_shadow_inventory_promotes_reviewed_same_pos_siblings(self) -> None:
        benchmark_targets = build_benchmark_shadow_targets(
            (
                {
                    "case_id": "en-es:pelota:1",
                    "target": "pelota",
                    "tier": "hard",
                    "expected_any": ["ball"],
                },
                {
                    "case_id": "en-es:baile:1",
                    "target": "baile",
                    "tier": "hard",
                    "expected_any": ["ball", "gala"],
                },
                {
                    "case_id": "en-es:bola_mala:1",
                    "target": "bola mala",
                    "tier": "hard",
                    "expected_any": ["bad ball"],
                },
            )
        )
        inventory = build_en_es_shadow_inventory(
            benchmark_targets=benchmark_targets,
            forward_records_by_target={
                "pelota": (
                    _record(
                        translation="ball",
                        entry_ord=10,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="object used in sports",
                    ),
                ),
            },
            reverse_records_by_source={
                "ball": (
                    _record(
                        translation="pelota",
                        entry_ord=10,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="object used in sports",
                    ),
                    _record(
                        translation="baile",
                        entry_ord=11,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="formal dance",
                    ),
                    _record(
                        translation="bola mala",
                        entry_ord=12,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="bad pitch outside the strike zone",
                    ),
                ),
            },
            forward_provider="wiktionary",
            reverse_provider="wiktionary",
        )

        pelota_row = next(row for row in inventory["targets"] if row["target"] == "pelota")
        trigger_row = pelota_row["trigger_entries"][0]
        self.assertEqual(trigger_row["trigger"], "ball")
        self.assertEqual(len(trigger_row["active_candidates"]), 1)
        self.assertEqual(len(trigger_row["shadow_candidates"]), 2)
        promoted = trigger_row["promoted_shadow_candidates"]
        self.assertEqual([candidate["target"] for candidate in promoted], ["baile", "bola mala"])
        self.assertEqual(
            promoted[0]["promotion_reasons"],
            [
                "reviewed_trigger_support",
                "benchmark_target_present",
                "same_pos_as_active",
            ],
        )

    def test_build_en_es_shadow_inventory_clusters_duplicate_reverse_rows_by_sense(self) -> None:
        benchmark_targets = build_benchmark_shadow_targets(
            (
                {
                    "case_id": "en-es:pelota:1",
                    "target": "pelota",
                    "tier": "hard",
                    "expected_any": ["ball"],
                },
                {
                    "case_id": "en-es:baile:1",
                    "target": "baile",
                    "tier": "hard",
                    "expected_any": ["ball"],
                },
            )
        )
        inventory = build_en_es_shadow_inventory(
            benchmark_targets=benchmark_targets,
            forward_records_by_target={
                "pelota": (
                    _record(
                        translation="ball",
                        entry_ord=10,
                        sense_ord=0,
                        sense_gloss="object used in sports",
                    ),
                ),
            },
            reverse_records_by_source={
                "ball": (
                    _record(
                        translation="baile",
                        entry_ord=11,
                        sense_ord=0,
                        sense_gloss="formal dance",
                    ),
                    _record(
                        translation="baile",
                        entry_ord=11,
                        sense_ord=0,
                        sense_gloss="formal dance",
                    ),
                ),
            },
            forward_provider="wiktionary",
            reverse_provider="wiktionary",
        )

        pelota_row = next(row for row in inventory["targets"] if row["target"] == "pelota")
        trigger_row = pelota_row["trigger_entries"][0]
        self.assertEqual(len(trigger_row["shadow_candidates"]), 1)
        self.assertEqual(trigger_row["shadow_candidates"][0]["target"], "baile")

    def test_build_en_es_shadow_inventory_matches_trigger_inside_split_forward_gloss(self) -> None:
        benchmark_targets = build_benchmark_shadow_targets(
            (
                {
                    "case_id": "en-es:coger:1",
                    "target": "coger",
                    "tier": "hard",
                    "expected_any": ["take", "catch"],
                },
                {
                    "case_id": "en-es:vista:1",
                    "target": "vista",
                    "tier": "hard",
                    "expected_any": ["sight", "view"],
                },
            )
        )
        inventory = build_en_es_shadow_inventory(
            benchmark_targets=benchmark_targets,
            forward_records_by_target={
                "coger": (
                    _record(
                        translation="to take, catch, hold, to get, to seize",
                        pos_raw="verb",
                        entry_ord=10,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="to take, catch, hold, to get, to seize",
                    ),
                ),
            },
            reverse_records_by_source={
                "catch": (
                    _record(
                        translation="vista",
                        pos_raw="noun",
                        entry_ord=11,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="the act of noticing, understanding or hearing",
                    ),
                ),
            },
            forward_provider="wiktionary",
            reverse_provider="wiktionary",
            promotion_policy="cross_checked_backoff_missing_active_v1",
        )

        coger_row = next(row for row in inventory["targets"] if row["target"] == "coger")
        trigger_row = next(row for row in coger_row["trigger_entries"] if row["trigger"] == "catch")
        self.assertEqual(
            [candidate["target"] for candidate in trigger_row["active_candidates"]], ["coger"]
        )
        self.assertEqual(trigger_row["active_candidates"][0]["matched_trigger"], "catch")
        self.assertEqual(trigger_row["promoted_shadow_candidates"], [])

    def test_build_en_es_shadow_inventory_supplements_missing_reverse_shadow_from_forward_index(
        self,
    ) -> None:
        benchmark_targets = build_benchmark_shadow_targets(
            (
                {
                    "case_id": "en-es:quitar:1",
                    "target": "quitar",
                    "tier": "hard",
                    "expected_any": ["remove"],
                },
                {
                    "case_id": "en-es:sacar:1",
                    "target": "sacar",
                    "tier": "hard",
                    "expected_any": ["remove", "take out"],
                },
            )
        )
        inventory = build_en_es_shadow_inventory(
            benchmark_targets=benchmark_targets,
            forward_records_by_target={
                "quitar": (
                    _record(
                        translation="remove",
                        pos_raw="verb",
                        entry_ord=10,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="to take away",
                    ),
                ),
                "sacar": (
                    _record(
                        translation="to remove, to extract, to take out",
                        pos_raw="verb",
                        entry_ord=11,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="to remove, to extract, to take out",
                    ),
                ),
            },
            reverse_records_by_source={
                "remove": (
                    _record(
                        translation="quitar",
                        pos_raw="verb",
                        entry_ord=10,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="to take away",
                    ),
                    _record(
                        translation="remover",
                        pos_raw="verb",
                        entry_ord=12,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="to take away",
                    ),
                ),
            },
            forward_provider="wiktionary",
            reverse_provider="wiktionary",
            promotion_policy="cross_checked_v1",
        )

        quitar_row = next(row for row in inventory["targets"] if row["target"] == "quitar")
        trigger_row = quitar_row["trigger_entries"][0]
        shadow_targets = [candidate["target"] for candidate in trigger_row["shadow_candidates"]]
        self.assertIn("sacar", shadow_targets)
        promoted = trigger_row["promoted_shadow_candidates"]
        self.assertEqual([candidate["target"] for candidate in promoted], ["sacar"])
        self.assertIn("forward_index", promoted[0]["candidate_sources"])

    def test_build_en_es_shadow_inventory_drops_zero_reason_promotions(self) -> None:
        benchmark_targets = build_benchmark_shadow_targets(
            (
                {
                    "case_id": "en-es:pelota:1",
                    "target": "pelota",
                    "tier": "hard",
                    "expected_any": ["ball"],
                },
            )
        )
        inventory = build_en_es_shadow_inventory(
            benchmark_targets=benchmark_targets,
            forward_records_by_target={
                "pelota": (
                    _record(
                        translation="ball",
                        pos_raw="noun",
                        entry_ord=10,
                        sense_ord=0,
                        sense_gloss="object used in sports",
                    ),
                ),
            },
            reverse_records_by_source={
                "ball": (
                    _record(
                        translation="ultimar",
                        pos_raw="verb",
                        entry_ord=11,
                        sense_ord=0,
                        sense_gloss="to put an end to, destroy",
                    ),
                ),
            },
            forward_provider="wiktionary",
            reverse_provider="wiktionary",
        )

        pelota_row = next(row for row in inventory["targets"] if row["target"] == "pelota")
        trigger_row = pelota_row["trigger_entries"][0]
        self.assertEqual(len(trigger_row["shadow_candidates"]), 1)
        self.assertEqual(trigger_row["shadow_candidates"][0]["target"], "ultimar")
        self.assertEqual(trigger_row["promoted_shadow_candidates"], [])

    def test_promote_shadow_candidates_for_policy_compares_policy_strictness(self) -> None:
        active_candidates = [{"canonical_pos": "noun"}]
        shadow_candidates = [
            {
                "target": "cuadro",
                "canonical_pos": "noun",
                "benchmark_target_present": True,
                "reviewed_trigger_support": False,
            },
            {
                "target": "estructura conceptual",
                "canonical_pos": "noun",
                "benchmark_target_present": False,
                "reviewed_trigger_support": False,
            },
            {
                "target": "red",
                "canonical_pos": "noun",
                "benchmark_target_present": True,
                "reviewed_trigger_support": True,
            },
        ]

        lenient = promote_shadow_candidates_for_policy(
            shadow_candidates=shadow_candidates,
            active_candidates=active_candidates,
            policy="same_pos_lenient_v1",
        )
        benchmark_backed = promote_shadow_candidates_for_policy(
            shadow_candidates=shadow_candidates,
            active_candidates=active_candidates,
            policy="benchmark_backed_v1",
        )
        cross_checked = promote_shadow_candidates_for_policy(
            shadow_candidates=shadow_candidates,
            active_candidates=active_candidates,
            policy="cross_checked_v1",
        )
        cross_checked_backoff = promote_shadow_candidates_for_policy(
            shadow_candidates=shadow_candidates,
            active_candidates=active_candidates,
            policy="cross_checked_backoff_missing_active_v1",
        )

        self.assertEqual(
            [candidate["target"] for candidate in lenient],
            ["red", "cuadro", "estructura conceptual"],
        )
        self.assertEqual([candidate["target"] for candidate in benchmark_backed], ["red", "cuadro"])
        self.assertEqual([candidate["target"] for candidate in cross_checked], ["red", "cuadro"])
        self.assertEqual(
            [candidate["target"] for candidate in cross_checked_backoff],
            ["red", "cuadro"],
        )

    def test_cross_checked_policy_drops_benchmark_target_without_same_pos_or_reviewed_trigger(
        self,
    ) -> None:
        promoted = promote_shadow_candidates_for_policy(
            shadow_candidates=[
                {
                    "target": "parte",
                    "canonical_pos": "noun",
                    "benchmark_target_present": True,
                    "reviewed_trigger_support": False,
                }
            ],
            active_candidates=[{"canonical_pos": "verb"}],
            policy="cross_checked_v1",
        )
        self.assertEqual(promoted, [])

    def test_cross_checked_backoff_missing_active_allows_benchmark_target_without_active_pos(
        self,
    ) -> None:
        promoted = promote_shadow_candidates_for_policy(
            shadow_candidates=[
                {
                    "target": "parte",
                    "canonical_pos": "noun",
                    "benchmark_target_present": True,
                    "reviewed_trigger_support": False,
                }
            ],
            active_candidates=[{"canonical_pos": ""}],
            policy="cross_checked_backoff_missing_active_v1",
        )
        self.assertEqual([candidate["target"] for candidate in promoted], ["parte"])

    def test_cross_checked_backoff_missing_active_drops_benchmark_target_when_active_side_is_empty(
        self,
    ) -> None:
        promoted = promote_shadow_candidates_for_policy(
            shadow_candidates=[
                {
                    "target": "vista",
                    "canonical_pos": "noun",
                    "benchmark_target_present": True,
                    "reviewed_trigger_support": False,
                }
            ],
            active_candidates=[],
            policy="cross_checked_backoff_missing_active_v1",
        )
        self.assertEqual(promoted, [])

    def test_cross_checked_backoff_missing_active_still_drops_cross_pos_rows_when_active_pos_exists(
        self,
    ) -> None:
        promoted = promote_shadow_candidates_for_policy(
            shadow_candidates=[
                {
                    "target": "subir",
                    "canonical_pos": "verb",
                    "benchmark_target_present": True,
                    "reviewed_trigger_support": False,
                }
            ],
            active_candidates=[{"canonical_pos": "noun"}],
            policy="cross_checked_backoff_missing_active_v1",
        )
        self.assertEqual(promoted, [])


if __name__ == "__main__":
    unittest.main()
