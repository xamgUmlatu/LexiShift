from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping, Sequence


ACTIVE_RELATION_TYPES = frozenset({"anchor_cue"})
SHADOW_RELATION_TYPES = frozenset({"shadow_candidate", "bridge_candidate"})
PHRASE_RELATION_TYPES = frozenset({"phrase_control_example"})


@dataclass(frozen=True)
class SourceSpec:
    mode: str
    label: str
    source_class: str
    payload: Mapping[str, object] | None
    path: str
    description: str


def resolve_source_specs(
    *,
    source_modes: Sequence[str],
    reverse_aux_path: Path,
    generated_composite_path: Path,
    extra_evidence_paths: Sequence[Path],
    overrides: Mapping[str, Mapping[str, object]],
) -> tuple[list[SourceSpec], list[dict[str, object]]]:
    specs: list[SourceSpec] = []
    skipped: list[dict[str, object]] = []
    custom_payloads = {
        f"custom_{index}": _load_json(path)
        for index, path in enumerate(extra_evidence_paths, start=1)
    }
    for mode in _normalize_string_list(source_modes):
        if mode in overrides:
            specs.append(
                SourceSpec(
                    mode=mode,
                    label=mode,
                    source_class="candidate_source",
                    payload=overrides[mode],
                    path="override",
                    description="caller-provided evidence batch",
                )
            )
            continue
        if mode in custom_payloads:
            specs.append(
                SourceSpec(
                    mode=mode,
                    label=mode,
                    source_class="candidate_source",
                    payload=custom_payloads[mode],
                    path=str(extra_evidence_paths[int(mode.split("_", 1)[1]) - 1]),
                    description="custom evidence batch",
                )
            )
            continue
        resolved = _default_source_spec(
            mode=mode,
            reverse_aux_path=reverse_aux_path,
            generated_composite_path=generated_composite_path,
            skipped=skipped,
        )
        if resolved is not None:
            specs.append(resolved)
    return specs, skipped


def _default_source_spec(
    *,
    mode: str,
    reverse_aux_path: Path,
    generated_composite_path: Path,
    skipped: list[dict[str, object]],
) -> SourceSpec | None:
    if mode == "reviewed_dataset":
        return SourceSpec(
            mode=mode,
            label="reviewed sentence-veto examples",
            source_class="oracle",
            payload=None,
            path="dataset cases",
            description="internal reviewed examples; upper bound only",
        )
    if mode == "empty_batch":
        return SourceSpec(
            mode=mode,
            label="empty evidence baseline",
            source_class="baseline",
            payload=_empty_evidence_payload(),
            path="synthetic",
            description="all source evidence removed",
        )
    if mode == "reverse_aux":
        payload = _optional_source_payload(mode, reverse_aux_path, skipped)
        if payload is None:
            return None
        return SourceSpec(
            mode=mode,
            label="reverse aux example frames",
            source_class="candidate_source",
            payload=payload,
            path=str(reverse_aux_path),
            description="cheap reverse-auxiliary source evidence",
        )
    if mode.startswith("generated_") or mode == "generated_composite":
        payload = _optional_source_payload(mode, generated_composite_path, skipped)
        if payload is None:
            return None
        return SourceSpec(
            mode=mode,
            label=mode.replace("_", " "),
            source_class="candidate_source",
            payload=_apply_generated_source_mode(payload, mode),
            path=str(generated_composite_path),
            description="current generated composite evidence variant",
        )
    skipped.append({"source_mode": mode, "reason": "unsupported_source_mode", "path": ""})
    return None


def _optional_source_payload(
    mode: str,
    path: Path,
    skipped: list[dict[str, object]],
) -> Mapping[str, object] | None:
    if not path.exists():
        skipped.append(
            {
                "source_mode": mode,
                "reason": "missing_source_json",
                "path": str(path),
            }
        )
        return None
    return _load_json(path)


def _apply_generated_source_mode(
    payload: Mapping[str, object],
    mode: str,
) -> dict[str, object]:
    if mode == "generated_composite":
        return dict(payload)
    if mode == "generated_active_only":
        return _filter_payload_relations(payload, mode, allowed=ACTIVE_RELATION_TYPES)
    if mode == "generated_no_phrase":
        return _filter_payload_relations(payload, mode, blocked=PHRASE_RELATION_TYPES)
    if mode == "generated_no_shadow":
        return _filter_payload_relations(payload, mode, blocked=SHADOW_RELATION_TYPES)
    return dict(payload)


def _filter_payload_relations(
    payload: Mapping[str, object],
    mode: str,
    *,
    allowed: frozenset[str] | None = None,
    blocked: frozenset[str] | None = None,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for row in payload.get("rows", ()):
        if not isinstance(row, Mapping):
            continue
        relation_type = str(row.get("relation_type") or "").strip()
        if allowed is not None and relation_type not in allowed:
            continue
        if blocked is not None and relation_type in blocked:
            continue
        rows.append(dict(row))
    filtered = dict(payload)
    filtered["source_id"] = f"{str(payload.get('source_id') or 'evidence').strip()}_{mode}"
    filtered["batch_id"] = f"{str(payload.get('batch_id') or 'batch').strip()}:{mode}"
    filtered["rows"] = rows
    filtered["row_count"] = len(rows)
    return filtered


def _empty_evidence_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "source_id": "empty_evidence_baseline",
        "batch_id": "empty",
        "rows": [],
        "row_count": 0,
    }


def _normalize_string_list(values: Sequence[str] | str) -> list[str]:
    if isinstance(values, str):
        raw_values = values.split(",")
    else:
        raw_values = values
    return [str(value or "").strip() for value in raw_values if str(value or "").strip()]


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}.")
    return payload
