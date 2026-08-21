#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence
from urllib.request import Request, urlopen

from srs_topic_todosloscorpus_overlay_en_es import (
    DEFAULT_FREQUENCY_DB,
    DEFAULT_REGISTRY_JSON,
    SOURCE_PROVIDER,
    USER_AGENT,
    _dedupe_preserve_order,
    _extract_source_entries,
    _load_frequency_rows,
    _load_source_payload,
    _normalize_lemma,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_topic_todosloscorpus_source_audit_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_topic_todosloscorpus_source_audit_en_es_latest.md"
TREE_URL = "https://api.github.com/repos/Lingwars/todosloscorpus/git/trees/HEAD?recursive=1"
RAW_PREFIX = "https://raw.githubusercontent.com/Lingwars/todosloscorpus/main/"

PROMOTE_DIRECT_RUNTIME = "promote_direct_runtime"
CANDIDATE_NOT_RUNTIME = "candidate_not_runtime"
BLOCKED_NOT_TOPIC = "blocked_not_topic_source"
BLOCKED_PROPER_NAMES = "blocked_proper_name_heavy"
BLOCKED_NO_SUPPORTED_TOPIC = "blocked_no_supported_topic"
BLOCKED_NO_MATCHES = "blocked_no_corpus_matches"

MANUAL_DECISIONS: dict[str, dict[str, object]] = {
    "data/materials/abridged-body-fluids.json": {
        "recommendation": PROMOTE_DIRECT_RUNTIME,
        "target_family": "medicine_health",
        "confidence": 0.94,
        "exclude_lemmas": ["cera"],
        "rationale": (
            "Literal body-fluid vocabulary. Exclude cera because its dominant standalone sense "
            "is wax rather than earwax."
        ),
    },
    "data/materials/building-materials.json": {
        "recommendation": CANDIDATE_NOT_RUNTIME,
        "target_family": "science_technology",
        "rationale": "Useful materials/construction list, but high-frequency rows are broad everyday materials.",
    },
    "data/materials/decorative-stones.json": {
        "recommendation": CANDIDATE_NOT_RUNTIME,
        "target_family": "science_technology",
        "rationale": "Good geology/materials source, but niche enough to keep candidate-only first.",
    },
    "data/materials/gemstones.json": {
        "recommendation": CANDIDATE_NOT_RUNTIME,
        "target_family": "science_technology",
        "rationale": "Literal mineral/gem list, but includes ambiguous rows such as hueso, jacinto, and coral.",
    },
    "data/materials/metals.json": {
        "recommendation": CANDIDATE_NOT_RUNTIME,
        "target_family": "science_technology",
        "rationale": "Full metals list includes ambiguous element names; layperson-metals is already safer.",
    },
    "data/humans/familyRelations.json": {
        "recommendation": BLOCKED_NO_SUPPORTED_TOPIC,
        "target_family": "future_family_people",
        "extract_fields": ["m", "f"],
        "rationale": "High-quality family vocabulary, but no current canonical family/people topic exists.",
    },
    "data/humans/occupations.json": {
        "recommendation": CANDIDATE_NOT_RUNTIME,
        "target_family": "work_office",
        "rationale": "Strong conceptually for work, but huge list needs row-level filtering before runtime.",
    },
    "data/books/academic_subjects.json": {
        "recommendation": CANDIDATE_NOT_RUNTIME,
        "target_family": "multiple",
        "rationale": "Could feed science/math/computing/humanities, but raw list is too broad for one topic.",
    },
    "data/books/bestsellers.json": {
        "recommendation": BLOCKED_PROPER_NAMES,
        "target_family": "arts_literature_humanities",
        "rationale": "Book-title list is proper-name/title heavy, not stable humanities vocabulary.",
    },
    "data/art/isms.json": {
        "recommendation": CANDIDATE_NOT_RUNTIME,
        "target_family": "arts_literature_humanities",
        "rationale": "Art/intellectual movements are useful, but broad/ambiguous rows need review.",
    },
    "data/games/fantasy_magics.json": {
        "recommendation": CANDIDATE_NOT_RUNTIME,
        "target_family": "games",
        "rationale": "Fantasy/game-adjacent lexicon, but topic membership is contextual rather than literal games.",
    },
    "data/animals/dog_names.json": {
        "recommendation": BLOCKED_PROPER_NAMES,
        "target_family": "animals",
        "rationale": "Dog-name list creates person/name false positives, not animal vocabulary.",
    },
    "data/animals/dinosaurs.json": {
        "recommendation": BLOCKED_NO_MATCHES,
        "target_family": "animals",
        "rationale": "Mostly rare dinosaur names and no current SPALEX matches in the audit.",
    },
    "data/geography/countries.json": {
        "recommendation": BLOCKED_PROPER_NAMES,
        "target_family": "travel_places_transport",
        "rationale": "Country names are mostly proper-name geography; keep out of lemma-only runtime topics.",
    },
    "data/geography/countries_with_capitals.json": {
        "recommendation": BLOCKED_PROPER_NAMES,
        "target_family": "travel_places_transport",
        "rationale": "Country/capital proper-name list has many homograph traps such as lima and victoria.",
    },
    "data/geography/spanish_regions.json": {
        "recommendation": BLOCKED_PROPER_NAMES,
        "target_family": "travel_places_transport",
        "rationale": "Spanish regions/provinces are mostly proper names and place-name homographs.",
    },
    "data/geography/galician_parishes.json": {
        "recommendation": BLOCKED_PROPER_NAMES,
        "target_family": "travel_places_transport",
        "rationale": "Parish names create severe common-word false positives.",
    },
    "data/geography/named_volcanoes.json": {
        "recommendation": BLOCKED_PROPER_NAMES,
        "target_family": "travel_places_transport",
        "rationale": "Named volcanoes are proper-name heavy and not safe as general travel vocabulary.",
    },
    "data/governments/spain_political_parties.json": {
        "recommendation": BLOCKED_PROPER_NAMES,
        "target_family": "law_politics_civics",
        "rationale": "Political party names/acronyms are proper-name heavy and region-specific.",
    },
    "data/foods/spanish_wines.json": {
        "recommendation": BLOCKED_PROPER_NAMES,
        "target_family": "food_cooking",
        "rationale": "Wine appellation list mostly matches place names, not ordinary food vocabulary.",
    },
    "data/film-tv/popular-movies.json": {
        "recommendation": BLOCKED_PROPER_NAMES,
        "target_family": "music_media_entertainment",
        "rationale": "Movie titles are proper names, not stable topic vocabulary.",
    },
    "data/film-tv/game-of-thrones-houses.json": {
        "recommendation": BLOCKED_PROPER_NAMES,
        "target_family": "anime_manga_pop_culture",
        "rationale": "Fictional house names are proper names and too franchise-specific.",
    },
    "data/film-tv/Westworld_quotes.json": {
        "recommendation": BLOCKED_NOT_TOPIC,
        "target_family": "music_media_entertainment",
        "rationale": "Quotes are sentence content, not a topic-membership vocabulary list.",
    },
    "data/games/dark_souls_iii_messages.json": {
        "recommendation": BLOCKED_NOT_TOPIC,
        "target_family": "games",
        "rationale": "In-game messages are contextual prose; matches are common words, not game-topic evidence.",
    },
    "data/games/chess_openings_regions.json": {
        "recommendation": BLOCKED_PROPER_NAMES,
        "target_family": "games",
        "rationale": "Chess opening region names mostly match countries/places, not chess vocabulary.",
    },
    "data/names/female_names.json": {
        "recommendation": BLOCKED_PROPER_NAMES,
        "target_family": "future_names",
        "rationale": "Name list should not feed ordinary topic preferences.",
    },
    "data/names/male_name..json": {
        "recommendation": BLOCKED_PROPER_NAMES,
        "target_family": "future_names",
        "rationale": "Name list should not feed ordinary topic preferences.",
    },
    "data/mythology/egyptian_gods.json": {
        "recommendation": BLOCKED_NOT_TOPIC,
        "target_family": "arts_literature_humanities",
        "rationale": "Nested deity associations pull common concepts such as time, life, and water.",
    },
    "data/mythology/greek_gods.json": {
        "recommendation": CANDIDATE_NOT_RUNTIME,
        "target_family": "arts_literature_humanities",
        "rationale": "Small mythology name list; keep candidate-only due proper-name semantics.",
    },
    "data/mythology/roman_deities.json": {
        "recommendation": CANDIDATE_NOT_RUNTIME,
        "target_family": "arts_literature_humanities",
        "rationale": "Small mythology name list; keep candidate-only due proper-name semantics.",
    },
    "data/mythology/lovecraft.json": {
        "recommendation": BLOCKED_NOT_TOPIC,
        "target_family": "anime_manga_pop_culture",
        "rationale": "Franchise/prose associations are too contextual for topic rows.",
    },
    "data/music/female_classical_guitarists.json": {
        "recommendation": BLOCKED_PROPER_NAMES,
        "target_family": "music_media_entertainment",
        "rationale": "Person-name list, not music vocabulary.",
    },
    "data/societies_and_groups/semi_secret.json": {
        "recommendation": BLOCKED_PROPER_NAMES,
        "target_family": "arts_literature_humanities",
        "rationale": "Organization names are proper-name heavy.",
    },
    "data/weapons/named_weapons.json": {
        "recommendation": BLOCKED_PROPER_NAMES,
        "target_family": "games",
        "rationale": "Named weapons are proper names; a generic weapons list would be different.",
    },
    "data/words/attitudes.json": {
        "recommendation": BLOCKED_NOT_TOPIC,
        "target_family": "formal_professional_register",
        "rationale": "Attitude adjectives are broad vocabulary/register signals, not a safe topic list.",
    },
    "data/words/nouns.json": {
        "recommendation": BLOCKED_NOT_TOPIC,
        "target_family": "multiple",
        "rationale": "General noun list is not topic evidence.",
    },
    "data/archetypes/character.json": {
        "recommendation": BLOCKED_NOT_TOPIC,
        "target_family": "arts_literature_humanities",
        "rationale": "Character archetype associations pull broad/common words rather than topic vocabulary.",
    },
    "data/divination/zodiac.json": {
        "recommendation": BLOCKED_NOT_TOPIC,
        "target_family": "hobbies_crafts",
        "rationale": "Nested zodiac traits pull personality adjectives, not astrology topic terms.",
    },
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit Lingwars/todosloscorpus static JSON lists for safe en-es SRS topic "
            "overlay use. This is an evidence artifact; it only recommends promotions."
        )
    )
    parser.add_argument("--registry-json", type=Path, default=DEFAULT_REGISTRY_JSON)
    parser.add_argument("--frequency-db", type=Path, default=DEFAULT_FREQUENCY_DB)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        registry_json=args.registry_json,
        frequency_db=args.frequency_db,
        source_root=args.source_root,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_report(
    *,
    registry_json: Path = DEFAULT_REGISTRY_JSON,
    frequency_db: Path = DEFAULT_FREQUENCY_DB,
    source_root: Path | None = None,
    generated_at: str | None = None,
    source_paths: Sequence[str] | None = None,
) -> dict[str, object]:
    registry = _load_json(registry_json)
    frequency_rows = _load_frequency_rows(frequency_db)
    registered_by_path = _registered_sources_by_path(registry)
    paths = list(source_paths) if source_paths is not None else _discover_source_paths()
    rows = [
        _audit_path(
            path=path,
            frequency_rows=frequency_rows,
            registered_source=registered_by_path.get(path),
            source_root=source_root,
        )
        for path in paths
    ]
    status = "ok" if rows and not any(row.get("fetch_error") for row in rows) else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "todosloscorpus_source_candidates_audited"
            if status == "ok"
            else "todosloscorpus_source_candidates_need_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "language_pair": "en-es",
        "source_license": {
            "provider": SOURCE_PROVIDER,
            "declared_license": "CC0",
            "homepage": "https://github.com/Lingwars/todosloscorpus",
            "license_evidence": [
                "README includes CC0 public-domain dedication.",
                "package.json declares license=CC0.",
            ],
        },
        "inputs": {
            "registry_json": _repo_path(registry_json),
            "frequency_db": str(frequency_db),
            "source_root": str(source_root) if source_root else "",
            "tree_url": TREE_URL if source_paths is None else "",
        },
        "summary": _summary(rows),
        "recommendation_policy": {
            "direct_runtime": (
                "Only sources with clean license, literal topic membership, stable extraction, "
                "low high-frequency false-positive risk, and SPALEX exact matches."
            ),
            "candidate_not_runtime": (
                "Useful list source, but requires row-level filters, topic split, or manual review."
            ),
            "blocked": "Proper-name-heavy, prose/contextual, unsupported-topic, or no-match sources.",
        },
        "rows": rows,
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Todos Los Corpus Source Audit",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Sources audited: `{summary.get('source_count', 0)}`",
        f"- Registered sources: `{summary.get('registered_source_count', 0)}`",
        f"- Promotion candidates: `{summary.get('promotion_candidate_count', 0)}`",
        f"- Candidate-only sources: `{summary.get('candidate_only_count', 0)}`",
        f"- Blocked sources: `{summary.get('blocked_count', 0)}`",
        "",
        "## Recommendation Counts",
        "",
        "| Recommendation | Count |",
        "| --- | ---: |",
    ]
    for recommendation, count in sorted(
        _as_mapping(summary.get("counts_by_recommendation")).items()
    ):
        lines.append(f"| `{recommendation}` | {int(count)} |")
    lines.extend(
        [
            "",
            "## Source Matrix",
            "",
            "| Source Path | Registered | Recommendation | Topic | Entries | Matches | Top Risk Matches | Rationale |",
            "| --- | --- | --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for row in _mapping_rows(report.get("rows")):
        risk = ", ".join(
            f"{item.get('lemma')}#{int(item.get('rank') or 0)}"
            for item in _mapping_rows(row.get("top_risk_matches"))[:4]
        )
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{row.get('source_path', '')}`",
                    f"`{row.get('registered_state', '')}`",
                    f"`{row.get('recommendation', '')}`",
                    f"`{row.get('target_family', '')}`",
                    str(row.get("normalized_entry_count", 0)),
                    str(row.get("matched_count", 0)),
                    risk or "-",
                    str(row.get("rationale") or "").replace("|", "/"),
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _audit_path(
    *,
    path: str,
    frequency_rows: Mapping[str, Mapping[str, object]],
    registered_source: Mapping[str, object] | None,
    source_root: Path | None,
) -> dict[str, object]:
    decision = _decision_for_path(path, registered_source)
    source = {
        "id": decision.get("source_id") or _source_id_for_path(path),
        "source_url": path if source_root is not None else RAW_PREFIX + path,
        "extract_fields": decision.get("extract_fields", []),
        "filters": decision.get("filters", {}),
    }
    try:
        payload = _load_source_payload(source, source_root=source_root)
        extracted = _extract_source_entries(
            payload,
            extract_fields=tuple(_string_list(source.get("extract_fields"))) or ("name",),
            filters=_as_mapping(source.get("filters")),
        )
        fetch_error = ""
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        extracted = []
        fetch_error = str(exc)
    normalized_entries = _dedupe_preserve_order(_normalize_lemma(entry) for entry in extracted)
    matches = [
        _match_row(lemma, frequency_rows[lemma])
        for lemma in normalized_entries
        if lemma in frequency_rows
    ]
    matches.sort(key=lambda row: float(row["rank"]))
    return {
        "source_path": path,
        "source_url": RAW_PREFIX + path,
        "registered_source_id": str(_as_mapping(registered_source).get("id") or ""),
        "registered_state": str(
            _as_mapping(registered_source).get("ingest_state") or "unregistered"
        ),
        "recommendation": str(decision.get("recommendation") or ""),
        "target_family": str(decision.get("target_family") or ""),
        "rationale": str(decision.get("rationale") or ""),
        "confidence": decision.get("confidence"),
        "exclude_lemmas": _string_list(decision.get("exclude_lemmas")),
        "fetch_error": fetch_error,
        "input_entry_count": len(extracted),
        "normalized_entry_count": len(normalized_entries),
        "matched_count": len(matches),
        "unmatched_count": max(0, len(normalized_entries) - len(matches)),
        "top_matches": matches[:12],
        "top_risk_matches": [row for row in matches if float(row["rank"]) <= 1500.0][:12],
        "sample_entries": normalized_entries[:12],
    }


def _decision_for_path(
    path: str,
    registered_source: Mapping[str, object] | None,
) -> dict[str, object]:
    if registered_source and str(registered_source.get("ingest_state") or "") == "direct_runtime":
        return {
            "recommendation": "already_direct_runtime",
            "target_family": str(registered_source.get("target_family") or ""),
            "rationale": str(
                registered_source.get("notes") or "Already emitted by source registry."
            ),
            "source_id": str(registered_source.get("id") or ""),
            "extract_fields": registered_source.get("extract_fields", []),
            "filters": registered_source.get("filters", {}),
        }
    if registered_source and path not in MANUAL_DECISIONS:
        return {
            "recommendation": str(registered_source.get("ingest_state") or CANDIDATE_NOT_RUNTIME),
            "target_family": str(registered_source.get("target_family") or ""),
            "rationale": str(registered_source.get("notes") or "Existing registry decision."),
            "source_id": str(registered_source.get("id") or ""),
            "extract_fields": registered_source.get("extract_fields", []),
            "filters": registered_source.get("filters", {}),
        }
    decision = dict(MANUAL_DECISIONS.get(path, {}))
    if decision:
        return decision
    return {
        "recommendation": "manual_review_required",
        "target_family": "",
        "rationale": "No source decision has been recorded yet.",
    }


def _registered_sources_by_path(registry: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    rows: dict[str, Mapping[str, object]] = {}
    for source in _mapping_rows(registry.get("sources")):
        if str(source.get("provider") or "") != SOURCE_PROVIDER:
            continue
        source_url = str(source.get("source_url") or "")
        path = source_url.replace(RAW_PREFIX, "")
        if path.startswith("data/"):
            rows[path] = source
    return rows


def _discover_source_paths() -> list[str]:
    request = Request(TREE_URL, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return sorted(
        str(item.get("path") or "")
        for item in _mapping_rows(payload.get("tree"))
        if item.get("type") == "blob"
        and str(item.get("path") or "").startswith("data/")
        and str(item.get("path") or "").endswith(".json")
    )


def _match_row(lemma: str, frequency: Mapping[str, object]) -> dict[str, object]:
    return {
        "lemma": lemma,
        "rank": _safe_float(frequency.get("source_rank"), default=999999.0),
        "pmw": _safe_float(frequency.get("pmw"), default=0.0),
        "pos_canonical": str(frequency.get("pos_canonical") or ""),
    }


def _summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    counts = Counter(str(row.get("recommendation") or "") for row in rows)
    return {
        "source_count": len(rows),
        "registered_source_count": sum(
            1 for row in rows if str(row.get("registered_state") or "") != "unregistered"
        ),
        "promotion_candidate_count": counts.get(PROMOTE_DIRECT_RUNTIME, 0),
        "candidate_only_count": counts.get(CANDIDATE_NOT_RUNTIME, 0),
        "blocked_count": sum(
            count
            for recommendation, count in counts.items()
            if recommendation.startswith("blocked_")
        ),
        "counts_by_recommendation": dict(sorted(counts.items())),
    }


def _source_id_for_path(path: str) -> str:
    stem = path.removeprefix("data/").removesuffix(".json").replace("/", "_")
    stem = stem.replace("-", "_").replace(".", "_")
    return f"todosloscorpus_{stem}"


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected JSON object at {path}")
    return dict(payload)


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    resolved = path.expanduser()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
