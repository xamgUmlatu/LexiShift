from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Mapping, Sequence
import unicodedata


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_BATCH_DIR = (
    PROJECT_ROOT / "docs" / "test_outputs" / "experiments" / "semantic_llm_prompt_batches"
)
DEFAULT_BAKEOFF_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_bakeoff_latest.json"
)
DEFAULT_BAKEOFF_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_bakeoff_latest.md"
)
DEFAULT_REPLAY_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_replay_latest.json"
)
DEFAULT_REPLAY_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_replay_latest.md"
)
DEFAULT_CONFIRMATION_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_confirmation_latest.json"
)
DEFAULT_CONFIRMATION_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_confirmation_latest.md"
)
DEFAULT_CHARS_PER_TOKEN = 4.0
DEFAULT_EXPECTED_OUTPUT_TOKENS = 90
DEFAULT_MAX_OUTPUT_TOKENS = 300

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{path} must contain a JSON object.")
    return dict(payload)


def _mapping_rows(value: object, label: str) -> list[dict[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{label} must be an array of objects.")
    return [dict(row) for row in value if isinstance(row, Mapping)]


def _coerce_mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _bundle_ref(path: Path, request_id: object) -> str:
    return f"{_display_path(path)}#{str(request_id or '').strip()}"


def _slug(value: str) -> str:
    lowered = str(value or "").strip().lower()
    lowered = unicodedata.normalize("NFKD", lowered).encode("ascii", "ignore").decode("ascii")
    normalized = _SLUG_RE.sub("-", lowered).strip("-")
    return normalized or "value"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _build_batch_id(
    *,
    pair: str,
    stage: str,
    generated_at: str,
    execution_mode: str,
    run_id: str = "",
) -> str:
    timestamp = generated_at.replace("-", "").replace(":", "").replace("T", "T").replace("Z", "Z")
    run_component = str(run_id or "").strip() or timestamp
    suffix = "" if execution_mode == "live" else f":{execution_mode}"
    return f"{pair}:{stage}:{run_component}{suffix}"


def _as_path(value: object) -> Path:
    if isinstance(value, Path):
        return value
    text = str(value or "").strip()
    if not text:
        raise ValueError("expected path value")
    return Path(text)


def _resolve_default_summary_paths(stage: str, execution_mode: str) -> tuple[Path, Path]:
    if execution_mode == "replay":
        return DEFAULT_REPLAY_JSON_OUT, DEFAULT_REPLAY_MARKDOWN_OUT
    if stage == "target":
        return DEFAULT_CONFIRMATION_JSON_OUT, DEFAULT_CONFIRMATION_MARKDOWN_OUT
    return DEFAULT_BAKEOFF_JSON_OUT, DEFAULT_BAKEOFF_MARKDOWN_OUT


def _sense_hint(*, target_key: str, canonical_pos: str, note: str) -> dict[str, object]:
    hint = {
        "provider": "sentence_veto_dataset",
        "locator_kind": "sense_id",
        "target_key": target_key,
        "note": note,
    }
    if canonical_pos:
        hint["canonical_pos"] = canonical_pos
    return hint


def _merge_roles(spec_slots: Sequence[Mapping[str, object] | None]) -> list[str]:
    merged: list[str] = []
    for spec_slot in spec_slots:
        if not isinstance(spec_slot, Mapping):
            continue
        for role in _string_list(spec_slot.get("roles")):
            if role not in merged:
                merged.append(role)
    return merged or ["cue_generation"]
