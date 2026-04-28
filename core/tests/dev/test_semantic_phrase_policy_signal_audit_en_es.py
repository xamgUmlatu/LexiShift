from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(CORE_ROOT), str(SCRIPTS_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_phrase_policy_signal_audit_en_es import (  # noqa: E402
    build_phrase_policy_signal_audit_report,
    render_phrase_policy_signal_audit_markdown,
)


class SemanticPhrasePolicySignalAuditTests(unittest.TestCase):
    def test_phrase_signal_audit_tracks_hits_and_counterexamples(self) -> None:
        report = build_phrase_policy_signal_audit_report(
            case_suite_payload=_case_suite(),
            generated_at="2026-04-26T12:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "phrase_signal_pass")
        self.assertEqual(report["summary"]["case_count"], 2)
        self.assertEqual(report["summary"]["failed_case_count"], 0)
        self.assertEqual(report["summary"]["false_positive_count"], 0)
        self.assertEqual(report["summary"]["false_negative_count"], 0)
        self.assertIn("modal_trigger_frame", report["summary"]["signal_code_counts"])

        markdown = render_phrase_policy_signal_audit_markdown(report)
        self.assertIn("Phrase Policy Signal Audit", markdown)
        self.assertIn("phrase_signal_pass", markdown)

    def test_phrase_signal_audit_flags_missing_required_signal_code(self) -> None:
        payload = _case_suite()
        payload["families"][0]["cases"][0]["required_signal_codes"] = ["not_present"]

        report = build_phrase_policy_signal_audit_report(
            case_suite_payload=payload,
            generated_at="2026-04-26T12:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["summary"]["failed_case_count"], 1)
        self.assertEqual(
            report["summary"]["failed_case_ids"],
            ["en-es:phrase-signal:test:rock:001"],
        )


def _case_suite() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "phrase_signal_test",
        "case_scope": "phrase_policy_signal_only",
        "families": [
            {
                "family_id": "family:rock",
                "family_pos_tags": ["noun", "noun"],
                "cases": [
                    {
                        "case_id": "en-es:phrase-signal:test:rock:001",
                        "sentence": "The policy could rock the market before Monday.",
                        "source_phrase": "rock",
                        "expected_phrase_preemption": True,
                        "required_signal_codes": ["modal_trigger_frame"],
                    },
                    {
                        "case_id": "en-es:phrase-signal:test:rock:002",
                        "sentence": "The rock beside the gate cracked overnight.",
                        "source_phrase": "rock",
                        "expected_phrase_preemption": False,
                        "required_signal_codes": [],
                    },
                ],
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
