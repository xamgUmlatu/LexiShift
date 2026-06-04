from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(CORE_ROOT), str(SCRIPTS_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_system_registry_summary import (  # noqa: E402
    build_semantic_veto_system_registry_report,
    render_markdown,
)


class SemanticVetoSystemRegistrySummaryTests(unittest.TestCase):
    def test_registry_report_audits_clean_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = Path(tmpdir) / "registry.json"
            registry.write_text(_registry_json(path="README.md"), encoding="utf-8")

            report = build_semantic_veto_system_registry_report(
                registry_path=registry,
                generated_at="2026-04-29T00:00:00Z",
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["entry_count"], 1)
        self.assertEqual(report["pass_count"], 1)
        self.assertEqual(report["state_counts"]["current_reference"], 1)
        self.assertEqual(report["data_artifact_lanes"][0]["lane_id"], "candidate_v1_lane")
        self.assertEqual(report["action_items"][0]["action_id"], "action_1")
        markdown = render_markdown(report)
        self.assertIn("Semantic Veto System Registry", markdown)
        self.assertIn("candidate_v1", markdown)
        self.assertIn("Data Artifact Lanes", markdown)
        self.assertIn("Action Items", markdown)

    def test_registry_report_flags_missing_candidate_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = Path(tmpdir) / "registry.json"
            registry.write_text(
                _registry_json(path="missing.md", state="current_candidate", evidence=[]),
                encoding="utf-8",
            )

            report = build_semantic_veto_system_registry_report(
                registry_path=registry,
                generated_at="2026-04-29T00:00:00Z",
            )

        self.assertEqual(report["status"], "review")
        messages = [issue["message"] for issue in report["issues"]]
        self.assertIn("Candidate entry needs verification artifacts.", messages)
        self.assertTrue(any("Path does not exist" in message for message in messages))


def _registry_json(
    *,
    path: str,
    state: str = "current_reference",
    evidence: list[str] | None = None,
) -> str:
    evidence = ["README.md"] if evidence is None else evidence
    return (
        "{\n"
        '  "schema_version": 1,\n'
        '  "registry_id": "test_registry",\n'
        '  "state_definitions": {\n'
        '    "current_reference": "Current reference.",\n'
        '    "current_candidate": "Candidate."\n'
        "  },\n"
        '  "component_definitions": {\n'
        '    "process_governance": "Governance."\n'
        "  },\n"
        '  "pass_checklist": [\n'
        "    {\n"
        '      "pass_id": "runtime_path",\n'
        '      "state": "queued_next",\n'
        '      "lens": "Trace runtime.",\n'
        '      "primary_outputs": ["map"],\n'
        '      "cracks_to_watch": ["drift"]\n'
        "    }\n"
        "  ],\n"
        '  "current_candidate": {\n'
        '    "candidate_id": "candidate_v1",\n'
        '    "production_status": "research_only",\n'
        '    "runtime_policy_change": "none",\n'
        '    "control": "control",\n'
        '    "candidate_summary": "summary",\n'
        '    "current_result": {"active_shadow_false_abstains": 0},\n'
        '    "promotion_blockers": ["breadth"]\n'
        "  },\n"
        '  "data_artifact_lanes": [\n'
        "    {\n"
        '      "lane_id": "candidate_v1_lane",\n'
        '      "status": "current_research_candidate",\n'
        '      "purpose": "Test lane.",\n'
        '      "durable_inputs": ["entry_1"],\n'
        '      "generated_reports": ["entry_1"],\n'
        '      "control_artifacts": ["entry_1"],\n'
        '      "local_artifact_cracks": ["local report"],\n'
        '      "rerun_order": ["entry_1"]\n'
        "    }\n"
        "  ],\n"
        '  "action_items": [\n'
        "    {\n"
        '      "action_id": "action_1",\n'
        '      "priority": "P1",\n'
        '      "status": "queued",\n'
        '      "pass_id": "runtime_path",\n'
        '      "source_artifacts": ["entry_1"],\n'
        '      "action": "Do the thing.",\n'
        '      "evidence_needed": "Evidence.",\n'
        '      "validation": "Validation.",\n'
        '      "promotion_impact": "Impact."\n'
        "    }\n"
        "  ],\n"
        '  "entries": [\n'
        "    {\n"
        '      "artifact_id": "entry_1",\n'
        '      "title": "Entry 1",\n'
        '      "component": "process_governance",\n'
        f'      "state": "{state}",\n'
        f'      "path": "{path}",\n'
        '      "role": "Role.",\n'
        '      "owner_doc": "README.md",\n'
        '      "current_use": "Use.",\n'
        '      "risk": "Risk.",\n'
        '      "next_audit_pass": "runtime_path",\n'
        f'      "verification_artifacts": {_json_list(evidence)}\n'
        "    }\n"
        "  ]\n"
        "}\n"
    )


def _json_list(values: list[str]) -> str:
    return "[" + ", ".join(f'"{value}"' for value in values) + "]"


if __name__ == "__main__":
    unittest.main()
