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

from semantic_llm_example_frame_contract_en_es import (  # noqa: E402
    build_example_frame_contract_report,
    render_example_frame_contract_markdown,
)


class SemanticLlmExampleFrameContractTests(unittest.TestCase):
    def test_contract_report_accepts_complete_example_frame_family(self) -> None:
        report = build_example_frame_contract_report(
            _complete_intake_batch(),
            generated_at="2026-04-25T12:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertTrue(report["summary"]["contract_complete"])
        self.assertEqual(report["summary"]["contract_complete_family_count"], 1)
        family = report["family_rows"][0]
        self.assertEqual(family["active_example_count"], 1)
        self.assertEqual(family["shadow_example_count"], 1)
        self.assertEqual(family["phrase_control_example_count"], 1)
        self.assertEqual(family["missing_requirements"], [])

        markdown = render_example_frame_contract_markdown(report)
        self.assertIn("Semantic Example-Frame Contract", markdown)
        self.assertIn("Complete families", markdown)

    def test_contract_report_flags_active_only_prompt_batches(self) -> None:
        report = build_example_frame_contract_report(
            _active_only_normalized_batch(),
            generated_at="2026-04-25T12:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertFalse(report["summary"]["contract_complete"])
        self.assertEqual(report["summary"]["missing_shadow_family_keys"], ["fam:check"])
        self.assertEqual(
            report["summary"]["missing_phrase_control_family_keys"],
            ["fam:check"],
        )
        self.assertEqual(
            report["family_rows"][0]["missing_requirements"],
            ["shadow_examples", "phrase_control_examples"],
        )

    def test_contract_report_can_require_missing_expected_families(self) -> None:
        report = build_example_frame_contract_report(
            _complete_intake_batch(),
            required_family_keys=["fam:check", "fam:order"],
            generated_at="2026-04-25T12:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertFalse(report["summary"]["contract_complete"])
        self.assertEqual(report["summary"]["families_total"], 2)
        self.assertEqual(report["summary"]["contract_complete_family_count"], 1)
        self.assertEqual(report["summary"]["missing_active_family_keys"], ["fam:order"])
        self.assertEqual(report["summary"]["missing_shadow_family_keys"], ["fam:order"])
        self.assertEqual(
            report["summary"]["missing_phrase_control_family_keys"],
            ["fam:order"],
        )

        missing = {
            str(row["family_key"]): row
            for row in report["family_rows"]
            if str(row["family_key"]) == "fam:order"
        }["fam:order"]
        self.assertEqual(
            missing["missing_requirements"],
            ["active_examples", "shadow_examples", "phrase_control_examples"],
        )


def _complete_intake_batch() -> dict[str, object]:
    return {
        "schema_version": 1,
        "batch_id": "example-frame-complete",
        "pair": "en-es",
        "source_type": "llm",
        "source_id": "llm_example_frame_source",
        "source_family": "silver_llm_generation",
        "roles": ["discrimination", "phrase_containment"],
        "generated_at": "2026-04-25T10:00:00Z",
        "ingested_at": "2026-04-25T10:05:00Z",
        "review_state": "unreviewed",
        "model_id": "gpt-5.4",
        "prompt_version": "example-frame-contract-v1",
        "items": [
            _intake_item(
                row_id="active",
                relation_type="anchor_cue",
                candidate_target="cheque",
                text="The check was signed and deposited yesterday.",
            ),
            _intake_item(
                row_id="shadow",
                relation_type="shadow_candidate",
                candidate_target="revisar",
                text="They will check the records carefully tonight.",
            ),
            _intake_item(
                row_id="phrase",
                relation_type="phrase_control_example",
                candidate_target="phrase_control",
                text="Please check in at the front desk.",
                roles=["discrimination", "phrase_containment"],
            ),
        ],
    }


def _intake_item(
    *,
    row_id: str,
    relation_type: str,
    candidate_target: str,
    text: str,
    roles: list[str] | None = None,
) -> dict[str, object]:
    item: dict[str, object] = {
        "row_id": row_id,
        "relation_type": relation_type,
        "trigger": "check",
        "active_target": "cheque",
        "candidate_target": candidate_target,
        "evidence_text": text,
        "metadata": {
            "family_id": "fam:check",
        },
    }
    if roles is not None:
        item["roles"] = roles
    return item


def _active_only_normalized_batch() -> dict[str, object]:
    return {
        "schema_version": 1,
        "normalization_version": "semantic_evidence_v1",
        "batch_id": "active-only",
        "pair": "en-es",
        "source_type": "llm",
        "source_id": "llm_anchor_cues",
        "source_family": "silver_llm_generation",
        "roles": ["cue_generation", "discrimination"],
        "generated_at": "2026-04-25T10:00:00Z",
        "ingested_at": "2026-04-25T10:05:00Z",
        "review_state": "unreviewed",
        "model_id": "gpt-5.4",
        "prompt_version": "anchor-cues-v1",
        "row_count": 1,
        "provenance": {},
        "rows": [
            {
                "evidence_id": "evidence:1",
                "dedupe_key": "dedupe:1",
                "batch_id": "active-only",
                "row_id": "active",
                "pair": "en-es",
                "source_type": "llm",
                "source_id": "llm_anchor_cues",
                "source_family": "silver_llm_generation",
                "roles": ["cue_generation", "discrimination"],
                "relation_type": "anchor_cue",
                "trigger": "check",
                "normalized_trigger": "check",
                "active_target": "cheque",
                "normalized_active_target": "cheque",
                "candidate_target": "revisar",
                "normalized_candidate_target": "revisar",
                "is_multiword": False,
                "evidence_text": "write a check to pay the rent",
                "review_state": "unreviewed",
                "promotion_state": "proposed",
                "linkage_status": "unlinked",
                "runtime_publishable": False,
                "metadata": {
                    "family_id": "fam:check",
                },
                "provenance": {},
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
