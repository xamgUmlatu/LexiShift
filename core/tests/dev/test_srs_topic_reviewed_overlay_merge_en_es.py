from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
CORE_ROOT = REPO_ROOT / "core"
for path in (SCRIPT_DIR, CORE_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from lexishift_core.srs.topic_overlay import (  # noqa: E402
    EN_ES_REVIEWED_OVERLAY_FILENAME,
    resolve_preview_profile_topic_overlay,
)
from srs_topic_reviewed_overlay_merge_en_es import build_overlay, render_markdown  # noqa: E402


class SrsTopicReviewedOverlayMergeEnEsTests(unittest.TestCase):
    def test_merge_dedupes_rows_and_reports_runtime_effective_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_a = root / "a.json"
            source_b = root / "b.json"
            _write_json(
                source_a,
                {
                    "status": "ok",
                    "overlay_id": "source_a",
                    "rows": [
                        _row("animal", "animals", 1.0, "strong"),
                        _row("juego", "games", 0.65, "light"),
                    ],
                },
            )
            _write_json(
                source_b,
                {
                    "status": "ok",
                    "overlay_id": "source_b",
                    "rows": [
                        _row("animal", "animals", 0.65, "light"),
                        _row("juego", "games", 1.0, "strong"),
                    ],
                },
            )

            report = build_overlay(
                overlay_paths=[source_a, source_b],
                generated_at="2026-07-06T00:00:00+00:00",
            )

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["summary"]["row_count"], 2)
            self.assertEqual(report["summary"]["duplicate_row_count"], 2)
            self.assertEqual(report["summary"]["runtime_effective_row_count"], 2)
            self.assertEqual(
                report["summary"]["runtime_effective_counts_by_topic"],
                {"animals": 1, "games": 1},
            )
            by_key = {(row["lemma"], row["topic"]): row for row in report["rows"]}
            self.assertEqual(by_key[("juego", "games")]["membership"], 1.0)
            self.assertEqual(
                set(by_key[("animal", "animals")]["provenance"]["source_overlay_ids"]),
                {"source_a", "source_b"},
            )
            markdown = render_markdown(report)
            self.assertIn("Reviewed Topic Overlay Merge", markdown)
            self.assertIn("Runtime-Effective Counts", markdown)

    def test_en_es_preview_resolver_prefers_merged_overlay_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            srs_dir = root / "srs"
            overlay_dir = srs_dir / "topic_overlays"
            overlay_dir.mkdir(parents=True)
            _write_json(
                overlay_dir / EN_ES_REVIEWED_OVERLAY_FILENAME,
                {
                    "status": "ok",
                    "overlay_id": "merged_en_es",
                    "rows": [_row("comida", "food_cooking", 1.0, "strong")],
                },
            )

            payload, diagnostics = resolve_preview_profile_topic_overlay(
                SimpleNamespace(srs_dir=srs_dir, data_root=root / "data"),
                pair="en-es",
                profile_context={"interests": ["food_cooking"]},
            )

            self.assertIsNotNone(payload)
            self.assertEqual(diagnostics["status"], "active")
            self.assertEqual(diagnostics["overlay_id"], "merged_en_es")
            self.assertEqual(diagnostics["active_topics"], ["food_cooking"])


def _row(
    lemma: str,
    topic: str,
    membership: float,
    confidence_label: str,
) -> dict[str, object]:
    return {
        "language_pair": "en-es",
        "lemma": lemma,
        "topic": topic,
        "membership": membership,
        "confidence_label": confidence_label,
        "evidence_score": membership,
    }


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
