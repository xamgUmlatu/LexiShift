#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path | None) -> dict[str, object] | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _heldout_family_ids(payload: Mapping[str, object]) -> list[str]:
    rows = _as_sequence(payload.get("heldout_families"))
    family_ids = [
        str(row.get("family_id") or "").strip()
        for row in rows
        if isinstance(row, Mapping) and str(row.get("family_id") or "").strip()
    ]
    return sorted(set(family_ids))


def _sense_sidecar_for(admission_path: Path) -> Path:
    prefix = admission_path.with_suffix("")
    return prefix.parent / f"{prefix.name}_sense.json"


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


def _best_comparator(comparator_admissions: Sequence[Mapping[str, object]]) -> Mapping[str, object]:
    if not comparator_admissions:
        return {}
    return min(
        comparator_admissions,
        key=lambda row: (
            int(row.get("sense_rejected_row_count") or 0),
            int(row.get("seed_harmful_replace_count") or 0),
            int(row.get("seed_false_abstain_count") or 0),
        ),
    )


def _label_at(labels: Sequence[str], index: int, default: str) -> str:
    if index < len(labels) and str(labels[index] or "").strip():
        return str(labels[index]).strip()
    return default


def _item_at(
    values: Sequence[Mapping[str, object] | None], index: int
) -> Mapping[str, object] | None:
    if index < len(values):
        return values[index]
    return None


def _family_token(identifier: str) -> str:
    parts = [part for part in str(identifier or "").split(":") if part]
    if not parts:
        return "unknown"
    if parts[-1].isdigit() and len(parts) >= 2:
        return parts[-2]
    if len(parts) >= 3 and parts[0] == "en-es":
        return parts[-2]
    return parts[-1]


def _reason_count_ids(reason_counts: Mapping[str, object]) -> list[str]:
    ids: list[str] = []
    for reason, count in reason_counts.items():
        ids.append(f"{reason}:{int(count or 0)}")
    return ids


def _safe_ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(float(numerator) / float(denominator), 4)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
