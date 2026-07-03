from __future__ import annotations

from datetime import datetime
from typing import Callable, Mapping, Optional, Sequence

from lexishift_core.helper.paths import HelperPaths
from lexishift_core.srs.browsing_admission import (
    BrowsingSignalIngestPolicy,
    BrowsingSignalPacket,
    BrowsingSignalPacketEntry,
    BrowsingSignalStore,
    aggregate_target_key,
    browsing_context_count,
    browsing_evidence_value,
    browsing_raw_value,
    browsing_signal_value,
    ingest_browsing_signal_packet,
    load_browsing_signal_store,
    maintain_browsing_signal_store,
    save_browsing_signal_store,
)
from lexishift_core.srs.time import parse_ts


PRIVATE_BROWSER_PAYLOAD_FIELDS = frozenset(
    {
        "url",
        "page_url",
        "raw_text",
        "page_text",
        "source_text",
        "context_text",
        "html",
    }
)


def ingest_browsing_admission_signals(
    paths: HelperPaths,
    *,
    pair: str,
    signals: Sequence[Mapping[str, object] | object],
    profile_id: str = "default",
    captured_at: str | None = None,
    opt_in: bool = False,
    policy: Optional[BrowsingSignalIngestPolicy] = None,
    now: Optional[datetime] = None,
    resolve_profile_id_fn: Callable[..., str],
) -> dict[str, object]:
    normalized_pair = str(pair or "").strip()
    if not normalized_pair:
        raise ValueError("Browsing admission ingest requires a language pair.")
    normalized_profile_id = resolve_profile_id_fn(paths, profile_id=profile_id)
    store_path = paths.srs_browsing_signal_store_path_for(normalized_profile_id, normalized_pair)
    policy = policy or BrowsingSignalIngestPolicy()

    if not opt_in:
        maintained_store = None
        if store_path.exists():
            maintained_store = maintain_browsing_signal_store(
                load_browsing_signal_store(store_path),
                policy=policy,
                now=now or parse_ts(captured_at),
            )
            if maintained_store.pair:
                save_browsing_signal_store(maintained_store, store_path)
        return {
            "status": "skipped",
            "reason": "browsing_admission_not_opted_in",
            "pair": normalized_pair,
            "profile_id": normalized_profile_id,
            "runtime_srs_mutation": False,
            "privacy": _privacy_payload(private_field_count=0),
            "aggregate_store": _summarize_store(
                maintained_store,
                policy=policy,
            )
            if maintained_store is not None
            else _empty_store_summary(normalized_pair, normalized_profile_id),
        }

    parsed_signals, private_field_count = _parse_signal_entries(signals)
    existing_store = load_browsing_signal_store(store_path)
    if (
        not existing_store.pair
        or existing_store.pair != normalized_pair
        or existing_store.profile_id != normalized_profile_id
    ):
        existing_store = BrowsingSignalStore(pair=normalized_pair, profile_id=normalized_profile_id)
    packet = BrowsingSignalPacket(
        pair=normalized_pair,
        profile_id=normalized_profile_id,
        signals=tuple(parsed_signals),
        captured_at=str(captured_at or "").strip() or None,
    )
    result = ingest_browsing_signal_packet(
        existing_store,
        packet,
        policy=policy,
        now=now or parse_ts(packet.captured_at),
    )
    save_browsing_signal_store(result.store, store_path)
    return {
        "status": "ok",
        "pair": normalized_pair,
        "profile_id": normalized_profile_id,
        "runtime_srs_mutation": False,
        "privacy": _privacy_payload(private_field_count=private_field_count),
        "policy": _policy_payload(policy),
        "ingest_result": result.to_dict(),
        "aggregate_store": _summarize_store(result.store, policy=policy),
    }


def _parse_signal_entries(
    signals: Sequence[Mapping[str, object] | object],
) -> tuple[tuple[BrowsingSignalPacketEntry, ...], int]:
    parsed: list[BrowsingSignalPacketEntry] = []
    private_field_count = 0
    for signal in signals or ():
        if not isinstance(signal, Mapping):
            parsed.append(
                BrowsingSignalPacketEntry(
                    target_lemma="",
                    side="",
                    count=0.0,
                    source_mapping_confidence=0.0,
                    reading_confidence=0.0,
                )
            )
            continue
        private_field_count += len(PRIVATE_BROWSER_PAYLOAD_FIELDS.intersection(signal.keys()))
        parsed.append(
            BrowsingSignalPacketEntry(
                target_lemma=str(
                    signal.get("target_lemma")
                    or signal.get("lemma")
                    or signal.get("targetLemma")
                    or ""
                ).strip(),
                target_key=str(signal.get("target_key") or signal.get("targetKey") or "").strip(),
                target_reading=str(
                    signal.get("target_reading")
                    or signal.get("targetReading")
                    or signal.get("reading")
                    or ""
                ).strip(),
                side=str(signal.get("side") or signal.get("signal_side") or "").strip(),
                count=_safe_float(signal.get("count"), default=1.0),
                source_mapping_confidence=_safe_float(
                    _first_present(
                        signal.get("source_mapping_confidence"),
                        signal.get("sourceMappingConfidence"),
                    ),
                    default=1.0,
                ),
                reading_confidence=_safe_float(
                    _first_present(
                        signal.get("reading_confidence"),
                        signal.get("readingConfidence"),
                    ),
                    default=1.0,
                ),
                observation_source=str(
                    signal.get("observation_source") or signal.get("observationSource") or ""
                ).strip(),
                context_key=str(
                    signal.get("context_key")
                    or signal.get("contextKey")
                    or signal.get("page_context_key")
                    or signal.get("pageContextKey")
                    or signal.get("session_key")
                    or signal.get("sessionKey")
                    or signal.get("document_id")
                    or signal.get("documentId")
                    or ""
                ).strip(),
            )
        )
    return tuple(parsed), private_field_count


def _summarize_store(
    store: BrowsingSignalStore,
    *,
    policy: BrowsingSignalIngestPolicy,
    limit: int = 10,
) -> dict[str, object]:
    rows = []
    for aggregate in store.items.values():
        rows.append(
            {
                "target_key": aggregate_target_key(aggregate),
                "target_lemma": aggregate.target_lemma,
                "target_reading": aggregate.target_reading,
                "source_hit_count": round(float(aggregate.source_hit_count), 6),
                "target_hit_count": round(float(aggregate.target_hit_count), 6),
                "replacement_exposure_count": round(
                    float(aggregate.replacement_exposure_count),
                    6,
                ),
                "source_mapping_confidence": round(
                    float(aggregate.source_mapping_confidence),
                    6,
                ),
                "reading_confidence": round(float(aggregate.reading_confidence), 6),
                "observation_sources": list(aggregate.observation_sources),
                "raw_browsing": round(browsing_raw_value(aggregate, policy=policy), 6),
                "browsing_evidence": round(browsing_evidence_value(aggregate, policy=policy), 6),
                "browsing_context_count": browsing_context_count(aggregate, policy=policy),
                "browsing_signal": round(browsing_signal_value(aggregate, policy=policy), 6),
                "last_seen_at": aggregate.last_seen_at,
            }
        )
    rows.sort(
        key=lambda row: (
            -_safe_float(row.get("browsing_signal"), default=0.0),
            str(row.get("target_key") or row.get("target_lemma") or ""),
        )
    )
    return {
        "pair": store.pair,
        "profile_id": store.profile_id,
        "updated_at": store.updated_at,
        "item_count": len(rows),
        "top_items": rows[: max(0, int(limit))],
    }


def _empty_store_summary(pair: str, profile_id: str) -> dict[str, object]:
    return {
        "pair": pair,
        "profile_id": profile_id,
        "updated_at": None,
        "item_count": 0,
        "top_items": [],
    }


def _privacy_payload(*, private_field_count: int) -> dict[str, object]:
    return {
        "raw_text_stored": False,
        "url_stored": False,
        "runtime_srs_mutation": False,
        "private_payload_fields_ignored": int(private_field_count),
    }


def _policy_payload(policy: BrowsingSignalIngestPolicy) -> dict[str, object]:
    return {
        "version": policy.version,
        "max_signals_per_packet": policy.max_signals_per_packet,
        "max_count_per_signal": policy.max_count_per_signal,
        "max_contexts_per_item": policy.max_contexts_per_item,
        "max_items_per_store": policy.max_items_per_store,
        "prune_signal_below": policy.prune_signal_below,
        "half_life_days": policy.half_life_days,
        "browsing_signal_cap": policy.browsing_signal_cap,
        "replacement_exposure_weight": policy.replacement_exposure_weight,
    }


def _safe_float(value: object, *, default: float) -> float:
    try:
        if isinstance(value, bool):
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
        return float(str(value or "").strip())
    except (TypeError, ValueError):
        return default


def _first_present(*values: object) -> object:
    for value in values:
        if value is not None and str(value).strip() != "":
            return value
    return None
