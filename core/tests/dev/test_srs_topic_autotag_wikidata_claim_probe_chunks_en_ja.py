from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_topic_autotag_wikidata_claim_probe_chunks_en_ja import (  # noqa: E402
    build_merged_report,
    _eligible_probe_candidates,
)


class SrsTopicAutotagWikidataClaimProbeChunksEnJaTests(unittest.TestCase):
    def test_eligible_candidates_keep_unique_runtime_safe_rows_and_can_include_covered(
        self,
    ) -> None:
        candidates = [
            _candidate(1, "寿司", "すし"),
            _candidate(2, "今日", "きょう"),
            _candidate(3, "今日", "こんにち"),
            _candidate(4, "音", "おん", topic_stretch_allowed="false"),
            _candidate(5, "居", "きょ", candidate_state="restricted_admission"),
            _candidate(6, "台風", "たいふう"),
        ]

        with_covered = _eligible_probe_candidates(
            candidates, covered_lemmas={"寿司"}, include_covered=True
        )
        without_covered = _eligible_probe_candidates(
            candidates, covered_lemmas={"寿司"}, include_covered=False
        )

        self.assertEqual([row["lemma"] for row in with_covered], ["寿司", "台風"])
        self.assertEqual([row["lemma"] for row in without_covered], ["台風"])

    def test_merged_report_dedupes_rows_and_marks_missing_or_incomplete_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            chunk_dir = root / "chunks"
            chunk_dir.mkdir()
            _write_json(
                chunk_dir / "chunk_0000.json",
                _chunk_report(0, [_evidence_row("寿司", "food_cooking", "Q2095")]),
            )
            _write_json(
                chunk_dir / "chunk_0001.json",
                _chunk_report(
                    1,
                    [
                        _evidence_row("寿司", "food_cooking", "Q2095"),
                        _evidence_row("台風", "plants_nature", "Q8092"),
                    ],
                    incomplete=True,
                ),
            )

            report = build_merged_report(
                chunk_dir=chunk_dir,
                expected_chunk_count=3,
                eligible_label_count=7,
                chunk_size=3,
                include_covered=True,
                candidates_csv=root / "candidates.csv",
                policy_json=root / "policy.json",
                existing_overlay_json=root / "overlay.json",
                cache_json=root / "cache.json",
                top_n=10,
                generated_at="2026-07-01T00:00:00+00:00",
            )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["chunk_summary"]["loaded_chunk_count"], 2)
        self.assertEqual(report["chunk_summary"]["complete_chunk_count"], 1)
        self.assertEqual(report["chunk_summary"]["incomplete_chunk_count"], 1)
        self.assertEqual(report["chunk_summary"]["missing_chunk_count"], 1)
        self.assertEqual(len(report["evidence_rows"]), 2)
        self.assertEqual({row["lemma"] for row in report["evidence_rows"]}, {"寿司", "台風"})


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
        "score": 0.5,
        "band": "0.50-0.55",
        "candidate_state": candidate_state,
        "topic_stretch_allowed": topic_stretch_allowed,
    }


def _chunk_report(
    chunk_index: int,
    evidence_rows: list[dict[str, object]],
    *,
    incomplete: bool = False,
) -> dict[str, object]:
    findings = []
    if incomplete:
        findings.append({"level": "WARN", "code": "wikidata_rate_limited", "message": "test"})
    return {
        "status": "ok",
        "decision": "test_chunk",
        "chunk": {
            "chunk_index": chunk_index,
            "label_count": 3,
            "complete": not incomplete,
        },
        "evidence_rows": evidence_rows,
        "findings": findings,
    }


def _evidence_row(lemma: str, topic: str, root_qid: str) -> dict[str, object]:
    qid = f"{root_qid}0"
    return {
        "lemma": lemma,
        "reading": lemma,
        "language_pair": "en-ja",
        "topic": topic,
        "membership": 0.8,
        "confidence": 0.76,
        "source": "wikidata_claim_probe",
        "source_label": topic,
        "score": 0.5,
        "extra": {
            "wikidata_qid": qid,
            "wikidata_root_qid": root_qid,
            "wikidata_path": [qid, root_qid],
        },
    }


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
