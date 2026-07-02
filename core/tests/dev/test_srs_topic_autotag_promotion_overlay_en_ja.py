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

from srs_topic_autotag_promotion_overlay_en_ja import build_report, render_markdown  # noqa: E402


class SrsTopicAutotagPromotionOverlayEnJaTests(unittest.TestCase):
    def test_product_safe_overlay_preserves_reviewed_rows_and_filters_dump_noise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_csv = root / "candidates.csv"
            reviewed_overlay_json = root / "reviewed_overlay.json"
            review_labels_json = root / "review_labels.json"
            local_evidence_json = root / "local_evidence.json"
            dump_evidence_json = root / "dump_evidence.json"
            wikidata_evidence_json = root / "wikidata_evidence.json"
            manual_semantic_evidence_json = root / "manual_semantic_evidence.json"
            _write_candidates(
                candidates_csv,
                [
                    ("1", "脳", "のう", "normal_vocab", "true"),
                    ("2", "展開", "てんかい", "normal_vocab", "true"),
                    ("3", "旅行", "りょこう", "normal_vocab", "true"),
                    ("4", "今日", "きょう", "normal_vocab", "true"),
                    ("5", "今日", "こんにち", "normal_vocab", "true"),
                    ("6", "食べ物", "たべもの", "normal_vocab", "true"),
                    ("7", "スポーツ", "すぽーつ", "normal_vocab", "true"),
                    ("8", "茶色", "ちゃいろ", "normal_vocab", "true"),
                    ("9", "水", "みず", "normal_vocab", "true"),
                    ("10", "大勢", "おおぜい", "normal_vocab", "true"),
                    ("11", "寿司", "すし", "normal_vocab", "true"),
                    ("12", "漫画", "まんが", "normal_vocab", "true"),
                    ("13", "エミュレート", "えみゅれーと", "normal_vocab", "true"),
                ],
            )
            _write_json(
                reviewed_overlay_json,
                {
                    "decision": "reviewed_overlay_ready",
                    "rows": [
                        _reviewed_overlay_row("脳", "のう", "medicine_health", 1.0, "anatomy"),
                        _reviewed_overlay_row(
                            "展開", "てんかい", "finance_business", 0.65, "business"
                        ),
                    ],
                },
            )
            _write_json(
                review_labels_json,
                {
                    "labels": [
                        {
                            "lemma": "大勢",
                            "family_id": "sports_fitness",
                            "decision": "reject_wrong_sense",
                        }
                    ]
                },
            )
            _write_json(
                local_evidence_json, {"decision": "local_evidence_unused_by_promotion_test"}
            )
            _write_json(manual_semantic_evidence_json, {"evidence_rows": []})
            _write_json(
                dump_evidence_json,
                {
                    "decision": "guarded_dump_evidence_ready",
                    "evidence_rows": [
                        _kaikki_row("旅行", "りょこう", "travel_places_transport", "travel", 1),
                        _kaikki_row("今日", "きょう", "medicine_health", "medicine", 1),
                        _kaikki_row("水", "みず", "sports_fitness", "sumo", 3),
                        _kaikki_row("大勢", "おおぜい", "sports_fitness", "sumo", 1),
                        _wiki_row("食べ物", "たべもの", "food_cooking", "食べ物", "食べ物"),
                        _wiki_row("スポーツ", "すぽーつ", "games", "ゲーム", "スポーツ"),
                        _wiki_row("茶色", "ちゃいろ", "food_cooking", "茶", "茶色"),
                    ],
                },
            )
            _write_json(
                wikidata_evidence_json,
                {
                    "decision": "wikidata_claim_probe_has_topic_evidence",
                    "evidence_rows": [
                        _wikidata_row("寿司", "すし", "food_cooking", "food", "Q2095"),
                        _wikidata_row(
                            "エミュレート",
                            "えみゅれーと",
                            "science_technology",
                            "software",
                            "Q7397",
                        ),
                        _wikidata_row(
                            "漫画", "まんが", "anime_manga_pop_culture", "manga", "Q8274"
                        ),
                        _wikidata_row(
                            "漫画",
                            "まんが",
                            "arts_literature_humanities",
                            "literary work",
                            "Q7725634",
                        ),
                        _wikidata_row(
                            "水",
                            "みず",
                            "sports_fitness",
                            "sport",
                            "Q349",
                            confidence=0.67,
                        ),
                        _wikidata_row(
                            "大勢",
                            "おおぜい",
                            "sports_fitness",
                            "sport",
                            "Q349",
                        ),
                    ],
                },
            )

            report = build_report(
                candidates_csv=candidates_csv,
                reviewed_overlay_json=reviewed_overlay_json,
                review_labels_json=review_labels_json,
                local_evidence_json=local_evidence_json,
                dump_evidence_json=dump_evidence_json,
                wikidata_evidence_json=wikidata_evidence_json,
                manual_semantic_evidence_json=manual_semantic_evidence_json,
                generated_at="2026-07-01T00:00:00+00:00",
            )

        self.assertEqual(report["status"], "ok")
        rows = report["topic_overlay"]["rows"]
        row_by_key = {(row["lemma"], row["topic"]): row for row in rows}
        self.assertIn(("脳", "medicine_health"), row_by_key)
        self.assertIn(("展開", "work_office"), row_by_key)
        self.assertIn(("旅行", "travel_places_transport"), row_by_key)
        self.assertIn(("食べ物", "food_cooking"), row_by_key)
        self.assertIn(("今日", "medicine_health"), row_by_key)
        self.assertIn(("寿司", "food_cooking"), row_by_key)
        self.assertIn(("エミュレート", "computing_internet"), row_by_key)
        self.assertIn(("漫画", "anime_manga_pop_culture"), row_by_key)
        self.assertIn(("漫画", "arts_literature_humanities"), row_by_key)
        self.assertNotIn(("展開", "finance_business"), row_by_key)
        self.assertNotIn(("エミュレート", "science_technology"), row_by_key)
        self.assertNotIn(("水", "sports_fitness"), row_by_key)
        self.assertNotIn(("大勢", "sports_fitness"), row_by_key)
        self.assertNotIn(("スポーツ", "games"), row_by_key)
        self.assertNotIn(("茶色", "food_cooking"), row_by_key)
        self.assertEqual(
            row_by_key[("脳", "medicine_health")]["promotion_rule"], "reviewed_jmdict_overlay"
        )
        self.assertEqual(row_by_key[("旅行", "travel_places_transport")]["membership"], 0.65)
        self.assertIn(
            "unreviewed_auto_topic_evidence_requires_manual_acceptance",
            row_by_key[("旅行", "travel_places_transport")]["runtime_blockers"],
        )
        self.assertEqual(row_by_key[("食べ物", "food_cooking")]["membership"], 0.65)
        self.assertEqual(
            row_by_key[("寿司", "food_cooking")]["promotion_rule"], "strict_wikidata_claim_probe"
        )
        self.assertEqual(
            row_by_key[("エミュレート", "computing_internet")]["promotion_rule"],
            "strict_wikidata_claim_probe",
        )
        self.assertEqual(row_by_key[("漫画", "anime_manga_pop_culture")]["membership"], 0.65)
        self.assertEqual(row_by_key[("漫画", "arts_literature_humanities")]["membership"], 0.65)
        self.assertEqual(row_by_key[("今日", "medicine_health")]["membership"], 0.65)
        self.assertIn(
            "runtime_overlay_is_lemma_only_but_candidate_has_multiple_readings",
            row_by_key[("今日", "medicine_health")]["runtime_blockers"],
        )

    def test_markdown_summarizes_runtime_effective_and_review_only_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_csv = root / "candidates.csv"
            reviewed_overlay_json = root / "reviewed_overlay.json"
            review_labels_json = root / "review_labels.json"
            local_evidence_json = root / "local_evidence.json"
            dump_evidence_json = root / "dump_evidence.json"
            wikidata_evidence_json = root / "wikidata_evidence.json"
            manual_semantic_evidence_json = root / "manual_semantic_evidence.json"
            _write_candidates(
                candidates_csv,
                [
                    ("1", "旅行", "りょこう", "normal_vocab", "true"),
                    ("2", "今日", "きょう", "normal_vocab", "true"),
                    ("3", "今日", "こんにち", "normal_vocab", "true"),
                ],
            )
            _write_json(reviewed_overlay_json, {"rows": []})
            _write_json(review_labels_json, {"labels": []})
            _write_json(local_evidence_json, {})
            _write_json(wikidata_evidence_json, {"evidence_rows": []})
            _write_json(manual_semantic_evidence_json, {"evidence_rows": []})
            _write_json(
                dump_evidence_json,
                {
                    "evidence_rows": [
                        _kaikki_row("旅行", "りょこう", "travel_places_transport", "travel", 1),
                        _kaikki_row("今日", "きょう", "medicine_health", "medicine", 1),
                    ]
                },
            )

            report = build_report(
                candidates_csv=candidates_csv,
                reviewed_overlay_json=reviewed_overlay_json,
                review_labels_json=review_labels_json,
                local_evidence_json=local_evidence_json,
                dump_evidence_json=dump_evidence_json,
                wikidata_evidence_json=wikidata_evidence_json,
                manual_semantic_evidence_json=manual_semantic_evidence_json,
                generated_at="2026-07-01T00:00:00+00:00",
            )

        markdown = render_markdown(report)
        self.assertIn("Runtime-effective rows: `0`", markdown)
        self.assertIn("Review-only rows: `2`", markdown)
        self.assertIn("旅行", markdown)
        self.assertIn("今日", markdown)

    def test_manual_semantic_lexicon_promotes_only_product_safe_topic_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_csv = root / "candidates.csv"
            reviewed_overlay_json = root / "reviewed_overlay.json"
            review_labels_json = root / "review_labels.json"
            local_evidence_json = root / "local_evidence.json"
            dump_evidence_json = root / "dump_evidence.json"
            wikidata_evidence_json = root / "wikidata_evidence.json"
            manual_semantic_evidence_json = root / "manual_semantic_evidence.json"
            _write_candidates(
                candidates_csv,
                [
                    ("1", "寿司", "すし", "normal_vocab", "true"),
                    ("2", "米", "こめ", "normal_vocab", "true"),
                    ("3", "米", "べい", "normal_vocab", "true"),
                    ("4", "赤", "あか", "normal_vocab", "true"),
                ],
            )
            _write_json(reviewed_overlay_json, {"rows": []})
            _write_json(review_labels_json, {"labels": []})
            _write_json(local_evidence_json, {})
            _write_json(dump_evidence_json, {"evidence_rows": []})
            _write_json(wikidata_evidence_json, {"evidence_rows": []})
            _write_json(
                manual_semantic_evidence_json,
                {
                    "decision": "manual_semantic_lexicon_evidence_ready",
                    "evidence_rows": [
                        _manual_semantic_row(
                            "寿司",
                            "すし",
                            "food_cooking",
                            "common_food_drink",
                            promotion_eligible=True,
                        ),
                        _manual_semantic_row(
                            "米",
                            "こめ",
                            "food_cooking",
                            "common_food_drink",
                            promotion_eligible=True,
                        ),
                        _manual_semantic_row(
                            "赤",
                            "あか",
                            "colors",
                            "colors_basic",
                            promotion_eligible=False,
                        ),
                    ],
                },
            )

            report = build_report(
                candidates_csv=candidates_csv,
                reviewed_overlay_json=reviewed_overlay_json,
                review_labels_json=review_labels_json,
                local_evidence_json=local_evidence_json,
                dump_evidence_json=dump_evidence_json,
                wikidata_evidence_json=wikidata_evidence_json,
                manual_semantic_evidence_json=manual_semantic_evidence_json,
                generated_at="2026-07-01T00:00:00+00:00",
            )

        rows = report["topic_overlay"]["rows"]
        row_by_key = {(row["lemma"], row["topic"]): row for row in rows}
        self.assertIn(("寿司", "food_cooking"), row_by_key)
        self.assertIn(("米", "food_cooking"), row_by_key)
        self.assertNotIn(("赤", "colors"), row_by_key)
        self.assertEqual(
            row_by_key[("寿司", "food_cooking")]["promotion_rule"],
            "product_owned_manual_semantic_lexicon",
        )
        self.assertEqual(row_by_key[("寿司", "food_cooking")]["membership"], 1.0)
        self.assertEqual(row_by_key[("米", "food_cooking")]["membership"], 0.65)
        self.assertIn(
            "runtime_overlay_is_lemma_only_but_candidate_has_multiple_readings",
            row_by_key[("米", "food_cooking")]["runtime_blockers"],
        )

    def test_auto_review_labels_accept_or_reject_auto_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_csv = root / "candidates.csv"
            reviewed_overlay_json = root / "reviewed_overlay.json"
            review_labels_json = root / "review_labels.json"
            auto_review_labels_json = root / "auto_review_labels.json"
            local_evidence_json = root / "local_evidence.json"
            dump_evidence_json = root / "dump_evidence.json"
            wikidata_evidence_json = root / "wikidata_evidence.json"
            manual_semantic_evidence_json = root / "manual_semantic_evidence.json"
            _write_candidates(
                candidates_csv,
                [
                    ("1", "旅行", "りょこう", "normal_vocab", "true"),
                    ("2", "妊娠", "にんしん", "normal_vocab", "true"),
                    ("3", "米", "こめ", "normal_vocab", "true"),
                    ("4", "米", "べい", "normal_vocab", "true"),
                ],
            )
            _write_json(reviewed_overlay_json, {"rows": []})
            _write_json(review_labels_json, {"labels": []})
            _write_json(
                auto_review_labels_json,
                {
                    "labels": [
                        {
                            "lemma": "旅行",
                            "reading": "りょこう",
                            "topic": "travel_places_transport",
                            "decision": "accept_runtime",
                            "reason": "Direct travel vocabulary.",
                        },
                        {
                            "lemma": "妊娠",
                            "reading": "にんしん",
                            "topic": "games",
                            "decision": "reject_wrong_sense",
                            "reason": "Video-game slang sense is not product-safe for pregnancy.",
                        },
                        {
                            "lemma": "米",
                            "reading": "こめ",
                            "topic": "food_cooking",
                            "decision": "accept_runtime",
                            "reason": "Rice is direct food vocabulary.",
                        },
                    ]
                },
            )
            _write_json(local_evidence_json, {})
            _write_json(wikidata_evidence_json, {"evidence_rows": []})
            _write_json(manual_semantic_evidence_json, {"evidence_rows": []})
            _write_json(
                dump_evidence_json,
                {
                    "evidence_rows": [
                        _kaikki_row("旅行", "りょこう", "travel_places_transport", "travel", 1),
                        _kaikki_row("妊娠", "にんしん", "games", "video games", 1),
                        _kaikki_row("米", "こめ", "food_cooking", "food", 1),
                    ]
                },
            )

            report = build_report(
                candidates_csv=candidates_csv,
                reviewed_overlay_json=reviewed_overlay_json,
                review_labels_json=review_labels_json,
                auto_review_labels_json=auto_review_labels_json,
                local_evidence_json=local_evidence_json,
                dump_evidence_json=dump_evidence_json,
                wikidata_evidence_json=wikidata_evidence_json,
                manual_semantic_evidence_json=manual_semantic_evidence_json,
                generated_at="2026-07-01T00:00:00+00:00",
            )

        rows = report["topic_overlay"]["rows"]
        row_by_key = {(row["lemma"], row["topic"]): row for row in rows}
        self.assertIn(("旅行", "travel_places_transport"), row_by_key)
        self.assertNotIn(("妊娠", "games"), row_by_key)
        self.assertEqual(row_by_key[("旅行", "travel_places_transport")]["membership"], 1.0)
        self.assertEqual(
            row_by_key[("旅行", "travel_places_transport")]["review_decision"],
            "auto_review_accepted_runtime_effective",
        )
        self.assertNotIn(
            "unreviewed_auto_topic_evidence_requires_manual_acceptance",
            row_by_key[("旅行", "travel_places_transport")]["runtime_blockers"],
        )
        self.assertEqual(row_by_key[("米", "food_cooking")]["membership"], 0.65)
        self.assertEqual(
            row_by_key[("米", "food_cooking")]["review_decision"],
            "auto_review_accepted_runtime_blocked",
        )
        self.assertIn(
            "runtime_overlay_is_lemma_only_but_candidate_has_multiple_readings",
            row_by_key[("米", "food_cooking")]["runtime_blockers"],
        )
        excluded = report["topic_overlay"]["overlay_policy"]["excluded_counts"]
        self.assertEqual(
            excluded["kaikki_wiktionary_topic:auto_review_rejected:reject_wrong_sense"], 1
        )


def _write_candidates(path: Path, rows: list[tuple[str, str, str, str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["rank", "lemma", "reading", "candidate_state", "topic_stretch_allowed"])
        writer.writerows(rows)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _reviewed_overlay_row(
    lemma: str,
    reading: str,
    topic: str,
    membership: float,
    source_label: str,
) -> dict[str, object]:
    return {
        "lemma": lemma,
        "reading": reading,
        "language_pair": "en-ja",
        "topic": topic,
        "membership": membership,
        "confidence_label": "strong" if membership >= 1.0 else "light",
        "review_id": f"reviewed-{lemma}-{topic}",
        "source_labels": [source_label],
        "primary_source_label": source_label,
        "evidence": {"rank": 1.0},
        "provenance": {},
    }


def _kaikki_row(
    lemma: str,
    reading: str,
    topic: str,
    source_label: str,
    sense_index: int,
) -> dict[str, object]:
    return {
        "lemma": lemma,
        "reading": reading,
        "language_pair": "en-ja",
        "topic": topic,
        "membership": 0.68,
        "confidence": 0.66,
        "source": "kaikki_wiktionary_topic",
        "source_label": source_label,
        "evidence_label": f"Kaikki/Wiktionary sense topic: {source_label}",
        "rank": 1,
        "core_rank": 1.0,
        "score": 0.5,
        "band": "0.00-0.05",
        "candidate_state": "normal_vocab",
        "topic_stretch_allowed": "true",
        "review_posture": "offline_dump_candidate_generation",
        "license_note": "test fixture",
        "extra": {
            "reading_identity": "external_unique_surface_reading",
            "kaikki_sense_index": sense_index,
            "kaikki_glosses": [source_label],
            "kaikki_categories": [source_label],
        },
    }


def _manual_semantic_row(
    lemma: str,
    reading: str,
    topic: str,
    collection_id: str,
    *,
    promotion_eligible: bool,
) -> dict[str, object]:
    return {
        "lemma": lemma,
        "reading": reading,
        "language_pair": "en-ja",
        "topic": topic,
        "membership": 1.0,
        "confidence": 0.98,
        "source": "manual_semantic_lexicon",
        "source_label": collection_id,
        "evidence_label": f"Manual semantic lexicon: {collection_id}",
        "rank": 1,
        "core_rank": 1.0,
        "score": 0.5,
        "band": "0.00-0.05",
        "candidate_state": "normal_vocab",
        "topic_stretch_allowed": "true",
        "review_posture": "product_owned_closed_set",
        "license_note": "test fixture",
        "extra": {
            "manual_semantic_collection_id": collection_id,
            "manual_semantic_output_kind": "topic",
            "manual_semantic_promotion_eligible": promotion_eligible,
        },
    }


def _wiki_row(
    lemma: str,
    reading: str,
    topic: str,
    source_label: str,
    title: str,
) -> dict[str, object]:
    return {
        "lemma": lemma,
        "reading": reading,
        "language_pair": "en-ja",
        "topic": topic,
        "membership": 0.72,
        "confidence": 0.68,
        "source": "jawikipedia_dump_category",
        "source_label": source_label,
        "evidence_label": f"ja.wikipedia dump category/title keyword: {source_label}",
        "rank": 1,
        "core_rank": 1.0,
        "score": 0.5,
        "band": "0.00-0.05",
        "candidate_state": "normal_vocab",
        "topic_stretch_allowed": "true",
        "review_posture": "offline_dump_candidate_generation",
        "license_note": "test fixture",
        "extra": {
            "reading_identity": "external_unique_surface_reading",
            "wikipedia_title": title,
            "wikipedia_resolved_title": title,
        },
    }


def _wikidata_row(
    lemma: str,
    reading: str,
    topic: str,
    source_label: str,
    root_qid: str,
    *,
    confidence: float = 0.72,
    membership: float = 0.76,
) -> dict[str, object]:
    qid = f"Q{abs(hash((lemma, topic))) % 100000 + 100000}"
    return {
        "lemma": lemma,
        "reading": reading,
        "language_pair": "en-ja",
        "topic": topic,
        "membership": membership,
        "confidence": confidence,
        "source": "wikidata_claim_probe",
        "source_label": source_label,
        "evidence_label": f"Wikidata claim path: {lemma} -> {source_label}",
        "rank": 1,
        "core_rank": 1.0,
        "score": 0.5,
        "band": "0.00-0.05",
        "candidate_state": "normal_vocab",
        "topic_stretch_allowed": "true",
        "review_posture": "online_probe_candidate_generation",
        "license_note": "test fixture",
        "extra": {
            "reading_identity": "external_unique_surface_reading",
            "source_readings": [],
            "wikidata_qid": qid,
            "wikidata_label": lemma,
            "wikidata_description": "test entity",
            "wikidata_root_qid": root_qid,
            "wikidata_root_label": source_label,
            "wikidata_path": [qid, root_qid],
            "wikidata_depth": 1,
            "wikidata_search_match": {
                "language": "ja",
                "text": lemma,
                "type": "jawikipedia_pageprops",
            },
        },
    }


if __name__ == "__main__":
    unittest.main()
