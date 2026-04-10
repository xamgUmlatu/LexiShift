from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.resources.dict_loaders import TranslationGlossRecord  # noqa: E402
from lexishift_core.rulegen.semantic_shadow_embedding_bridge import (  # noqa: E402
    augment_inventory_with_embedding_bridge,
    build_target_embedding_bridge_profiles,
    rank_embedding_bridge_neighbors_with_encoder,
)
from lexishift_core.rulegen.semantic_shadow_inventory import BenchmarkShadowTarget  # noqa: E402


def _record(
    *,
    translation: str,
    pos_raw: str = "noun",
    sense_gloss: str = "",
    topics: tuple[str, ...] = (),
) -> TranslationGlossRecord:
    metadata: dict[str, object] = {"dictionary_pos_canonical": pos_raw}
    if sense_gloss:
        metadata["sense_raw_glosses"] = (sense_gloss,)
    if topics:
        metadata["sense_topics"] = topics
    return TranslationGlossRecord(translation=translation, pos_raw=pos_raw, metadata=metadata)


class TestSemanticShadowEmbeddingBridge(unittest.TestCase):
    def test_build_target_embedding_bridge_profiles_collects_high_signal_fragments(self) -> None:
        profiles = build_target_embedding_bridge_profiles(
            benchmark_targets=(
                BenchmarkShadowTarget(
                    target="trabajo",
                    case_ids=("en-es:trabajo",),
                    tiers=("hard",),
                    reviewed_triggers=("job",),
                ),
            ),
            forward_records_by_target={
                "trabajo": (
                    _record(
                        translation="work",
                        pos_raw="noun",
                        sense_gloss="labour, employment, occupation, job",
                        topics=("employment",),
                    ),
                )
            },
            target_reverse_records_by_target={
                "trabajo": (
                    _record(
                        translation="job",
                        pos_raw="noun",
                        sense_gloss="task",
                    ),
                )
            },
        )

        trabajo = profiles["trabajo"]
        self.assertEqual(trabajo["primary_pos"], "noun")
        self.assertIn("work", trabajo["fragments"])
        self.assertIn("labour, employment, occupation, job", trabajo["fragments"])
        self.assertIn("job", trabajo["fragments"])
        self.assertIn("task", trabajo["fragments"])

    def test_rank_embedding_bridge_neighbors_with_encoder_prefers_same_pos_neighbors(self) -> None:
        profiles = {
            "trabajo": {
                "card_text": "job work labour",
                "primary_pos": "noun",
                "fragments": ("job work labour",),
            },
            "cargo": {
                "card_text": "position office function",
                "primary_pos": "noun",
                "fragments": ("position office function",),
            },
            "quitar": {
                "card_text": "remove take away",
                "primary_pos": "verb",
                "fragments": ("remove take away",),
            },
        }

        def _fake_encoder(texts: list[str], normalize_embeddings: bool = True) -> list[list[float]]:
            mapping = {
                "job work labour": [1.0, 0.0],
                "position office function": [0.9, 0.1],
                "remove take away": [0.0, 1.0],
            }
            return [mapping[text] for text in texts]

        neighbor_index = rank_embedding_bridge_neighbors_with_encoder(
            target_profiles=profiles,
            encoder=_fake_encoder,
            min_similarity=0.5,
            top_k=2,
        )

        self.assertEqual([row["target"] for row in neighbor_index["trabajo"]], ["cargo"])
        self.assertEqual([row["target"] for row in neighbor_index["cargo"]], ["trabajo"])
        self.assertEqual(neighbor_index["quitar"], [])

    def test_augment_inventory_with_embedding_bridge_adds_backoff_candidate(self) -> None:
        inventory = {
            "targets": [
                {
                    "target": "trabajo",
                    "trigger_entries": [
                        {
                            "trigger": "job",
                            "active_candidates": [{"target": "trabajo", "canonical_pos": "noun"}],
                            "shadow_candidates": [
                                {
                                    "target": "tarea",
                                    "canonical_pos": "noun",
                                    "benchmark_target_present": False,
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        updated = augment_inventory_with_embedding_bridge(
            inventory=inventory,
            target_profiles={
                "cargo": {
                    "card_text": "position office function",
                    "primary_pos": "noun",
                    "fragments": ("position", "office", "function"),
                }
            },
            neighbor_index={
                "trabajo": [
                    {
                        "target": "cargo",
                        "similarity": 0.71,
                        "primary_pos": "noun",
                        "fragments": ["position", "office"],
                    }
                ]
            },
        )

        trigger_entry = updated["targets"][0]["trigger_entries"][0]
        cargo = next(
            candidate
            for candidate in trigger_entry["shadow_candidates"]
            if candidate["target"] == "cargo"
        )
        self.assertEqual(cargo["candidate_sources"], ["semantic_embedding_bridge"])
        self.assertEqual(cargo["benchmark_target_present"], True)
        self.assertAlmostEqual(cargo["embedding_bridge_similarity"], 0.71, places=6)

    def test_augment_inventory_with_embedding_bridge_skips_rows_with_existing_benchmark_shadow(
        self,
    ) -> None:
        inventory = {
            "targets": [
                {
                    "target": "trabajo",
                    "trigger_entries": [
                        {
                            "trigger": "job",
                            "active_candidates": [{"target": "trabajo", "canonical_pos": "noun"}],
                            "shadow_candidates": [
                                {
                                    "target": "empleo",
                                    "canonical_pos": "noun",
                                    "benchmark_target_present": True,
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        updated = augment_inventory_with_embedding_bridge(
            inventory=inventory,
            target_profiles={
                "cargo": {
                    "card_text": "position office function",
                    "primary_pos": "noun",
                    "fragments": ("position",),
                }
            },
            neighbor_index={
                "trabajo": [
                    {
                        "target": "cargo",
                        "similarity": 0.71,
                        "primary_pos": "noun",
                        "fragments": ["position"],
                    }
                ]
            },
        )

        trigger_entry = updated["targets"][0]["trigger_entries"][0]
        self.assertEqual(
            [candidate["target"] for candidate in trigger_entry["shadow_candidates"]],
            ["empleo"],
        )

    def test_augment_inventory_with_embedding_bridge_skips_rows_with_existing_supported_shadow(
        self,
    ) -> None:
        inventory = {
            "targets": [
                {
                    "target": "trabajo",
                    "trigger_entries": [
                        {
                            "trigger": "job",
                            "active_candidates": [{"target": "trabajo", "canonical_pos": "noun"}],
                            "shadow_candidates": [
                                {
                                    "target": "empleo",
                                    "canonical_pos": "noun",
                                    "benchmark_target_present": True,
                                    "reviewed_trigger_support": False,
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        updated = augment_inventory_with_embedding_bridge(
            inventory=inventory,
            target_profiles={
                "cargo": {
                    "card_text": "position office function",
                    "primary_pos": "noun",
                    "fragments": ("position",),
                }
            },
            neighbor_index={
                "trabajo": [
                    {
                        "target": "cargo",
                        "similarity": 0.71,
                        "primary_pos": "noun",
                        "fragments": ["position"],
                    }
                ]
            },
            only_when_no_benchmark_target_shadow=False,
            support_score_min_for_backoff=3.0,
        )

        trigger_entry = updated["targets"][0]["trigger_entries"][0]
        self.assertEqual(
            [candidate["target"] for candidate in trigger_entry["shadow_candidates"]],
            ["empleo"],
        )


if __name__ == "__main__":
    unittest.main()
