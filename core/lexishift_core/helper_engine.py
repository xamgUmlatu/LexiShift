from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Optional

from lexishift_core.helper_paths import HelperPaths
from lexishift_core.helper_rulegen import (
    RulegenConfig,
    SeedConfig,
    run_rulegen_for_pair,
    write_rulegen_outputs,
)
from lexishift_core.helper_status import HelperStatus, load_status, save_status
from lexishift_core.srs import SrsSettings, SrsStore, load_srs_settings, load_srs_store, save_srs_settings, save_srs_store
from lexishift_core.srs_store_ops import record_exposure, record_feedback
from lexishift_core.srs_time import now_utc


@dataclass(frozen=True)
class RulegenJobConfig:
    pair: str
    jmdict_path: Path
    seed_db: Optional[Path] = None
    seed_top_n: int = 2000
    confidence_threshold: float = 0.0
    snapshot_targets: int = 50
    snapshot_sources: int = 6
    seed_if_empty: bool = True
    debug: bool = False
    debug_sample_size: int = 10


def _ensure_settings(paths: HelperPaths) -> SrsSettings:
    if paths.srs_settings_path.exists():
        return load_srs_settings(paths.srs_settings_path)
    settings = SrsSettings()
    save_srs_settings(settings, paths.srs_settings_path)
    return settings


def _ensure_store(paths: HelperPaths) -> SrsStore:
    if paths.srs_store_path.exists():
        return load_srs_store(paths.srs_store_path)
    store = SrsStore()
    save_srs_store(store, paths.srs_store_path)
    return store


def _update_status(
    *,
    paths: HelperPaths,
    pair: str,
    rule_count: int,
    target_count: int,
    error: Optional[str] = None,
) -> None:
    status = load_status(paths.srs_status_path)
    status = HelperStatus(
        version=status.version,
        helper_version=status.helper_version,
        last_run_at=now_utc().isoformat(),
        last_error=error,
        last_pair=pair,
        last_rule_count=rule_count,
        last_target_count=target_count,
    )
    save_status(status, paths.srs_status_path)


def load_snapshot(paths: HelperPaths, *, pair: str) -> dict:
    snapshot_path = paths.snapshot_path(pair)
    if not snapshot_path.exists():
        raise FileNotFoundError(snapshot_path)
    return json.loads(snapshot_path.read_text(encoding="utf-8"))


def load_ruleset(paths: HelperPaths, *, pair: str) -> dict:
    ruleset_path = paths.ruleset_path(pair)
    if not ruleset_path.exists():
        raise FileNotFoundError(ruleset_path)
    return json.loads(ruleset_path.read_text(encoding="utf-8"))


def run_rulegen_job(
    paths: HelperPaths,
    *,
    config: RulegenJobConfig,
) -> dict:
    if not config.jmdict_path.exists():
        raise FileNotFoundError(config.jmdict_path)
    settings = _ensure_settings(paths)
    store = _ensure_store(paths)
    diagnostics: dict[str, object] | None = None
    seed_config = None
    if config.seed_db and config.seed_db.exists():
        seed_config = SeedConfig(
            frequency_db=config.seed_db,
            jmdict_path=config.jmdict_path,
            top_n=config.seed_top_n,
            language_pair=config.pair,
        )
    rulegen_config = RulegenConfig(
        language_pair=config.pair,
        confidence_threshold=config.confidence_threshold,
        max_snapshot_targets=config.snapshot_targets,
        max_snapshot_sources=config.snapshot_sources,
    )
    if config.debug:
        missing_inputs = []
        if config.seed_db and not config.seed_db.exists():
            missing_inputs.append(
                {"type": "seed_db", "path": str(config.seed_db)}
            )
        diagnostics = {
            "pair": config.pair,
            "jmdict_path": str(config.jmdict_path),
            "jmdict_exists": config.jmdict_path.exists(),
            "seed_db": str(config.seed_db) if config.seed_db else None,
            "seed_db_exists": bool(config.seed_db and config.seed_db.exists()),
            "missing_inputs": missing_inputs,
            "store_items": len(store.items),
            "store_items_for_pair": len([item for item in store.items if item.language_pair == config.pair]),
            "store_sample": [
                item.lemma for item in store.items if item.language_pair == config.pair
            ][: max(1, int(config.debug_sample_size))],
        }
    store, output = run_rulegen_for_pair(
        paths=paths,
        pair=config.pair,
        store=store,
        settings=settings,
        jmdict_path=config.jmdict_path,
        seed_config=seed_config,
        rulegen_config=rulegen_config,
        seed_if_empty=config.seed_if_empty,
    )
    write_rulegen_outputs(
        paths=paths,
        pair=config.pair,
        rules=output.rules,
        snapshot=output.snapshot,
    )
    if store:
        save_srs_store(store, paths.srs_store_path)
    _update_status(
        paths=paths,
        pair=config.pair,
        rule_count=len(output.rules),
        target_count=output.target_count,
        error=None,
    )
    response = {
        "pair": config.pair,
        "targets": output.target_count,
        "rules": len(output.rules),
        "snapshot_path": str(paths.snapshot_path(config.pair)),
        "ruleset_path": str(paths.ruleset_path(config.pair)),
    }
    if diagnostics is not None:
        response["diagnostics"] = diagnostics
    return response


def apply_feedback(
    paths: HelperPaths,
    *,
    pair: str,
    lemma: str,
    rating: str,
    source_type: str = "extension",
) -> None:
    store = _ensure_store(paths)
    store = record_feedback(
        store,
        language_pair=pair,
        lemma=lemma,
        rating=rating,
        create_if_missing=True,
        source_type=source_type,
    )
    save_srs_store(store, paths.srs_store_path)


def apply_exposure(
    paths: HelperPaths,
    *,
    pair: str,
    lemma: str,
    source_type: str = "extension",
) -> None:
    store = _ensure_store(paths)
    store = record_exposure(
        store,
        language_pair=pair,
        lemma=lemma,
        create_if_missing=True,
        source_type=source_type,
    )
    save_srs_store(store, paths.srs_store_path)


def _remove_file(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    path.unlink()
    return True


def reset_srs_data(
    paths: HelperPaths,
    *,
    pair: Optional[str] = None,
) -> dict:
    scoped_pair = str(pair or "").strip() or None

    removed_items = 0
    remaining_items = 0
    if paths.srs_store_path.exists():
        store = load_srs_store(paths.srs_store_path)
        if scoped_pair:
            kept_items = tuple(item for item in store.items if item.language_pair != scoped_pair)
        else:
            kept_items = tuple()
        removed_items = len(store.items) - len(kept_items)
        remaining_items = len(kept_items)
        save_srs_store(SrsStore(items=kept_items, version=store.version), paths.srs_store_path)
    else:
        save_srs_store(SrsStore(), paths.srs_store_path)

    removed_snapshots = 0
    removed_rulesets = 0
    if scoped_pair:
        if _remove_file(paths.snapshot_path(scoped_pair)):
            removed_snapshots += 1
        if _remove_file(paths.ruleset_path(scoped_pair)):
            removed_rulesets += 1
    else:
        for snapshot in paths.srs_dir.glob("srs_rulegen_snapshot_*.json"):
            if _remove_file(snapshot):
                removed_snapshots += 1
        for ruleset in paths.srs_dir.glob("srs_ruleset_*.json"):
            if _remove_file(ruleset):
                removed_rulesets += 1

    status = load_status(paths.srs_status_path)
    save_status(
        HelperStatus(
            version=status.version,
            helper_version=status.helper_version,
            last_run_at=now_utc().isoformat(),
            last_error=None,
            last_pair=scoped_pair,
            last_rule_count=0,
            last_target_count=0,
        ),
        paths.srs_status_path,
    )

    return {
        "pair": scoped_pair or "all",
        "removed_items": removed_items,
        "remaining_items": remaining_items,
        "removed_snapshots": removed_snapshots,
        "removed_rulesets": removed_rulesets,
    }
