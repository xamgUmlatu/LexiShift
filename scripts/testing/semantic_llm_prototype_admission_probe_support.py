from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


def _config_label(label: str, prototype_source_label: str) -> str:
    source_label = str(prototype_source_label or "").strip() or "reviewed examples"
    return str(label).replace("reviewed examples", source_label)


def _prototype_source_label(evidence_source_id: str) -> str:
    source_id = str(evidence_source_id or "").strip()
    if not source_id or source_id == "reviewed_sentence_veto_example_frames":
        return "reviewed examples"
    return source_id


def _source_shape(evidence_source_id: str) -> str:
    source_id = str(evidence_source_id or "").strip()
    if source_id:
        return f"{source_id}_as_per_sense_prototypes"
    return "reviewed_sentence_veto_examples_as_per_sense_prototypes"


def _round_float(value: object) -> float:
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return 0.0


def _unique_texts(values: Sequence[str]) -> list[str]:
    texts: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in texts:
            texts.append(text)
    return texts


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
