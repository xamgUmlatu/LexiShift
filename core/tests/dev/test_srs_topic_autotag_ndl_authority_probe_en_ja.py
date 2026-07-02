from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from collections import Counter


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_topic_autotag_ndl_authority_probe_en_ja import (  # noqa: E402
    NdlAuthorityCache,
    build_merged_report,
    _evidence_rows_from_authorities,
    _is_topical_authority,
    _select_candidates,
)


class SrsTopicAutotagNdlAuthorityProbeEnJaTests(unittest.TestCase):
    def test_topical_subject_authority_emits_topic_evidence_but_name_authority_does_not(
        self,
    ) -> None:
        candidates = [_candidate(1, "野球", "やきゅう")]
        rules = [
            {
                "target_family": "sports_fitness",
                "membership": 0.7,
                "confidence": 0.66,
                "include_any": ["野球"],
            }
        ]
        topical = _authority(
            "http://id.ndl.go.jp/auth/ndlsh/00574218",
            "topicalTerms",
            "野球",
        )
        personal_name = _authority(
            "http://id.ndl.go.jp/auth/ndlna/000000000",
            "personalNames",
            "野球",
        )

        rows = _evidence_rows_from_authorities(
            lemma="野球",
            candidate_rows=candidates,
            authority_rows=[topical, personal_name],
            rules=rules,
            posture={},
            include_non_topical_authorities=False,
            reading_identity_stats=Counter(),
        )

        self.assertTrue(_is_topical_authority(topical))
        self.assertFalse(_is_topical_authority(personal_name))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["lemma"], "野球")
        self.assertEqual(rows[0]["topic"], "sports_fitness")
        self.assertEqual(rows[0]["extra"]["ndl_authority_kind"], "ndlsh")
        self.assertTrue(rows[0]["extra"]["ndl_topical_authority"])

    def test_non_topical_authorities_can_be_included_for_research_when_requested(self) -> None:
        candidates = [_candidate(1, "桜", "さくら")]
        rules = [
            {
                "target_family": "plants_nature",
                "membership": 0.72,
                "confidence": 0.68,
                "include_any": ["桜"],
            }
        ]
        personal_name = _authority(
            "http://id.ndl.go.jp/auth/ndlna/001322136",
            "personalNames",
            "桜",
        )

        rows = _evidence_rows_from_authorities(
            lemma="桜",
            candidate_rows=candidates,
            authority_rows=[personal_name],
            rules=rules,
            posture={},
            include_non_topical_authorities=True,
            reading_identity_stats=Counter(),
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["extra"]["ndl_authority_kind"], "ndlna")
        self.assertFalse(rows[0]["extra"]["ndl_topical_authority"])

    def test_related_labels_are_review_context_not_keyword_triggers(self) -> None:
        candidates = [_candidate(1, "漫画", "まんが")]
        rules = [
            {
                "target_family": "food_cooking",
                "membership": 0.72,
                "confidence": 0.68,
                "include_any": ["茶"],
            }
        ]
        topical = _authority(
            "http://id.ndl.go.jp/auth/ndlsh/00567438",
            "topicalTerms",
            "漫画",
            broader_labels=["絵画"],
            related_labels=["漫画喫茶"],
        )

        rows = _evidence_rows_from_authorities(
            lemma="漫画",
            candidate_rows=candidates,
            authority_rows=[topical],
            rules=rules,
            posture={},
            include_non_topical_authorities=False,
            reading_identity_stats=Counter(),
        )

        self.assertEqual(rows, [])

    def test_candidate_selection_requires_unique_runtime_safe_reading_and_can_exclude_covered(
        self,
    ) -> None:
        candidates = [
            _candidate(1, "寿司", "すし"),
            _candidate(2, "今日", "きょう"),
            _candidate(3, "今日", "こんにち"),
            _candidate(4, "音", "おん", topic_stretch_allowed="false"),
            _candidate(5, "台風", "たいふう"),
        ]

        selected = _select_candidates(
            candidates,
            explicit_lemmas=(),
            covered_lemmas={"寿司"},
            include_covered=False,
        )

        self.assertEqual([row["lemma"] for row in selected], ["台風"])

    def test_cache_load_tolerates_missing_errors_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "cache.json"
            cache_path.write_text(
                json.dumps({"labels": {"野球": []}}, ensure_ascii=False), encoding="utf-8"
            )

            cache = NdlAuthorityCache.load(cache_path)

        self.assertEqual(cache.labels, {"野球": []})
        self.assertEqual(cache.errors, {})

    def test_merged_report_marks_missing_chunks_and_dedupes_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            chunk_dir = root / "chunks"
            chunk_dir.mkdir()
            row = {
                "lemma": "野球",
                "reading": "やきゅう",
                "language_pair": "en-ja",
                "topic": "sports_fitness",
                "source_label": "野球",
                "score": 0.2,
                "extra": {"ndl_uri": "http://id.ndl.go.jp/auth/ndlsh/00574218"},
            }
            _write_json(
                chunk_dir / "chunk_0000.json",
                {
                    "chunk": {"run_id": "test-run", "chunk_index": 0, "label_count": 2},
                    "authority_scheme_counts": {"topicalTerms": 1},
                    "authority_kind_counts": {"ndlsh": 1},
                    "evidence_rows": [row, row],
                    "findings": [],
                },
            )
            _write_json(
                chunk_dir / "chunk_0001.json",
                {
                    "chunk": {"run_id": "other-run", "chunk_index": 1, "label_count": 2},
                    "authority_scheme_counts": {"topicalTerms": 99},
                    "authority_kind_counts": {"ndlsh": 99},
                    "evidence_rows": [],
                    "findings": [],
                },
            )

            report = build_merged_report(
                chunk_dir=chunk_dir,
                run_id="test-run",
                expected_chunk_count=2,
                eligible_label_count=3,
                chunk_size=2,
                include_covered=True,
                include_non_topical_authorities=False,
                candidates_csv=root / "candidates.csv",
                policy_json=root / "policy.json",
                existing_overlay_json=root / "overlay.json",
                cache_json=root / "cache.json",
                top_n=10,
                generated_at="2026-07-01T00:00:00+00:00",
            )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["chunk_summary"]["missing_chunk_count"], 1)
        self.assertEqual(report["authority_scheme_counts"], {"topicalTerms": 1})
        self.assertEqual(len(report["evidence_rows"]), 1)


def _candidate(
    rank: int,
    lemma: str,
    reading: str,
    *,
    candidate_state: str = "normal_vocab",
    topic_stretch_allowed: str = "true",
) -> dict[str, object]:
    return {
        "rank": rank,
        "lemma": lemma,
        "reading": reading,
        "score": 0.4,
        "band": "0.40-0.45",
        "candidate_state": candidate_state,
        "topic_stretch_allowed": topic_stretch_allowed,
    }


def _authority(
    uri: str,
    scheme_kind: str,
    label: str,
    *,
    broader_labels: list[str] | None = None,
    related_labels: list[str] | None = None,
) -> dict[str, object]:
    return {
        "uri": uri,
        "authority_kind": uri.rstrip("/").split("/")[-2],
        "label": label,
        "alt_labels": [],
        "scheme_uris": [f"http://id.ndl.go.jp/auth#{scheme_kind}"],
        "scheme_kinds": [scheme_kind],
        "broader_labels": broader_labels or [],
        "related_labels": related_labels or [],
    }


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
