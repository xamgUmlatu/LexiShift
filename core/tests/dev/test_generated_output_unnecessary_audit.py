from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import textwrap
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "dev"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generated_output_unnecessary_audit import (  # noqa: E402
    build_generated_output_unnecessary_audit,
    render_generated_output_unnecessary_markdown,
)


class GeneratedOutputUnnecessaryAuditTests(unittest.TestCase):
    def test_flags_unreferenced_dated_report_views_only_when_json_remains(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_tree(root)

            report = build_generated_output_unnecessary_audit(root)

        definite = _groups_by_status(report, "definite_prune")
        report_view_groups = [
            group
            for group in definite
            if group["rule_id"] == "unreferenced_root_dated_report_view_with_json_counterpart"
        ]
        paths = {path for group in report_view_groups for path in group["paths"]}
        self.assertIn("docs/test_outputs/report_2026-01-02.html", paths)
        self.assertIn("docs/test_outputs/report_2026-01-02.md", paths)
        self.assertNotIn("docs/test_outputs/report_2026-01-02.json", paths)

    def test_keeps_referenced_views_and_generated_output_provenance_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_tree(root)

            report = build_generated_output_unnecessary_audit(root)

        retained = _groups_by_status(report, "retain")
        retained_paths = {path for group in retained for path in group["paths"]}
        self.assertIn("docs/test_outputs/referenced_2026-01-02.md", retained_paths)
        self.assertIn(_repair_generated_rows_path("001"), retained_paths)

    def test_flags_unreferenced_semantic_repair_reports_not_generated_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_tree(root)

            report = build_generated_output_unnecessary_audit(root)

        definite = _groups_by_status(report, "definite_prune")
        repair_groups = [
            group
            for group in definite
            if group["rule_id"] == "unreferenced_semantic_repair_report_bundle"
        ]
        paths = {path for group in repair_groups for path in group["paths"]}
        self.assertIn(_repair_admission_path("001"), paths)
        self.assertNotIn(_repair_generated_rows_path("001"), paths)

    def test_flags_unreferenced_semantic_install_root_when_source_evidence_remains(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_tree(root)

            report = build_generated_output_unnecessary_audit(root)

        definite = _groups_by_status(report, "definite_prune")
        install_groups = [
            group
            for group in definite
            if group["rule_id"]
            == "unreferenced_semantic_install_root_with_retained_source_evidence"
        ]
        paths = {path for group in install_groups for path in group["paths"]}
        self.assertIn(
            "docs/test_outputs/experiments/semantic_veto_source_packaging/"
            "en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/"
            "srs/profiles/default/srs_ruleset_en-es.json",
            paths,
        )

    def test_markdown_renderer_summarizes_definite_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_tree(root)

            report = build_generated_output_unnecessary_audit(root)
            markdown = render_generated_output_unnecessary_markdown(report)

        self.assertIn("# Generated Output Unnecessary File Audit", markdown)
        self.assertIn("## Definite Prune Groups", markdown)
        self.assertIn("unreferenced_root_dated_report_view_with_json_counterpart", markdown)


def _groups_by_status(report: dict[str, object], status: str) -> list[dict[str, object]]:
    return [
        group
        for group in report["groups"]
        if isinstance(group, dict) and group.get("status") == status
    ]


def _write_fixture_tree(root: Path) -> None:
    files = {
        "docs/current.md": textwrap.dedent(
            """
            # Current

            This doc intentionally references
            `docs/test_outputs/referenced_2026-01-02.md`.
            """
        ).strip()
        + "\n",
        "docs/test_outputs/report_2026-01-02.json": "{}\n",
        "docs/test_outputs/report_2026-01-02.html": "<html></html>\n",
        "docs/test_outputs/report_2026-01-02.md": "# Report\n",
        "docs/test_outputs/referenced_2026-01-02.json": "{}\n",
        "docs/test_outputs/referenced_2026-01-02.md": "# Referenced\n",
        (
            "docs/test_outputs/semantic_veto_llm_pilot_admission_en_es_repair_20260505_001.json"
        ): "{}\n",
        (
            "docs/test_outputs/semantic_veto_llm_pilot_admission_en_es_repair_20260505_001.md"
        ): "# Admission\n",
        (
            "docs/test_outputs/"
            "semantic_veto_llm_pilot_generation_run_en_es_repair_20260505_001.json"
        ): "{}\n",
        _repair_generated_rows_path("001"): "{}\n",
        "docs/test_outputs/semantic_veto_llm_pilot_generated_rows_en_es_latest.json": (
            "{"
            '"source": '
            '"docs/test_outputs/'
            'semantic_veto_llm_pilot_generated_rows_en_es_repair_20260505_001.json"'
            "}\n"
        ),
        (
            "docs/test_outputs/experiments/semantic_veto_source_packaging/"
            "en-es-active-only-combined-full-v1-tranche-001-normalized_evidence.json"
        ): "{}\n",
        (
            "docs/test_outputs/experiments/semantic_veto_source_packaging/"
            "en-es-active-only-combined-full-v1-tranche-001_semantic_inventory.json"
        ): "{}\n",
        (
            "docs/test_outputs/experiments/semantic_veto_source_packaging/"
            "en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/"
            "srs/profiles/default/srs_ruleset_en-es.json"
        ): "{}\n",
    }
    for relative_path, content in files.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _repair_admission_path(repair_id: str) -> str:
    return (
        "docs/test_outputs/"
        f"semantic_veto_llm_pilot_admission_en_es_repair_20260505_{repair_id}.json"
    )


def _repair_generated_rows_path(repair_id: str) -> str:
    return (
        "docs/test_outputs/"
        f"semantic_veto_llm_pilot_generated_rows_en_es_repair_20260505_{repair_id}.json"
    )


if __name__ == "__main__":
    unittest.main()
