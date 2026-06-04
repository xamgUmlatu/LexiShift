from __future__ import annotations

from typing import Callable, Mapping, Optional

from lexishift_core.helper.lp_capabilities import resolve_pair_capability
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.srs.auto_refresh import (
    SrsAutoRefreshPairState,
    SrsAutoRefreshPolicy,
    auto_refresh_decision_to_dict,
    load_auto_refresh_state,
    plan_auto_refresh,
    record_auto_refresh_attempt,
    save_auto_refresh_state,
)
from lexishift_core.srs.signal_queue import load_signal_events
from lexishift_core.srs.time import now_utc


def maybe_auto_refresh_srs_set(
    paths: HelperPaths,
    *,
    config,
    resolve_profile_id_fn: Callable[..., str],
    build_refresh_config_fn: Callable[..., object],
    refresh_srs_set_fn: Callable[..., dict[str, object]],
) -> dict[str, object]:
    raw_pair = str(config.pair or "").strip()
    if not raw_pair:
        raise ValueError("Missing pair.")
    pair = resolve_pair_capability(raw_pair).pair
    profile_context = getattr(config, "profile_context", None)
    profile_id = resolve_profile_id_fn(
        paths,
        profile_id=config.profile_id,
        profile_context=profile_context if isinstance(profile_context, Mapping) else None,
    )

    state_path = paths.srs_auto_refresh_state_path_for(profile_id)
    state = load_auto_refresh_state(state_path)
    pair_state = dict(state.pairs or {}).get(pair, SrsAutoRefreshPairState())
    default_policy = SrsAutoRefreshPolicy()
    policy = SrsAutoRefreshPolicy(
        enabled=getattr(config, "auto_refresh_enabled", True) is not False,
        min_feedback_events=_coerce_int_or_default(
            getattr(config, "auto_refresh_min_feedback_events", None),
            default_policy.min_feedback_events,
        ),
        min_good_easy=_coerce_int_or_default(
            getattr(config, "auto_refresh_min_good_easy", None),
            default_policy.min_good_easy,
        ),
        repeat_min_good_easy=_coerce_int_or_default(
            getattr(config, "auto_refresh_repeat_min_good_easy", None),
            default_policy.repeat_min_good_easy,
        ),
        cooldown_minutes=_coerce_int_or_default(
            getattr(config, "auto_refresh_cooldown_minutes", None),
            default_policy.cooldown_minutes,
        ),
    )
    events = load_signal_events(paths.srs_signal_queue_path_for(profile_id))
    now = now_utc()
    decision = plan_auto_refresh(
        events,
        pair=pair,
        state=pair_state,
        policy=policy,
        now=now,
    )
    decision_payload = auto_refresh_decision_to_dict(decision)
    base_payload: dict[str, object] = {
        "pair": pair,
        "profile_id": profile_id,
        "state_path": str(state_path),
        "attempted": False,
        "applied": False,
        "auto_refresh": decision_payload,
        "refresh": None,
    }
    if not decision.eligible:
        return base_payload

    refresh_payload: Optional[dict[str, object]] = None
    refresh_error: Optional[str] = None
    applied = False
    result_reason = "refresh_not_applied"
    try:
        refresh_config = build_refresh_config_fn(
            config,
            pair=pair,
            profile_id=profile_id,
            trigger="auto_feedback_threshold",
        )
        refresh_payload = refresh_srs_set_fn(paths, config=refresh_config)
        applied = bool(refresh_payload.get("applied"))
        admission_refresh = refresh_payload.get("admission_refresh")
        if isinstance(admission_refresh, Mapping):
            result_reason = str(admission_refresh.get("reason_code") or result_reason)
        elif applied:
            result_reason = "refresh_applied"
    except Exception as exc:  # noqa: BLE001
        refresh_error = str(exc)
        result_reason = "refresh_error"

    updated_state = record_auto_refresh_attempt(
        state,
        pair=pair,
        now=now,
        applied=applied,
        reason_code=result_reason,
    )
    save_auto_refresh_state(updated_state, state_path)

    return {
        **base_payload,
        "attempted": True,
        "applied": applied,
        "auto_refresh": {
            **decision_payload,
            "attempted_at": now.isoformat(),
            "result_reason_code": result_reason,
        },
        "refresh": refresh_payload,
        "error": refresh_error,
    }


def _coerce_int_or_default(value: object, fallback: int) -> int:
    if value is None:
        return int(fallback)
    try:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        return int(str(value or "").strip())
    except (TypeError, ValueError):
        return int(fallback)
