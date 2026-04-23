from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.resources.dict_loaders import TranslationGlossRecord  # noqa: E402
from lexishift_core.rulegen.semantic_shadow_inventory import (  # noqa: E402
    DEFAULT_FORWARD_SEED_MAX_WORDS,
    DEFAULT_REPRESENTATIVE_PRUNING_MODE,
    BenchmarkShadowTarget,
    augment_shadow_targets_with_forward_gloss_triggers,
    build_shadow_candidate_support_details,
    build_shadow_trigger_source_index,
    build_shadow_trigger_support_details,
    build_benchmark_shadow_targets,
    build_en_es_shadow_inventory,
    build_rulegen_shadow_targets,
    filter_shadow_targets_by_trigger_support,
    promote_shadow_candidates_for_policy,
    promote_shadow_candidates_with_support_score,
    subtract_shadow_target_triggers,
)
from lexishift_core.rulegen.semantic_shadow_seed_borrowing import (  # noqa: E402
    augment_shadow_targets_with_neighbor_borrowed_triggers,
)


def _record(
    *,
    translation: str,
    pos_raw: str = "noun",
    entry_ord: int | None = None,
    sense_ord: int | None = None,
    gloss_ord: int | None = None,
    sense_gloss: str = "",
    extra_metadata: dict[str, object] | None = None,
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
    if extra_metadata:
        metadata.update(extra_metadata)
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

    def test_build_rulegen_shadow_targets_groups_rulegen_sources(self) -> None:
        targets = build_rulegen_shadow_targets(
            (
                {
                    "case_id": "en-es:pelota",
                    "target": "pelota",
                    "top3_sources": ["Ball", "sphere", "ball"],
                    "all_sources": ["ball", "sphere", "orb"],
                },
                {
                    "case_id": "en-es:pelota:alt",
                    "target": "pelota",
                    "top3_sources": ["orb"],
                    "all_sources": ["ball", "sphere", "orb", "globe"],
                },
                {
                    "case_id": "en-es:baile",
                    "target": "baile",
                    "top3_sources": ["dance", "ball"],
                    "all_sources": ["dance", "ball", "gala"],
                },
            ),
            source_field="top3_sources",
        )

        self.assertEqual([item.target for item in targets], ["baile", "pelota"])
        pelota = next(item for item in targets if item.target == "pelota")
        self.assertEqual(pelota.case_ids, ("en-es:pelota", "en-es:pelota:alt"))
        self.assertEqual(pelota.tiers, ("rulegen_top3_sources",))
        self.assertEqual(pelota.reviewed_triggers, ("ball", "sphere", "orb"))

    def test_augment_shadow_targets_with_forward_gloss_triggers_adds_short_source_only_fragments(
        self,
    ) -> None:
        seed_targets = build_rulegen_shadow_targets(
            (
                {
                    "case_id": "en-es:sacar",
                    "target": "sacar",
                    "top3_sources": ["withdraw", "draw", "unsheathe"],
                },
            ),
            source_field="top3_sources",
        )
        augmented = augment_shadow_targets_with_forward_gloss_triggers(
            seed_targets,
            forward_records_by_target={
                "sacar": (
                    _record(
                        translation="to remove, to extract, to get out, to take out",
                        pos_raw="verb",
                        entry_ord=10,
                        sense_ord=0,
                        sense_gloss="to remove, to extract, to get out, to take out",
                    ),
                    _record(
                        translation="to send out or move out something or somebody from some place",
                        pos_raw="verb",
                        entry_ord=10,
                        sense_ord=1,
                        sense_gloss="to send out or move out something or somebody from some place",
                    ),
                ),
            },
            max_words=DEFAULT_FORWARD_SEED_MAX_WORDS,
        )

        self.assertEqual(len(augmented), 1)
        sacar = augmented[0]
        self.assertEqual(sacar.target, "sacar")
        self.assertIn("forward_gloss_fragments", sacar.tiers)
        self.assertEqual(
            sacar.reviewed_triggers,
            ("withdraw", "draw", "unsheathe", "remove", "extract", "get out", "take out"),
        )

    def test_subtract_shadow_target_triggers_keeps_only_new_forward_gloss_fragments(self) -> None:
        base_targets = build_rulegen_shadow_targets(
            (
                {
                    "case_id": "en-es:sacar",
                    "target": "sacar",
                    "top3_sources": ["withdraw", "draw", "unsheathe"],
                },
            ),
            source_field="top3_sources",
        )
        augmented_targets = augment_shadow_targets_with_forward_gloss_triggers(
            base_targets,
            forward_records_by_target={
                "sacar": (
                    _record(
                        translation="to remove, to extract, to get out",
                        pos_raw="verb",
                        entry_ord=10,
                        sense_ord=0,
                        sense_gloss="to remove, to extract, to get out",
                    ),
                ),
            },
            max_words=DEFAULT_FORWARD_SEED_MAX_WORDS,
        )

        difference = subtract_shadow_target_triggers(
            augmented_targets,
            base_targets,
            tier_label="forward_gloss_fragments",
        )

        self.assertEqual(len(difference), 1)
        self.assertEqual(difference[0].reviewed_triggers, ("remove", "extract", "get out"))
        self.assertIn("forward_gloss_fragments", difference[0].tiers)

    def test_augment_shadow_targets_with_neighbor_borrowed_triggers_adds_missing_seed_from_neighbor(
        self,
    ) -> None:
        seed_targets = (
            BenchmarkShadowTarget(
                target="cargo",
                case_ids=("en-es:cargo",),
                tiers=("rulegen_top3_sources",),
                reviewed_triggers=("position",),
            ),
            BenchmarkShadowTarget(
                target="trabajo",
                case_ids=("en-es:trabajo",),
                tiers=("rulegen_top3_sources",),
                reviewed_triggers=("work", "job"),
            ),
        )

        augmented = augment_shadow_targets_with_neighbor_borrowed_triggers(
            seed_targets,
            neighbor_index={"cargo": [{"target": "trabajo", "similarity": 0.61}]},
            reverse_records_by_source={
                "work": (
                    _record(translation="trabajo"),
                    _record(translation="obra"),
                ),
                "job": (_record(translation="trabajo"),),
            },
            min_reverse_target_count=1,
            max_borrowed_triggers_per_target=1,
            max_words=1,
        )

        cargo = next(target for target in augmented if target.target == "cargo")
        trabajo = next(target for target in augmented if target.target == "trabajo")
        self.assertEqual(cargo.reviewed_triggers, ("position", "job"))
        self.assertIn("neighbor_trigger_borrow", cargo.tiers)
        self.assertEqual(trabajo.reviewed_triggers, ("work", "job"))

    def test_augment_shadow_targets_with_neighbor_borrowed_triggers_skips_zero_fanout_borrow(
        self,
    ) -> None:
        seed_targets = (
            BenchmarkShadowTarget(
                target="trabajo",
                case_ids=("en-es:trabajo",),
                tiers=("rulegen_top3_sources",),
                reviewed_triggers=("job",),
            ),
            BenchmarkShadowTarget(
                target="cargo",
                case_ids=("en-es:cargo",),
                tiers=("rulegen_top3_sources",),
                reviewed_triggers=("higher-up", "debit"),
            ),
        )

        augmented = augment_shadow_targets_with_neighbor_borrowed_triggers(
            seed_targets,
            neighbor_index={"trabajo": [{"target": "cargo", "similarity": 0.61}]},
            reverse_records_by_source={
                "higher-up": (),
                "debit": (_record(translation="débito"),),
            },
            min_reverse_target_count=1,
            max_borrowed_triggers_per_target=1,
            max_words=1,
        )

        trabajo = next(target for target in augmented if target.target == "trabajo")
        self.assertEqual(trabajo.reviewed_triggers, ("job", "debit"))

    def test_build_shadow_trigger_source_index_tracks_source_labels_per_trigger(self) -> None:
        top3_targets = build_rulegen_shadow_targets(
            (
                {
                    "case_id": "en-es:sacar",
                    "target": "sacar",
                    "top3_sources": ["withdraw", "draw"],
                },
            ),
            source_field="top3_sources",
        )
        all_targets = build_rulegen_shadow_targets(
            (
                {
                    "case_id": "en-es:sacar",
                    "target": "sacar",
                    "all_sources": ["withdraw", "draw", "remove"],
                },
            ),
            source_field="all_sources",
        )

        source_index = build_shadow_trigger_source_index(
            source_targets_by_label={
                "rulegen_top3_sources": top3_targets,
                "rulegen_all_sources": all_targets,
            }
        )

        self.assertEqual(
            source_index[("sacar", "withdraw")],
            ("rulegen_top3_sources", "rulegen_all_sources"),
        )
        self.assertEqual(source_index[("sacar", "remove")], ("rulegen_all_sources",))

    def test_build_shadow_trigger_support_details_scores_compact_source_supported_trigger(
        self,
    ) -> None:
        benchmark_target_map = {
            target.target: target
            for target in build_benchmark_shadow_targets(
                (
                    {
                        "case_id": "en-es:sacar",
                        "target": "sacar",
                        "expected_any": ["remove"],
                    },
                    {
                        "case_id": "en-es:quitar",
                        "target": "quitar",
                        "expected_any": ["remove"],
                    },
                )
            )
        }
        details = build_shadow_trigger_support_details(
            target="sacar",
            trigger="remove",
            source_labels=("rulegen_top3_sources", "forward_gloss_fragments"),
            forward_records_by_target={
                "sacar": (
                    _record(
                        translation="to remove, to extract, to get out",
                        pos_raw="verb",
                        entry_ord=10,
                        sense_ord=0,
                        sense_gloss="to remove, to extract, to get out",
                    ),
                ),
            },
            reverse_records_by_source={
                "remove": (
                    _record(
                        translation="quitar",
                        pos_raw="verb",
                        entry_ord=11,
                        sense_ord=0,
                        sense_gloss="to take away",
                    ),
                ),
            },
            forward_provider="wiktionary",
            reverse_provider="wiktionary",
            benchmark_target_map=benchmark_target_map,
        )

        self.assertEqual(
            details["trigger_support_features"],
            [
                "rulegen_top3_source",
                "forward_gloss_fragment",
                "multi_source_support",
                "active_side_support",
                "reverse_shadow_support",
            ],
        )
        self.assertEqual(details["trigger_support_penalties"], [])
        self.assertEqual(details["trigger_support_score"], 6.0)

    def test_filter_shadow_targets_by_trigger_support_drops_weak_multiword_seed(self) -> None:
        seed_targets = build_rulegen_shadow_targets(
            (
                {
                    "case_id": "en-es:sacar",
                    "target": "sacar",
                    "top3_sources": ["remove", "take out"],
                },
            ),
            source_field="top3_sources",
        )
        benchmark_target_map = {
            target.target: target
            for target in build_benchmark_shadow_targets(
                (
                    {
                        "case_id": "en-es:sacar",
                        "target": "sacar",
                        "expected_any": ["remove", "take out"],
                    },
                    {
                        "case_id": "en-es:quitar",
                        "target": "quitar",
                        "expected_any": ["remove"],
                    },
                )
            )
        }
        filtered_targets, support_rows = filter_shadow_targets_by_trigger_support(
            seed_targets=seed_targets,
            source_targets_by_label={"rulegen_top3_sources": seed_targets},
            forward_records_by_target={
                "sacar": (
                    _record(
                        translation="to remove, to extract, to get out, to take out",
                        pos_raw="verb",
                        entry_ord=10,
                        sense_ord=0,
                        sense_gloss="to remove, to extract, to get out, to take out",
                    ),
                ),
            },
            reverse_records_by_source={
                "remove": (
                    _record(
                        translation="quitar",
                        pos_raw="verb",
                        entry_ord=11,
                        sense_ord=0,
                        sense_gloss="to take away",
                    ),
                ),
                "take out": (),
            },
            forward_provider="wiktionary",
            reverse_provider="wiktionary",
            benchmark_target_map=benchmark_target_map,
            min_score=4.0,
        )

        self.assertEqual(len(filtered_targets), 1)
        self.assertEqual(filtered_targets[0].reviewed_triggers, ("remove",))
        score_by_trigger = {row["trigger"]: row["trigger_support_score"] for row in support_rows}
        self.assertGreater(score_by_trigger["remove"], score_by_trigger["take out"])

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

    def test_build_en_es_shadow_inventory_uses_active_profile_fallback_for_unmatched_trigger(
        self,
    ) -> None:
        benchmark_targets = build_benchmark_shadow_targets(
            (
                {
                    "case_id": "en-es:cargo:1",
                    "target": "cargo",
                    "tier": "hard",
                    "expected_any": ["job"],
                },
                {
                    "case_id": "en-es:trabajo:1",
                    "target": "trabajo",
                    "tier": "hard",
                    "expected_any": ["job"],
                },
            )
        )
        inventory = build_en_es_shadow_inventory(
            benchmark_targets=benchmark_targets,
            forward_records_by_target={
                "cargo": (
                    _record(
                        translation="position",
                        pos_raw="noun",
                        entry_ord=10,
                        sense_ord=0,
                        sense_gloss="professional or official position",
                    ),
                    _record(
                        translation="post",
                        pos_raw="noun",
                        entry_ord=10,
                        sense_ord=1,
                        sense_gloss="official appointment",
                    ),
                ),
                "trabajo": (
                    _record(
                        translation="work, job",
                        pos_raw="noun",
                        entry_ord=11,
                        sense_ord=0,
                        sense_gloss="work, job",
                    ),
                ),
            },
            reverse_records_by_source={
                "job": (
                    _record(
                        translation="trabajo",
                        pos_raw="noun",
                        entry_ord=12,
                        sense_ord=0,
                        sense_gloss="work, job",
                    ),
                ),
            },
            forward_provider="wiktionary",
            reverse_provider="wiktionary",
            promotion_policy="support_score_v1",
        )

        cargo_row = next(row for row in inventory["targets"] if row["target"] == "cargo")
        trigger_row = cargo_row["trigger_entries"][0]
        self.assertEqual(trigger_row["trigger"], "job")
        self.assertEqual(trigger_row["active_candidates"], [])
        self.assertEqual(trigger_row["active_profile_fallback"]["canonical_pos"], "noun")
        self.assertEqual(trigger_row["promoted_shadow_candidates"][0]["target"], "trabajo")
        self.assertIn(
            "active_profile_support",
            trigger_row["promoted_shadow_candidates"][0]["support_features"],
        )

    def test_build_en_es_shadow_inventory_uses_profile_backed_forward_index_for_seed_only_trigger(
        self,
    ) -> None:
        benchmark_targets = (
            BenchmarkShadowTarget(
                target="cargo",
                case_ids=("en-es:cargo:1",),
                tiers=("neighbor_trigger_borrow",),
                reviewed_triggers=("job",),
            ),
            BenchmarkShadowTarget(
                target="trabajo",
                case_ids=("en-es:trabajo:1",),
                tiers=("rulegen_top3_sources",),
                reviewed_triggers=("job",),
            ),
        )
        inventory = build_en_es_shadow_inventory(
            benchmark_targets=benchmark_targets,
            forward_records_by_target={
                "cargo": (
                    _record(
                        translation="position",
                        pos_raw="noun",
                        entry_ord=10,
                        sense_ord=0,
                        sense_gloss="professional or official position",
                    ),
                    _record(
                        translation="post",
                        pos_raw="noun",
                        entry_ord=10,
                        sense_ord=1,
                        sense_gloss="official appointment",
                    ),
                ),
                "trabajo": (
                    _record(
                        translation="work, job",
                        pos_raw="noun",
                        entry_ord=11,
                        sense_ord=0,
                        sense_gloss="work, job",
                    ),
                ),
            },
            reverse_records_by_source={
                "job": (
                    _record(
                        translation="trabajo",
                        pos_raw="noun",
                        entry_ord=12,
                        sense_ord=0,
                        sense_gloss="work, job",
                    ),
                ),
            },
            forward_provider="wiktionary",
            reverse_provider="wiktionary",
        )

        trabajo_row = next(row for row in inventory["targets"] if row["target"] == "trabajo")
        trigger_row = next(row for row in trabajo_row["trigger_entries"] if row["trigger"] == "job")
        cargo_shadow = next(
            candidate
            for candidate in trigger_row["shadow_candidates"]
            if candidate["target"] == "cargo"
        )
        self.assertIn("forward_index_active_profile_fallback", cargo_shadow["candidate_sources"])
        self.assertTrue(cargo_shadow.get("reviewed_trigger_support"))
        self.assertEqual(cargo_shadow["forward_trigger_support"], True)
        self.assertEqual(cargo_shadow["canonical_pos"], "noun")
        self.assertEqual(cargo_shadow["locator"]["locator_kind"], "forward_target_pos_profile")
        self.assertEqual(
            [candidate["target"] for candidate in trigger_row["promoted_shadow_candidates"]],
            ["cargo"],
        )

    def test_build_en_es_shadow_inventory_merges_duplicate_forward_index_evidence(self) -> None:
        benchmark_targets = build_benchmark_shadow_targets(
            (
                {
                    "case_id": "en-es:trabajo:1",
                    "target": "trabajo",
                    "tier": "hard",
                    "expected_any": ["work"],
                },
                {
                    "case_id": "en-es:empleo:1",
                    "target": "empleo",
                    "tier": "hard",
                    "expected_any": ["work", "employment"],
                },
            )
        )

        inventory = build_en_es_shadow_inventory(
            benchmark_targets=benchmark_targets,
            forward_records_by_target={
                "trabajo": (
                    _record(
                        translation="work",
                        pos_raw="noun",
                        entry_ord=10,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="labour",
                    ),
                ),
                "empleo": (
                    _record(
                        translation="work",
                        pos_raw="noun",
                        entry_ord=11,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="employment work",
                    ),
                    _record(
                        translation="employment",
                        pos_raw="noun",
                        entry_ord=11,
                        sense_ord=1,
                        gloss_ord=0,
                        sense_gloss="employment",
                    ),
                ),
            },
            reverse_records_by_source={
                "work": (
                    _record(
                        translation="trabajo",
                        pos_raw="noun",
                        entry_ord=20,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="labour",
                    ),
                    _record(
                        translation="empleo",
                        pos_raw="noun",
                        entry_ord=21,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="employment work",
                    ),
                ),
                "employment": (
                    _record(
                        translation="empleo",
                        pos_raw="noun",
                        entry_ord=22,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="employment",
                    ),
                ),
            },
            forward_provider="wiktionary",
            reverse_provider="wiktionary",
        )

        trabajo_row = next(row for row in inventory["targets"] if row["target"] == "trabajo")
        trigger_row = next(
            row for row in trabajo_row["trigger_entries"] if row["trigger"] == "work"
        )
        empleo_shadow = next(
            candidate
            for candidate in trigger_row["shadow_candidates"]
            if candidate["target"] == "empleo"
        )

        self.assertIn("reverse_lookup", empleo_shadow["candidate_sources"])
        self.assertIn("forward_index", empleo_shadow["candidate_sources"])
        self.assertIn("semantic_bridge", empleo_shadow["candidate_sources"])
        self.assertTrue(empleo_shadow["benchmark_target_present"])
        self.assertTrue(empleo_shadow["reviewed_trigger_support"])
        self.assertTrue(empleo_shadow["forward_trigger_support"])
        self.assertIn("employment", empleo_shadow["target_trigger_family_terms"])
        self.assertIn("employment", empleo_shadow["forward_neighborhood_terms"])
        self.assertIn("work", trigger_row["active_candidates"][0]["target_trigger_family_terms"])
        self.assertIn("work", trigger_row["active_candidates"][0]["forward_neighborhood_terms"])

    def test_support_score_uses_active_profile_fallback_when_active_candidates_are_missing(
        self,
    ) -> None:
        promoted = promote_shadow_candidates_with_support_score(
            shadow_candidates=(
                {
                    "target": "trabajo",
                    "canonical_pos": "noun",
                    "reviewed_trigger_support": True,
                    "benchmark_target_present": True,
                },
            ),
            active_candidates=(),
            active_profile_fallback={"canonical_pos": "noun"},
            min_score=5.0,
            max_promoted_shadows=1,
        )

        self.assertEqual([candidate["target"] for candidate in promoted], ["trabajo"])
        self.assertEqual(promoted[0]["support_score"], 5.0)
        self.assertEqual(promoted[0]["same_pos_as_active"], True)
        self.assertIn("active_profile_support", promoted[0]["support_features"])
        self.assertNotIn("active_side_support", promoted[0]["support_features"])

    def test_support_score_representative_pruning_keeps_one_sense_label_pos_representative(
        self,
    ) -> None:
        active_candidates = [{"canonical_pos": "noun", "target_frequency_score": 0.8}]
        shadow_candidates = [
            {
                "target": "chochera",
                "sense_label": "person whose company one enjoys",
                "canonical_pos": "noun",
                "reviewed_trigger_support": False,
                "benchmark_target_present": False,
                "target_frequency_score": 0.2,
            },
            {
                "target": "amistad",
                "sense_label": "person whose company one enjoys",
                "canonical_pos": "noun",
                "reviewed_trigger_support": True,
                "benchmark_target_present": True,
                "target_frequency_score": 0.5,
            },
            {
                "target": "colega",
                "sense_label": "workmate or colleague",
                "canonical_pos": "noun",
                "reviewed_trigger_support": True,
                "benchmark_target_present": True,
                "target_frequency_score": 0.6,
            },
        ]

        unpruned = promote_shadow_candidates_with_support_score(
            shadow_candidates=shadow_candidates,
            active_candidates=active_candidates,
            min_score=1.0,
            max_promoted_shadows=3,
            representative_pruning_mode=DEFAULT_REPRESENTATIVE_PRUNING_MODE,
        )
        pruned = promote_shadow_candidates_with_support_score(
            shadow_candidates=shadow_candidates,
            active_candidates=active_candidates,
            min_score=1.0,
            max_promoted_shadows=3,
            representative_pruning_mode="sense_label_pos_v1",
        )

        self.assertEqual(
            [candidate["target"] for candidate in unpruned], ["colega", "amistad", "chochera"]
        )
        self.assertEqual([candidate["target"] for candidate in pruned], ["colega", "amistad"])
        amistad = next(candidate for candidate in pruned if candidate["target"] == "amistad")
        self.assertEqual(amistad["representative_pruning_mode"], "sense_label_pos_v1")
        self.assertEqual(amistad["representative_cluster_size"], 2)

    def test_support_score_representative_pruning_falls_back_to_target_when_sense_label_missing(
        self,
    ) -> None:
        promoted = promote_shadow_candidates_with_support_score(
            shadow_candidates=(
                {
                    "target": "alpha",
                    "canonical_pos": "noun",
                    "reviewed_trigger_support": True,
                    "benchmark_target_present": True,
                },
                {
                    "target": "beta",
                    "canonical_pos": "noun",
                    "reviewed_trigger_support": True,
                    "benchmark_target_present": True,
                },
            ),
            active_candidates=({"canonical_pos": "noun"},),
            min_score=1.0,
            max_promoted_shadows=3,
            representative_pruning_mode="sense_label_pos_v1",
        )

        self.assertEqual([candidate["target"] for candidate in promoted], ["beta", "alpha"])

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

    def test_build_en_es_shadow_inventory_adds_semantic_bridge_candidate_from_shared_marker(
        self,
    ) -> None:
        benchmark_targets = (
            BenchmarkShadowTarget(
                target="trabajo",
                case_ids=("en-es:trabajo:1",),
                tiers=("rulegen_top3_sources",),
                reviewed_triggers=("job",),
            ),
            BenchmarkShadowTarget(
                target="cargo",
                case_ids=("en-es:cargo:1",),
                tiers=("rulegen_top3_sources", "forward_gloss_fragments"),
                reviewed_triggers=("position",),
            ),
        )
        inventory = build_en_es_shadow_inventory(
            benchmark_targets=benchmark_targets,
            forward_records_by_target={
                "trabajo": (
                    _record(
                        translation="job",
                        pos_raw="noun",
                        entry_ord=10,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="economic role for which a person is paid",
                    ),
                ),
                "cargo": (
                    _record(
                        translation="position",
                        pos_raw="noun",
                        entry_ord=11,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="professional or official position",
                    ),
                ),
            },
            reverse_records_by_source={
                "job": (
                    _record(
                        translation="trabajo",
                        pos_raw="noun",
                        entry_ord=20,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="employment role position",
                        extra_metadata={"entry_categories": ("en:Employment",)},
                    ),
                ),
                "position": (
                    _record(
                        translation="puesto",
                        pos_raw="noun",
                        entry_ord=21,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="post of employment",
                    ),
                ),
            },
            target_reverse_records_by_target={
                "trabajo": (
                    _record(
                        translation="job",
                        pos_raw="noun",
                        entry_ord=30,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="employment role position",
                        extra_metadata={"entry_categories": ("en:Employment",)},
                    ),
                ),
                "cargo": (
                    _record(
                        translation="function",
                        pos_raw="noun",
                        entry_ord=31,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="employment role position",
                    ),
                ),
            },
            forward_provider="wiktionary",
            reverse_provider="wiktionary",
            promotion_policy="support_score_v1",
        )

        trabajo_row = next(row for row in inventory["targets"] if row["target"] == "trabajo")
        trigger_row = trabajo_row["trigger_entries"][0]
        bridge_candidate = next(
            candidate
            for candidate in trigger_row["shadow_candidates"]
            if candidate["target"] == "cargo"
        )
        self.assertEqual(bridge_candidate["candidate_sources"], ["semantic_bridge"])
        self.assertIn("employment", bridge_candidate["semantic_bridge_markers"])
        promoted = trigger_row["promoted_shadow_candidates"]
        self.assertEqual([candidate["target"] for candidate in promoted], ["cargo"])

    def test_build_en_es_shadow_inventory_marks_forward_profile_candidate_with_seed_trigger_support(
        self,
    ) -> None:
        benchmark_targets = (
            BenchmarkShadowTarget(
                target="trabajo",
                case_ids=("en-es:trabajo:1",),
                tiers=("rulegen_top3_sources",),
                reviewed_triggers=("job",),
            ),
            BenchmarkShadowTarget(
                target="cargo",
                case_ids=("en-es:cargo:1",),
                tiers=("rulegen_top3_sources",),
                reviewed_triggers=("job", "position"),
            ),
        )
        inventory = build_en_es_shadow_inventory(
            benchmark_targets=benchmark_targets,
            forward_records_by_target={
                "trabajo": (
                    _record(
                        translation="job",
                        pos_raw="noun",
                        entry_ord=10,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="economic role for which a person is paid",
                    ),
                ),
                "cargo": (
                    _record(
                        translation="position",
                        pos_raw="noun",
                        entry_ord=11,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="professional or official position",
                    ),
                ),
            },
            reverse_records_by_source={
                "job": (
                    _record(
                        translation="trabajo",
                        pos_raw="noun",
                        entry_ord=20,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="employment role position",
                        extra_metadata={"entry_categories": ("en:Employment",)},
                    ),
                ),
                "position": (
                    _record(
                        translation="puesto",
                        pos_raw="noun",
                        entry_ord=21,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="post of employment",
                    ),
                ),
            },
            target_reverse_records_by_target={
                "trabajo": (
                    _record(
                        translation="job",
                        pos_raw="noun",
                        entry_ord=30,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="employment role position",
                        extra_metadata={"entry_categories": ("en:Employment",)},
                    ),
                ),
                "cargo": (
                    _record(
                        translation="function",
                        pos_raw="noun",
                        entry_ord=31,
                        sense_ord=0,
                        gloss_ord=0,
                        sense_gloss="employment role position",
                    ),
                ),
            },
            forward_provider="wiktionary",
            reverse_provider="wiktionary",
            promotion_policy="support_score_v1",
        )

        trabajo_row = next(row for row in inventory["targets"] if row["target"] == "trabajo")
        trigger_row = trabajo_row["trigger_entries"][0]
        bridge_candidate = next(
            candidate
            for candidate in trigger_row["shadow_candidates"]
            if candidate["target"] == "cargo"
        )
        self.assertEqual(bridge_candidate["forward_trigger_support"], True)
        self.assertTrue(bridge_candidate.get("reviewed_trigger_support"))

    def test_build_en_es_shadow_inventory_can_bridge_from_sense_examples(self) -> None:
        inventory_without_examples = build_en_es_shadow_inventory(
            benchmark_targets=(
                BenchmarkShadowTarget(
                    target="trabajo",
                    case_ids=("en-es:trabajo",),
                    tiers=("reviewed",),
                    reviewed_triggers=("job",),
                ),
                BenchmarkShadowTarget(
                    target="cargo",
                    case_ids=("en-es:cargo",),
                    tiers=("reviewed",),
                    reviewed_triggers=("position",),
                ),
            ),
            forward_records_by_target={
                "trabajo": (
                    _record(
                        translation="job",
                        pos_raw="noun",
                        entry_ord=10,
                        sense_ord=0,
                        gloss_ord=0,
                        extra_metadata={
                            "sense_examples": (
                                {
                                    "text": "She accepted an office role with pension duties.",
                                    "translation": "She accepted an office role with pension duties.",
                                },
                            )
                        },
                    ),
                ),
                "cargo": (
                    _record(
                        translation="function",
                        pos_raw="noun",
                        entry_ord=11,
                        sense_ord=0,
                        gloss_ord=0,
                        extra_metadata={
                            "sense_examples": (
                                {
                                    "text": "He took an office role with pension duties.",
                                    "translation": "He took an office role with pension duties.",
                                },
                            )
                        },
                    ),
                ),
            },
            reverse_records_by_source={"job": ()},
            target_reverse_records_by_target={},
            forward_provider="wiktionary",
            reverse_provider="wiktionary",
            promotion_policy="support_score_v1",
            semantic_bridge_include_examples=False,
        )

        inventory_with_examples = build_en_es_shadow_inventory(
            benchmark_targets=(
                BenchmarkShadowTarget(
                    target="trabajo",
                    case_ids=("en-es:trabajo",),
                    tiers=("reviewed",),
                    reviewed_triggers=("job",),
                ),
                BenchmarkShadowTarget(
                    target="cargo",
                    case_ids=("en-es:cargo",),
                    tiers=("reviewed",),
                    reviewed_triggers=("position",),
                ),
            ),
            forward_records_by_target={
                "trabajo": (
                    _record(
                        translation="job",
                        pos_raw="noun",
                        entry_ord=10,
                        sense_ord=0,
                        gloss_ord=0,
                        extra_metadata={
                            "sense_examples": (
                                {
                                    "text": "She accepted an office role with pension duties.",
                                    "translation": "She accepted an office role with pension duties.",
                                },
                            )
                        },
                    ),
                ),
                "cargo": (
                    _record(
                        translation="function",
                        pos_raw="noun",
                        entry_ord=11,
                        sense_ord=0,
                        gloss_ord=0,
                        extra_metadata={
                            "sense_examples": (
                                {
                                    "text": "He took an office role with pension duties.",
                                    "translation": "He took an office role with pension duties.",
                                },
                            )
                        },
                    ),
                ),
            },
            reverse_records_by_source={"job": ()},
            target_reverse_records_by_target={},
            forward_provider="wiktionary",
            reverse_provider="wiktionary",
            promotion_policy="support_score_v1",
            semantic_bridge_include_examples=True,
        )

        trabajo_row_without = next(
            row for row in inventory_without_examples["targets"] if row["target"] == "trabajo"
        )
        trigger_row_without = trabajo_row_without["trigger_entries"][0]
        self.assertFalse(
            any(
                candidate["target"] == "cargo"
                for candidate in trigger_row_without["shadow_candidates"]
            )
        )

        trabajo_row = next(
            row for row in inventory_with_examples["targets"] if row["target"] == "trabajo"
        )
        trigger_row = trabajo_row["trigger_entries"][0]
        bridge_candidate = next(
            candidate
            for candidate in trigger_row["shadow_candidates"]
            if candidate["target"] == "cargo"
        )
        self.assertIn("office", bridge_candidate.get("semantic_bridge_markers", ()))
        self.assertIn("pension", bridge_candidate.get("semantic_bridge_markers", ()))

    def test_build_en_es_shadow_inventory_can_bridge_from_aux_text_metadata(self) -> None:
        inventory_without_aux_text = build_en_es_shadow_inventory(
            benchmark_targets=(
                BenchmarkShadowTarget(
                    target="trabajo",
                    case_ids=("en-es:trabajo",),
                    tiers=("reviewed",),
                    reviewed_triggers=("job",),
                ),
                BenchmarkShadowTarget(
                    target="cargo",
                    case_ids=("en-es:cargo",),
                    tiers=("reviewed",),
                    reviewed_triggers=("position",),
                ),
            ),
            forward_records_by_target={
                "trabajo": (
                    _record(
                        translation="job",
                        pos_raw="noun",
                        entry_ord=10,
                        sense_ord=0,
                        gloss_ord=0,
                        extra_metadata={
                            "translation_sense_text": "office role with pension duties",
                        },
                    ),
                ),
                "cargo": (
                    _record(
                        translation="function",
                        pos_raw="noun",
                        entry_ord=11,
                        sense_ord=0,
                        gloss_ord=0,
                        extra_metadata={
                            "translation_sense_text": "office role with pension duties",
                        },
                    ),
                ),
            },
            reverse_records_by_source={"job": ()},
            target_reverse_records_by_target={},
            forward_provider="wiktionary",
            reverse_provider="wiktionary",
            promotion_policy="support_score_v1",
            semantic_bridge_include_aux_text=False,
        )

        inventory_with_aux_text = build_en_es_shadow_inventory(
            benchmark_targets=(
                BenchmarkShadowTarget(
                    target="trabajo",
                    case_ids=("en-es:trabajo",),
                    tiers=("reviewed",),
                    reviewed_triggers=("job",),
                ),
                BenchmarkShadowTarget(
                    target="cargo",
                    case_ids=("en-es:cargo",),
                    tiers=("reviewed",),
                    reviewed_triggers=("position",),
                ),
            ),
            forward_records_by_target={
                "trabajo": (
                    _record(
                        translation="job",
                        pos_raw="noun",
                        entry_ord=10,
                        sense_ord=0,
                        gloss_ord=0,
                        extra_metadata={
                            "translation_sense_text": "office role with pension duties",
                        },
                    ),
                ),
                "cargo": (
                    _record(
                        translation="function",
                        pos_raw="noun",
                        entry_ord=11,
                        sense_ord=0,
                        gloss_ord=0,
                        extra_metadata={
                            "translation_sense_text": "office role with pension duties",
                        },
                    ),
                ),
            },
            reverse_records_by_source={"job": ()},
            target_reverse_records_by_target={},
            forward_provider="wiktionary",
            reverse_provider="wiktionary",
            promotion_policy="support_score_v1",
            semantic_bridge_include_aux_text=True,
        )

        trabajo_row_without = next(
            row for row in inventory_without_aux_text["targets"] if row["target"] == "trabajo"
        )
        trigger_row_without = trabajo_row_without["trigger_entries"][0]
        self.assertFalse(
            any(
                candidate["target"] == "cargo"
                for candidate in trigger_row_without["shadow_candidates"]
            )
        )

        trabajo_row = next(
            row for row in inventory_with_aux_text["targets"] if row["target"] == "trabajo"
        )
        trigger_row = trabajo_row["trigger_entries"][0]
        bridge_candidate = next(
            candidate
            for candidate in trigger_row["shadow_candidates"]
            if candidate["target"] == "cargo"
        )
        self.assertIn("office", bridge_candidate.get("semantic_bridge_markers", ()))
        self.assertIn("pension", bridge_candidate.get("semantic_bridge_markers", ()))

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

    def test_build_shadow_candidate_support_details_scores_cross_pos_mismatch_conservatively(
        self,
    ) -> None:
        support = build_shadow_candidate_support_details(
            candidate={
                "target": "vista",
                "canonical_pos": "noun",
                "benchmark_target_present": True,
                "reviewed_trigger_support": False,
            },
            active_candidates=[{"canonical_pos": "verb"}],
        )

        self.assertEqual(
            support["support_features"],
            ["benchmark_target_present", "active_side_support"],
        )
        self.assertEqual(support["support_penalties"], ["cross_pos_mismatch_penalty"])
        self.assertEqual(support["support_score"], 1.0)

    def test_build_shadow_candidate_support_details_adds_semantic_bridge_feature(self) -> None:
        support = build_shadow_candidate_support_details(
            candidate={
                "target": "cargo",
                "canonical_pos": "noun",
                "benchmark_target_present": True,
                "reviewed_trigger_support": False,
                "semantic_bridge_markers": ["employment"],
            },
            active_candidates=[{"canonical_pos": "noun"}],
        )

        self.assertEqual(
            support["support_features"],
            [
                "benchmark_target_present",
                "same_pos_as_active",
                "active_side_support",
                "semantic_bridge_support",
            ],
        )
        self.assertEqual(support["support_penalties"], [])
        self.assertEqual(support["support_score"], 4.0)

    def test_build_shadow_candidate_support_details_adds_multi_source_candidate_feature(
        self,
    ) -> None:
        support = build_shadow_candidate_support_details(
            candidate={
                "target": "cargo",
                "canonical_pos": "noun",
                "benchmark_target_present": True,
                "candidate_sources": ["reverse_lookup", "forward_index"],
            },
            active_candidates=[{"canonical_pos": "noun"}],
            score_weights={"multi_source_candidate_support": 1.5},
        )

        self.assertIn("multi_source_candidate_support", support["support_features"])
        self.assertEqual(support["support_penalties"], [])
        self.assertEqual(support["support_score"], 4.5)

    def test_build_shadow_candidate_support_details_adds_triplet_core_bonus(self) -> None:
        support = build_shadow_candidate_support_details(
            candidate={
                "target": "terreno",
                "canonical_pos": "noun",
                "benchmark_target_present": True,
            },
            active_candidates=[{"canonical_pos": "noun"}],
            score_weights={"triplet_core_bonus": 1.0},
        )

        self.assertIn("triplet_core_bonus", support["support_features"])
        self.assertEqual(support["support_penalties"], [])
        self.assertEqual(float(support["support_score_breakdown"]["triplet_core_bonus"]), 1.0)
        self.assertEqual(support["support_score"], 4.0)

    def test_build_shadow_candidate_support_details_adds_triplet_forward_bonus(self) -> None:
        support = build_shadow_candidate_support_details(
            candidate={
                "target": "empleo",
                "canonical_pos": "noun",
                "benchmark_target_present": True,
                "forward_trigger_support": True,
            },
            active_candidates=[{"canonical_pos": "noun"}],
            score_weights={
                "triplet_core_bonus": 1.0,
                "triplet_forward_bonus": 0.5,
            },
        )

        self.assertIn("triplet_core_bonus", support["support_features"])
        self.assertIn("triplet_forward_bonus", support["support_features"])
        self.assertEqual(float(support["support_score_breakdown"]["triplet_core_bonus"]), 1.0)
        self.assertEqual(
            float(support["support_score_breakdown"]["triplet_forward_bonus"]),
            0.5,
        )
        self.assertEqual(support["support_score"], 5.0)

    def test_build_shadow_candidate_support_details_adds_triplet_bridge_guard_bonus(
        self,
    ) -> None:
        support = build_shadow_candidate_support_details(
            candidate={
                "target": "rejilla",
                "canonical_pos": "noun",
                "benchmark_target_present": True,
                "semantic_bridge_markers": ["mesh"],
            },
            active_candidates=[{"canonical_pos": "noun"}],
            score_weights={
                "triplet_core_bonus": 1.0,
                "triplet_bridge_guard_bonus": 1.0,
            },
        )

        self.assertIn("triplet_core_bonus", support["support_features"])
        self.assertIn("triplet_bridge_guard_bonus", support["support_features"])
        self.assertEqual(
            float(support["support_score_breakdown"]["triplet_bridge_guard_bonus"]),
            1.0,
        )
        self.assertEqual(support["support_score"], 6.0)

    def test_build_shadow_candidate_support_details_adds_forward_neighborhood_overlap(
        self,
    ) -> None:
        support = build_shadow_candidate_support_details(
            candidate={
                "target": "tierra",
                "canonical_pos": "noun",
                "benchmark_target_present": True,
                "forward_neighborhood_terms": ["land", "ground", "earth"],
            },
            active_candidates=[
                {
                    "canonical_pos": "noun",
                    "forward_neighborhood_terms": ["land", "earth", "soil"],
                }
            ],
            score_weights={"forward_neighborhood_overlap": 2.0},
        )

        self.assertIn("forward_neighborhood_overlap", support["support_features"])
        self.assertEqual(support["support_penalties"], [])
        self.assertAlmostEqual(support["forward_neighborhood_overlap_score"], 0.5)
        self.assertEqual(
            support["forward_neighborhood_overlap_terms"],
            ["earth", "land"],
        )
        self.assertAlmostEqual(support["support_score"], 4.0)

    def test_build_shadow_candidate_support_details_adds_trigger_family_reentry(
        self,
    ) -> None:
        support = build_shadow_candidate_support_details(
            candidate={
                "target": "terreno",
                "canonical_pos": "noun",
                "benchmark_target_present": True,
                "target_trigger_family_terms": ["field", "land", "ground"],
                "forward_neighborhood_terms": ["land", "ground", "terrain"],
            },
            active_candidates=[
                {
                    "canonical_pos": "noun",
                    "target_trigger_family_terms": ["field", "land", "ground"],
                    "forward_neighborhood_terms": ["field", "country", "land"],
                }
            ],
            active_trigger="field",
            score_weights={"trigger_family_reentry": 2.0},
        )

        self.assertIn("trigger_family_reentry", support["support_features"])
        self.assertEqual(support["support_penalties"], [])
        self.assertAlmostEqual(support["trigger_family_reentry_score"], 0.5)
        self.assertEqual(support["trigger_family_reentry_terms"], ["ground", "land"])
        self.assertEqual(support["trigger_family_reentry_shared_alias_count"], 2)
        self.assertAlmostEqual(support["support_score"], 4.0)

    def test_build_shadow_candidate_support_details_adds_frequency_similarity_bonus(self) -> None:
        support = build_shadow_candidate_support_details(
            candidate={
                "target": "cargo",
                "canonical_pos": "noun",
                "benchmark_target_present": True,
                "reviewed_trigger_support": False,
                "target_frequency_score": 0.82,
            },
            active_candidates=[{"canonical_pos": "noun", "target_frequency_score": 0.80}],
            frequency_similarity_weight=0.5,
            frequency_similarity_tau=0.10,
        )

        self.assertIn("frequency_similarity_bonus", support["support_features"])
        self.assertTrue(support["frequency_similarity_present"])
        self.assertGreater(float(support["frequency_similarity_score"]), 0.8)
        self.assertGreater(
            float(support["support_score_breakdown"]["frequency_similarity_bonus"]),
            0.4,
        )

    def test_build_shadow_candidate_support_details_treats_forward_trigger_support_as_weaker_evidence(
        self,
    ) -> None:
        support = build_shadow_candidate_support_details(
            candidate={
                "target": "cargo",
                "canonical_pos": "noun",
                "benchmark_target_present": True,
                "forward_trigger_support": True,
            },
            active_candidates=[{"canonical_pos": "noun"}],
        )

        self.assertEqual(
            support["support_features"],
            [
                "forward_trigger_support",
                "benchmark_target_present",
                "same_pos_as_active",
                "active_side_support",
            ],
        )
        self.assertEqual(support["support_penalties"], [])
        self.assertEqual(support["support_score"], 3.5)

    def test_build_shadow_candidate_support_details_counts_embedding_bridge_similarity(
        self,
    ) -> None:
        support = build_shadow_candidate_support_details(
            candidate={
                "target": "cargo",
                "canonical_pos": "noun",
                "benchmark_target_present": True,
                "reviewed_trigger_support": False,
                "embedding_bridge_similarity": 0.71,
            },
            active_candidates=[{"canonical_pos": "noun"}],
        )

        self.assertEqual(
            support["support_features"],
            [
                "benchmark_target_present",
                "same_pos_as_active",
                "active_side_support",
                "semantic_bridge_support",
            ],
        )
        self.assertEqual(support["support_score"], 4.0)

    def test_promote_shadow_candidates_with_support_score_prefers_supported_rows(self) -> None:
        promoted = promote_shadow_candidates_with_support_score(
            shadow_candidates=[
                {
                    "target": "cuadro",
                    "canonical_pos": "noun",
                    "benchmark_target_present": True,
                    "reviewed_trigger_support": False,
                },
                {
                    "target": "vista",
                    "canonical_pos": "verb",
                    "benchmark_target_present": True,
                    "reviewed_trigger_support": False,
                },
                {
                    "target": "estructura conceptual",
                    "canonical_pos": "noun",
                    "benchmark_target_present": False,
                    "reviewed_trigger_support": False,
                },
            ],
            active_candidates=[{"canonical_pos": "noun"}],
            min_score=3.0,
            max_promoted_shadows=2,
        )

        self.assertEqual([candidate["target"] for candidate in promoted], ["cuadro"])
        self.assertEqual(promoted[0]["support_score"], 3.0)
        self.assertEqual(
            promoted[0]["promotion_reasons"],
            [
                "benchmark_target_present",
                "same_pos_as_active",
                "active_side_support",
            ],
        )

    def test_promote_shadow_candidates_with_support_score_drops_forward_only_candidate_at_strict_threshold(
        self,
    ) -> None:
        promoted = promote_shadow_candidates_with_support_score(
            shadow_candidates=[
                {
                    "target": "cargo",
                    "canonical_pos": "noun",
                    "benchmark_target_present": True,
                    "forward_trigger_support": True,
                },
                {
                    "target": "trabajo",
                    "canonical_pos": "noun",
                    "benchmark_target_present": True,
                    "reviewed_trigger_support": True,
                },
            ],
            active_candidates=[{"canonical_pos": "noun"}],
            min_score=5.0,
            max_promoted_shadows=2,
        )

        self.assertEqual([candidate["target"] for candidate in promoted], ["trabajo"])

    def test_promote_shadow_candidates_with_support_score_can_use_overlap_with_raised_threshold(
        self,
    ) -> None:
        promoted = promote_shadow_candidates_with_support_score(
            shadow_candidates=[
                {
                    "target": "tierra",
                    "canonical_pos": "noun",
                    "reviewed_trigger_support": True,
                    "forward_trigger_support": True,
                    "benchmark_target_present": True,
                    "candidate_sources": ["reverse_lookup", "forward_index"],
                    "forward_neighborhood_terms": ["land", "ground", "earth"],
                },
                {
                    "target": "hora",
                    "canonical_pos": "noun",
                    "reviewed_trigger_support": True,
                    "forward_trigger_support": True,
                    "benchmark_target_present": True,
                    "candidate_sources": ["reverse_lookup", "forward_index"],
                    "forward_neighborhood_terms": ["period", "hour", "time"],
                },
            ],
            active_candidates=[
                {
                    "canonical_pos": "verb",
                    "forward_neighborhood_terms": ["land", "ground", "earth", "soil"],
                }
            ],
            min_score=5.5,
            max_promoted_shadows=2,
            support_score_weights={
                "multi_source_candidate_support": 1.5,
                "forward_neighborhood_overlap": 2.0,
            },
        )

        self.assertEqual([candidate["target"] for candidate in promoted], ["tierra"])
        self.assertAlmostEqual(promoted[0]["forward_neighborhood_overlap_score"], 0.75)
        self.assertAlmostEqual(promoted[0]["support_score"], 6.5)

    def test_promote_shadow_candidates_with_support_score_can_use_trigger_family_reentry(
        self,
    ) -> None:
        promoted = promote_shadow_candidates_with_support_score(
            shadow_candidates=[
                {
                    "target": "terreno",
                    "canonical_pos": "noun",
                    "reviewed_trigger_support": True,
                    "forward_trigger_support": True,
                    "benchmark_target_present": True,
                    "candidate_sources": ["reverse_lookup", "forward_index"],
                    "target_trigger_family_terms": ["field", "land", "ground"],
                    "forward_neighborhood_terms": ["land", "ground", "terrain"],
                },
                {
                    "target": "area",
                    "canonical_pos": "noun",
                    "reviewed_trigger_support": True,
                    "forward_trigger_support": True,
                    "benchmark_target_present": True,
                    "candidate_sources": ["reverse_lookup", "forward_index"],
                    "target_trigger_family_terms": ["field", "area"],
                    "forward_neighborhood_terms": ["field", "area", "region"],
                },
            ],
            active_candidates=[
                {
                    "canonical_pos": "verb",
                    "target_trigger_family_terms": ["field", "land", "ground"],
                    "forward_neighborhood_terms": ["field", "country", "land"],
                }
            ],
            active_trigger="field",
            min_score=5.5,
            max_promoted_shadows=2,
            support_score_weights={
                "multi_source_candidate_support": 1.5,
                "trigger_family_reentry": 2.0,
            },
        )

        self.assertEqual([candidate["target"] for candidate in promoted], ["terreno"])
        self.assertAlmostEqual(promoted[0]["trigger_family_reentry_score"], 0.5)
        self.assertEqual(promoted[0]["trigger_family_reentry_shared_alias_count"], 2)
        self.assertAlmostEqual(promoted[0]["support_score"], 6.0)

    def test_promote_shadow_candidates_with_support_score_can_prefer_frequency_representative(
        self,
    ) -> None:
        promoted = promote_shadow_candidates_with_support_score(
            shadow_candidates=[
                {
                    "target": "camello",
                    "canonical_pos": "noun",
                    "benchmark_target_present": True,
                    "reviewed_trigger_support": False,
                    "target_frequency_present": True,
                    "target_frequency_value": 5.0,
                    "target_frequency_rank": 50.0,
                    "target_frequency_score": 0.20,
                },
                {
                    "target": "cargo",
                    "canonical_pos": "noun",
                    "benchmark_target_present": True,
                    "reviewed_trigger_support": False,
                    "target_frequency_present": True,
                    "target_frequency_value": 90.0,
                    "target_frequency_rank": 2.0,
                    "target_frequency_score": 0.95,
                },
            ],
            active_candidates=[{"canonical_pos": "noun"}],
            min_score=3.0,
            max_promoted_shadows=1,
            frequency_representative_bonus=1.0,
            frequency_representative_top_k=1,
        )

        self.assertEqual([candidate["target"] for candidate in promoted], ["cargo"])
        self.assertIn("frequency_representative_bonus", promoted[0]["support_features"])

    def test_promote_shadow_candidates_with_support_score_can_use_frequency_similarity(
        self,
    ) -> None:
        promoted = promote_shadow_candidates_with_support_score(
            shadow_candidates=[
                {
                    "target": "cargo",
                    "canonical_pos": "noun",
                    "benchmark_target_present": True,
                    "reviewed_trigger_support": False,
                    "target_frequency_score": 0.82,
                },
                {
                    "target": "camello",
                    "canonical_pos": "noun",
                    "benchmark_target_present": True,
                    "reviewed_trigger_support": False,
                    "target_frequency_score": 0.20,
                },
            ],
            active_candidates=[{"canonical_pos": "noun", "target_frequency_score": 0.80}],
            min_score=3.4,
            max_promoted_shadows=1,
            frequency_similarity_weight=0.5,
            frequency_similarity_tau=0.10,
        )

        self.assertEqual([candidate["target"] for candidate in promoted], ["cargo"])
        self.assertIn("frequency_similarity_bonus", promoted[0]["support_features"])


if __name__ == "__main__":
    unittest.main()
