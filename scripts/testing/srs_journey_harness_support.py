from __future__ import annotations

from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
from types import SimpleNamespace
from typing import Iterator, Mapping, Sequence
from unittest.mock import patch

from lexishift_core.helper.paths import HelperPaths
from lexishift_core.replacement.core import VocabRule

from srs_journey_installed_support import (
    ROLE_REF_DIFFICULT_1,
    ROLE_REF_GROWTH_1,
    ROLE_REF_GROWTH_2,
    ROLE_REF_STABLE_1,
    ROLE_REF_STABLE_2,
    stage_installed_pair_resources,
)
from synthetic_translation_fixture_support import (
    write_freedict_tei_fixture,
    write_jmdict_fixture,
    write_translation_dictionary_sqlite_fixture,
)

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
    topics: tuple[str, ...] = tuple()


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
    strategy: str = "frequency_bootstrap"
    profile_context: Mapping[str, object] | None = None
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
    topics_by_lemma: Mapping[str, Sequence[str]] | None = None,
) -> tuple[CandidateSpec, ...]:
    topic_map = topics_by_lemma or {}
    return tuple(
        CandidateSpec(
            lemma=lemma,
            source_gloss=source_gloss,
            cohort=cohort,
            base_weight=base_weight,
            frequency_pos_raw=frequency_pos_raw,
            topics=tuple(str(topic) for topic in topic_map.get(lemma, ()) if str(topic).strip()),
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
    ),
    topics_by_lemma={"madre": ("family", "people")},
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
        translation_dict_reverse_filename="wiktionary-en-es.sqlite",
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
EN_ES_PROFILE_SCENARIO_NAME = "en-es_profile_preference_journey_v1"

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

EN_ES_PROFILE_PHASE_PLANS = (
    JourneyPhasePlan(label="bootstrap_publish", observe_at=BASE_TIME),
    JourneyPhasePlan(label="baseline_observe", observe_at=BASE_TIME + timedelta(minutes=5)),
    JourneyPhasePlan(
        label="high_retention_growth",
        observe_at=BASE_TIME + timedelta(days=1),
        feedback_events=(
            ("casa", "good"),
            ("libro", "easy"),
            ("casa", "good"),
            ("libro", "easy"),
            ("casa", "easy"),
            ("libro", "good"),
            ("casa", "easy"),
            ("libro", "good"),
        ),
        refresh_at=BASE_TIME + timedelta(days=1),
    ),
    JourneyPhasePlan(
        label="low_retention_pause",
        observe_at=BASE_TIME + timedelta(days=2),
        feedback_events=(
            ("madre", "again"),
            ("madre", "hard"),
            ("madre", "again"),
            ("madre", "hard"),
            ("madre", "again"),
            ("madre", "hard"),
            ("madre", "again"),
            ("madre", "hard"),
        ),
        refresh_at=BASE_TIME + timedelta(days=2),
    ),
    JourneyPhasePlan(
        label="recovery_resume",
        observe_at=BASE_TIME + timedelta(days=3),
        feedback_events=(
            ("hora", "good"),
            ("campo", "easy"),
            ("hora", "good"),
            ("campo", "easy"),
            ("hora", "easy"),
            ("campo", "good"),
            ("hora", "easy"),
            ("campo", "good"),
        ),
        refresh_at=BASE_TIME + timedelta(days=3),
    ),
    JourneyPhasePlan(label="final_observe", observe_at=BASE_TIME + timedelta(days=7)),
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
    EN_ES_PROFILE_SCENARIO_NAME: JourneyScenario(
        name=EN_ES_PROFILE_SCENARIO_NAME,
        pair="en-es",
        lane="profile_preference_journey",
        phase_plans=EN_ES_PROFILE_PHASE_PLANS,
        strategy="profile_bootstrap",
        profile_context={"topic_weights": {"family": 1.0}},
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
        conn.execute(
            "CREATE TABLE frequency "
            "(lemma TEXT, core_rank REAL, pmw REAL, pos TEXT, profile_topics TEXT);"
        )
        conn.executemany(
            "INSERT INTO frequency "
            "(lemma, core_rank, pmw, pos, profile_topics) VALUES (?, ?, ?, ?, ?);",
            [
                (
                    spec.lemma,
                    float(index + 1),
                    float(len(specs) - index),
                    spec.frequency_pos_raw,
                    ",".join(spec.topics) if spec.topics else None,
                )
                for index, spec in enumerate(specs)
            ],
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
        resources["jmdict_path"] = write_jmdict_fixture(
            paths.language_packs_dir / fixture.jmdict_filename,
            entries=[(spec.lemma, spec.source_gloss) for spec in specs],
        )
    if fixture.translation_dict_forward_filename:
        forward_path = paths.language_packs_dir / fixture.translation_dict_forward_filename
        forward_entries = [(spec.lemma, spec.source_gloss, spec.pos_bucket) for spec in specs]
        if forward_path.suffix == ".sqlite":
            resources["translation_dict_path"] = write_translation_dictionary_sqlite_fixture(
                forward_path,
                entries=forward_entries,
                metadata_source="synthetic_srs_journey",
            )
        else:
            resources["translation_dict_path"] = write_freedict_tei_fixture(
                forward_path,
                entries=forward_entries,
                target_lang="en",
            )
    if fixture.translation_dict_reverse_filename:
        reverse_path = paths.language_packs_dir / fixture.translation_dict_reverse_filename
        reverse_entries = [(spec.source_gloss, spec.lemma, spec.pos_bucket) for spec in specs]
        if reverse_path.suffix == ".sqlite":
            resources["reverse_translation_dict_path"] = (
                write_translation_dictionary_sqlite_fixture(
                    reverse_path,
                    entries=reverse_entries,
                    metadata_source="synthetic_srs_journey_reverse",
                )
            )
        else:
            target_lang = pair.split("-", 1)[1]
            resources["reverse_translation_dict_path"] = write_freedict_tei_fixture(
                reverse_path,
                entries=reverse_entries,
                target_lang=target_lang,
            )
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
                metadata={
                    "cohort": spec.cohort,
                    "topics": list(spec.topics),
                },
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
            "topics": list(candidate.topics),
        }
        for index, candidate in enumerate(fixture.candidate_specs)
    ]
