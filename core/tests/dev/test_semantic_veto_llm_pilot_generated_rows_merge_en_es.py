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

from semantic_veto_llm_pilot_generated_rows_merge_en_es import (  # noqa: E402
    build_semantic_veto_llm_pilot_generated_rows_merge_bundle,
    write_semantic_veto_llm_pilot_generated_rows_merge_bundle,
)


class SemanticVetoLlmPilotGeneratedRowsMergeTests(unittest.TestCase):
    def test_overlay_payload_replaces_matching_row_id(self) -> None:
        bundle = build_semantic_veto_llm_pilot_generated_rows_merge_bundle(
            base_generated_rows_payload=_generated_rows_payload(
                rows=[
                    _row("row:a", "Old sentence."),
                    _row("row:b", "Kept sentence."),
                ]
            ),
            overlay_generated_rows_payloads=[
                _generated_rows_payload(rows=[_row("row:a", "Fixed sentence.")])
            ],
            generation_requests_payload=_request_payload(["row:a", "row:b"]),
            base_generated_rows_path=Path("base.json"),
            overlay_generated_rows_paths=[Path("repair.json")],
            generation_requests_path=Path("requests.json"),
            generated_at="2026-05-05T00:00:00Z",
        )

        report = bundle["report"]
        payload = bundle["generated_rows_payload"]
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["replacement_count"], 1)
        self.assertEqual([row["row_id"] for row in payload["rows"]], ["row:a", "row:b"])
        self.assertEqual(payload["rows"][0]["sentence"], "Fixed sentence.")
        self.assertEqual(payload["rows"][1]["sentence"], "Kept sentence.")

    def test_reports_missing_expected_rows(self) -> None:
        bundle = build_semantic_veto_llm_pilot_generated_rows_merge_bundle(
            base_generated_rows_payload=_generated_rows_payload(rows=[_row("row:a", "Only.")]),
            overlay_generated_rows_payloads=[],
            generation_requests_payload=_request_payload(["row:a", "row:b"]),
            generated_at="2026-05-05T00:00:00Z",
        )

        report = bundle["report"]
        self.assertEqual(report["status"], "review")
        self.assertEqual(report["missing_row_ids"], ["row:b"])

    def test_writes_report_and_assembled_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = build_semantic_veto_llm_pilot_generated_rows_merge_bundle(
                base_generated_rows_payload=_generated_rows_payload(rows=[_row("row:a", "Only.")]),
                overlay_generated_rows_payloads=[],
                generation_requests_payload=_request_payload(["row:a"]),
                generated_at="2026-05-05T00:00:00Z",
            )

            write_semantic_veto_llm_pilot_generated_rows_merge_bundle(
                bundle=bundle,
                json_out=Path(tmp) / "report.json",
                markdown_out=Path(tmp) / "report.md",
                generated_rows_out=Path(tmp) / "rows.json",
            )

            self.assertTrue((Path(tmp) / "report.json").exists())
            self.assertTrue((Path(tmp) / "report.md").exists())
            self.assertTrue((Path(tmp) / "rows.json").exists())


def _generated_rows_payload(*, rows: list[dict[str, object]]) -> dict[str, object]:
    row_ids = [str(row["row_id"]) for row in rows]
    return {
        "schema_version": 1,
        "pair": "en-es",
        "selected_request_ids": [f"req:{row_id}" for row_id in row_ids],
        "selected_expected_row_ids": row_ids,
        "rows": rows,
    }


def _request_payload(row_ids: list[str]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "requests": [
            {
                "request_id": f"req:{row_id}",
                "expected_row_id": row_id,
            }
            for row_id in row_ids
        ],
    }


def _row(row_id: str, sentence: str) -> dict[str, object]:
    return {
        "row_id": row_id,
        "sentence": sentence,
    }


if __name__ == "__main__":
    unittest.main()
