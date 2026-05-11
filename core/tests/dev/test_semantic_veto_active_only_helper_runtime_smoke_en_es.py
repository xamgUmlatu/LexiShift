from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = (
    PROJECT_ROOT / "scripts" / "testing" / "semantic_veto_active_only_helper_runtime_smoke_en_es.py"
)


def _load_script_module():
    spec = importlib.util.spec_from_file_location(
        "semantic_veto_active_only_helper_smoke", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SemanticVetoActiveOnlyHelperRuntimeSmokeTests(unittest.TestCase):
    def test_helper_runtime_smoke_publishes_fixture_and_scores_active_only_family(self) -> None:
        module = _load_script_module()
        dataset_payload = {
            "schema_version": 1,
            "pair": "en-es",
            "families": [
                {
                    "family_id": "en-es:unit:dentist:dentista",
                    "trigger": "dentist",
                    "cases": [
                        {
                            "case_id": "case:dentist:positive",
                            "sentence": "She booked a dentist appointment near the station.",
                            "gold_decision": "replace",
                            "gold_winner": "sense:dentista",
                        }
                    ],
                }
            ],
        }
        candidate_inventory_payload = {
            "schema_version": 1,
            "pair": "en-es",
            "profile_id": "inventory_replay",
            "generated_at": "2026-05-08T00:00:00Z",
            "triggers": {
                "en-es:unit:dentist:dentista:trigger": {
                    "trigger_id": "en-es:unit:dentist:dentista:trigger",
                    "source_phrase": "dentist",
                    "normalized_source_phrase": "dentist",
                    "token_count": 1,
                }
            },
            "senses": {
                "sense:dentista": {
                    "sense_id": "sense:dentista",
                    "target_lemma": "dentista",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "all_evidence_text": "dentist appointment medical professional station",
                        "sense_label": "dentist -> dentista",
                    },
                }
            },
            "competition_sets": {
                "comp:dentist": {
                    "competition_set_id": "comp:dentist",
                    "trigger_id": "en-es:unit:dentist:dentista:trigger",
                    "status": "ready",
                    "active_sense_id": "sense:dentista",
                    "shadow_sense_ids": [],
                    "selection_mode": "offline_inventory_replay",
                    "selection_policy_version": "active_only_inventory_replay_v1",
                }
            },
            "phrase_sets": {},
        }

        with tempfile.TemporaryDirectory() as tmp:
            report = module.build_helper_runtime_smoke_report(
                dataset_payload=dataset_payload,
                candidate_inventory_payload=candidate_inventory_payload,
                fixture_root=Path(tmp) / "fixture",
                profile_id="default",
                decision_policy_id="en_es_sentence_veto_v2",
                generated_at="2026-05-09T00:00:00Z",
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "manual_testing_ready")
        self.assertEqual(report["summary"]["case_count"], 1)
        self.assertEqual(report["summary"]["active_only_competition_set_count"], 1)
        self.assertEqual(report["summary"]["fallback_decision_count"], 0)
        self.assertEqual(report["summary"]["policy_decision_count"], 1)
        self.assertEqual(report["sample_decisions"][0]["decision_source"], "policy")
        self.assertEqual(report["sample_decisions"][0]["decision"], "replace")


if __name__ == "__main__":
    unittest.main()
