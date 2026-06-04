from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.rulegen.semantic_shadow_inventory import (  # noqa: E402
    BenchmarkShadowTarget,
    filter_shadow_targets_by_trigger_support,
    promote_shadow_candidates_with_support_score,
)
from lexishift_core.rulegen.semantic_shadow_support import (  # noqa: E402
    resolve_shadow_support_score_weights,
)
from lexishift_core.rulegen.semantic_shadow_trigger_support import (  # noqa: E402
    resolve_trigger_support_score_weights,
)


class TestSemanticShadowScoring(unittest.TestCase):
    def test_promote_shadow_candidates_with_support_score_accepts_weight_overrides(self) -> None:
        shadow_candidates = [
            {
                "target": "cargo",
                "canonical_pos": "noun",
                "benchmark_target_present": True,
                "forward_trigger_support": True,
            }
        ]

        promoted_default = promote_shadow_candidates_with_support_score(
            shadow_candidates=shadow_candidates,
            active_candidates=[{"canonical_pos": "noun"}],
            min_score=3.5,
            max_promoted_shadows=1,
        )
        promoted_without_forward_reward = promote_shadow_candidates_with_support_score(
            shadow_candidates=shadow_candidates,
            active_candidates=[{"canonical_pos": "noun"}],
            min_score=3.5,
            max_promoted_shadows=1,
            support_score_weights={"forward_trigger_support": 0.0},
        )

        self.assertEqual([candidate["target"] for candidate in promoted_default], ["cargo"])
        self.assertEqual(promoted_without_forward_reward, [])

    def test_filter_shadow_targets_by_trigger_support_accepts_weight_overrides(self) -> None:
        seed_targets = (
            BenchmarkShadowTarget(
                target="cargo",
                case_ids=("en-es:cargo",),
                tiers=("hard",),
                reviewed_triggers=("job",),
            ),
        )
        filtered_default, _rows_default = filter_shadow_targets_by_trigger_support(
            seed_targets=seed_targets,
            source_targets_by_label={"forward_gloss_fragments": seed_targets},
            forward_records_by_target={"cargo": ()},
            reverse_records_by_source={"job": ()},
            forward_provider="wiktionary",
            reverse_provider="wiktionary",
            benchmark_target_map={"cargo": seed_targets[0]},
            min_score=1.0,
        )
        filtered_without_forward_fragment, _rows_overridden = (
            filter_shadow_targets_by_trigger_support(
                seed_targets=seed_targets,
                source_targets_by_label={"forward_gloss_fragments": seed_targets},
                forward_records_by_target={"cargo": ()},
                reverse_records_by_source={"job": ()},
                forward_provider="wiktionary",
                reverse_provider="wiktionary",
                benchmark_target_map={"cargo": seed_targets[0]},
                min_score=1.0,
                trigger_support_weights={"forward_gloss_fragment": 0.0},
            )
        )

        self.assertEqual(
            [tuple(target.reviewed_triggers) for target in filtered_default],
            [("job",)],
        )
        self.assertEqual(
            [tuple(target.reviewed_triggers) for target in filtered_without_forward_fragment],
            [()],
        )

    def test_resolve_shadow_support_score_weights_rejects_unknown_key(self) -> None:
        with self.assertRaises(ValueError):
            resolve_shadow_support_score_weights({"not_a_real_feature": 1.0})

    def test_resolve_trigger_support_score_weights_rejects_unknown_key(self) -> None:
        with self.assertRaises(ValueError):
            resolve_trigger_support_score_weights({"not_a_real_feature": 1.0})


if __name__ == "__main__":
    unittest.main()
