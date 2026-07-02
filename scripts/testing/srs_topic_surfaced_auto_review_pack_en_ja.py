#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_SAMPLE_JSON = TEST_OUTPUTS_ROOT / "srs_admission_product_acceptance_en_ja_latest.json"
DEFAULT_OVERLAY_JSON = TEST_OUTPUTS_ROOT / "srs_topic_autotag_promotion_overlay_en_ja_latest.json"
DEFAULT_DUMP_EVIDENCE_JSON = (
    TEST_OUTPUTS_ROOT / "srs_topic_autotag_dump_source_bakeoff_en_ja_latest.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_topic_surfaced_auto_review_pack_en_ja_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_topic_surfaced_auto_review_pack_en_ja_latest.md"
RUNTIME_MEMBERSHIP = 1.0
TRUSTED_RUNTIME_RULES = {
    "product_owned_manual_semantic_lexicon",
    "reviewed_jmdict_overlay",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a review pack from auto topic rows that surfaced in en-ja "
            "SRS user-setting samples."
        )
    )
    parser.add_argument("--sample-json", type=Path, default=DEFAULT_SAMPLE_JSON)
    parser.add_argument("--overlay-json", type=Path, default=DEFAULT_OVERLAY_JSON)
    parser.add_argument("--dump-evidence-json", type=Path, default=DEFAULT_DUMP_EVIDENCE_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        sample_json=resolve_path(args.sample_json),
        overlay_json=resolve_path(args.overlay_json),
        dump_evidence_json=resolve_path(args.dump_evidence_json),
    )
    json_out = resolve_path(args.json_out)
    markdown_out = resolve_path(args.markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    return 0


def build_report(
    *,
    sample_json: Path,
    overlay_json: Path,
    dump_evidence_json: Path,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or datetime.now(timezone.utc).isoformat()
    sample = load_json(sample_json)
    overlay = load_json(overlay_json)
    dump_evidence = load_json(dump_evidence_json)
    overlay_rows = mapping_rows(overlay.get("rows"))
    overlay_by_key = build_overlay_index(overlay_rows)
    evidence_by_key = build_evidence_index(mapping_rows(dump_evidence.get("evidence_rows")))
    candidate_map: dict[tuple[str, str, str], dict[str, object]] = {}
    appearances_by_key: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)

    for appearance in iter_sample_word_appearances(sample):
        word = appearance["word"]
        if isinstance(word, Mapping):
            topic = topic_from_affinity(word.get("topic_affinity_source"))
            if not topic:
                continue
            lemma = str(word.get("lemma") or "")
            reading = str(word.get("reading") or "")
            key = (lemma, reading, topic)
            overlay_row = overlay_by_key.get(key) or overlay_by_key.get((lemma, "", topic))
            if not overlay_row or is_runtime_trusted(overlay_row):
                continue
            evidence_row = evidence_by_key.get(key) or evidence_by_key.get((lemma, "", topic))
            candidate_map[key] = review_candidate(
                word=word,
                overlay_row=overlay_row,
                evidence_row=evidence_row,
            )
            appearances_by_key[key].append(appearance_payload(appearance, word=word))

    rows = []
    for key, row in candidate_map.items():
        appearances = appearances_by_key[key]
        min_reranked_rank = min(
            (
                int_or_none(item.get("reranked_rank"))
                for item in appearances
                if int_or_none(item.get("reranked_rank")) is not None
            ),
            default=None,
        )
        rows.append(
            {
                **row,
                "appearance_count": len(appearances),
                "min_reranked_rank": min_reranked_rank,
                "appearances": appearances,
            }
        )
    rows.sort(
        key=lambda row: (
            str(row.get("topic") or ""),
            int_or_none(row.get("min_reranked_rank")) or 10_000,
            str(row.get("lemma") or ""),
            str(row.get("reading") or ""),
        )
    )
    counts_by_topic = Counter(str(row.get("topic") or "") for row in rows)
    counts_by_rule = Counter(str(row.get("promotion_rule") or "") for row in rows)
    return {
        "schema_version": 1,
        "status": "ok",
        "decision": "surfaced_auto_topic_review_pack_ready",
        "generated_at": generated_at,
        "language_pair": "en-ja",
        "inputs": {
            "sample_json": repo_path(sample_json),
            "overlay_json": repo_path(overlay_json),
            "dump_evidence_json": repo_path(dump_evidence_json),
            "sample_generated_at": sample.get("generated_at"),
            "overlay_generated_at": overlay.get("generated_at"),
        },
        "method": {
            "scope": "auto topic rows that surfaced in user-setting admission samples",
            "runtime_policy": "rows below membership 1.0 are review candidates only",
            "review_goal": "accept true topic rows into a product-owned or reviewed source; reject sense-contaminated rows",
        },
        "summary": {
            "row_count": len(rows),
            "counts_by_topic": dict(sorted(counts_by_topic.items())),
            "counts_by_promotion_rule": dict(sorted(counts_by_rule.items())),
        },
        "rows": rows,
    }


def iter_sample_word_appearances(sample: Mapping[str, object]) -> list[dict[str, object]]:
    appearances: list[dict[str, object]] = []
    for scenario in mapping_rows(sample.get("scenarios")):
        scenario_name = str(scenario.get("name") or "")
        for word in mapping_rows(scenario.get("admitted_words")):
            appearances.append(
                {
                    "scenario": scenario_name,
                    "draw_index": None,
                    "preview_seed": None,
                    "word": word,
                }
            )
        for draw in mapping_rows(scenario.get("draws")):
            for word in mapping_rows(draw.get("admitted_words")):
                appearances.append(
                    {
                        "scenario": scenario_name,
                        "draw_index": draw.get("draw_index"),
                        "preview_seed": draw.get("preview_seed"),
                        "word": word,
                    }
                )
    return appearances


def appearance_payload(
    appearance: Mapping[str, object],
    *,
    word: Mapping[str, object],
) -> dict[str, object]:
    payload = {
        "scenario": appearance.get("scenario"),
        "reranked_rank": word.get("reranked_rank"),
        "base_rank": word.get("base_rank"),
        "rank_delta": word.get("rank_delta"),
    }
    if appearance.get("draw_index") is not None:
        payload["draw_index"] = appearance.get("draw_index")
    if appearance.get("preview_seed") is not None:
        payload["preview_seed"] = appearance.get("preview_seed")
    return payload


def review_candidate(
    *,
    word: Mapping[str, object],
    overlay_row: Mapping[str, object],
    evidence_row: Mapping[str, object] | None,
) -> dict[str, object]:
    evidence = as_mapping(overlay_row.get("evidence"))
    extra = as_mapping(evidence_row.get("extra") if evidence_row else {})
    return {
        "topic": overlay_row.get("topic"),
        "lemma": overlay_row.get("lemma"),
        "reading": overlay_row.get("reading") or word.get("reading"),
        "corrected_difficulty": word.get("corrected_difficulty"),
        "corrected_rank": word.get("corrected_rank"),
        "promotion_rule": overlay_row.get("promotion_rule"),
        "membership": overlay_row.get("membership"),
        "review_decision": overlay_row.get("review_decision"),
        "runtime_blockers": list(overlay_row.get("runtime_blockers") or []),
        "source_labels": list(overlay_row.get("source_labels") or []),
        "source": evidence.get("source"),
        "evidence_label": evidence.get("evidence_label"),
        "evidence_glosses": list(extra.get("kaikki_glosses") or [])[:5],
        "wikipedia_categories": list(extra.get("wikipedia_categories") or [])[:10],
    }


def build_overlay_index(
    rows: Sequence[Mapping[str, object]],
) -> dict[tuple[str, str, str], Mapping[str, object]]:
    index: dict[tuple[str, str, str], Mapping[str, object]] = {}
    for row in rows:
        lemma = str(row.get("lemma") or "")
        reading = str(row.get("reading") or "")
        topic = str(row.get("topic") or "")
        if lemma and topic:
            index[(lemma, reading, topic)] = row
    return index


def build_evidence_index(
    rows: Sequence[Mapping[str, object]],
) -> dict[tuple[str, str, str], Mapping[str, object]]:
    index: dict[tuple[str, str, str], Mapping[str, object]] = {}
    for row in rows:
        lemma = str(row.get("lemma") or "")
        reading = str(row.get("reading") or "")
        topic = str(row.get("topic") or "")
        if lemma and topic:
            index[(lemma, reading, topic)] = row
    return index


def is_runtime_trusted(row: Mapping[str, object]) -> bool:
    membership = float_or_none(row.get("membership")) or 0.0
    rule = str(row.get("promotion_rule") or "")
    return membership >= RUNTIME_MEMBERSHIP and rule in TRUSTED_RUNTIME_RULES


def topic_from_affinity(value: object) -> str:
    raw = str(value or "")
    if not raw.startswith("topic_hint:"):
        return ""
    return raw.removeprefix("topic_hint:").split("->")[-1].strip()


def render_markdown(report: Mapping[str, object]) -> str:
    summary = as_mapping(report.get("summary"))
    rows = mapping_rows(report.get("rows"))
    lines = [
        "# en-ja Surfaced Auto Topic Review Pack",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Rows: `{summary.get('row_count', 0)}`",
        "",
        "## Counts By Topic",
        "",
    ]
    for topic, count in as_mapping(summary.get("counts_by_topic")).items():
        lines.append(f"- `{topic}`: `{count}`")
    lines.extend(
        [
            "",
            "## Review Rows",
            "",
            "| Topic | Lemma | Reading | Difficulty | Best Rank | Rule | Labels | Gloss / Categories | Blockers |",
            "| --- | --- | --- | ---: | ---: | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        glosses = string_list(row.get("evidence_glosses"))
        categories = string_list(row.get("wikipedia_categories"))
        evidence_hint = "; ".join(glosses[:2]) or ", ".join(categories[:4])
        lines.append(
            f"| `{row.get('topic', '')}` | `{row.get('lemma', '')}` | "
            f"`{row.get('reading', '')}` | {row.get('corrected_difficulty', '')} | "
            f"{row.get('min_reranked_rank', '')} | `{row.get('promotion_rule', '')}` | "
            f"`{', '.join(string_list(row.get('source_labels'))[:4])}` | "
            f"{evidence_hint} | `{', '.join(string_list(row.get('runtime_blockers'))[:3])}` |"
        )
    return "\n".join(lines) + "\n"


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def string_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        return []
    return [str(item) for item in value if str(item)]


def float_or_none(value: object) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def int_or_none(value: object) -> int | None:
    parsed = float_or_none(value)
    if parsed is None:
        return None
    return int(parsed)


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
