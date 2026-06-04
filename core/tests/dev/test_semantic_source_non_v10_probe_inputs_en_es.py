from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(CORE_ROOT), str(SCRIPTS_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402
from semantic_source_heldout_validation_en_es import (  # noqa: E402
    build_heldout_sentence_dataset,
)

INPUT_ROOT = REPO_ROOT / "docs" / "test_inputs"
BASE_DATASET = INPUT_ROOT / "semantic_routing_cases" / "en_es_source_non_v10_probe_v1.json"
HELDOUT_CASES = INPUT_ROOT / "semantic_routing_cases" / "en_es_source_non_v10_heldout_cases_v1.json"
QUEUE_JSON = INPUT_ROOT / "semantic_routing" / "semantic_source_non_v10_probe_queue_en_es_v1.json"


class SemanticSourceNonV10ProbeInputTests(unittest.TestCase):
    def test_queue_base_dataset_and_heldout_cases_stay_aligned(self) -> None:
        base_dataset = load_sentence_veto_dataset(BASE_DATASET)
        heldout_payload = _load_json(HELDOUT_CASES)
        queue_payload = _load_json(QUEUE_JSON)

        base_family_ids = _family_ids(base_dataset)
        heldout_family_ids = _family_ids(heldout_payload)
        queue_family_ids = _family_ids(queue_payload)

        self.assertEqual(len(base_family_ids), 8)
        self.assertEqual(base_family_ids, heldout_family_ids)
        self.assertEqual(base_family_ids, queue_family_ids)

        resolved_heldout = build_heldout_sentence_dataset(
            base_dataset_payload=base_dataset,
            heldout_case_payload=heldout_payload,
        )
        self.assertEqual(sum(len(family["cases"]) for family in base_dataset["families"]), 24)
        self.assertEqual(sum(len(family["cases"]) for family in resolved_heldout["families"]), 16)
        self.assertEqual(_decision_counts(resolved_heldout), {"replace": 8, "abstain": 8})

    def test_non_v10_probe_includes_mixed_noun_shadow_guardrail(self) -> None:
        base_dataset = load_sentence_veto_dataset(BASE_DATASET)
        case_family = next(
            family
            for family in base_dataset["families"]
            if family["family_id"] == "en-es:sentence-veto:case:caso"
        )

        shadow_pos_tags = {
            str(shadow.get("canonical_pos") or "").strip()
            for shadow in case_family["shadows"]
            if str(shadow.get("canonical_pos") or "").strip()
        }
        self.assertEqual(shadow_pos_tags, {"noun", "verb"})


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Expected JSON object in {path}.")
    return payload


def _family_ids(payload: dict[str, object]) -> list[str]:
    return [
        str(family.get("family_id") or "").strip()
        for family in payload.get("families", ())
        if isinstance(family, dict)
    ]


def _decision_counts(payload: dict[str, object]) -> dict[str, int]:
    counts = {"replace": 0, "abstain": 0}
    for family in payload.get("families", ()):
        if not isinstance(family, dict):
            continue
        for case in family.get("cases", ()):
            if isinstance(case, dict):
                decision = str(case.get("gold_decision") or "").strip()
                if decision in counts:
                    counts[decision] += 1
    return counts


if __name__ == "__main__":
    unittest.main()
