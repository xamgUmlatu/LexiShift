from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_topic_manual_semantic_lexicon_en_ja import build_report, render_markdown  # noqa: E402


class SrsTopicManualSemanticLexiconEnJaTests(unittest.TestCase):
    def test_exact_readings_are_required_for_ambiguous_lemmas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_csv = root / "candidates.csv"
            lexicon_json = root / "lexicon.json"
            _write_candidates(
                candidates_csv,
                [
                    ("1", "米", "こめ", "0.12"),
                    ("2", "米", "べい", "0.32"),
                    ("3", "猫", "ねこ", "0.08"),
                    ("4", "水", "みず", "0.05"),
                ],
            )
            _write_json(
                lexicon_json,
                {
                    "collections": [
                        {
                            "id": "food",
                            "target_family": "food_cooking",
                            "facet_id": "food_drink",
                            "promotion_eligible": True,
                            "entries": [
                                {"lemma": "米", "reading": "コメ"},
                                "猫",
                                "米",
                                "missing",
                            ],
                        }
                    ]
                },
            )

            report = build_report(
                candidates_csv=candidates_csv,
                lexicon_json=lexicon_json,
                top_n=10,
                generated_at="2026-07-01T00:00:00+00:00",
            )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["summary"]["matched_entry_count"], 2)
        self.assertEqual(report["summary"]["unmatched_entry_count"], 2)
        row_keys = {(row["lemma"], row["reading"], row["topic"]) for row in report["evidence_rows"]}
        self.assertIn(("米", "こめ", "food_cooking"), row_keys)
        self.assertIn(("猫", "ねこ", "food_cooking"), row_keys)
        self.assertNotIn(("米", "べい", "food_cooking"), row_keys)
        unmatched = {(row["lemma"], row["reason"]) for row in report["unmatched_entries"]}
        self.assertIn(("米", "candidate_ambiguous"), unmatched)
        self.assertIn(("missing", "candidate_missing"), unmatched)

        markdown = render_markdown(report)
        self.assertIn("en-ja SRS Manual Semantic Lexicon Evidence", markdown)
        self.assertIn("candidate_ambiguous", markdown)

    def test_checked_in_seed_resolves_against_corrected_ranking(self) -> None:
        report = build_report(generated_at="2026-07-01T00:00:00+00:00")

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["unmatched_entry_count"], 0)
        self.assertGreaterEqual(report["summary"]["topic_evidence_row_count"], 300)
        self.assertGreaterEqual(report["summary"]["facet_row_count"], 400)


def _write_candidates(path: Path, rows: list[tuple[str, str, str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["rank", "lemma", "reading", "score", "candidate_state", "topic_stretch_allowed"]
        )
        for rank, lemma, reading, score in rows:
            writer.writerow([rank, lemma, reading, score, "normal_vocab", "true"])


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
