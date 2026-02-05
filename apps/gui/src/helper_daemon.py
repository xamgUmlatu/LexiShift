from __future__ import annotations

import argparse
from dataclasses import dataclass
import time
from pathlib import Path

from lexishift_core.helper_engine import RulegenJobConfig, run_rulegen_job
from lexishift_core.helper_paths import build_helper_paths
from lexishift_core.helper_status import HelperStatus, load_status, save_status
from lexishift_core.srs import SrsSettings, load_srs_settings
from lexishift_core.srs_growth import resolve_allowed_pairs
from lexishift_core.srs_time import now_utc


@dataclass(frozen=True)
class DaemonConfig:
    interval_seconds: int = 1800
    seed_top_n: int = 2000
    confidence_threshold: float = 0.0
    snapshot_targets: int = 50
    snapshot_sources: int = 6


def _load_settings(paths) -> SrsSettings:
    if paths.srs_settings_path.exists():
        return load_srs_settings(paths.srs_settings_path)
    return SrsSettings()


def _supported_pairs() -> tuple[str, ...]:
    return ("en-ja",)


def _build_job_config(pair: str, paths, config: DaemonConfig) -> RulegenJobConfig | None:
    if pair not in _supported_pairs():
        return None
    jmdict_path = paths.language_packs_dir / "JMdict_e"
    if not jmdict_path.exists():
        return None
    seed_db = paths.frequency_packs_dir / "freq-ja-bccwj.sqlite"
    if not seed_db.exists():
        seed_db = None
    return RulegenJobConfig(
        pair=pair,
        jmdict_path=jmdict_path,
        seed_db=seed_db,
        seed_top_n=config.seed_top_n,
        confidence_threshold=config.confidence_threshold,
        snapshot_targets=config.snapshot_targets,
        snapshot_sources=config.snapshot_sources,
        seed_if_empty=True,
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
    parser.add_argument("--seed-top-n", type=int, default=2000)
    parser.add_argument("--confidence-threshold", type=float, default=0.0)
    parser.add_argument("--snapshot-targets", type=int, default=50)
    parser.add_argument("--snapshot-sources", type=int, default=6)
    args = parser.parse_args(argv)
    config = DaemonConfig(
        interval_seconds=args.interval_seconds,
        seed_top_n=args.seed_top_n,
        confidence_threshold=args.confidence_threshold,
        snapshot_targets=args.snapshot_targets,
        snapshot_sources=args.snapshot_sources,
    )
    run_daemon(config)
