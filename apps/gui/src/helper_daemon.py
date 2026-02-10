from __future__ import annotations

import argparse
from dataclasses import dataclass
import time
from pathlib import Path
from typing import Optional

from lexishift_core.helper.engine import RulegenJobConfig, run_rulegen_job
from lexishift_core.helper.paths import build_helper_paths
from lexishift_core.helper.status import HelperStatus, load_status, save_status
from lexishift_core.helper.lp_capabilities import (
    default_freedict_de_en_path,
    default_frequency_db_path,
    default_jmdict_path,
    resolve_pair_capability,
    supported_rulegen_pairs,
)
from lexishift_core.srs import SrsSettings, load_srs_settings
from lexishift_core.srs.growth import resolve_allowed_pairs
from lexishift_core.srs.time import now_utc


@dataclass(frozen=True)
class DaemonConfig:
    interval_seconds: int = 1800
    set_top_n: Optional[int] = None
    confidence_threshold: float = 0.0
    snapshot_targets: int = 50
    snapshot_sources: int = 6


def _load_settings(paths) -> SrsSettings:
    if paths.srs_settings_path.exists():
        return load_srs_settings(paths.srs_settings_path)
    return SrsSettings()


def _supported_pairs() -> tuple[str, ...]:
    return supported_rulegen_pairs()


def _build_job_config(pair: str, paths, config: DaemonConfig) -> RulegenJobConfig | None:
    if pair not in _supported_pairs():
        return None
    capability = resolve_pair_capability(pair)
    jmdict_path = default_jmdict_path(pair, language_packs_dir=paths.language_packs_dir)
    if capability.requires_jmdict_for_rulegen and (jmdict_path is None or not jmdict_path.exists()):
        return None
    freedict_de_en_path = default_freedict_de_en_path(
        pair,
        language_packs_dir=paths.language_packs_dir,
    )
    if capability.requires_freedict_de_en_for_rulegen and (
        freedict_de_en_path is None or not freedict_de_en_path.exists()
    ):
        return None
    set_source_db = default_frequency_db_path(pair, frequency_packs_dir=paths.frequency_packs_dir)
    if set_source_db is not None and not set_source_db.exists():
        set_source_db = None
    return RulegenJobConfig(
        pair=pair,
        jmdict_path=jmdict_path,
        freedict_de_en_path=freedict_de_en_path,
        set_source_db=set_source_db,
        set_top_n=config.set_top_n,
        confidence_threshold=config.confidence_threshold,
        snapshot_targets=config.snapshot_targets,
        snapshot_sources=config.snapshot_sources,
        initialize_if_empty=True,
    )


def _update_status_error(paths, error: str) -> None:
    status = load_status(paths.srs_status_path)
    status = HelperStatus(
        version=status.version,
        helper_version=status.helper_version,
        last_run_at=now_utc().isoformat(),
        last_error=error,
        last_pair=status.last_pair,
        last_rule_count=status.last_rule_count,
        last_target_count=status.last_target_count,
    )
    save_status(status, paths.srs_status_path)


def run_daemon(config: DaemonConfig) -> None:
    paths = build_helper_paths()
    save_status(
        HelperStatus(last_run_at=now_utc().isoformat(), last_error=None),
        paths.srs_status_path,
    )
    while True:
        try:
            settings = _load_settings(paths)
            pairs = resolve_allowed_pairs(settings)
            if not pairs:
                pairs = _supported_pairs()
            for pair in pairs:
                job = _build_job_config(pair, paths, config)
                if not job:
                    continue
                run_rulegen_job(paths, config=job)
        except Exception as exc:  # noqa: BLE001
            _update_status_error(paths, str(exc))
        time.sleep(max(10, int(config.interval_seconds)))


def run_daemon_from_cli(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="LexiShift helper background daemon.")
    parser.add_argument("--interval-seconds", type=int, default=1800)
    parser.add_argument("--set-top-n", type=int)
    parser.add_argument("--confidence-threshold", type=float, default=0.0)
    parser.add_argument("--snapshot-targets", type=int, default=50)
    parser.add_argument("--snapshot-sources", type=int, default=6)
    args = parser.parse_args(argv)
    config = DaemonConfig(
        interval_seconds=args.interval_seconds,
        set_top_n=args.set_top_n,
        confidence_threshold=args.confidence_threshold,
        snapshot_targets=args.snapshot_targets,
        snapshot_sources=args.snapshot_sources,
    )
    run_daemon(config)
