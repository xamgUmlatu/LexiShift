from __future__ import annotations

from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace
from typing import Iterator, Mapping, Sequence
from unittest.mock import patch
from xml.sax.saxutils import escape

from lexishift_core.helper.engine import get_srs_runtime_diagnostics
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.replacement.core import VocabRule
from lexishift_core.srs import SrsItem, SrsSettings, load_srs_settings, load_srs_store
from lexishift_core.srs.scheduler import get_item_retrievability, select_active_items
from lexishift_core.srs.signal_queue import load_signal_events

from srs_journey_installed_support import (
    ROLE_REF_DIFFICULT_1,
    ROLE_REF_GROWTH_1,
    ROLE_REF_GROWTH_2,
    ROLE_REF_STABLE_1,
    ROLE_REF_STABLE_2,
    stage_installed_pair_resources,
)
from srs_journey_review_support import word_package_preview

CLOCK_PATCH_TARGETS = (
    "lexishift_core.srs.time.now_utc",
    "lexishift_core.srs.scheduler.now_utc",
    "lexishift_core.srs.store_ops.now_utc",
    "lexishift_core.srs.signal_queue.now_utc",
    "lexishift_core.srs.admission_refresh.now_utc",
    "lexishift_core.helper.engine.now_utc",
)

BASE_TIME = datetime(2026, 3, 21, 9, 0, tzinfo=timezone.utc)
DEFAULT_PROFILE_ID = "default"
DEFAULT_PAIR = "en-ja"


@dataclass(frozen=True)
class CandidateSpec:
    lemma: str
    source_gloss: str
    cohort: str
    base_weight: float
    pos_bucket: str = "noun"
    pos_weight: float = 1.0
    frequency_pos_raw: str = "n"


@dataclass(frozen=True)
class JourneyPairFixture:
    pair: str
    frequency_filename: str
    candidate_specs: tuple[CandidateSpec, ...]
    jmdict_filename: str | None = None
    translation_dict_forward_filename: str | None = None
    translation_dict_reverse_filename: str | None = None


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
    pair: str
    lane: str
    phase_plans: tuple[JourneyPhasePlan, ...]
    resource_mode: str = "synthetic"
    use_stub_seed_candidates: bool = True
    use_stub_rulegen: bool = True
    expect_fade_checks: bool = False
    set_top_n: int = 7
    bootstrap_top_n: int = 7
    initial_active_count: int = 3
    max_active_items: int = 8
    max_new_items_per_day: int = 2


def _candidate_specs(
    rows: Sequence[tuple[str, str, str, float]],
    *,
    frequency_pos_raw: str = "n",
) -> tuple[CandidateSpec, ...]:
    return tuple(
        CandidateSpec(
            lemma=lemma,
            source_gloss=source_gloss,
            cohort=cohort,
            base_weight=base_weight,
            frequency_pos_raw=frequency_pos_raw,
        )
        for lemma, source_gloss, cohort, base_weight in rows
    )


JA_NOUN_FREQ_POS = "名詞-普通名詞-一般"

EN_JA_CANDIDATE_SPECS = _candidate_specs(
    (
        ("alpha", "eng_alpha", "stable", 0.97),
        ("beta", "eng_beta", "stable", 0.93),
        ("gamma", "eng_gamma", "difficult", 0.90),
        ("delta", "eng_delta", "frontier", 0.86),
        ("epsilon", "eng_epsilon", "frontier", 0.82),
        ("zeta", "eng_zeta", "frontier", 0.78),
        ("eta", "eng_eta", "frontier", 0.74),
    ),
    frequency_pos_raw=JA_NOUN_FREQ_POS,
)

EN_ES_CANDIDATE_SPECS = _candidate_specs(
    (
        ("casa", "house", "stable", 0.97),
        ("libro", "book", "stable", 0.93),
        ("hora", "hour", "difficult", 0.90),
        ("madre", "mother", "frontier", 0.86),
        ("campo", "field", "frontier", 0.82),
        ("ventana", "window", "frontier", 0.78),
        ("mesa", "table", "frontier", 0.74),
    )
)

PAIR_FIXTURES = {
    "en-ja": JourneyPairFixture(
        pair="en-ja",
        frequency_filename="freq-ja-bccwj.sqlite",
        candidate_specs=EN_JA_CANDIDATE_SPECS,
        jmdict_filename="JMdict_e",
    ),
    "en-es": JourneyPairFixture(
        pair="en-es",
        frequency_filename="freq-es-cde.sqlite",
        candidate_specs=EN_ES_CANDIDATE_SPECS,
        translation_dict_forward_filename="wiktionary-es-en.sqlite",
        translation_dict_reverse_filename="eng-spa.tei",
    ),
}

EN_JA_CORE_SCENARIO_NAME = "en-ja_core_journey_v1"
EN_JA_EDGE_SCENARIO_NAME = "en-ja_edge_behaviors_v1"
EN_JA_REAL_SCENARIO_NAME = "en-ja_real_publication_v1"
EN_JA_INSTALLED_SCENARIO_NAME = "en-ja_installed_data_journey_v1"
EN_ES_CORE_SCENARIO_NAME = "en-es_core_journey_v1"
EN_ES_EDGE_SCENARIO_NAME = "en-es_edge_behaviors_v1"
EN_ES_REAL_SCENARIO_NAME = "en-es_real_publication_v1"
EN_ES_INSTALLED_SCENARIO_NAME = "en-es_installed_data_journey_v1"

CORE_SCENARIO_NAME = EN_JA_CORE_SCENARIO_NAME
EDGE_SCENARIO_NAME = EN_JA_EDGE_SCENARIO_NAME
REAL_SCENARIO_NAME = EN_JA_REAL_SCENARIO_NAME

EN_ES_PHASE_LEMMA_MAP = dict(
    zip(
        ("alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta"),
        ("casa", "libro", "hora", "madre", "campo", "ventana", "mesa"),
        strict=True,
    )
)


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
    JourneyPhasePlan(label="fade_check", observe_at=BASE_TIME + timedelta(days=7)),
)

ROLE_CORE_PHASE_PLANS = (
    JourneyPhasePlan(label="bootstrap_publish", observe_at=BASE_TIME),
    JourneyPhasePlan(label="baseline_observe", observe_at=BASE_TIME + timedelta(minutes=5)),
    JourneyPhasePlan(
        label="high_retention_growth",
        observe_at=BASE_TIME + timedelta(days=1),
        feedback_events=(
            (ROLE_REF_STABLE_1, "good"),
            (ROLE_REF_STABLE_2, "easy"),
            (ROLE_REF_STABLE_1, "good"),
            (ROLE_REF_STABLE_2, "easy"),
            (ROLE_REF_STABLE_1, "easy"),
            (ROLE_REF_STABLE_2, "good"),
            (ROLE_REF_STABLE_1, "easy"),
            (ROLE_REF_STABLE_2, "good"),
        ),
        refresh_at=BASE_TIME + timedelta(days=1),
    ),
    JourneyPhasePlan(
        label="low_retention_pause",
        observe_at=BASE_TIME + timedelta(days=2),
        feedback_events=(
            (ROLE_REF_DIFFICULT_1, "again"),
            (ROLE_REF_DIFFICULT_1, "hard"),
            (ROLE_REF_DIFFICULT_1, "again"),
            (ROLE_REF_DIFFICULT_1, "hard"),
            (ROLE_REF_DIFFICULT_1, "again"),
            (ROLE_REF_DIFFICULT_1, "hard"),
            (ROLE_REF_DIFFICULT_1, "again"),
            (ROLE_REF_DIFFICULT_1, "hard"),
        ),
        refresh_at=BASE_TIME + timedelta(days=2),
    ),
    JourneyPhasePlan(
        label="recovery_resume",
        observe_at=BASE_TIME + timedelta(days=3),
        feedback_events=(
            (ROLE_REF_GROWTH_1, "good"),
            (ROLE_REF_GROWTH_2, "easy"),
            (ROLE_REF_GROWTH_1, "good"),
            (ROLE_REF_GROWTH_2, "easy"),
            (ROLE_REF_GROWTH_1, "easy"),
            (ROLE_REF_GROWTH_2, "good"),
            (ROLE_REF_GROWTH_1, "easy"),
            (ROLE_REF_GROWTH_2, "good"),
        ),
        refresh_at=BASE_TIME + timedelta(days=3),
    ),
    JourneyPhasePlan(label="fade_check", observe_at=BASE_TIME + timedelta(days=7)),
)

EDGE_PHASE_PLANS = (
    JourneyPhasePlan(label="bootstrap_publish", observe_at=BASE_TIME),
    JourneyPhasePlan(
        label="duplicate_feedback_burst",
        observe_at=BASE_TIME + timedelta(minutes=15),
        feedback_events=(("alpha", "good"), ("alpha", "easy")),
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
        exposure_events=("alpha", "alpha", "beta", "gamma", "gamma", "gamma"),
        refresh_at=BASE_TIME + timedelta(days=2),
    ),
    JourneyPhasePlan(label="final_observe", observe_at=BASE_TIME + timedelta(days=3)),
)


def _translate_phase_plans(
    phase_plans: Sequence[JourneyPhasePlan],
    lemma_map: Mapping[str, str],
) -> tuple[JourneyPhasePlan, ...]:
    translated: list[JourneyPhasePlan] = []
    for phase in phase_plans:
        translated.append(
            JourneyPhasePlan(
                label=phase.label,
                observe_at=phase.observe_at,
                feedback_events=tuple(
                    (lemma_map.get(lemma, lemma), rating) for lemma, rating in phase.feedback_events
                ),
                exposure_events=tuple(
                    lemma_map.get(lemma, lemma) for lemma in phase.exposure_events
                ),
                refresh_at=phase.refresh_at,
            )
        )
    return tuple(translated)


SCENARIOS = {
    EN_JA_CORE_SCENARIO_NAME: JourneyScenario(
        name=EN_JA_CORE_SCENARIO_NAME,
        pair="en-ja",
        lane="deterministic_core_journey",
        phase_plans=CORE_PHASE_PLANS,
        expect_fade_checks=True,
    ),
    EN_JA_EDGE_SCENARIO_NAME: JourneyScenario(
        name=EN_JA_EDGE_SCENARIO_NAME,
        pair="en-ja",
        lane="deterministic_edge_behaviors",
        phase_plans=EDGE_PHASE_PLANS,
    ),
    EN_JA_REAL_SCENARIO_NAME: JourneyScenario(
        name=EN_JA_REAL_SCENARIO_NAME,
        pair="en-ja",
        lane="real_publication_journey",
        phase_plans=CORE_PHASE_PLANS,
        use_stub_seed_candidates=False,
        use_stub_rulegen=False,
        expect_fade_checks=True,
    ),
    EN_JA_INSTALLED_SCENARIO_NAME: JourneyScenario(
        name=EN_JA_INSTALLED_SCENARIO_NAME,
        pair="en-ja",
        lane="installed_resource_journey",
        phase_plans=ROLE_CORE_PHASE_PLANS,
        resource_mode="installed",
        use_stub_seed_candidates=False,
        use_stub_rulegen=False,
        expect_fade_checks=True,
        set_top_n=200,
        bootstrap_top_n=200,
    ),
    EN_ES_CORE_SCENARIO_NAME: JourneyScenario(
        name=EN_ES_CORE_SCENARIO_NAME,
        pair="en-es",
        lane="deterministic_core_journey",
        phase_plans=_translate_phase_plans(CORE_PHASE_PLANS, EN_ES_PHASE_LEMMA_MAP),
        expect_fade_checks=True,
    ),
    EN_ES_EDGE_SCENARIO_NAME: JourneyScenario(
        name=EN_ES_EDGE_SCENARIO_NAME,
        pair="en-es",
        lane="deterministic_edge_behaviors",
        phase_plans=_translate_phase_plans(EDGE_PHASE_PLANS, EN_ES_PHASE_LEMMA_MAP),
    ),
    EN_ES_REAL_SCENARIO_NAME: JourneyScenario(
        name=EN_ES_REAL_SCENARIO_NAME,
        pair="en-es",
        lane="real_publication_journey",
        phase_plans=_translate_phase_plans(CORE_PHASE_PLANS, EN_ES_PHASE_LEMMA_MAP),
        use_stub_seed_candidates=False,
        use_stub_rulegen=False,
        expect_fade_checks=True,
    ),
    EN_ES_INSTALLED_SCENARIO_NAME: JourneyScenario(
        name=EN_ES_INSTALLED_SCENARIO_NAME,
        pair="en-es",
        lane="installed_resource_journey",
        phase_plans=ROLE_CORE_PHASE_PLANS,
        resource_mode="installed",
        use_stub_seed_candidates=False,
        use_stub_rulegen=False,
        expect_fade_checks=True,
        set_top_n=50,
        bootstrap_top_n=50,
    ),
}


def get_pair_fixture(pair: str) -> JourneyPairFixture:
    normalized = str(pair or "").strip().lower()
    try:
        return PAIR_FIXTURES[normalized]
    except KeyError as exc:
        raise KeyError(f"Unsupported SRS journey pair fixture: {pair}") from exc


def cohort_by_lemma_for_pair(pair: str) -> dict[str, str]:
    fixture = get_pair_fixture(pair)
    return {spec.lemma: spec.cohort for spec in fixture.candidate_specs}


def scenario_cohorts(pair: str) -> dict[str, list[str]]:
    fixture = get_pair_fixture(pair)
    grouped = {"stable": [], "difficult": [], "frontier": []}
    for spec in fixture.candidate_specs:
        grouped.setdefault(spec.cohort, []).append(spec.lemma)
    return grouped


def create_frequency_db(path: Path, *, specs: Sequence[CandidateSpec]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute("DROP TABLE IF EXISTS frequency;")
        conn.execute("CREATE TABLE frequency (lemma TEXT, core_rank REAL, pmw REAL, pos TEXT);")
        conn.executemany(
            "INSERT INTO frequency (lemma, core_rank, pmw, pos) VALUES (?, ?, ?, ?);",
            [
                (
                    spec.lemma,
                    float(index + 1),
                    float(len(specs) - index),
                    spec.frequency_pos_raw,
                )
                for index, spec in enumerate(specs)
            ],
        )
        conn.commit()
    finally:
        conn.close()
    return path


def _write_jmdict(path: Path, *, specs: Sequence[CandidateSpec]) -> Path:
    entries: list[str] = []
    for spec in specs:
        entries.append(
            "<entry>"
            f"<k_ele><keb>{escape(spec.lemma)}</keb></k_ele>"
            f"<r_ele><reb>{escape(spec.lemma)}</reb></r_ele>"
            f"<sense><gloss>{escape(spec.source_gloss)}</gloss></sense>"
            "</entry>"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("<JMdict>" + "".join(entries) + "</JMdict>", encoding="utf-8")
    return path


def _write_freedict_tei(
    path: Path,
    *,
    entries: Sequence[tuple[str, str, str]],
    target_lang: str,
) -> Path:
    payload_entries: list[str] = []
    for headword, translation, pos_raw in entries:
        pos_xml = f"<gramGrp><pos>{escape(pos_raw)}</pos></gramGrp>" if pos_raw else ""
        payload_entries.append(
            "<entry>"
            f"<form><orth>{escape(headword)}</orth></form>"
            f"{pos_xml}"
            "<sense>"
            f"<cit type='trans'><quote xml:lang='{escape(target_lang)}'>{escape(translation)}</quote></cit>"
            "</sense>"
            "</entry>"
        )
    payload = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<TEI xmlns='http://www.tei-c.org/ns/1.0'>"
        "<text><body>" + "".join(payload_entries) + "</body></text></TEI>"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")
    return path


def _write_translation_dictionary_sqlite(
    path: Path,
    *,
    entries: Sequence[tuple[str, str, str]],
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute("DROP TABLE IF EXISTS meta;")
        conn.execute("DROP TABLE IF EXISTS entries;")
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);")
        conn.execute(
            "CREATE TABLE entries ("
            "headword TEXT NOT NULL, "
            "headword_lc TEXT NOT NULL, "
            "translation TEXT NOT NULL, "
            "translation_lc TEXT NOT NULL, "
            "rank INTEGER NOT NULL, "
            "pos TEXT, "
            "entry_ord INTEGER NOT NULL, "
            "gloss_ord INTEGER NOT NULL, "
            "PRIMARY KEY (headword_lc, translation_lc)"
            ");"
        )
        conn.executemany(
            "INSERT INTO entries ("
            "headword, headword_lc, translation, translation_lc, rank, pos, entry_ord, gloss_ord"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    headword,
                    headword.lower(),
                    translation,
                    translation.lower(),
                    index + 1,
                    pos_raw,
                    index + 1,
                    0,
                )
                for index, (headword, translation, pos_raw) in enumerate(entries)
            ],
        )
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            ("metadata", json.dumps({"source": "synthetic_srs_journey"}, ensure_ascii=False)),
        )
        conn.commit()
    finally:
        conn.close()
    return path


def create_pair_resources(
    paths: HelperPaths,
    *,
    pair: str,
    resource_mode: str = "synthetic",
) -> dict[str, Path | None]:
    if resource_mode == "installed":
        return stage_installed_pair_resources(paths, pair=pair)
    if resource_mode != "synthetic":
        raise ValueError(f"Unsupported SRS journey resource mode: {resource_mode}")
    fixture = get_pair_fixture(pair)
    specs = fixture.candidate_specs
    frequency_db = create_frequency_db(
        paths.frequency_packs_dir / fixture.frequency_filename,
        specs=specs,
    )
    resources: dict[str, Path | None] = {
        "frequency_db": frequency_db,
        "jmdict_path": None,
        "translation_dict_path": None,
        "reverse_translation_dict_path": None,
    }
    if fixture.jmdict_filename:
        resources["jmdict_path"] = _write_jmdict(
            paths.language_packs_dir / fixture.jmdict_filename,
            specs=specs,
        )
    if fixture.translation_dict_forward_filename:
        forward_path = paths.language_packs_dir / fixture.translation_dict_forward_filename
        forward_entries = [(spec.lemma, spec.source_gloss, spec.pos_bucket) for spec in specs]
        if forward_path.suffix == ".sqlite":
            resources["translation_dict_path"] = _write_translation_dictionary_sqlite(
                forward_path,
                entries=forward_entries,
            )
        else:
            resources["translation_dict_path"] = _write_freedict_tei(
                forward_path,
                entries=forward_entries,
                target_lang="en",
            )
    if fixture.translation_dict_reverse_filename:
        target_lang = pair.split("-", 1)[1]
        resources["reverse_translation_dict_path"] = _write_freedict_tei(
            paths.language_packs_dir / fixture.translation_dict_reverse_filename,
            entries=[(spec.source_gloss, spec.lemma, spec.pos_bucket) for spec in specs],
            target_lang=target_lang,
        )
    resources["freedict_path"] = resources["translation_dict_path"]
    resources["freedict_reverse_path"] = resources["reverse_translation_dict_path"]
    return resources


def build_seed_candidates(*args, pair: str = "", **kwargs) -> list[SimpleNamespace]:
    config = kwargs.get("config")
    resolved_pair = (
        str(pair or getattr(config, "language_pair", "") or DEFAULT_PAIR).strip().lower()
    )
    fixture = get_pair_fixture(resolved_pair)
    candidates: list[SimpleNamespace] = []
    for index, spec in enumerate(fixture.candidate_specs):
        candidates.append(
            SimpleNamespace(
                lemma=spec.lemma,
                language_pair=fixture.pair,
                core_rank=float(index + 1),
                pos=f"{spec.pos_bucket}-tag",
                pos_bucket=spec.pos_bucket,
                pos_weight=spec.pos_weight,
                pmw=float(len(fixture.candidate_specs) - index),
                base_weight=spec.base_weight,
                admission_weight=round(spec.base_weight * spec.pos_weight, 6),
                metadata={"cohort": spec.cohort},
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


def scenario_candidate_universe(*, pair: str) -> list[dict[str, object]]:
    fixture = get_pair_fixture(pair)
    return [
        {
            "lemma": candidate.lemma,
            "cohort": candidate.cohort,
            "base_weight": candidate.base_weight,
            "admission_weight": round(candidate.base_weight * candidate.pos_weight, 6),
            "core_rank": float(index + 1),
            "source_gloss": candidate.source_gloss,
        }
        for index, candidate in enumerate(fixture.candidate_specs)
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


def published_sources_from_ruleset(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rules = payload.get("rules", [])
    sources = sorted(
        {
            str(rule.get("source_phrase") or "").strip()
            for rule in rules
            if isinstance(rule, Mapping) and str(rule.get("source_phrase") or "").strip()
        }
    )
    return sources


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
    item: SrsItem,
    *,
    settings: SrsSettings,
    now: datetime,
    due_lemmas: set[str],
    due_rank_by_lemma: Mapping[str, int],
    published_lemmas: set[str],
    cohort_by_lemma: Mapping[str, str],
) -> dict[str, object]:
    return {
        "lemma": item.lemma,
        "cohort": cohort_by_lemma.get(item.lemma, "frontier"),
        "status": _infer_status(item),
        "source_type": item.source_type,
        "confidence": item.confidence,
        "next_due": item.next_due,
        "due_rank": due_rank_by_lemma.get(item.lemma),
        "stability": item.stability,
        "difficulty": item.difficulty,
        "retrievability": get_item_retrievability(item, settings=settings, now=now),
        "scheduler_state": item.scheduler_state,
        "scheduler_step": item.scheduler_step,
        "last_seen": item.last_seen,
        "last_review": item.last_review,
        "exposures": int(item.exposures),
        "history_count": len(item.history),
        "recent_history": [
            {"ts": entry.ts, "rating": entry.rating} for entry in list(item.history)[-4:]
        ],
        "in_admitted": True,
        "in_due": item.lemma in due_lemmas,
        "in_published": item.lemma in published_lemmas,
        "word_package": word_package_preview(item.word_package),
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
    cohort_by_lemma: Mapping[str, str],
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
    due_rank_by_lemma = {item.lemma: index for index, item in enumerate(due_items, start=1)}
    ruleset_path = Path(str(diagnostics.get("ruleset_path") or ""))
    snapshot_path = Path(str(diagnostics.get("snapshot_path") or ""))
    published_lemmas = (
        set(published_targets_from_ruleset(ruleset_path)) if ruleset_path.exists() else set()
    )
    published_sources = (
        published_sources_from_ruleset(ruleset_path) if ruleset_path.exists() else []
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
            "ruleset_sources_preview": published_sources[:5],
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
            _item_payload(
                item,
                settings=settings,
                now=now,
                due_lemmas=due_lemmas,
                due_rank_by_lemma=due_rank_by_lemma,
                published_lemmas=published_lemmas,
                cohort_by_lemma=cohort_by_lemma,
            )
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
