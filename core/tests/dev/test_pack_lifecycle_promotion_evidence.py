from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from pack_lifecycle_promotion_evidence import (  # noqa: E402
    build_promotion_evidence_report,
    promotion_evidence_exit_code,
    render_promotion_evidence_markdown,
)


class PackLifecyclePromotionEvidenceTests(unittest.TestCase):
    def test_frequency_candidate_bundle_can_be_promotion_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lifecycle = _write_json(root / "pack_lifecycle.json", _lifecycle_payload())
            source = _write_json(root / "source_readiness.json", _status_payload("source"))
            bridge = _write_json(
                root / "srs_zipf_bridge.json",
                _status_payload("bridge", decision="srs_zipf_bridge_established"),
            )
            denominator = _write_json(
                root / "denominator.json",
                _status_payload(
                    "denominator",
                    decision="semantic_veto_denominator_audit_current",
                ),
            )

            report = build_promotion_evidence_report(
                pack_id="freq-es-expanded-v1",
                pack_kind="frequency",
                pair="en-es",
                pack_lifecycle_json=lifecycle,
                source_readiness_json=source,
                srs_zipf_bridge_json=bridge,
                denominator_json=denominator,
                generated_at="2026-05-15T00:00:00+00:00",
            )
            markdown = render_promotion_evidence_markdown(report)

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "pack_promotion_evidence_ready")
        self.assertEqual(report["summary"]["required_count"], 4)
        self.assertEqual(report["summary"]["blocking_issue_count"], 0)
        self.assertEqual(promotion_evidence_exit_code(report, fail_on_review=True), 0)
        self.assertIn("pack_lifecycle_audit", markdown)
        self.assertIn("source_readiness_audit", markdown)
        self.assertIn("srs_zipf_bridge", markdown)
        self.assertIn("denominator_audit", markdown)

    def test_missing_required_artifact_blocks_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lifecycle_payload = _lifecycle_payload(
                summary_status="review",
                provenance_review_required=True,
            )
            lifecycle = _write_json(root / "pack_lifecycle.json", lifecycle_payload)
            bridge = _write_json(
                root / "srs_zipf_bridge.json",
                _status_payload("bridge", decision="srs_zipf_bridge_established"),
            )
            denominator = _write_json(
                root / "denominator.json",
                _status_payload(
                    "denominator",
                    decision="semantic_veto_denominator_audit_current",
                ),
            )

            report = build_promotion_evidence_report(
                pack_id="freq-es-expanded-v1",
                pack_kind="frequency",
                pack_lifecycle_json=lifecycle,
                source_readiness_json=root / "missing-source.json",
                srs_zipf_bridge_json=bridge,
                denominator_json=denominator,
                generated_at="2026-05-15T00:00:00+00:00",
            )

        self.assertEqual(report["status"], "error")
        self.assertIn("source_readiness_json_missing", report["blocking_issues"])
        self.assertIn("pack_lifecycle_summary_not_ok", report["blocking_issues"])
        self.assertIn("pack_lifecycle_provenance_review_required", report["blocking_issues"])
        self.assertEqual(promotion_evidence_exit_code(report, fail_on_review=True), 1)

    def test_pack_missing_from_lifecycle_audit_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lifecycle_payload = _lifecycle_payload()
            lifecycle_payload["installed_pack_families"]["frequency"]["packs"] = []
            lifecycle = _write_json(root / "pack_lifecycle.json", lifecycle_payload)
            source = _write_json(root / "source_readiness.json", _status_payload("source"))
            bridge = _write_json(
                root / "srs_zipf_bridge.json",
                _status_payload("bridge", decision="srs_zipf_bridge_established"),
            )
            denominator = _write_json(
                root / "denominator.json",
                _status_payload(
                    "denominator",
                    decision="semantic_veto_denominator_audit_current",
                ),
            )

            report = build_promotion_evidence_report(
                pack_id="freq-es-expanded-v1",
                pack_kind="frequency",
                pack_lifecycle_json=lifecycle,
                source_readiness_json=source,
                srs_zipf_bridge_json=bridge,
                denominator_json=denominator,
                generated_at="2026-05-15T00:00:00+00:00",
            )

        self.assertEqual(report["status"], "error")
        self.assertIn("pack_lifecycle_pack_not_found", report["blocking_issues"])


def _write_json(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _lifecycle_payload(
    *,
    summary_status: str = "ok",
    provenance_review_required: bool = False,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "decision": "pack_lifecycle_state_audited",
        "summary": {
            "status": summary_status,
            "provenance_review_required_count": 1 if provenance_review_required else 0,
        },
        "installed_pack_families": {
            "frequency": {
                "packs": [
                    {
                        "pack_id": "freq-es-expanded-v1",
                        "manifest_exists": True,
                        "artifact_exists": True,
                        "provenance_exists": True,
                        "provenance_valid": True,
                        "provenance_review": {
                            "review_required": provenance_review_required,
                        },
                    }
                ]
            }
        },
    }


def _status_payload(name: str, *, decision: str | None = None) -> dict[str, object]:
    decisions = {
        "source": "srs_corpus_expansion_candidates_audited",
        "bridge": "srs_zipf_bridge_established",
        "denominator": "semantic_veto_denominator_audit_current",
    }
    return {
        "schema_version": 1,
        "pair": "en-es",
        "status": "ok",
        "decision": decision or decisions[name],
    }


if __name__ == "__main__":
    unittest.main()
