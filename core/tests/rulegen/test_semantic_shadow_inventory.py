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


if __name__ == "__main__":
    unittest.main()
