from __future__ import annotations

from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace
from typing import Any, Iterator, Mapping, Sequence
from unittest.mock import patch

from lexishift_core.helper.engine import get_srs_runtime_diagnostics, load_ruleset, load_snapshot
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.replacement.core import VocabRule
from lexishift_core.srs import SrsItem, load_srs_settings, load_srs_store
from lexishift_core.srs.scheduler import select_active_items
from lexishift_core.srs.signal_queue import load_signal_events

CLOCK_PATCH_TARGETS = (
    "lexishift_core.srs.time.now_utc",
    "lexishift_core.srs.scheduler.now_utc",
    "lexishift_core.srs.store_ops.now_utc",
    "lexishift_core.srs.signal_queue.now_utc",
    "lexishift_core.srs.admission_refresh.now_utc",
    "lexishift_core.helper.engine.now_utc",
)

BASE_TIME = datetime(2026, 3, 21, 9, 0, tzinfo=timezone.utc)
SCENARIO_LEMMAS = ("alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta")
DEFAULT_PROFILE_ID = "default"
DEFAULT_PAIR = "en-ja"
COHORT_BY_LEMMA = {
    "alpha": "stable",
    "beta": "stable",
    "gamma": "difficult",
    "delta": "frontier",
    "epsilon": "frontier",
    "zeta": "frontier",
    "eta": "frontier",
}


@dataclass(frozen=True)
class JourneyPhasePlan:
    label: str
    observe_at: datetime
    feedback_events: tuple[tuple[str, str], ...] = tuple()
    exposure_events: tuple[str, ...] = tuple()
    refresh_at: datetime | None = None


@dataclass(frozen=True)
class JourneyScenario:
    name: str
    lane: str
    phase_plans: tuple[JourneyPhasePlan, ...]
    set_top_n: int = 7
    bootstrap_top_n: int = 7
    initial_active_count: int = 3
    max_active_items: int = 8
    max_new_items_per_day: int = 2


CORE_SCENARIO_NAME = "en-ja_core_journey_v1"
EDGE_SCENARIO_NAME = "en-ja_edge_behaviors_v1"


CORE_PHASE_PLANS = (
    JourneyPhasePlan(label="bootstrap_publish", observe_at=BASE_TIME),
    JourneyPhasePlan(label="baseline_observe", observe_at=BASE_TIME + timedelta(minutes=5)),
    JourneyPhasePlan(
        label="high_retention_growth",
        observe_at=BASE_TIME + timedelta(days=1),
        feedback_events=(
            ("alpha", "good"),
            ("beta", "easy"),
            ("alpha", "good"),
            ("beta", "easy"),
            ("alpha", "easy"),
            ("beta", "good"),
            ("alpha", "easy"),
            ("beta", "good"),
        ),
        refresh_at=BASE_TIME + timedelta(days=1),
    ),
    JourneyPhasePlan(
        label="low_retention_pause",
        observe_at=BASE_TIME + timedelta(days=2),
        feedback_events=(
            ("gamma", "again"),
            ("gamma", "hard"),
            ("gamma", "again"),
            ("gamma", "hard"),
            ("gamma", "again"),
            ("gamma", "hard"),
            ("gamma", "again"),
            ("gamma", "hard"),
        ),
        refresh_at=BASE_TIME + timedelta(days=2),
    ),
    JourneyPhasePlan(
        label="recovery_resume",
        observe_at=BASE_TIME + timedelta(days=3),
        feedback_events=(
            ("delta", "good"),
            ("epsilon", "easy"),
            ("delta", "good"),
            ("epsilon", "easy"),
            ("delta", "easy"),
            ("epsilon", "good"),
            ("delta", "easy"),
            ("epsilon", "good"),
        ),
        refresh_at=BASE_TIME + timedelta(days=3),
    ),
    JourneyPhasePlan(label="fade_check", observe_at=BASE_TIME + timedelta(days=10)),
)

EDGE_PHASE_PLANS = (
    JourneyPhasePlan(label="bootstrap_publish", observe_at=BASE_TIME),
    JourneyPhasePlan(
        label="duplicate_feedback_burst",
        observe_at=BASE_TIME + timedelta(minutes=15),
        feedback_events=(
            ("alpha", "good"),
            ("alpha", "easy"),
        ),
    ),
    JourneyPhasePlan(
        label="low_retention_seed",
        observe_at=BASE_TIME + timedelta(days=1),
        feedback_events=(
            ("gamma", "again"),
            ("gamma", "hard"),
            ("gamma", "again"),
            ("gamma", "hard"),
            ("gamma", "again"),
            ("gamma", "hard"),
            ("gamma", "again"),
            ("gamma", "hard"),
        ),
        refresh_at=BASE_TIME + timedelta(days=1),
    ),
    JourneyPhasePlan(
        label="exposure_only_pause_probe",
        observe_at=BASE_TIME + timedelta(days=2),
        exposure_events=(
            "alpha",
            "alpha",
            "beta",
            "gamma",
            "gamma",
            "gamma",
        ),
        refresh_at=BASE_TIME + timedelta(days=2),
    ),
    JourneyPhasePlan(label="final_observe", observe_at=BASE_TIME + timedelta(days=3)),
)

SCENARIOS = {
    CORE_SCENARIO_NAME: JourneyScenario(
        name=CORE_SCENARIO_NAME,
        lane="deterministic_core_journey",
        phase_plans=CORE_PHASE_PLANS,
    ),
    EDGE_SCENARIO_NAME: JourneyScenario(
        name=EDGE_SCENARIO_NAME,
        lane="deterministic_edge_behaviors",
        phase_plans=EDGE_PHASE_PLANS,
    ),
}


def create_en_ja_frequency_db(path: Path, *, lemmas: Sequence[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute("DROP TABLE IF EXISTS frequency;")
        conn.execute("CREATE TABLE frequency (lemma TEXT, core_rank REAL, pmw REAL, pos TEXT);")
        conn.executemany(
            "INSERT INTO frequency (lemma, core_rank, pmw, pos) VALUES (?, ?, ?, ?);",
            [
                (lemma, float(index + 1), float(len(lemmas) - index), "名詞-普通名詞-一般")
                for index, lemma in enumerate(lemmas)
            ],
        )
        conn.commit()
    finally:
        conn.close()
    return path


def create_en_ja_jmdict(path: Path, *, lemmas: Sequence[str]) -> Path:
    entries = []
    for lemma in lemmas:
        entries.append(
            "<entry>"
            f"<k_ele><keb>{lemma}</keb></k_ele>"
            f"<r_ele><reb>{lemma}</reb></r_ele>"
            f"<sense><gloss>eng_{lemma}</gloss></sense>"
            "</entry>"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("<JMdict>" + "".join(entries) + "</JMdict>", encoding="utf-8")
    return path


def create_en_ja_resources(
    paths: HelperPaths, *, lemmas: Sequence[str] = SCENARIO_LEMMAS
) -> dict[str, Path]:
    frequency_db = create_en_ja_frequency_db(
        paths.frequency_packs_dir / "freq-ja-bccwj.sqlite",
        lemmas=lemmas,
    )
    jmdict_path = create_en_ja_jmdict(paths.language_packs_dir / "JMdict_e", lemmas=lemmas)
    return {
        "frequency_db": frequency_db,
        "jmdict_path": jmdict_path,
    }


def build_seed_candidates(*args, pair: str = DEFAULT_PAIR, **_kwargs) -> list[SimpleNamespace]:
    specs = [
        ("alpha", 0.97, "noun", 1.00),
        ("beta", 0.93, "noun", 1.00),
        ("gamma", 0.90, "noun", 1.00),
        ("delta", 0.86, "noun", 1.00),
        ("epsilon", 0.82, "noun", 1.00),
        ("zeta", 0.78, "noun", 1.00),
        ("eta", 0.74, "noun", 1.00),
    ]
    candidates: list[SimpleNamespace] = []
    for index, (lemma, base_weight, bucket, pos_weight) in enumerate(specs):
        candidates.append(
            SimpleNamespace(
                lemma=lemma,
                language_pair=pair,
                core_rank=float(index + 1),
                pos=f"{bucket}-tag",
                pos_bucket=bucket,
                pos_weight=pos_weight,
                pmw=100.0 - (index * 5.0),
                base_weight=base_weight,
                admission_weight=round(base_weight * pos_weight, 6),
                metadata={"cohort": COHORT_BY_LEMMA.get(lemma, "frontier")},
            )
        )
    return candidates


def stub_run_rulegen_for_pair(*, store, pair, **_kwargs):
    pair_lemmas = sorted({item.lemma for item in store.items if item.language_pair == pair})
    rules = tuple(
        VocabRule(source_phrase=f"journey_src_{lemma}", replacement=lemma) for lemma in pair_lemmas
    )
    snapshot_targets = [
        {"lemma": lemma, "sources": [f"journey_src_{lemma}"], "replacement": lemma}
        for lemma in pair_lemmas
    ]
    snapshot = {
        "version": 1,
        "pair": pair,
        "targets": snapshot_targets,
        "stats": {
            "target_count": len(pair_lemmas),
            "rule_count": len(rules),
            "source_count": len(rules),
        },
    }
    return store, SimpleNamespace(rules=rules, snapshot=snapshot, target_count=len(pair_lemmas))


@contextmanager
def patched_now(now: datetime) -> Iterator[None]:
    with ExitStack() as stack:
        for target in CLOCK_PATCH_TARGETS:
            stack.enter_context(patch(target, return_value=now))
        yield


def get_scenario(name: str) -> JourneyScenario:
    try:
        return SCENARIOS[name]
    except KeyError as exc:
        raise KeyError(f"Unsupported SRS journey scenario: {name}") from exc


def scenario_clock(phase_plans: Sequence[JourneyPhasePlan]) -> dict[str, str]:
    return {phase.label: phase.observe_at.isoformat() for phase in phase_plans}


def scenario_candidate_universe() -> list[dict[str, object]]:
    return [
        {
            "lemma": candidate.lemma,
            "cohort": COHORT_BY_LEMMA.get(candidate.lemma, "frontier"),
            "base_weight": candidate.base_weight,
            "admission_weight": candidate.admission_weight,
            "core_rank": candidate.core_rank,
        }
        for candidate in build_seed_candidates()
    ]


def load_signal_log(
    paths: HelperPaths, *, profile_id: str = DEFAULT_PROFILE_ID
) -> list[dict[str, object]]:
    events = load_signal_events(paths.srs_signal_queue_path_for(profile_id))
    payload: list[dict[str, object]] = []
    for index, event in enumerate(events, start=1):
        payload.append(
            {
                "index": index,
                "event_type": event.event_type,
                "pair": event.pair,
                "lemma": event.lemma,
                "source_type": event.source_type,
                "rating": event.rating,
                "ts": event.ts,
                "metadata": dict(event.metadata or {}),
            }
        )
    return payload


def _load_ruleset_payload(path: Path) -> dict[str, Any]:
    payload = load_ruleset(build_helper_paths_from_path(path), pair=DEFAULT_PAIR)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected ruleset object in {path}")
    return payload


def _load_snapshot_payload(path: Path) -> dict[str, Any]:
    payload = load_snapshot(build_helper_paths_from_path(path), pair=DEFAULT_PAIR)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected snapshot object in {path}")
    return payload


def build_helper_paths_from_path(path: Path) -> HelperPaths:
    profile_dir = path.parent
    data_root = profile_dir.parents[2]
    from lexishift_core.helper.paths import build_helper_paths

    return build_helper_paths(data_root)


def published_targets_from_ruleset(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rules = payload.get("rules", [])
    targets = sorted(
        {
            str(rule.get("replacement") or "").strip()
            for rule in rules
            if isinstance(rule, Mapping) and str(rule.get("replacement") or "").strip()
        }
    )
    return targets


def snapshot_targets_from_snapshot(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    targets = payload.get("targets", [])
    if not isinstance(targets, list):
        return []
    resolved: list[str] = []
    for target in targets:
        if isinstance(target, Mapping):
            lemma = str(target.get("lemma") or target.get("replacement") or "").strip()
            if lemma:
                resolved.append(lemma)
    return sorted(set(resolved))


def _item_payload(
    item: SrsItem, *, due_lemmas: set[str], published_lemmas: set[str]
) -> dict[str, object]:
    return {
        "lemma": item.lemma,
        "cohort": COHORT_BY_LEMMA.get(item.lemma, "frontier"),
        "status": _infer_status(item),
        "next_due": item.next_due,
        "stability": item.stability,
        "difficulty": item.difficulty,
        "last_seen": item.last_seen,
        "exposures": int(item.exposures),
        "history_count": len(item.history),
        "recent_history": [
            {"ts": entry.ts, "rating": entry.rating} for entry in list(item.history)[-4:]
        ],
        "in_admitted": True,
        "in_due": item.lemma in due_lemmas,
        "in_published": item.lemma in published_lemmas,
    }


def _infer_status(item: SrsItem) -> str:
    history_count = len(item.history)
    if history_count == 0:
        return "new"
    if item.stability is None:
        return "learning"
    if item.stability >= 4.0:
        return "mature"
    if item.stability >= 2.0:
        return "review"
    return "learning"


def phase_snapshot(
    paths: HelperPaths,
    *,
    pair: str,
    profile_id: str,
    now: datetime,
) -> dict[str, object]:
    diagnostics = get_srs_runtime_diagnostics(paths, pair=pair, profile_id=profile_id)
    store = load_srs_store(paths.srs_store_path_for(profile_id))
    settings = load_srs_settings(paths.srs_settings_path)
    pair_items = sorted(
        [item for item in store.items if item.language_pair == pair],
        key=lambda item: item.lemma,
    )
    due_items = select_active_items(
        pair_items,
        now=now,
        max_active=settings.max_active_items,
        allowed_pairs=[pair],
    )
    due_lemmas = {item.lemma for item in due_items}
    ruleset_path = Path(str(diagnostics.get("ruleset_path") or ""))
    snapshot_path = Path(str(diagnostics.get("snapshot_path") or ""))
    published_lemmas = (
        set(published_targets_from_ruleset(ruleset_path)) if ruleset_path.exists() else set()
    )
    snapshot_lemmas = (
        set(snapshot_targets_from_snapshot(snapshot_path)) if snapshot_path.exists() else set()
    )
    admitted = [item.lemma for item in pair_items]
    due = sorted(due_lemmas)
    published = sorted(published_lemmas)
    return {
        "runtime": {
            "diagnostics": diagnostics,
            "ruleset_path": str(ruleset_path),
            "snapshot_path": str(snapshot_path),
            "snapshot_targets": sorted(snapshot_lemmas),
        },
        "sets": {
            "admitted": admitted,
            "due": due,
            "published": published,
        },
        "relationships": {
            "published_not_due": sorted(published_lemmas - due_lemmas),
            "published_not_admitted": sorted(published_lemmas - set(admitted)),
            "due_not_published": sorted(due_lemmas - published_lemmas),
        },
        "counts": {
            "admitted": len(admitted),
            "due": len(due),
            "published": len(published),
        },
        "items": [
            _item_payload(item, due_lemmas=due_lemmas, published_lemmas=published_lemmas)
            for item in pair_items
        ],
    }


def phase_deltas(
    previous: Mapping[str, object] | None, current: Mapping[str, object]
) -> dict[str, list[str]]:
    if previous is None:
        return {
            "admitted_in": list(current.get("sets", {}).get("admitted", [])),
            "admitted_out": [],
            "due_in": list(current.get("sets", {}).get("due", [])),
            "due_out": [],
            "published_in": list(current.get("sets", {}).get("published", [])),
            "published_out": [],
        }

    previous_sets = previous.get("sets", {}) if isinstance(previous, Mapping) else {}
    current_sets = current.get("sets", {}) if isinstance(current, Mapping) else {}

    def _delta(key: str) -> tuple[list[str], list[str]]:
        before = (
            set(previous_sets.get(key, []))
            if isinstance(previous_sets.get(key, []), list)
            else set()
        )
        after = (
            set(current_sets.get(key, [])) if isinstance(current_sets.get(key, []), list) else set()
        )
        return sorted(after - before), sorted(before - after)

    admitted_in, admitted_out = _delta("admitted")
    due_in, due_out = _delta("due")
    published_in, published_out = _delta("published")
    return {
        "admitted_in": admitted_in,
        "admitted_out": admitted_out,
        "due_in": due_in,
        "due_out": due_out,
        "published_in": published_in,
        "published_out": published_out,
    }
