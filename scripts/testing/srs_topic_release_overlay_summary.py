from __future__ import annotations

from collections import Counter
from typing import Mapping, Sequence


def summarize_topic_overlays(
    overlay_payloads: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    by_topic: dict[str, dict[str, object]] = {}
    overlay_ids: list[str] = []
    for payload in overlay_payloads:
        if str(payload.get("status") or "") != "ok":
            continue
        overlay_ids.append(str(payload.get("overlay_id") or ""))
        for row in _mapping_rows(payload.get("rows")):
            topic = str(row.get("topic") or "").strip()
            lemma = str(row.get("lemma") or "").strip()
            if not topic or not lemma:
                continue
            _record_overlay_row(by_topic, topic=topic, lemma=lemma, row=row)

    return {
        "overlay_count": len(overlay_payloads),
        "ready_overlay_ids": [overlay_id for overlay_id in overlay_ids if overlay_id],
        "topics_with_reviewed_overlay": sorted(by_topic),
        "by_topic": {
            topic: _public_topic_overlay_summary(row) for topic, row in sorted(by_topic.items())
        },
    }


def _record_overlay_row(
    by_topic: dict[str, dict[str, object]],
    *,
    topic: str,
    lemma: str,
    row: Mapping[str, object],
) -> None:
    topic_entry = by_topic.setdefault(
        topic,
        {
            "row_count": 0,
            "raw_row_count": 0,
            "lemmas": set(),
            "raw_lemmas": set(),
            "counts_by_confidence": Counter(),
            "raw_counts_by_confidence": Counter(),
        },
    )
    confidence = str(row.get("confidence_label") or "unknown").strip() or "unknown"
    topic_entry["raw_row_count"] = int(topic_entry["raw_row_count"]) + 1
    _add_to_set(topic_entry.get("raw_lemmas"), lemma)
    _increment_counter(topic_entry.get("raw_counts_by_confidence"), confidence)
    if _overlay_row_is_runtime_eligible(row):
        topic_entry["row_count"] = int(topic_entry["row_count"]) + 1
        _add_to_set(topic_entry.get("lemmas"), lemma)
        _increment_counter(topic_entry.get("counts_by_confidence"), confidence)


def _public_topic_overlay_summary(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "row_count": int(row.get("row_count") or 0),
        "raw_row_count": int(row.get("raw_row_count") or 0),
        "lemma_count": _set_len(row.get("lemmas")),
        "raw_lemma_count": _set_len(row.get("raw_lemmas")),
        "counts_by_confidence": _counter_dict(row.get("counts_by_confidence")),
        "raw_counts_by_confidence": _counter_dict(row.get("raw_counts_by_confidence")),
    }


def _overlay_row_is_runtime_eligible(row: Mapping[str, object]) -> bool:
    return _safe_float(row.get("membership")) >= 1.0


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _safe_float(value: object) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _add_to_set(value: object, item: str) -> None:
    if isinstance(value, set):
        value.add(item)


def _increment_counter(value: object, item: str) -> None:
    if isinstance(value, Counter):
        value[item] += 1


def _set_len(value: object) -> int:
    return len(value) if isinstance(value, set) else 0


def _counter_dict(value: object) -> dict[str, int]:
    return dict(value) if isinstance(value, Counter) else {}
