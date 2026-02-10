from __future__ import annotations

from typing import Callable

from lexishift_core.helper.paths import HelperPaths
from lexishift_core.srs import save_srs_store
from lexishift_core.srs.signal_queue import (
    SIGNAL_EXPOSURE,
    SIGNAL_FEEDBACK,
    SrsSignalEvent,
    append_signal_event,
)
from lexishift_core.srs.source import SOURCE_EXTENSION
from lexishift_core.srs.store_ops import record_exposure, record_feedback


def apply_feedback(
    paths: HelperPaths,
    *,
    pair: str,
    lemma: str,
    rating: str,
    profile_id: str = "default",
    source_type: str = SOURCE_EXTENSION,
    resolve_profile_id_fn: Callable[..., str],
    ensure_store_fn: Callable[..., object],
) -> None:
    normalized_profile_id = resolve_profile_id_fn(paths, profile_id=profile_id)
    store = ensure_store_fn(paths, profile_id=normalized_profile_id)
    normalized_pair = str(pair or "").strip()
    normalized_lemma = str(lemma or "").strip()
    normalized_source_type = str(source_type or SOURCE_EXTENSION).strip() or SOURCE_EXTENSION
    store = record_feedback(
        store,
        language_pair=normalized_pair,
        lemma=normalized_lemma,
        rating=rating,
        create_if_missing=True,
        source_type=normalized_source_type,
    )
    save_srs_store(store, paths.srs_store_path_for(normalized_profile_id))
    if normalized_pair and normalized_lemma:
        append_signal_event(
            paths.srs_signal_queue_path_for(normalized_profile_id),
            SrsSignalEvent(
                event_type=SIGNAL_FEEDBACK,
                pair=normalized_pair,
                lemma=normalized_lemma,
                source_type=normalized_source_type,
                rating=rating,
            ),
        )


def apply_exposure(
    paths: HelperPaths,
    *,
    pair: str,
    lemma: str,
    profile_id: str = "default",
    source_type: str = SOURCE_EXTENSION,
    resolve_profile_id_fn: Callable[..., str],
    ensure_store_fn: Callable[..., object],
) -> None:
    normalized_profile_id = resolve_profile_id_fn(paths, profile_id=profile_id)
    store = ensure_store_fn(paths, profile_id=normalized_profile_id)
    normalized_pair = str(pair or "").strip()
    normalized_lemma = str(lemma or "").strip()
    normalized_source_type = str(source_type or SOURCE_EXTENSION).strip() or SOURCE_EXTENSION
    store = record_exposure(
        store,
        language_pair=normalized_pair,
        lemma=normalized_lemma,
        create_if_missing=True,
        source_type=normalized_source_type,
    )
    save_srs_store(store, paths.srs_store_path_for(normalized_profile_id))
    if normalized_pair and normalized_lemma:
        append_signal_event(
            paths.srs_signal_queue_path_for(normalized_profile_id),
            SrsSignalEvent(
                event_type=SIGNAL_EXPOSURE,
                pair=normalized_pair,
                lemma=normalized_lemma,
                source_type=normalized_source_type,
            ),
        )

