from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Optional, Sequence

from lexishift_core.lexicon.word_package import WORD_PACKAGE_VERSION
from lexishift_core.resources.japanese_learner_signals import JAPANESE_LEARNER_SIGNALS_VERSION
from lexishift_core.srs.admission_policy import resolve_default_pos_weights
from lexishift_core.srs.candidate_classification import CANDIDATE_CLASSIFICATION_VERSION
from lexishift_core.srs.candidate_identity import CANDIDATE_IDENTITY_VERSION
from lexishift_core.srs.learner_difficulty import (
    LEARNER_DIFFICULTY_MODEL_VERSION,
    resolve_corrected_en_ja_learner_difficulty_csv_path,
)

SEED_FRONTIER_CACHE_SCHEMA_VERSION = 2
SEED_FRONTIER_CACHE_KIND = "srs_seed_frontier"
SEED_FRONTIER_CACHE_LOCK_TIMEOUT_SECONDS = 120.0
SEED_FRONTIER_CACHE_LOCK_POLL_SECONDS = 0.25
SEED_FRONTIER_CACHE_LOCK_STALE_SECONDS = 30.0 * 60.0


def seed_frontier_cache_path(
    *,
    frequency_db: Path,
    config,
) -> Path | None:
    if not getattr(config, "cache_dir", None):
        return None
    fingerprint = seed_frontier_fingerprint(frequency_db=frequency_db, config=config)
    safe_pair = safe_cache_segment(getattr(config, "language_pair", None))
    cache_root = Path(config.cache_dir).expanduser()
    return cache_root / safe_pair / f"{fingerprint}.jsonl"


def seed_frontier_fingerprint(
    *,
    frequency_db: Path,
    config,
) -> str:
    language_pair = str(getattr(config, "language_pair", "") or "").strip().lower()
    resolved_pos_weights = getattr(
        config,
        "admission_pos_weights",
        None,
    ) or resolve_default_pos_weights(language_pair=language_pair)
    pmw_weighting = getattr(config, "pmw_weighting")
    payload = {
        "kind": SEED_FRONTIER_CACHE_KIND,
        "schema_version": SEED_FRONTIER_CACHE_SCHEMA_VERSION,
        "word_package_version": WORD_PACKAGE_VERSION,
        "candidate_classification_version": CANDIDATE_CLASSIFICATION_VERSION,
        "candidate_identity_version": CANDIDATE_IDENTITY_VERSION,
        "learner_difficulty_model_version": LEARNER_DIFFICULTY_MODEL_VERSION,
        "japanese_learner_signals_version": JAPANESE_LEARNER_SIGNALS_VERSION,
        "language_pair": language_pair,
        "frequency_db": path_fingerprint(frequency_db),
        "columns": {
            "lemma": getattr(config, "lemma_column", None),
            "rank": getattr(config, "rank_column", None),
            "pmw": getattr(config, "pmw_column", None),
            "pos": getattr(config, "pos_column", None),
            "lform": getattr(config, "lform_column", None),
            "wtype": getattr(config, "wtype_column", None),
            "sublemma": getattr(config, "sublemma_column", None),
            "topics": list(getattr(config, "topic_columns", ()) or ()),
        },
        "top_n": getattr(config, "top_n", None),
        "pmw_weighting": {
            "mode": pmw_weighting.mode,
            "min_value": pmw_weighting.min_value,
        },
        "admission_pos_weights": resolved_pos_weights.to_dict(),
        "sort_by_admission_weight": bool(getattr(config, "sort_by_admission_weight", True)),
        "apply_learner_signal_classification": bool(
            getattr(config, "apply_learner_signal_classification", True)
        ),
        "require_jmdict": bool(getattr(config, "require_jmdict", False)),
        "jmdict": (
            path_fingerprint(getattr(config, "jmdict_path", None))
            if getattr(config, "require_jmdict", False)
            else None
        ),
        "jmnedict": path_fingerprint(_resolved_jmnedict_path_for_cache(config)),
        "kanjidic2": path_fingerprint(_resolved_kanjidic2_path_for_cache(config)),
        "kanjivg": path_fingerprint(_resolved_kanjivg_path_for_cache(config)),
        "jlpt_vocabulary": path_fingerprint(_resolved_jlpt_vocabulary_path_for_cache(config)),
        "lesson_vocabulary": path_fingerprint(_resolved_lesson_vocabulary_path_for_cache(config)),
        "stopwords": {
            "path": path_fingerprint(getattr(config, "stopwords_path", None)),
            "inline_hash": inline_stopwords_hash(getattr(config, "stopwords", None)),
        },
        "source_label": str(getattr(config, "source_label", "") or "").strip(),
        "pos_overlay": path_fingerprint(getattr(config, "pos_overlay_path", None)),
        "corrected_learner_difficulty": path_fingerprint(
            resolve_corrected_en_ja_learner_difficulty_csv_path()
        ),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def seed_frontier_cache_status(
    *,
    frequency_db: Path,
    config,
) -> dict[str, object]:
    cache_path = seed_frontier_cache_path(frequency_db=frequency_db, config=config)
    if cache_path is None:
        return {
            "status": "disabled",
            "cache_enabled": False,
            "cache_path": None,
            "lock_path": None,
            "seed_count": 0,
            "stale_cache_count": 0,
        }

    lock_path = seed_frontier_cache_lock_path(cache_path)
    payload: dict[str, object] = {
        "status": "missing",
        "cache_enabled": True,
        "cache_path": str(cache_path),
        "lock_path": str(lock_path),
        "seed_count": 0,
        "size_bytes": 0,
        "mtime_ns": None,
        "stale_cache_count": count_stale_seed_frontier_caches(cache_path),
        "lock_active": seed_frontier_cache_lock_is_active(lock_path),
    }
    if cache_path.exists():
        try:
            stat = cache_path.stat()
            payload["size_bytes"] = int(stat.st_size)
            payload["mtime_ns"] = int(stat.st_mtime_ns)
            header = read_seed_frontier_cache_header(cache_path)
            if valid_seed_frontier_cache_header(header):
                payload["status"] = "ready"
                payload["seed_count"] = int(header.get("seed_count") or 0)
            else:
                payload["status"] = "error"
                payload["error"] = "invalid_cache_header"
        except OSError as exc:
            payload["status"] = "error"
            payload["error"] = str(exc)
        return payload
    if payload["lock_active"]:
        payload["status"] = "building"
    elif payload["stale_cache_count"]:
        payload["status"] = "stale"
    return payload


def _resolved_kanjidic2_path_for_cache(config) -> Path | None:
    configured = getattr(config, "kanjidic2_path", None)
    if configured:
        return Path(configured)
    jmdict_path = getattr(config, "jmdict_path", None)
    if not jmdict_path:
        return None
    for root in (Path(jmdict_path).parent, Path(jmdict_path).parent.parent):
        for candidate in (
            root / "kanjidic2-ja" / "kanjidic2.xml",
            root / "kanjidic2-ja" / "kanjidic2.xml.gz",
            root / "kanjidic2.xml",
            root / "kanjidic2.xml.gz",
        ):
            if candidate.is_file():
                return candidate
    return None


def _resolved_jmnedict_path_for_cache(config) -> Path | None:
    configured = getattr(config, "jmnedict_path", None)
    if configured:
        return Path(configured)
    jmdict_path = getattr(config, "jmdict_path", None)
    if not jmdict_path:
        return None
    for root in (Path(jmdict_path).parent, Path(jmdict_path).parent.parent):
        for candidate in (
            root / "jmnedict-ja" / "JMnedict.xml",
            root / "jmnedict-ja" / "JMnedict.xml.gz",
            root / "JMnedict.xml",
            root / "JMnedict.xml.gz",
        ):
            if candidate.is_file():
                return candidate
    return None


def _resolved_kanjivg_path_for_cache(config) -> Path | None:
    configured = getattr(config, "kanjivg_path", None)
    if configured:
        return Path(configured)
    jmdict_path = getattr(config, "jmdict_path", None)
    if not jmdict_path:
        return None
    for root in (Path(jmdict_path).parent, Path(jmdict_path).parent.parent):
        for candidate in (
            root / "kanjivg-ja" / "kanjivg-20250816.xml",
            root / "kanjivg-ja" / "kanjivg.xml",
            root / "kanjivg-ja" / "kanjivg.xml.gz",
            root / "kanjivg-20250816.xml",
            root / "kanjivg.xml",
            root / "kanjivg.xml.gz",
        ):
            if candidate.is_file():
                return candidate
    return None


def _resolved_jlpt_vocabulary_path_for_cache(config) -> Path | None:
    configured = getattr(config, "jlpt_vocabulary_path", None)
    if configured:
        return Path(configured)
    jmdict_path = getattr(config, "jmdict_path", None)
    if not jmdict_path:
        return None
    for root in (Path(jmdict_path).parent, Path(jmdict_path).parent.parent):
        for candidate in (
            root / "jlpt-tanos-vocab-ja" / "JLPT_vocab_ALL.csv",
            root / "jlpt-tanos-vocab-ja" / "JLPT_vocab_ALL.json",
            root / "JLPT_vocab_ALL.csv",
            root / "JLPT_vocab_ALL.json",
        ):
            if candidate.is_file():
                return candidate
    return None


def _resolved_lesson_vocabulary_path_for_cache(config) -> Path | None:
    configured = getattr(config, "lesson_vocabulary_path", None)
    if configured:
        return Path(configured)
    jmdict_path = getattr(config, "jmdict_path", None)
    if not jmdict_path:
        return None
    for root in (Path(jmdict_path).parent, Path(jmdict_path).parent.parent):
        for candidate in (
            root / "sbsjapanese1-ja",
            root / "sbsjapanese1-ja" / "EPUB",
            root / "sbsjapanese1",
            root / "sbsjapanese1" / "EPUB",
        ):
            if candidate.exists():
                return candidate
    return None


def read_seed_frontier_cache_rows(cache_path: Path) -> list[dict[str, object]] | None:
    try:
        with Path(cache_path).open("r", encoding="utf-8") as handle:
            header = json.loads(handle.readline())
            if not valid_seed_frontier_cache_header(header):
                return None
            rows: list[dict[str, object]] = []
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                row = json.loads(stripped)
                if not isinstance(row, dict):
                    return None
                rows.append(row)
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return None
    return rows


def write_seed_frontier_cache_rows(
    *,
    cache_path: Path,
    rows: Sequence[dict[str, object]],
    config,
) -> None:
    header = {
        "kind": SEED_FRONTIER_CACHE_KIND,
        "schema_version": SEED_FRONTIER_CACHE_SCHEMA_VERSION,
        "language_pair": str(getattr(config, "language_pair", "") or "").strip().lower(),
        "seed_count": len(rows),
    }
    target = Path(cache_path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(json.dumps(header, ensure_ascii=False, sort_keys=True) + "\n")
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        os.replace(temp_name, target)
    except OSError:
        try:
            if "temp_name" in locals():
                Path(temp_name).unlink(missing_ok=True)
        except OSError:
            pass


def cleanup_seed_frontier_cache(
    *,
    cache_dir: Path | None,
    pair: str,
    active_cache_path: Path | None = None,
) -> dict[str, object]:
    if cache_dir is None:
        return {"deleted_cache_count": 0, "deleted_lock_count": 0, "errors": []}
    pair_dir = Path(cache_dir).expanduser() / safe_cache_segment(pair)
    active_path = Path(active_cache_path).resolve(strict=False) if active_cache_path else None
    deleted_cache_count = 0
    deleted_lock_count = 0
    errors: list[str] = []
    if not pair_dir.exists():
        return {"deleted_cache_count": 0, "deleted_lock_count": 0, "errors": []}
    for cache_file in pair_dir.glob("*.jsonl"):
        if active_path is not None and cache_file.resolve(strict=False) == active_path:
            continue
        try:
            cache_file.unlink()
            deleted_cache_count += 1
        except OSError as exc:
            errors.append(f"{cache_file}: {exc}")
    for lock_file in pair_dir.glob("*.jsonl.lock"):
        if seed_frontier_cache_lock_is_active(lock_file):
            continue
        try:
            lock_file.unlink()
            deleted_lock_count += 1
        except OSError as exc:
            errors.append(f"{lock_file}: {exc}")
    return {
        "deleted_cache_count": deleted_cache_count,
        "deleted_lock_count": deleted_lock_count,
        "errors": errors,
    }


def read_seed_frontier_cache_header(cache_path: Path) -> dict[str, object]:
    try:
        with Path(cache_path).open("r", encoding="utf-8") as handle:
            header = json.loads(handle.readline())
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return {}
    return header if isinstance(header, dict) else {}


def valid_seed_frontier_cache_header(header: object) -> bool:
    if not isinstance(header, dict):
        return False
    return (
        header.get("kind") == SEED_FRONTIER_CACHE_KIND
        and header.get("schema_version") == SEED_FRONTIER_CACHE_SCHEMA_VERSION
    )


def seed_frontier_cache_lock_path(cache_path: Path) -> Path:
    return Path(f"{cache_path}.lock")


def acquire_seed_frontier_cache_lock(cache_path: Path) -> Path | None:
    lock_path = seed_frontier_cache_lock_path(cache_path)
    deadline = time.monotonic() + SEED_FRONTIER_CACHE_LOCK_TIMEOUT_SECONDS
    lock_payload = {
        "kind": f"{SEED_FRONTIER_CACHE_KIND}_lock",
        "pid": os.getpid(),
        "created_at": time.time(),
        "cache_path": str(cache_path),
    }
    while True:
        try:
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(str(lock_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(lock_payload, handle, ensure_ascii=False, sort_keys=True)
                handle.write("\n")
            return lock_path
        except FileExistsError:
            if not seed_frontier_cache_lock_is_active(lock_path):
                try:
                    lock_path.unlink()
                except OSError:
                    pass
                continue
            if time.monotonic() >= deadline:
                return None
            time.sleep(SEED_FRONTIER_CACHE_LOCK_POLL_SECONDS)
        except OSError:
            return None


def release_seed_frontier_cache_lock(lock_path: Path | None) -> None:
    if lock_path is None:
        return
    try:
        lock_path.unlink()
    except (FileNotFoundError, OSError):
        return


def seed_frontier_cache_lock_is_active(lock_path: Path) -> bool:
    try:
        stat = Path(lock_path).stat()
    except OSError:
        return False
    age_seconds = max(0.0, time.time() - float(stat.st_mtime))
    return age_seconds < SEED_FRONTIER_CACHE_LOCK_STALE_SECONDS


def count_stale_seed_frontier_caches(cache_path: Path) -> int:
    active = Path(cache_path).resolve(strict=False)
    try:
        return sum(
            1
            for candidate in Path(cache_path).parent.glob("*.jsonl")
            if candidate.resolve(strict=False) != active
        )
    except OSError:
        return 0


def path_fingerprint(path: Optional[Path]) -> dict[str, object] | None:
    if not path:
        return None
    resolved = Path(path).expanduser().resolve(strict=False)
    try:
        stat = resolved.stat()
    except OSError:
        return {
            "path": str(resolved),
            "exists": False,
            "size": None,
            "mtime_ns": None,
        }
    return {
        "path": str(resolved),
        "exists": True,
        "size": int(stat.st_size),
        "mtime_ns": int(stat.st_mtime_ns),
    }


def inline_stopwords_hash(stopwords: Optional[set[str]]) -> str | None:
    if stopwords is None:
        return None
    normalized = sorted(str(item).strip() for item in stopwords if str(item).strip())
    encoded = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def safe_cache_segment(value: object) -> str:
    raw = str(value or "unknown").strip().lower()
    safe = "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in raw)
    return safe or "unknown"
