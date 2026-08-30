from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time
from typing import Mapping, Sequence, cast

from lexishift_core.helper.rulegen import SetInitializationConfig, SetInitializationReport
from lexishift_core.helper.rulegen_bootstrap_selection import (
    build_weight_preview_entry,
)
from lexishift_core.srs import SrsItem, SrsStore
from lexishift_core.srs.admission_features import (
    ADMISSION_CANDIDATE_FEATURES_METADATA_KEY,
    ADMISSION_CANDIDATE_FEATURES_PRECOMPUTE_VERSION_KEY,
    canonicalize_topic_token,
    normalize_admission_profile_features,
)
from lexishift_core.srs.admission_policy import resolve_default_pos_weights
from lexishift_core.srs.candidate_identity import candidate_identity_key_from_seed
from lexishift_core.srs.profile_bootstrap import (
    FRONTIER_GAUSSIAN_HYBRID_PROFILE_BOOTSTRAP_POLICY,
    ProfileBootstrapFrontierLaneEntry,
    ProfileBootstrapScoredEntry,
    extract_profile_bootstrap_candidate_traits,
    score_seed_words_for_frontier_gaussian_hybrid_profile,
)
from lexishift_core.srs.seed import SeedSelectionConfig, SeedWord, build_seed_candidates
from lexishift_core.srs.seed_cache import seed_frontier_fingerprint
from lexishift_core.srs.seed_frontier_rows import seed_from_cache_row, seed_to_cache_row
from lexishift_core.srs.source import SOURCE_INITIAL_SET
from lexishift_core.srs.store_ops import build_item_id, upsert_item
from lexishift_core.srs.time import format_ts, now_utc
from lexishift_core.srs.topic_overlay import (
    PROFILE_TOPIC_OVERLAY_MIN_MEMBERSHIP,
    apply_profile_topic_overlay_to_seeds,
)

ADMISSION_CANDIDATE_INDEX_SCHEMA_VERSION = 1
ADMISSION_CANDIDATE_INDEX_KIND = "srs_admission_candidate_index"
ADMISSION_CANDIDATE_INDEX_MIN_POOL_FACTOR = 3
ADMISSION_CANDIDATE_INDEX_GENERAL_LIMIT_MIN = 900
ADMISSION_CANDIDATE_INDEX_TOPIC_LIMIT_MIN = 700
ADMISSION_CANDIDATE_INDEX_COMMON_LIMIT = 240


def try_preview_from_admission_candidate_index(
    store: SrsStore,
    *,
    config: SetInitializationConfig,
    profile_topic_overlay: Mapping[str, object] | None,
    profile_topic_overlay_diagnostics: Mapping[str, object] | None = None,
    index_cache_dir: Path,
) -> tuple[SrsStore, SetInitializationReport, Mapping[str, object]] | None:
    if os.environ.get("LEXISHIFT_DISABLE_SRS_ADMISSION_CANDIDATE_INDEX"):
        return None
    if config.strategy != "profile_bootstrap":
        return None
    started_at = time.perf_counter()
    seed_config = _seed_config_from_initialization_config(config)
    index_path, fingerprint = _admission_candidate_index_path(
        index_cache_dir=index_cache_dir,
        frequency_db=config.frequency_db,
        seed_config=seed_config,
    )
    build_started_at = time.perf_counter()
    build_status = _ensure_admission_candidate_index(
        index_path=index_path,
        frequency_db=config.frequency_db,
        seed_config=seed_config,
        fingerprint=fingerprint,
    )
    build_ms = round((time.perf_counter() - build_started_at) * 1000.0, 3)
    candidate_started_at = time.perf_counter()
    candidates, query_diagnostics = _load_profile_preview_candidates(
        index_path=index_path,
        profile_context=config.profile_context,
        profile_topic_overlay=profile_topic_overlay,
        initial_active_count=config.initial_active_count,
        top_n=config.top_n,
    )
    candidate_ms = round((time.perf_counter() - candidate_started_at) * 1000.0, 3)
    if len(candidates) < max(
        int(config.initial_active_count) * ADMISSION_CANDIDATE_INDEX_MIN_POOL_FACTOR,
        int(config.initial_active_count),
    ):
        return None
    overlay_started_at = time.perf_counter()
    overlay_candidates, overlay_diagnostics = apply_profile_topic_overlay_to_seeds(
        candidates,
        overlay_payload=profile_topic_overlay,
        profile_context=config.profile_context,
        pair=config.language_pair,
        diagnostics=profile_topic_overlay_diagnostics,
    )
    candidates = list(cast(Sequence[SeedWord], overlay_candidates))
    overlay_ms = round((time.perf_counter() - overlay_started_at) * 1000.0, 3)
    score_started_at = time.perf_counter()
    frontier_entries, profile_bootstrap_diagnostics = (
        score_seed_words_for_frontier_gaussian_hybrid_profile(
            candidates,
            profile_context=config.profile_context,
            selection_count=config.initial_active_count,
            preview_limit=min(len(candidates), 20),
            policy=FRONTIER_GAUSSIAN_HYBRID_PROFILE_BOOTSTRAP_POLICY,
        )
    )
    score_ms = round((time.perf_counter() - score_started_at) * 1000.0, 3)
    report_store, report = _build_index_preview_report(
        store,
        config=config,
        frontier_entries=frontier_entries,
        profile_bootstrap_diagnostics={
            **dict(profile_bootstrap_diagnostics),
            "profile_topic_overlay": dict(overlay_diagnostics or {}),
            "compiled_candidate_index": {
                "status": "used",
                "schema_version": ADMISSION_CANDIDATE_INDEX_SCHEMA_VERSION,
                "index_path": str(index_path),
                "fingerprint": fingerprint,
                "build_status": build_status,
                "query": dict(query_diagnostics),
                "timing_ms": {
                    "build_or_validate": build_ms,
                    "candidate_query": candidate_ms,
                    "topic_overlay": overlay_ms,
                    "profile_score": score_ms,
                    "total": round((time.perf_counter() - started_at) * 1000.0, 3),
                },
            },
        },
    )
    return report_store, report, report.profile_bootstrap_diagnostics


def _seed_config_from_initialization_config(
    config: SetInitializationConfig,
) -> SeedSelectionConfig:
    return SeedSelectionConfig(
        language_pair=config.language_pair,
        top_n=config.top_n,
        jmdict_path=config.jmdict_path,
        stopwords_path=config.stopwords_path,
        require_jmdict=config.require_jmdict,
        admission_pos_weights=resolve_default_pos_weights(language_pair=config.language_pair),
        source_label=config.source_label,
        pos_overlay_path=config.pos_overlay_path,
        cache_dir=config.seed_cache_dir,
    )


def _admission_candidate_index_path(
    *,
    index_cache_dir: Path,
    frequency_db: Path,
    seed_config: SeedSelectionConfig,
) -> tuple[Path, str]:
    seed_fingerprint = seed_frontier_fingerprint(frequency_db=frequency_db, config=seed_config)
    payload = {
        "kind": ADMISSION_CANDIDATE_INDEX_KIND,
        "schema_version": ADMISSION_CANDIDATE_INDEX_SCHEMA_VERSION,
        "seed_fingerprint": seed_fingerprint,
        "profile_bootstrap_policy": FRONTIER_GAUSSIAN_HYBRID_PROFILE_BOOTSTRAP_POLICY.version,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    fingerprint = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    pair_dir = index_cache_dir / str(seed_config.language_pair or "unknown").replace("/", "-")
    pair_dir.mkdir(parents=True, exist_ok=True)
    return pair_dir / f"{fingerprint}.sqlite", fingerprint


def _ensure_admission_candidate_index(
    *,
    index_path: Path,
    frequency_db: Path,
    seed_config: SeedSelectionConfig,
    fingerprint: str,
) -> str:
    if _index_is_ready(index_path, fingerprint=fingerprint):
        return "ready"
    seeds = build_seed_candidates(frequency_db=frequency_db, config=seed_config)
    _write_admission_candidate_index(
        index_path=index_path,
        seeds=seeds,
        fingerprint=fingerprint,
    )
    return "built"


def _index_is_ready(index_path: Path, *, fingerprint: str) -> bool:
    if not index_path.exists():
        return False
    try:
        with sqlite3.connect(index_path) as conn:
            row = conn.execute("SELECT value FROM metadata WHERE key = 'fingerprint'").fetchone()
            version = conn.execute(
                "SELECT value FROM metadata WHERE key = 'schema_version'"
            ).fetchone()
    except sqlite3.Error:
        return False
    return (
        row is not None
        and str(row[0]) == fingerprint
        and version is not None
        and str(version[0]) == str(ADMISSION_CANDIDATE_INDEX_SCHEMA_VERSION)
    )


def _write_admission_candidate_index(
    *,
    index_path: Path,
    seeds: Sequence[object],
    fingerprint: str,
) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "wb",
        dir=index_path.parent,
        prefix=f".{index_path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)
    try:
        with sqlite3.connect(temp_path) as conn:
            _create_schema(conn)
            conn.executemany(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                (
                    ("kind", ADMISSION_CANDIDATE_INDEX_KIND),
                    ("schema_version", str(ADMISSION_CANDIDATE_INDEX_SCHEMA_VERSION)),
                    ("fingerprint", fingerprint),
                    ("candidate_count", str(len(seeds))),
                ),
            )
            candidate_rows = []
            topic_rows = []
            for ordinal, seed in enumerate(seeds):
                traits = extract_profile_bootstrap_candidate_traits(
                    seed,
                    policy=FRONTIER_GAUSSIAN_HYBRID_PROFILE_BOOTSTRAP_POLICY,
                )
                identity_key = traits.candidate_identity_key or candidate_identity_key_from_seed(
                    seed
                )
                if not identity_key:
                    continue
                seed_row = seed_to_cache_row(seed)
                traits_payload = traits.to_dict()
                candidate_rows.append(
                    (
                        identity_key,
                        str(getattr(seed, "language_pair", "") or "").strip(),
                        traits.lemma,
                        ordinal,
                        _safe_float(getattr(seed, "core_rank", None)),
                        float(traits.difficulty_estimate),
                        float(traits.lexical_commonness),
                        float(traits.admission_suitability),
                        str(traits.candidate_state or ""),
                        str(traits.presentation_mode or ""),
                        str(traits.problem_class or ""),
                        json.dumps(seed_row, ensure_ascii=False, sort_keys=True),
                        json.dumps(traits_payload, ensure_ascii=False, sort_keys=True),
                    )
                )
                for topic in traits.topic_hints:
                    normalized_topic = canonicalize_topic_token(topic)
                    if normalized_topic:
                        topic_rows.append((normalized_topic, identity_key, 1.0, "seed_traits"))
            conn.executemany(
                """
                INSERT OR REPLACE INTO candidates(
                    identity_key, language_pair, lemma, ordinal, core_rank, difficulty,
                    lexical_commonness, admission_suitability, candidate_state,
                    presentation_mode, problem_class, seed_json, traits_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                candidate_rows,
            )
            conn.executemany(
                """
                INSERT OR IGNORE INTO candidate_topics(topic, identity_key, membership, source)
                VALUES (?, ?, ?, ?)
                """,
                topic_rows,
            )
            conn.commit()
        os.replace(temp_path, index_path)
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE metadata(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE candidates(
            identity_key TEXT PRIMARY KEY,
            language_pair TEXT NOT NULL,
            lemma TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            core_rank REAL,
            difficulty REAL NOT NULL,
            lexical_commonness REAL NOT NULL,
            admission_suitability REAL NOT NULL,
            candidate_state TEXT NOT NULL,
            presentation_mode TEXT NOT NULL,
            problem_class TEXT NOT NULL,
            seed_json TEXT NOT NULL,
            traits_json TEXT NOT NULL
        );
        CREATE TABLE candidate_topics(
            topic TEXT NOT NULL,
            identity_key TEXT NOT NULL,
            membership REAL NOT NULL,
            source TEXT NOT NULL,
            PRIMARY KEY(topic, identity_key, source)
        );
        CREATE INDEX idx_candidates_difficulty ON candidates(difficulty);
        CREATE INDEX idx_candidates_commonness ON candidates(lexical_commonness DESC);
        CREATE INDEX idx_candidates_state_difficulty ON candidates(candidate_state, difficulty);
        CREATE INDEX idx_candidates_lemma ON candidates(lemma);
        CREATE INDEX idx_candidate_topics_topic ON candidate_topics(topic);
        """
    )


def _load_profile_preview_candidates(
    *,
    index_path: Path,
    profile_context: Mapping[str, object] | None,
    profile_topic_overlay: Mapping[str, object] | None,
    initial_active_count: int,
    top_n: int | None,
) -> tuple[list[SeedWord], Mapping[str, object]]:
    normalized_context = normalize_admission_profile_features(profile_context)
    proficiency = normalized_context.proficiency_estimate
    target = max(1, int(initial_active_count))
    general_limit = max(ADMISSION_CANDIDATE_INDEX_GENERAL_LIMIT_MIN, target * 36)
    topic_limit = max(ADMISSION_CANDIDATE_INDEX_TOPIC_LIMIT_MIN, target * 28)
    if top_n is not None:
        general_limit = min(general_limit, max(target, int(top_n)))
        topic_limit = min(topic_limit, max(target, int(top_n)))
    lower, upper = _query_difficulty_window(proficiency)
    active_topics = tuple(
        topic
        for topic, weight in normalized_context.topic_weights.items()
        if str(topic or "").strip() and float(weight or 0.0) > 0.0
    )
    with sqlite3.connect(index_path) as conn:
        conn.row_factory = sqlite3.Row
        identity_keys: list[str] = []
        identity_keys.extend(
            _query_general_identity_keys(
                conn,
                proficiency=proficiency,
                lower=lower,
                upper=upper,
                limit=general_limit,
            )
        )
        identity_keys.extend(
            _query_topic_identity_keys(
                conn,
                active_topics=active_topics,
                proficiency=proficiency,
                lower=max(0.0, lower - 0.20),
                upper=min(1.0, upper + 0.12),
                limit=topic_limit,
            )
        )
        identity_keys.extend(
            _query_overlay_identity_keys(
                conn,
                overlay_payload=profile_topic_overlay,
                active_topics=active_topics,
                proficiency=proficiency,
                lower=max(0.0, lower - 0.20),
                upper=min(1.0, upper + 0.12),
                limit=topic_limit,
            )
        )
        identity_keys.extend(
            _query_common_identity_keys(
                conn,
                limit=min(ADMISSION_CANDIDATE_INDEX_COMMON_LIMIT, general_limit),
            )
        )
        ordered_identity_keys = tuple(dict.fromkeys(identity_keys))
        seeds = _load_seed_rows_for_identity_keys(conn, ordered_identity_keys)
    return seeds, {
        "candidate_count": len(seeds),
        "identity_key_count": len(ordered_identity_keys),
        "active_topics": list(active_topics),
        "proficiency_estimate": proficiency,
        "difficulty_window": [round(lower, 6), round(upper, 6)],
        "general_limit": general_limit,
        "topic_limit": topic_limit,
    }


def _query_difficulty_window(proficiency: float | None) -> tuple[float, float]:
    if proficiency is None:
        return 0.0, 1.0
    return max(0.0, float(proficiency) - 0.30), min(1.0, float(proficiency) + 0.28)


def _query_general_identity_keys(
    conn: sqlite3.Connection,
    *,
    proficiency: float | None,
    lower: float,
    upper: float,
    limit: int,
) -> list[str]:
    if proficiency is None:
        rows = conn.execute(
            """
            SELECT identity_key FROM candidates
            WHERE admission_suitability > 0
            ORDER BY lexical_commonness DESC, ordinal ASC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT identity_key FROM candidates
            WHERE admission_suitability > 0
              AND difficulty BETWEEN ? AND ?
            ORDER BY ABS(difficulty - ?) ASC, lexical_commonness DESC, ordinal ASC
            LIMIT ?
            """,
            (float(lower), float(upper), float(proficiency), int(limit)),
        ).fetchall()
    return [str(row["identity_key"]) for row in rows]


def _query_topic_identity_keys(
    conn: sqlite3.Connection,
    *,
    active_topics: Sequence[str],
    proficiency: float | None,
    lower: float,
    upper: float,
    limit: int,
) -> list[str]:
    normalized_topics = tuple(
        dict.fromkeys(
            topic
            for topic in (canonicalize_topic_token(raw_topic) for raw_topic in active_topics)
            if topic
        )
    )
    if not normalized_topics:
        return []
    placeholders = ",".join("?" for _topic in normalized_topics)
    params: list[object] = list(normalized_topics)
    order_center = float(proficiency) if proficiency is not None else 0.5
    params.extend([float(lower), float(upper), order_center, int(limit)])
    rows = conn.execute(
        f"""
        SELECT c.identity_key, c.difficulty, c.lexical_commonness, c.ordinal
        FROM candidates c
        JOIN candidate_topics t ON t.identity_key = c.identity_key
        WHERE c.admission_suitability > 0
          AND t.topic IN ({placeholders})
          AND c.difficulty BETWEEN ? AND ?
        ORDER BY ABS(c.difficulty - ?) ASC, c.lexical_commonness DESC, c.ordinal ASC
        LIMIT ?
        """,
        params,
    ).fetchall()
    return list(dict.fromkeys(str(row["identity_key"]) for row in rows))


def _query_overlay_identity_keys(
    conn: sqlite3.Connection,
    *,
    overlay_payload: Mapping[str, object] | None,
    active_topics: Sequence[str],
    proficiency: float | None,
    lower: float,
    upper: float,
    limit: int,
) -> list[str]:
    if not active_topics or not isinstance(overlay_payload, Mapping):
        return []
    active_topic_set = {
        canonicalize_topic_token(topic)
        for topic in active_topics
        if canonicalize_topic_token(topic)
    }
    if not active_topic_set:
        return []
    lemmas = []
    for row in _overlay_rows(overlay_payload):
        topic = canonicalize_topic_token(row.get("topic"))
        membership = _safe_float(row.get("membership")) or 0.0
        lemma = str(row.get("lemma") or "").strip()
        if (
            topic in active_topic_set
            and membership >= PROFILE_TOPIC_OVERLAY_MIN_MEMBERSHIP
            and lemma
        ):
            lemmas.append(lemma)
    ordered_lemmas = tuple(dict.fromkeys(lemmas))
    if not ordered_lemmas:
        return []
    order_center = float(proficiency) if proficiency is not None else 0.5
    rows: list[sqlite3.Row] = []
    for chunk in _chunked(ordered_lemmas, 500):
        placeholders = ",".join("?" for _lemma in chunk)
        rows.extend(
            conn.execute(
                f"""
                SELECT identity_key, difficulty, lexical_commonness, ordinal
                FROM candidates
                WHERE admission_suitability > 0
                  AND lemma IN ({placeholders})
                  AND difficulty BETWEEN ? AND ?
                """,
                (*chunk, float(lower), float(upper)),
            ).fetchall()
        )
    rows.sort(
        key=lambda row: (
            abs(float(row["difficulty"]) - order_center),
            -float(row["lexical_commonness"]),
            int(row["ordinal"]),
        )
    )
    return [str(row["identity_key"]) for row in rows[: int(limit)]]


def _query_common_identity_keys(conn: sqlite3.Connection, *, limit: int) -> list[str]:
    rows = conn.execute(
        """
        SELECT identity_key FROM candidates
        WHERE admission_suitability > 0
        ORDER BY lexical_commonness DESC, ordinal ASC
        LIMIT ?
        """,
        (int(limit),),
    ).fetchall()
    return [str(row["identity_key"]) for row in rows]


def _load_seed_rows_for_identity_keys(
    conn: sqlite3.Connection,
    identity_keys: Sequence[str],
) -> list[SeedWord]:
    if not identity_keys:
        return []
    placeholders = ",".join("?" for _identity in identity_keys)
    rows = conn.execute(
        f"""
        SELECT identity_key, ordinal, seed_json, traits_json
        FROM candidates
        WHERE identity_key IN ({placeholders})
        """,
        tuple(identity_keys),
    ).fetchall()
    row_by_identity = {str(row["identity_key"]): row for row in rows}
    ordered_rows = sorted(
        (
            row_by_identity[identity_key]
            for identity_key in dict.fromkeys(identity_keys)
            if identity_key in row_by_identity
        ),
        key=lambda row: int(row["ordinal"]),
    )
    seeds: list[SeedWord] = []
    for row in ordered_rows:
        seed_payload = json.loads(str(row["seed_json"]))
        traits_payload = json.loads(str(row["traits_json"]))
        seed = seed_from_cache_row(
            seed_payload,
            language_pair=str(seed_payload.get("language_pair") or ""),
            seed_factory=SeedWord,
        )
        if isinstance(seed.metadata, dict):
            seed.metadata[ADMISSION_CANDIDATE_FEATURES_METADATA_KEY] = traits_payload
            seed.metadata[ADMISSION_CANDIDATE_FEATURES_PRECOMPUTE_VERSION_KEY] = (
                FRONTIER_GAUSSIAN_HYBRID_PROFILE_BOOTSTRAP_POLICY.version
            )
        seeds.append(seed)
    return seeds


def _build_index_preview_report(
    store: SrsStore,
    *,
    config: SetInitializationConfig,
    frontier_entries: Sequence[ProfileBootstrapFrontierLaneEntry],
    profile_bootstrap_diagnostics: Mapping[str, object],
) -> tuple[SrsStore, SetInitializationReport]:
    selection_policy = str(profile_bootstrap_diagnostics.get("selection_policy") or "").strip()
    admitted_entries = [entry.source_entry for entry in frontier_entries]
    updated_store, inserted_count, updated_count = _upsert_preview_items(
        store,
        admitted_entries=admitted_entries,
    )
    selected_count = int(
        str(
            profile_bootstrap_diagnostics.get("selectable_candidate_count") or len(admitted_entries)
        )
    )
    ranking_preview = profile_bootstrap_diagnostics.get("ranking_preview")
    diagnostics = {
        **dict(profile_bootstrap_diagnostics),
        "selection_policy": selection_policy,
        "active_profile_bootstrap_policy": (
            FRONTIER_GAUSSIAN_HYBRID_PROFILE_BOOTSTRAP_POLICY.version
        ),
        "initial_active_diagnostic_preview": tuple(
            dict(entry)
            for entry in (
                ranking_preview
                if isinstance(ranking_preview, Sequence)
                and not isinstance(ranking_preview, (str, bytes))
                else ()
            )
            if isinstance(entry, Mapping)
        ),
    }
    return updated_store, SetInitializationReport(
        selected_count=selected_count,
        selected_unique_count=selected_count,
        admitted_count=len(admitted_entries),
        inserted_count=inserted_count,
        updated_count=updated_count,
        selected_preview=tuple(
            str(getattr(entry.seed, "lemma", "") or "").strip()
            for entry in admitted_entries[:10]
            if str(getattr(entry.seed, "lemma", "") or "").strip()
        ),
        selected_unique_lemmas=tuple(
            str(getattr(entry.seed, "lemma", "") or "").strip()
            for entry in admitted_entries
            if str(getattr(entry.seed, "lemma", "") or "").strip()
        ),
        initial_active_preview=tuple(
            str(getattr(entry.seed, "lemma", "") or "").strip()
            for entry in admitted_entries[: config.initial_active_count]
            if str(getattr(entry.seed, "lemma", "") or "").strip()
        ),
        admission_weight_profile=resolve_default_pos_weights(
            language_pair=config.language_pair
        ).to_dict(),
        initial_active_weight_preview=tuple(
            build_weight_preview_entry(entry.seed) for entry in admitted_entries[:20]
        ),
        selection_strategy="profile_bootstrap",
        selection_policy=selection_policy,
        selection_seed=config.selection_seed,
        selector_version=str(diagnostics.get("selector_version") or "") or None,
        profile_bootstrap_diagnostics=diagnostics,
        selected_unique_identity_keys=tuple(
            entry.traits.candidate_identity_key
            for entry in admitted_entries
            if entry.traits.candidate_identity_key
        ),
        initial_active_identity_keys=tuple(
            entry.traits.candidate_identity_key
            for entry in admitted_entries[: config.initial_active_count]
            if entry.traits.candidate_identity_key
        ),
        blocked_lemmas=tuple(sorted(config.blocked_lemmas)),
    )


def _upsert_preview_items(
    store: SrsStore,
    *,
    admitted_entries: Sequence[ProfileBootstrapScoredEntry],
) -> tuple[SrsStore, int, int]:
    existing_by_id = {item.item_id: item for item in store.items}
    inserted_count = 0
    updated_count = 0
    updated = store
    admitted_at = format_ts(now_utc())
    for entry in admitted_entries:
        seed = entry.seed
        item_id = build_item_id(str(getattr(seed, "language_pair", "") or ""), entry.traits.lemma)
        word_package = getattr(seed, "word_package", None)
        confidence = _safe_float(getattr(seed, "admission_weight", None))
        existing_item = existing_by_id.get(item_id)
        if existing_item is not None:
            updated_count += 1
            item = existing_item
            if item.confidence is None and confidence is not None:
                item = replace(item, confidence=confidence)
            if item.word_package is None and isinstance(word_package, Mapping):
                item = replace(item, word_package=word_package)
        else:
            inserted_count += 1
            item = SrsItem(
                item_id=item_id,
                lemma=entry.traits.lemma,
                language_pair=str(getattr(seed, "language_pair", "") or ""),
                source_type=SOURCE_INITIAL_SET,
                confidence=confidence,
                admitted_at=admitted_at,
                word_package=word_package if isinstance(word_package, Mapping) else None,
            )
            existing_by_id[item_id] = item
        updated = upsert_item(updated, item)
    return updated, inserted_count, updated_count


def _overlay_rows(payload: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    rows = payload.get("rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        return tuple()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _chunked(values: Sequence[str], size: int) -> tuple[tuple[str, ...], ...]:
    chunk_size = max(1, int(size))
    return tuple(
        tuple(values[index : index + chunk_size]) for index in range(0, len(values), chunk_size)
    )


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
