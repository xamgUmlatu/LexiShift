from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(SCRIPTS_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_full_family_human_review_packet_en_es import (  # noqa: E402
    build_full_family_human_review_packet,
    render_human_review_packet_markdown,
)


class SemanticVetoFullFamilyHumanReviewPacketTests(unittest.TestCase):
    def test_builds_pending_user_review_packet_without_trusting_rows(self) -> None:
        report = build_full_family_human_review_packet(
            dataset_payload=_dataset(),
            sense_rows_by_source={
                "change": [
                    _sense("n", "the act of becoming different", "The change was slow."),
                    _sense("n", "coins received after payment", "I need change."),
                ],
                "abate": [_sense("v", "to become less intense", "The storm abated.")],
                "bark": [
                    _sense("v", "to make a dog sound", "The dog barked."),
                    _sense("n", "tree covering", "The bark was rough."),
                ],
            },
            weakness_taxonomy=_weakness_taxonomy(),
            pilot_family_count=3,
            generated_at="2026-05-07T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "full_family_human_review_packet_ready")
        self.assertEqual(report["summary"]["review_family_count"], 3)
        self.assertEqual(report["summary"]["trusted_case_count"], 0)
        self.assertEqual(
            report["summary"]["human_review_status_counts"],
            {"pending_user_review": 3},
        )
        self.assertIn("active_target_sense_not_audited", report["summary"]["weakness_counts"])
        self.assertIn("pilot_not_hard_case_representative", report["summary"]["weakness_counts"])
        self.assertIn("pilot_not_hard_case_representative", report["summary"]["packet_weaknesses"])
        self.assertEqual(
            report["summary"]["weakness_severity_counts"]["review_required"],
            4,
        )
        self.assertEqual(
            report["summary"]["weakness_severity_counts"]["blocking"],
            2,
        )
        self.assertTrue(report["e2e_checks"]["multiple_source_bands_present"])
        self.assertTrue(report["e2e_checks"]["shadow_negative_rows_present"])

        families = report["family_review_rows"]
        for family in families:
            self.assertEqual(family["human_review_status"], "pending_user_review")
            self.assertEqual(family["active_sense_status"], "pending_user_review")
            self.assertIn("active_target_sense_not_audited", family["agent_pretriage_weaknesses"])
            self.assertIn("user_review", family)
            for case in family["case_review_rows"]:
                self.assertEqual(case["human_review_status"], "pending_user_review")
                self.assertNotEqual(case["row_quality_status"], "trusted")

        phrase_rows = [
            case
            for family in families
            for case in family["case_review_rows"]
            if case["manual_case_type"] == "phrase_no_winner"
        ]
        shadow_rows = [
            case
            for family in families
            for case in family["case_review_rows"]
            if case["manual_case_type"] == "shadow_negative"
        ]
        self.assertTrue(phrase_rows)
        self.assertTrue(shadow_rows)
        self.assertEqual(phrase_rows[0]["no_winner_subtype"], "mention_only_template_control")
        self.assertIn(
            "shadow_competitor_target_not_reviewed",
            shadow_rows[0]["agent_pretriage_weaknesses"],
        )
        self.assertIn(
            "phrase_no_winner_template_control_only",
            phrase_rows[0]["agent_pretriage_weaknesses"],
        )

        markdown = render_human_review_packet_markdown(report)
        self.assertIn("Human Review Packet", markdown)
        self.assertIn("pending user review", markdown)
        self.assertIn("active_sense_status:", markdown)
        self.assertIn("Weakness Taxonomy", markdown)
        self.assertIn("Use independent review contexts", markdown)


def _dataset() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "unit_full_family",
        "families": [
            _family("change", "cambio", "zipf_5_plus_very_common", shadow=True),
            _family("abate", "decrecer", "zipf_below_3_rare", shadow=False),
            _family("bark", "ladrar", "zipf_3_to_4_mid", shadow=True),
        ],
    }


def _family(source: str, target: str, source_band: str, *, shadow: bool) -> dict[str, object]:
    family_id = f"fam:{source}:{target}"
    active_id = f"{family_id}:active"
    shadows = []
    if shadow:
        shadows.append(
            {
                "sense_id": f"{family_id}:shadow:1",
                "target_lemma": f"{source} alternate sense 1",
                "canonical_pos": "noun",
                "evidence_views": {
                    "sense_label": f"{source} alternate sense 1",
                    "gloss_text": "alternate meaning",
                    "all_evidence_text": "alternate meaning",
                },
            }
        )
    cases = [
        _case(family_id, 1, source, "replace", active_id, "positive_active", source_band),
        _case(family_id, 2, source, "abstain", "none", "phrase_no_winner", source_band),
    ]
    if shadow:
        cases.append(
            _case(
                family_id,
                3,
                source,
                "abstain",
                f"{family_id}:shadow:1",
                "shadow_negative",
                source_band,
            )
        )
    return {
        "family_id": family_id,
        "trigger": source,
        "active": {
            "sense_id": active_id,
            "target_lemma": target,
            "canonical_pos": "noun",
            "evidence_views": {
                "sense_label": f"{source} -> {target}",
                "gloss_text": f"intended meaning of {source}",
                "all_evidence_text": f"{source} -> {target} | intended meaning",
            },
        },
        "shadows": shadows,
        "cases": cases,
    }


def _case(
    family_id: str,
    index: int,
    source: str,
    gold_decision: str,
    gold_winner: str,
    case_type: str,
    source_band: str,
) -> dict[str, object]:
    if case_type == "positive_active":
        sentence = f"The article used {source} to describe intended meaning."
    elif case_type == "phrase_no_winner":
        sentence = f'The page listed "{source}" as a vocabulary term, not as a sentence meaning.'
    else:
        sentence = f"In this sentence, {source} referred to alternate meaning."
    return {
        "case_id": f"{family_id}:{index:03d}",
        "sentence": sentence,
        "source_phrase": source,
        "gold_winner": gold_winner,
        "gold_decision": gold_decision,
        "slice_dimensions": {
            "source_zipf_band_en": [source_band],
            "target_zipf_band_es": ["zipf_4_to_5_common"],
            "polysemy_band": ["low_1_to_3"],
            "pos_shape": ["same_pos_polysemy"],
            "manual_case_type": [case_type],
        },
        "notes": "draft active-positive context from WordNet or deterministic template",
    }


def _sense(pos: str, definition: str, example: str) -> dict[str, object]:
    return {
        "pos": pos,
        "definition": definition,
        "examples": [example],
        "members": [],
        "synset_id": definition.replace(" ", "_"),
    }


def _weakness_taxonomy() -> dict[str, object]:
    def row(weakness_id: str, severity: str) -> dict[str, str]:
        return {
            "id": weakness_id,
            "scope": "case",
            "severity": severity,
            "detection": "unit",
            "meaning": f"{weakness_id} meaning",
            "avoid_by": "Use independent review contexts.",
            "review_action": f"{weakness_id} action",
        }

    return {
        "taxonomy_id": "unit_taxonomy",
        "purpose": "Unit taxonomy purpose.",
        "weakness_types": [
            row("active_target_sense_not_audited", "review_required"),
            row("pilot_not_hard_case_representative", "review_required"),
            row("active_context_template_circular", "diagnostic_only"),
            row("evidence_context_overlap_risk", "diagnostic_only"),
            row("phrase_no_winner_template_control_only", "diagnostic_only"),
            row("shadow_competitor_target_not_reviewed", "blocking"),
            row("shadow_negative_synthetic_definition_context", "diagnostic_only"),
            row("no_winner_token_boundary_artifact", "review_required"),
        ],
    }


if __name__ == "__main__":
    unittest.main()
