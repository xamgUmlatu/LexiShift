#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Mapping, Sequence
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from srs_admission_lab_source_support import (  # noqa: E402
    path_if_exists,
    prepare_lab_frequency_db,
    resolve_kaikki_forward_db,
)

DEFAULT_PAIR = "en-es"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_SET_TOP_N = 5000
DEFAULT_ANIMALS_PLANTS_TOPIC_OVERLAY_SOURCE_PATH = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_animals_plants_topic_overlay_en_es_spalex_10k_latest.json"
)
DEFAULT_FOOD_COOKING_TOPIC_OVERLAY_SOURCE_PATH = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_food_cooking_topic_overlay_en_es_spalex_10k_latest.json"
)
DEFAULT_TOPIC_TAXONOMY_PATH = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_topic_preference_taxonomy_en_es.json"
)
DEFAULT_TOPIC_OVERLAY_SOURCE_PATHS = (
    DEFAULT_ANIMALS_PLANTS_TOPIC_OVERLAY_SOURCE_PATH,
    DEFAULT_FOOD_COOKING_TOPIC_OVERLAY_SOURCE_PATH,
)
DEFAULT_ZIPF_BRIDGE_PATH = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_veto_srs_zipf_bridge_en_es_spalex_10k_full_rulegen_latest.json"
)
SUPPORTED_SAMPLING_MODES = frozenset({"ranked", "weighted_without_replacement"})


@dataclass(frozen=True)
class LabConfig:
    pair: str = DEFAULT_PAIR
    set_top_n: int = DEFAULT_SET_TOP_N
    initial_active_count: int = 120
    preview_count: int = 10
    preview_sampling_mode: str = "ranked"
    preview_seed: int | None = 424242
    frequency_db: Path | None = None
    overlay_source_path: Path | None = None
    overlay_source_paths: Sequence[Path] = field(
        default_factory=lambda: DEFAULT_TOPIC_OVERLAY_SOURCE_PATHS
    )
    topic_taxonomy_path: Path | None = DEFAULT_TOPIC_TAXONOMY_PATH
    augment_with_zipf_bridge: bool = True
    zipf_bridge_path: Path | None = DEFAULT_ZIPF_BRIDGE_PATH
    kaikki_forward_db: Path | None = None


HTML_PATH = Path(__file__).with_name("srs_admission_lab_static.html")


def load_lab_html() -> str:
    return HTML_PATH.read_text(encoding="utf-8")


def safe_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed == parsed else None


def safe_int(value: object) -> int | None:
    parsed = safe_float(value)
    if parsed is None:
        return None
    return int(parsed)


def clamp_float(value: object, *, default: float, minimum: float, maximum: float) -> float:
    parsed = safe_float(value)
    if parsed is None:
        parsed = default
    return min(maximum, max(minimum, parsed))


def clamp_int(value: object, *, default: int, minimum: int, maximum: int) -> int:
    parsed = safe_int(value)
    if parsed is None:
        parsed = default
    return min(maximum, max(minimum, parsed))


def string_list(value: object) -> list[str]:
    if isinstance(value, str):
        candidates = value.split(",")
    elif isinstance(value, list | tuple | set):
        candidates = value
    else:
        candidates = ()
    return [str(item).strip() for item in candidates if str(item).strip()]


def weight_map(value: object) -> dict[str, float]:
    if not isinstance(value, Mapping):
        return {}
    normalized: dict[str, float] = {}
    for key, raw_weight in value.items():
        topic = str(key).strip()
        weight = safe_float(raw_weight)
        if not topic or weight is None:
            continue
        normalized[topic] = min(1.0, max(0.0, weight))
    return {key: value for key, value in normalized.items() if value > 0.0}


def load_topic_options(path: Path | None = DEFAULT_TOPIC_TAXONOMY_PATH) -> list[dict[str, object]]:
    source = path_if_exists(path)
    if source is None:
        return []
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(payload, Mapping):
        return []

    aliases_by_family: dict[str, set[str]] = {}
    for row in payload.get("source_label_mappings", ()):
        if not isinstance(row, Mapping):
            continue
        family_id = str(row.get("target_family") or "").strip()
        label = str(row.get("source_label") or "").strip()
        if not family_id or not label:
            continue
        aliases_by_family.setdefault(family_id, set()).add(label)

    options: list[dict[str, object]] = []
    for family in payload.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        family_id = str(family.get("id") or "").strip()
        if not family_id:
            continue
        options.append(
            {
                "id": family_id,
                "display_name": str(family.get("display_name") or family_id),
                "axis": str(family.get("axis") or "topic"),
                "readiness_state": str(family.get("readiness_state") or "unknown"),
                "product_priority": str(family.get("product_priority") or ""),
                "pair_scope": str(family.get("pair_scope") or ""),
                "runtime_aliases": sorted(aliases_by_family.get(family_id, set())),
            }
        )
    return options


def truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def build_profile_context(payload: Mapping[str, object]) -> dict[str, object]:
    raw_profile_context = payload.get("profile_context")
    if truthy(payload.get("use_profile_context")) and isinstance(raw_profile_context, Mapping):
        return dict(raw_profile_context)

    profile_context: dict[str, object] = {}
    interests = string_list(payload.get("interests"))
    topic_weights = weight_map(payload.get("topic_weights"))
    proficiency_estimate = safe_float(payload.get("proficiency_estimate"))
    challenge_target = safe_float(payload.get("challenge_target"))
    challenge_spread = safe_float(payload.get("challenge_spread"))

    if interests:
        profile_context["interests"] = interests
    if topic_weights:
        profile_context["topic_weights"] = topic_weights
    if proficiency_estimate is not None:
        profile_context["proficiency"] = {
            "estimated_value": min(1.0, max(0.0, proficiency_estimate))
        }
    if challenge_target is not None or challenge_spread is not None:
        profile_context["difficulty_preferences"] = {
            "target_challenge_center": clamp_float(
                challenge_target,
                default=0.45,
                minimum=0.0,
                maximum=1.0,
            ),
            "target_challenge_spread": clamp_float(
                challenge_spread,
                default=0.2,
                minimum=0.01,
                maximum=1.0,
            ),
        }
    return profile_context


def resolve_frequency_db(pair: str, frequency_db: Path | None) -> Path:
    if frequency_db is not None:
        return frequency_db.expanduser()

    from lexishift_core.helper.pair_resources import resolve_pair_resources
    from lexishift_core.helper.paths import build_helper_paths

    paths = build_helper_paths()
    _jmdict_path, _translation_dict_path, resolved_frequency_db = resolve_pair_resources(
        paths,
        pair=pair,
        jmdict_path=None,
        translation_dict_path=None,
        set_source_db=None,
    )
    if resolved_frequency_db is None:
        raise ValueError(f"Could not resolve a default frequency DB for {pair}.")
    return resolved_frequency_db


def copy_overlay_fixture(srs_dir: Path, overlay_source_path: Path | None) -> Path | None:
    if overlay_source_path is None:
        return None
    source = overlay_source_path.expanduser()
    if not source.exists():
        raise FileNotFoundError(source)

    from lexishift_core.srs.topic_overlay import ANIMALS_PLANTS_OVERLAY_FILENAME

    target = srs_dir / "topic_overlays" / ANIMALS_PLANTS_OVERLAY_FILENAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return target


def display_topic_source(source: object) -> str:
    value = str(source or "").strip()
    for prefix in ("topic_hint:", "lexical:"):
        if value.startswith(prefix):
            return value[len(prefix) :]
    return value


def configured_overlay_source_paths(config: LabConfig) -> list[Path]:
    if config.overlay_source_path is not None:
        return [config.overlay_source_path]
    return [Path(path) for path in config.overlay_source_paths if path is not None]


def prepare_overlay_source_for_lab(
    *,
    work_dir: Path,
    pair: str,
    overlay_source_paths: Sequence[Path],
) -> Path | None:
    existing_paths = [
        path for path in (path_if_exists(path) for path in overlay_source_paths) if path
    ]
    if not existing_paths:
        return None
    if len(existing_paths) == 1:
        return existing_paths[0]

    rows: list[Mapping[str, object]] = []
    input_ids: list[str] = []
    input_paths: list[str] = []
    policies: list[Mapping[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    for path in existing_paths:
        payload = _load_overlay_payload(path)
        if payload is None:
            continue
        input_ids.append(str(payload.get("overlay_id") or path.stem))
        input_paths.append(str(path))
        policy = payload.get("overlay_policy")
        if isinstance(policy, Mapping):
            policies.append(policy)
        for row in payload.get("rows", ()):
            if not isinstance(row, Mapping):
                continue
            if str(row.get("language_pair") or "").strip() != pair:
                continue
            lemma = str(row.get("lemma") or "").strip()
            topic = str(row.get("topic") or "").strip()
            if not lemma or not topic:
                continue
            key = (lemma, topic, str(row.get("review_id") or ""))
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)

    if not rows:
        return None
    rows.sort(
        key=lambda row: (
            str(row.get("topic") or ""),
            str(row.get("lemma") or ""),
            str(row.get("review_id") or ""),
        )
    )
    merged = {
        "schema_version": 1,
        "status": "ok",
        "decision": "srs_admission_lab_merged_topic_overlay_ready",
        "overlay_id": "srs_admission_lab_merged_topic_overlay_en_es_latest",
        "overlay_policy": {
            "promotion_state": "poc_candidate_not_product_overlay",
            "runtime_policy_change": "none",
            "input_overlay_ids": input_ids,
            "input_overlay_policies": policies,
        },
        "inputs": {"overlay_source_paths": input_paths},
        "summary": {
            "row_count": len(rows),
            "topics": sorted({str(row.get("topic") or "") for row in rows if row.get("topic")}),
        },
        "rows": rows,
    }
    output = work_dir / "srs-admission-lab-merged-topic-overlay.json"
    output.write_text(json.dumps(merged, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return output


def _load_overlay_payload(path: Path) -> Mapping[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping) or str(payload.get("status") or "").strip() != "ok":
        return None
    return payload


def rounded(value: object, digits: int = 3) -> float | None:
    parsed = safe_float(value)
    if parsed is None:
        return None
    return round(parsed, digits)


def simplify_admitted_word(entry: Mapping[str, object]) -> dict[str, object]:
    signals = entry.get("signals") if isinstance(entry.get("signals"), Mapping) else {}
    source = signals.get("topic_affinity_source") if isinstance(signals, Mapping) else None
    return {
        "lemma": str(entry.get("lemma") or ""),
        "pos_bucket": entry.get("pos_bucket"),
        "pos_raw": entry.get("pos_raw"),
        "pos_canonical": entry.get("pos_canonical"),
        "pos_source_profile": entry.get("pos_source_profile"),
        "pos_matched_rule": entry.get("pos_matched_rule"),
        "pos_weight": rounded(entry.get("pos_weight")),
        "base_rank": entry.get("base_rank"),
        "reranked_rank": entry.get("reranked_rank"),
        "rank_delta": entry.get("rank_delta"),
        "profile_score": rounded(entry.get("profile_score")),
        "penalties": list(entry.get("penalties") or [])
        if isinstance(entry.get("penalties"), list | tuple)
        else [],
        "admission_weight": rounded(entry.get("admission_weight")),
        "difficulty_estimate": rounded(signals.get("difficulty_estimate"))
        if isinstance(signals, Mapping)
        else None,
        "proficiency_fit": rounded(signals.get("proficiency_fit"))
        if isinstance(signals, Mapping)
        else None,
        "challenge_fit": rounded(signals.get("challenge_fit"))
        if isinstance(signals, Mapping)
        else None,
        "readiness_multiplier": rounded(signals.get("readiness_multiplier"))
        if isinstance(signals, Mapping)
        else None,
        "readiness_lower_bound": rounded(signals.get("readiness_lower_bound"))
        if isinstance(signals, Mapping)
        else None,
        "readiness_upper_bound": rounded(signals.get("readiness_upper_bound"))
        if isinstance(signals, Mapping)
        else None,
        "readiness_topic_strength": rounded(signals.get("readiness_topic_strength"))
        if isinstance(signals, Mapping)
        else None,
        "readiness_too_easy_gap": rounded(signals.get("readiness_too_easy_gap"))
        if isinstance(signals, Mapping)
        else None,
        "readiness_too_hard_gap": rounded(signals.get("readiness_too_hard_gap"))
        if isinstance(signals, Mapping)
        else None,
        "topic_affinity_source": source,
        "topic_affinity_source_display": display_topic_source(source),
        "topic_affinity": rounded(signals.get("topic_affinity"))
        if isinstance(signals, Mapping)
        else None,
        "scarcity_bonus": rounded(signals.get("scarcity_bonus"))
        if isinstance(signals, Mapping)
        else None,
        "weighted_components": dict(entry.get("weighted_components") or {})
        if isinstance(entry.get("weighted_components"), Mapping)
        else {},
        "explanation": str(entry.get("explanation") or ""),
    }


def summarize_preview(payload: Mapping[str, object]) -> dict[str, object]:
    preview = payload.get("preview") if isinstance(payload.get("preview"), Mapping) else {}
    plan = payload.get("plan") if isinstance(payload.get("plan"), Mapping) else {}
    profile_bootstrap = (
        preview.get("profile_bootstrap")
        if isinstance(preview.get("profile_bootstrap"), Mapping)
        else {}
    )
    admitted_words = [
        simplify_admitted_word(entry)
        for entry in preview.get("admitted_words", ())
        if isinstance(entry, Mapping)
    ]
    topic_movers = [
        entry for entry in admitted_words if str(entry.get("topic_affinity_source") or "").strip()
    ]
    selected_count = len(admitted_words)
    return {
        "plan": {
            key: plan.get(key)
            for key in ("strategy_requested", "strategy_effective", "execution_mode", "can_execute")
        },
        "preview_counts": {
            key: preview.get(key)
            for key in (
                "selected_count",
                "selected_unique_count",
                "admitted_count",
                "sample_count_requested",
                "sample_count_effective",
                "sampling_mode",
            )
        },
        "top_lemmas": [str(entry.get("lemma") or "") for entry in admitted_words],
        "admitted_words": admitted_words,
        "topic_mover_count": len(topic_movers),
        "topic_mover_share": rounded(len(topic_movers) / selected_count if selected_count else 0.0),
        "effective_profile_context": dict(profile_bootstrap.get("profile_context") or {}),
        "active_topic_support": profile_bootstrap.get("active_topic_support") or {},
        "topic_depth_by_level": profile_bootstrap.get("topic_depth_by_level") or {},
        "profile_topic_overlay": profile_bootstrap.get("profile_topic_overlay") or {},
    }


def run_preview_sample(
    *,
    paths: object,
    pair: str,
    frequency_db: Path,
    profile_context: Mapping[str, object],
    set_top_n: int,
    initial_active_count: int,
    preview_count: int,
    preview_sampling_mode: str,
    preview_seed: int | None,
    trigger: str,
) -> dict[str, object]:
    from lexishift_core.helper.engine import SetAdmissionPreviewJobConfig, preview_srs_admission

    payload = preview_srs_admission(
        paths,
        config=SetAdmissionPreviewJobConfig(
            pair=pair,
            set_source_db=frequency_db,
            strategy="profile_bootstrap",
            objective="bootstrap",
            set_top_n=set_top_n,
            initial_active_count=initial_active_count,
            preview_count=preview_count,
            preview_sampling_mode=preview_sampling_mode,
            preview_seed=preview_seed,
            profile_context=profile_context,
            trigger=trigger,
        ),
    )
    return summarize_preview(payload)


def compare_samples(
    *,
    neutral_words: list[Mapping[str, object]],
    preference_words: list[Mapping[str, object]],
) -> dict[str, object]:
    neutral_positions = {
        str(entry.get("lemma") or ""): index + 1
        for index, entry in enumerate(neutral_words)
        if str(entry.get("lemma") or "").strip()
    }
    changed_or_new: list[dict[str, object]] = []
    moved_up: list[dict[str, object]] = []
    new_to_sample: list[dict[str, object]] = []
    for index, entry in enumerate(preference_words):
        lemma = str(entry.get("lemma") or "").strip()
        if not lemma:
            continue
        preference_position = index + 1
        neutral_position = neutral_positions.get(lemma)
        comparison = {
            "lemma": lemma,
            "preference_position": preference_position,
            "neutral_position": neutral_position,
        }
        if neutral_position is None:
            new_to_sample.append(comparison)
            changed_or_new.append(comparison)
        elif preference_position < neutral_position:
            moved_up.append(comparison)
            changed_or_new.append(comparison)
    return {
        "changed_or_new": changed_or_new,
        "moved_up": moved_up,
        "new_to_sample": new_to_sample,
    }


def build_lab_response(
    payload: Mapping[str, object],
    *,
    config: LabConfig | None = None,
) -> dict[str, object]:
    resolved_config = config or LabConfig()
    pair = str(payload.get("pair") or resolved_config.pair).strip() or resolved_config.pair
    set_top_n = clamp_int(
        payload.get("set_top_n"),
        default=resolved_config.set_top_n,
        minimum=1,
        maximum=50000,
    )
    initial_active_count = clamp_int(
        payload.get("initial_active_count"),
        default=resolved_config.initial_active_count,
        minimum=1,
        maximum=10000,
    )
    preview_count = clamp_int(
        payload.get("preview_count"),
        default=resolved_config.preview_count,
        minimum=1,
        maximum=20,
    )
    sampling_mode = str(
        payload.get("preview_sampling_mode") or resolved_config.preview_sampling_mode
    ).strip()
    if sampling_mode not in SUPPORTED_SAMPLING_MODES:
        sampling_mode = resolved_config.preview_sampling_mode
    preview_seed = safe_int(payload.get("preview_seed"))
    if preview_seed is None:
        preview_seed = resolved_config.preview_seed
    profile_context = build_profile_context(payload)
    frequency_db = resolve_frequency_db(pair, resolved_config.frequency_db)
    if not frequency_db.exists():
        raise FileNotFoundError(frequency_db)
    configured_overlay_paths = configured_overlay_source_paths(resolved_config)
    kaikki_forward_db = resolve_kaikki_forward_db(pair, resolved_config.kaikki_forward_db)

    with tempfile.TemporaryDirectory(prefix="lexishift-srs-admission-lab-") as tmp:
        from lexishift_core.helper.paths import build_helper_paths

        tmp_root = Path(tmp)
        paths = build_helper_paths(tmp_root)
        overlay_source_path = prepare_overlay_source_for_lab(
            work_dir=tmp_root,
            pair=pair,
            overlay_source_paths=configured_overlay_paths,
        )
        preview_frequency_db, source_augmentation = prepare_lab_frequency_db(
            base_frequency_db=frequency_db,
            pair=pair,
            work_dir=tmp_root,
            overlay_source_path=overlay_source_path,
            augment_with_zipf_bridge=resolved_config.augment_with_zipf_bridge,
            zipf_bridge_path=resolved_config.zipf_bridge_path,
            kaikki_forward_db=kaikki_forward_db,
        )
        copied_overlay_path = copy_overlay_fixture(
            paths.srs_dir,
            overlay_source_path,
        )
        neutral = run_preview_sample(
            paths=paths,
            pair=pair,
            frequency_db=preview_frequency_db,
            profile_context={},
            set_top_n=set_top_n,
            initial_active_count=initial_active_count,
            preview_count=preview_count,
            preview_sampling_mode=sampling_mode,
            preview_seed=preview_seed,
            trigger="dev_admission_lab_neutral",
        )
        preference = run_preview_sample(
            paths=paths,
            pair=pair,
            frequency_db=preview_frequency_db,
            profile_context=profile_context,
            set_top_n=set_top_n,
            initial_active_count=initial_active_count,
            preview_count=preview_count,
            preview_sampling_mode=sampling_mode,
            preview_seed=preview_seed,
            trigger="dev_admission_lab_preference",
        )

    return {
        "ok": True,
        "pair": pair,
        "parameters": {
            "set_top_n": set_top_n,
            "initial_active_count": initial_active_count,
            "preview_count": preview_count,
            "preview_sampling_mode": sampling_mode,
            "preview_seed": preview_seed,
        },
        "profile_context": profile_context,
        "source": {
            "frequency_db": str(frequency_db),
            "preview_frequency_db": str(preview_frequency_db),
            "source_augmentation": source_augmentation,
            "overlay_source_path": str(overlay_source_path) if overlay_source_path else None,
            "configured_overlay_source_paths": [
                str(path) for path in configured_overlay_paths if path_if_exists(path)
            ],
            "copied_overlay_path": str(copied_overlay_path) if copied_overlay_path else None,
            "zipf_bridge_path": str(resolved_config.zipf_bridge_path)
            if resolved_config.zipf_bridge_path
            else None,
            "kaikki_forward_db": str(kaikki_forward_db) if kaikki_forward_db else None,
        },
        "neutral": neutral,
        "preference": preference,
        "comparison": compare_samples(
            neutral_words=list(neutral.get("admitted_words") or []),
            preference_words=list(preference.get("admitted_words") or []),
        ),
    }


def response_json(handler: BaseHTTPRequestHandler, payload: object, *, status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("content-type", "application/json; charset=utf-8")
    handler.send_header("content-length", str(len(body)))
    handler.send_header("cache-control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def response_html(handler: BaseHTTPRequestHandler, body_text: str) -> None:
    body = body_text.encode("utf-8")
    handler.send_response(HTTPStatus.OK)
    handler.send_header("content-type", "text/html; charset=utf-8")
    handler.send_header("content-length", str(len(body)))
    handler.send_header("cache-control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def make_handler(config: LabConfig) -> type[BaseHTTPRequestHandler]:
    class SrsAdmissionLabHandler(BaseHTTPRequestHandler):
        server_version = "LexiShiftSrsAdmissionLab/0.1"

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            sys.stderr.write("[srs-admission-lab] " + format % args + "\n")

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path in {"", "/"}:
                response_html(self, load_lab_html())
                return
            if path == "/api/config":
                response_json(
                    self,
                    {
                        "ok": True,
                        "defaults": {
                            "pair": config.pair,
                            "set_top_n": config.set_top_n,
                            "initial_active_count": config.initial_active_count,
                            "preview_count": config.preview_count,
                            "preview_sampling_mode": config.preview_sampling_mode,
                            "preview_seed": config.preview_seed,
                        },
                        "topics": load_topic_options(config.topic_taxonomy_path),
                    },
                )
                return
            response_json(self, {"ok": False, "error": "Not found."}, status=404)

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            if path != "/api/preview":
                response_json(self, {"ok": False, "error": "Not found."}, status=404)
                return
            try:
                length = int(self.headers.get("content-length", "0"))
            except ValueError:
                length = 0
            if length > 512 * 1024:
                response_json(self, {"ok": False, "error": "Request too large."}, status=413)
                return
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            except json.JSONDecodeError as exc:
                response_json(self, {"ok": False, "error": f"Invalid JSON: {exc}"}, status=400)
                return
            if not isinstance(payload, Mapping):
                response_json(
                    self, {"ok": False, "error": "Request must be a JSON object."}, status=400
                )
                return
            try:
                response_json(self, build_lab_response(payload, config=config))
            except Exception as exc:  # noqa: BLE001
                response_json(self, {"ok": False, "error": str(exc)}, status=500)

    return SrsAdmissionLabHandler


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a local read-only SRS admission preference testing lab."
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--pair", default=DEFAULT_PAIR)
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument("--overlay-source-path", type=Path)
    parser.add_argument("--topic-taxonomy-path", type=Path, default=DEFAULT_TOPIC_TAXONOMY_PATH)
    parser.add_argument("--set-top-n", type=int, default=DEFAULT_SET_TOP_N)
    parser.add_argument("--initial-active-count", type=int, default=120)
    parser.add_argument("--preview-count", type=int, default=10)
    parser.add_argument(
        "--preview-sampling-mode",
        choices=tuple(sorted(SUPPORTED_SAMPLING_MODES)),
        default="ranked",
    )
    parser.add_argument("--preview-seed", type=int, default=424242)
    parser.add_argument(
        "--augment-with-zipf-bridge",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Build a temporary dev-only frequency DB from the local Zipf bridge artifact.",
    )
    parser.add_argument("--zipf-bridge-path", type=Path, default=DEFAULT_ZIPF_BRIDGE_PATH)
    parser.add_argument("--kaikki-forward-db", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = LabConfig(
        pair=args.pair,
        set_top_n=args.set_top_n,
        initial_active_count=args.initial_active_count,
        preview_count=args.preview_count,
        preview_sampling_mode=args.preview_sampling_mode,
        preview_seed=args.preview_seed,
        frequency_db=args.frequency_db,
        overlay_source_path=args.overlay_source_path,
        topic_taxonomy_path=args.topic_taxonomy_path,
        augment_with_zipf_bridge=args.augment_with_zipf_bridge,
        zipf_bridge_path=args.zipf_bridge_path,
        kaikki_forward_db=args.kaikki_forward_db,
    )
    server = ThreadingHTTPServer((args.host, args.port), make_handler(config))
    url = f"http://{args.host}:{args.port}"
    print(f"SRS admission lab listening on {url}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping SRS admission lab.", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
