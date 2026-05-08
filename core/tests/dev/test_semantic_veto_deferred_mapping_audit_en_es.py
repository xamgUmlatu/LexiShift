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

from semantic_veto_deferred_mapping_audit_en_es import (  # noqa: E402
    build_deferred_mapping_audit_report,
    render_deferred_mapping_audit_markdown,
)


def _family(family_id: str, trigger: str, target: str, gloss: str) -> dict[str, object]:
    return {
        "family_id": family_id,
        "trigger": trigger,
        "active": {
            "target_lemma": target,
            "evidence_views": {
                "sense_label": f"{trigger} -> {target}",
                "gloss_text": gloss,
            },
        },
        "cases": [],
    }


class SemanticVetoDeferredMappingAuditTests(unittest.TestCase):
    def test_audits_deferred_mappings_without_promoting_trusted_seed(self) -> None:
        trusted_seed = {
            "families": [],
            "deferred_families": [
                {
                    "family_id": "en-es:full-family-representative:bar:cercar",
                },
                {
                    "family_id": "en-es:full-family-representative:offset:distancia",
                },
                {
                    "family_id": "en-es:full-family-representative:demand:deduccion",
                },
            ],
        }
        repaired_pilot = dict(trusted_seed)
        draft_dataset = {
            "families": [
                _family(
                    "en-es:full-family-representative:bar:cercar",
                    "bar",
                    "cercar",
                    "a room or establishment where alcoholic drinks are served",
                ),
                _family(
                    "en-es:full-family-representative:offset:distancia",
                    "offset",
                    "distancia",
                    "the time at which something is supposed to begin",
                ),
                _family(
                    "en-es:full-family-representative:demand:deduccion",
                    "demand",
                    "deducción",
                    "an urgent or peremptory request",
                ),
            ]
        }
        srs_bridge = {
            "full_source_target_pairs": [
                {"source": "bar", "target": "cercar"},
                {"source": "offset", "target": "distancia"},
                {"source": "demand", "target": "deducción"},
            ]
        }
        evidence = {
            "bar->cercar": {
                "installed_evidence_status": "found",
                "target_to_source_exact": [{"headword": "cercar", "translation": "bar"}],
                "source_to_target_exact": [],
                "source_sense_rows": [
                    {
                        "headword": "bar",
                        "translation": "barrear",
                        "raw_glosses_json": '["to obstruct the passage of"]',
                    }
                ],
                "target_gloss_rows": [
                    {
                        "headword": "cercar",
                        "translation": "to corral, fence, fence off",
                        "raw_glosses_json": '["to corral, fence, fence off"]',
                    }
                ],
            },
            "offset->distancia": {
                "installed_evidence_status": "found",
                "target_to_source_exact": [{"headword": "distancia", "translation": "offset"}],
                "source_to_target_exact": [],
                "source_sense_rows": [
                    {
                        "headword": "offset",
                        "translation": "desfase",
                        "raw_glosses_json": (
                            '["distance by which one thing is out of alignment with another"]'
                        ),
                    }
                ],
                "target_gloss_rows": [
                    {
                        "headword": "distancia",
                        "translation": "distance",
                        "raw_glosses_json": '["distance"]',
                    }
                ],
            },
            "demand->deducción": {
                "installed_evidence_status": "found",
                "target_to_source_exact": [{"headword": "deducción", "translation": "demand"}],
                "source_to_target_exact": [],
                "source_sense_rows": [
                    {
                        "headword": "demand",
                        "translation": "demanda",
                        "raw_glosses_json": '["forceful claim for something"]',
                    }
                ],
                "target_gloss_rows": [
                    {
                        "headword": "deducción",
                        "translation": "deduction",
                        "raw_glosses_json": "",
                    }
                ],
            },
        }

        report = build_deferred_mapping_audit_report(
            trusted_seed_payload=trusted_seed,
            repaired_pilot_payload=repaired_pilot,
            draft_dataset_payload=draft_dataset,
            srs_zipf_bridge_payload=srs_bridge,
            installed_evidence_by_pair=evidence,
            generated_at="2026-05-07T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertTrue(all(report["e2e_checks"].values()))
        self.assertEqual(
            report["summary"]["status_counts"],
            {
                "reject_mapping_source_target_mismatch": 1,
                "salvageable_with_corrected_active_sense": 2,
            },
        )
        rows = {row["mapping_id"]: row for row in report["mapping_rows"]}
        self.assertEqual(
            rows["demand->deducción"]["audit_status"],
            "reject_mapping_source_target_mismatch",
        )
        self.assertEqual(
            rows["bar->cercar"]["audit_status"],
            "salvageable_with_corrected_active_sense",
        )
        self.assertEqual(rows["bar->cercar"]["source_to_target_exact_count"], 0)
        self.assertEqual(rows["bar->cercar"]["target_to_source_exact_count"], 1)
        self.assertEqual(rows["bar->cercar"]["trusted_seed_status"], "excluded")

        markdown = render_deferred_mapping_audit_markdown(report)
        self.assertIn("deferred Mapping Audit".lower(), markdown.lower())
        self.assertIn("demand->deducción", markdown)

    def test_trusted_seed_leak_turns_report_to_review(self) -> None:
        report = build_deferred_mapping_audit_report(
            trusted_seed_payload={
                "families": [
                    _family(
                        "en-es:full-family-representative:bar:cercar",
                        "bar",
                        "cercar",
                        "bad",
                    )
                ],
                "deferred_families": [],
            },
            repaired_pilot_payload={
                "families": [],
                "deferred_families": [
                    {"family_id": row}
                    for row in [
                        "en-es:full-family-representative:bar:cercar",
                        "en-es:full-family-representative:offset:distancia",
                        "en-es:full-family-representative:demand:deduccion",
                    ]
                ],
            },
            draft_dataset_payload={
                "families": [
                    _family(
                        "en-es:full-family-representative:bar:cercar",
                        "bar",
                        "cercar",
                        "bar",
                    ),
                    _family(
                        "en-es:full-family-representative:offset:distancia",
                        "offset",
                        "distancia",
                        "offset",
                    ),
                    _family(
                        "en-es:full-family-representative:demand:deduccion",
                        "demand",
                        "deducción",
                        "demand",
                    ),
                ]
            },
            srs_zipf_bridge_payload={"full_source_target_pairs": []},
            installed_evidence_by_pair={
                "bar->cercar": {"installed_evidence_status": "missing"},
                "offset->distancia": {"installed_evidence_status": "missing"},
                "demand->deducción": {"installed_evidence_status": "missing"},
            },
            generated_at="2026-05-07T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertIn("some_deferred_mappings_leaked_into_trusted_seed", report["issues"])


if __name__ == "__main__":
    unittest.main()
