from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import lexishift_core.rulegen.pairs.en_es_compiled_selection as selection_module  # noqa: E402
from lexishift_core.rulegen.pairs.en_es_compiled_result_limiting import (  # noqa: E402
    EnEsCompiledDefinitionRowGroup,
    _apply_compiled_reverse_definition_hygiene,
    _build_compiled_definition_row_group,
    _flatten_compiled_definition_groups,
    _limit_compiled_rule_count_row_ids,
)
from lexishift_core.rulegen.pairs.en_es_compiled_scoring import (  # noqa: E402
    EnEsCompiledCandidateScoreTable,
)
from lexishift_core.rulegen.ranking import ReverseCheckScoringConfig  # noqa: E402


class TestRulegenEnEsCompiledResultLimiting(unittest.TestCase):
    def test_selection_module_reexports_definition_row_group_helper(self) -> None:
        self.assertIs(
            selection_module.EnEsCompiledDefinitionRowGroup,
            EnEsCompiledDefinitionRowGroup,
        )
        self.assertIs(
            selection_module._build_compiled_definition_row_group,
            _build_compiled_definition_row_group,
        )

    def test_flatten_compiled_definition_groups_interleaves_rows(self) -> None:
        self.assertEqual(
            _flatten_compiled_definition_groups(
                ((10, 11), (20,), (30, 31)), interleave_groups=True
            ),
            (10, 20, 30, 11, 31),
        )
        self.assertEqual(
            _flatten_compiled_definition_groups(
                ((10, 11), (20,), (30, 31)), interleave_groups=False
            ),
            (10, 11, 20, 30, 31),
        )

    def test_apply_compiled_reverse_definition_hygiene_keeps_anchor_and_strong_rows(self) -> None:
        groups = (
            EnEsCompiledDefinitionRowGroup(
                row_ids=(0,),
                sorted_row_ids=(0,),
                best_row_id=0,
                sort_key=(0.0, 0.0, 0),
                reverse_strength=0.9,
                allows_reverse_hygiene_anchor=True,
            ),
            EnEsCompiledDefinitionRowGroup(
                row_ids=(1,),
                sorted_row_ids=(1,),
                best_row_id=1,
                sort_key=(1.0, 0.0, 0),
                reverse_strength=0.2,
                allows_reverse_hygiene_anchor=False,
            ),
            EnEsCompiledDefinitionRowGroup(
                row_ids=(2,),
                sorted_row_ids=(2,),
                best_row_id=2,
                sort_key=(2.0, 0.0, 0),
                reverse_strength=None,
                allows_reverse_hygiene_anchor=False,
            ),
            EnEsCompiledDefinitionRowGroup(
                row_ids=(3,),
                sorted_row_ids=(3,),
                best_row_id=3,
                sort_key=(3.0, 0.0, 0),
                reverse_strength=0.5,
                allows_reverse_hygiene_anchor=False,
            ),
        )

        filtered = _apply_compiled_reverse_definition_hygiene(
            groups,
            reverse_check=ReverseCheckScoringConfig(enabled=True),
        )

        self.assertEqual([group.best_row_id for group in filtered], [0, 2, 3])

    def test_limit_compiled_rule_count_row_ids_uses_ranked_target_order(self) -> None:
        score_table = EnEsCompiledCandidateScoreTable(
            target_ids=(0, 0, 0),
            row_sort_keys=((3.0, 0.0, 0), (1.0, 0.0, 0), (2.0, 0.0, 0)),
            ranked_candidate_row_ids_by_target_id={0: (1, 2, 0)},
        )

        limited = _limit_compiled_rule_count_row_ids(
            (0, 2, 1),
            score_table=score_table,
            max_rules_per_target=2,
        )

        self.assertEqual(limited, (1, 2))


if __name__ == "__main__":
    unittest.main()
