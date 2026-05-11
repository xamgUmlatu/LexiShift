from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_PATH = (
    PROJECT_ROOT / "scripts" / "testing" / "semantic_veto_active_only_live_page_scan_en_es.py"
)

if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.helper.rulegen_outputs import build_snapshot, write_rulegen_outputs  # noqa: E402
from lexishift_core.replacement.core import RuleMetadata, VocabRule  # noqa: E402


def _load_script_module():
    spec = importlib.util.spec_from_file_location(
        "semantic_veto_active_only_live_page_scan", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SemanticVetoActiveOnlyLivePageScanTests(unittest.TestCase):
    def test_live_page_scan_builds_manual_review_rows_from_fixture(self) -> None:
        module = _load_script_module()
        with tempfile.TemporaryDirectory() as tmp:
            fixture_root = Path(tmp) / "fixture"
            paths = build_helper_paths(fixture_root)
            rule = VocabRule(
                source_phrase="dentist",
                replacement="dentista",
                metadata=RuleMetadata(
                    language_pair="en-es",
                    semantic_admission={
                        "schema_version": 1,
                        "status": "ready",
                        "trigger_id": "trigger:dentist",
                        "sense_id": "sense:dentista",
                        "competition_set_id": "comp:dentist",
                    },
                ),
            )
            inventory = {
                "schema_version": 1,
                "pair": "en-es",
                "profile_id": "default",
                "generated_at": "2026-05-09T00:00:00Z",
                "capability": {
                    "pointer_modes": ["trigger_only"],
                    "default_unavailable_reason_code": "missing_source_sense_locator",
                    "competition_mode": "active_only_anchor_cue",
                    "competition_reason_code": "missing_shadow_selection",
                    "phrase_mode": "not_published",
                    "phrase_reason_code": "missing_phrase_inventory",
                },
                "triggers": {
                    "trigger:dentist": {
                        "trigger_id": "trigger:dentist",
                        "source_phrase": "dentist",
                        "normalized_source_phrase": "dentist",
                        "token_count": 1,
                    }
                },
                "senses": {
                    "sense:dentista": {
                        "sense_id": "sense:dentista",
                        "trigger_id": "trigger:dentist",
                        "status": "ready",
                        "target_lemma": "dentista",
                        "provider": "unit",
                        "locator": {
                            "provider": "unit",
                            "locator_kind": "opaque",
                            "opaque_id": "sense:dentista",
                        },
                        "evidence_views": {
                            "all_evidence_text": "dentist appointment medical professional station"
                        },
                    }
                },
                "competition_sets": {
                    "comp:dentist": {
                        "competition_set_id": "comp:dentist",
                        "trigger_id": "trigger:dentist",
                        "status": "ready",
                        "active_sense_id": "sense:dentista",
                        "shadow_sense_ids": [],
                        "selection_mode": "active_only",
                        "selection_policy_version": "unit_active_only",
                    }
                },
                "phrase_sets": {},
            }
            write_rulegen_outputs(
                paths=paths,
                pair="en-es",
                profile_id="default",
                rules=(rule,),
                snapshot=build_snapshot(
                    rules=(rule,),
                    pair="en-es",
                    max_targets=1,
                    max_sources=1,
                    generated_at="2026-05-09T00:00:00Z",
                ),
                semantic_inventory=inventory,
            )
            manifest = {
                "schema_version": 1,
                "scan_id": "unit",
                "pages": [
                    {
                        "page_id": "unit_page",
                        "url": "https://example.test/dentist",
                        "expected_triggers": ["dentist"],
                    }
                ],
            }
            html = (
                "<html><body><p>She booked a dentist appointment near the station "
                "with a medical professional.</p></body></html>"
            )

            report = module.build_live_page_scan_report(
                manifest_payload=manifest,
                fixture_root=fixture_root,
                fetch_text=lambda _page: module.html_to_text(html),
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "manual_review_packet_ready")
        self.assertEqual(report["summary"]["review_row_count"], 1)
        self.assertEqual(report["review_rows"][0]["source_phrase"], "dentist")
        self.assertEqual(report["review_rows"][0]["decision_source"], "policy")
        self.assertEqual(report["review_rows"][0]["decision"], "replace")


if __name__ == "__main__":
    unittest.main()
