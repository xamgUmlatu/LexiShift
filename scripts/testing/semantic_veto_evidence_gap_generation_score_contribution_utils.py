from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Mapping, Sequence


def _application_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    return {
        "active_items_applied": sum(
            1 for row in rows if row.get("action") == "active_evidence_appended"
        ),
        "active_items_ignored": sum(
            1 for row in rows if row.get("action") == "active_evidence_ignored"
        ),
        "existing_shadow_items_applied": sum(
            1 for row in rows if row.get("action") == "existing_shadow_evidence_appended"
        ),
        "shadow_items_ignored": sum(
            1 for row in rows if row.get("action") == "shadow_evidence_ignored"
        ),
        "synthetic_shadow_items_applied": sum(
            1 for row in rows if row.get("action") == "synthetic_shadow_created"
        ),
        "new_shadow_items_ignored": sum(
            1 for row in rows if row.get("action") == "new_shadow_target_ignored"
        ),
        "no_winner_items_ignored": sum(
            1 for row in rows if row.get("action") == "no_winner_context_not_runtime_evidence"
        ),
    }


def _report_modes(*, include_base: bool = False) -> tuple[str, ...]:
    modes = (
        "generated_active_only",
        "generated_shadow_existing_only",
        "generated_shadow_synthetic_only",
        "generated_existing_shadows",
        "generated_synthetic_shadows",
    )
    return ("base", *modes) if include_base else modes


def _write_dataset(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _count_by(rows: Sequence[Mapping[str, object]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _delta(candidate: Mapping[str, object], base: Mapping[str, object], key: str) -> float | None:
    candidate_value = candidate.get(key)
    base_value = base.get(key)
    if candidate_value is None or base_value is None:
        return None
    return round(float(candidate_value) - float(base_value), 6)


def _fmt(value: object) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _normalize_target(value: str) -> str:
    return " ".join(value.lower().split())


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", value.strip()).strip("-").lower()
    return slug or "unnamed"


def _load_json(path: Path) -> Mapping[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [row for row in value if isinstance(row, Mapping)]
    return []


def _as_mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
