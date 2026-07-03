from __future__ import annotations

from pathlib import Path
from typing import Mapping

from lexishift_core.srs.browsing_admission import (
    BrowsingSignalIngestPolicy,
    BrowsingSignalPacket,
    BrowsingSignalPacketEntry,
    BrowsingSignalStore,
    aggregate_target_key,
    browsing_raw_value,
    browsing_signal_value,
    ingest_browsing_signal_packet,
)
from lexishift_core.srs.time import parse_ts
from srs_browsing_admission_saved_page_admission_hygiene import build_signal_hygiene
from srs_browsing_admission_saved_page_pack_en_ja import build_signal_entries
from srs_browsing_admission_saved_page_support import (
    SavedPagePolicy,
    build_jmdict_indexes,
    collect_source_counts,
    counter_preview,
    document_summary,
    load_json_mapping,
    load_saved_documents,
    repo_path,
    resolve_pair_data_paths,
    ruby_preview,
)


SAVED_PAGE_PROFILE_ID = "saved_page_admission_pack"
SAVED_PAGE_CAPTURED_AT = "2026-07-03T00:00:00Z"


def build_saved_page_aggregate(
    *,
    manifest_json: Path,
    pair: str,
    jmdict_path: Path,
    frequency_db: Path | None,
    policy: SavedPagePolicy,
) -> dict[str, object]:
    manifest = load_json_mapping(manifest_json)
    resolved_jmdict_path, resolved_frequency_db = resolve_pair_data_paths(
        pair=pair,
        jmdict_path=jmdict_path,
        frequency_db=frequency_db,
    )
    documents = load_saved_documents(manifest)
    source_counts = collect_source_counts(documents)
    target_text = "\n".join(document.text for document in documents if document.side == "target")
    source_index, target_index, exact_pairs, jmdict_summary = build_jmdict_indexes(
        resolved_jmdict_path,
        source_terms=set(source_counts),
        target_text=target_text,
        frequency_db=resolved_frequency_db,
        policy=policy,
    )
    signals, signal_debug = build_signal_entries(
        documents=documents,
        source_counts=source_counts,
        source_index=source_index,
        target_index=target_index,
        exact_pairs=exact_pairs,
        policy=policy,
    )
    hygiene = build_signal_hygiene(signals)
    accepted_signals = [
        signal
        for signal, decision in zip(signals, hygiene["decisions"], strict=True)
        if decision["status"] in {"accepted", "suspect"}
    ]
    ingest_policy = BrowsingSignalIngestPolicy(
        max_signals_per_packet=300,
        max_count_per_signal=policy.max_count_per_signal,
        max_items_per_store=1000,
    )
    packet = BrowsingSignalPacket(
        pair=pair,
        profile_id=SAVED_PAGE_PROFILE_ID,
        captured_at=SAVED_PAGE_CAPTURED_AT,
        signals=tuple(packet_entry_from_signal(signal) for signal in accepted_signals),
    )
    ingest_result = ingest_browsing_signal_packet(
        BrowsingSignalStore(pair=pair, profile_id=SAVED_PAGE_PROFILE_ID),
        packet,
        policy=ingest_policy,
        now=parse_ts(SAVED_PAGE_CAPTURED_AT),
    )
    store = ingest_result.store
    return {
        "store": store,
        "summary": {
            "signal_count": len(signals),
            "hygiene_accepted_signal_count": int(hygiene["summary"]["accepted_signal_count"]),
            "hygiene_retained_signal_count": len(accepted_signals),
            "hygiene_rejected_signal_count": len(hygiene["rejected"]),
            "hygiene_retained_suspect_signal_count": len(hygiene["retained_suspect"]),
            "store_item_count": len(store.items),
            "source_term_count": len(source_counts),
            "target_document_count": sum(1 for document in documents if document.side == "target"),
            "source_document_count": sum(1 for document in documents if document.side == "source"),
        },
        "policy": policy.to_dict(),
        "ingest_policy": ingest_policy.__dict__,
        "ingest_result": ingest_result.to_dict(),
        "inputs": {
            "manifest_json": repo_path(manifest_json),
            "jmdict_path": str(resolved_jmdict_path),
            "frequency_db": str(resolved_frequency_db),
            "documents": [document_summary(document) for document in documents],
        },
        "jmdict": jmdict_summary,
        "extraction": {
            "source_terms": counter_preview(source_counts),
            "ruby_pair_count": sum(sum(document.ruby_pairs.values()) for document in documents),
            "top_ruby_pairs": ruby_preview(documents),
        },
        "signals": {
            "count": len(signals),
            "retained_count": len(accepted_signals),
            "rejected_count": len(hygiene["rejected"]),
            "top": signal_debug[:30],
        },
        "hygiene": hygiene,
        "store_preview": store_preview(store, ingest_policy),
    }


def packet_entry_from_signal(signal: Mapping[str, object]) -> BrowsingSignalPacketEntry:
    return BrowsingSignalPacketEntry(
        target_lemma=str(signal.get("target_lemma") or signal.get("lemma") or "").strip(),
        target_key=str(signal.get("target_key") or "").strip(),
        target_reading=str(signal.get("target_reading") or signal.get("reading") or "").strip(),
        side=str(signal.get("side") or "").strip(),
        count=safe_float(signal.get("count")) or 1.0,
        source_mapping_confidence=safe_float(signal.get("source_mapping_confidence")) or 1.0,
        reading_confidence=safe_float(signal.get("reading_confidence")) or 1.0,
        observation_source=str(signal.get("observation_source") or "").strip(),
    )


def store_preview(
    store: BrowsingSignalStore,
    policy: BrowsingSignalIngestPolicy,
    *,
    limit: int = 30,
) -> list[dict[str, object]]:
    rows = []
    for aggregate in store.items.values():
        rows.append(
            {
                "target_key": aggregate_target_key(aggregate),
                "target_lemma": aggregate.target_lemma,
                "target_reading": aggregate.target_reading,
                "source_hit_count": round(float(aggregate.source_hit_count), 6),
                "target_hit_count": round(float(aggregate.target_hit_count), 6),
                "replacement_exposure_count": round(float(aggregate.replacement_exposure_count), 6),
                "source_mapping_confidence": round(float(aggregate.source_mapping_confidence), 6),
                "reading_confidence": round(float(aggregate.reading_confidence), 6),
                "raw_value": round(browsing_raw_value(aggregate, policy=policy), 6),
                "signal_value": round(browsing_signal_value(aggregate, policy=policy), 6),
                "observation_sources": list(aggregate.observation_sources),
            }
        )
    rows.sort(
        key=lambda row: (
            -(safe_float(row.get("raw_value")) or 0.0),
            str(row.get("target_key") or ""),
        )
    )
    return rows[:limit]


def safe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed
