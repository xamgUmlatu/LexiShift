#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


from srs_topic_family_depth_audit_config import (  # noqa: E402
    DEFAULT_CURRENT_FREQUENCY_DB,
    DEFAULT_DIFFICULTY_RANKING_CSV,
    DEFAULT_JSON_OUT,
    DEFAULT_KAIKKI_FORWARD_DB,
    DEFAULT_MARKDOWN_OUT,
    DEFAULT_PRIOR_EXPANSION_AUDIT,
    DEFAULT_TAXONOMY,
    DEFAULT_TOP_N,
    DIFFICULTY_BANDS,
    PROJECT_ROOT,
    REGISTER_REVIEW_LABELS,
)

CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.srs.admission_features import normalize_topic_token  # noqa: E402
from lexishift_core.srs.seed import SeedSelectionConfig, build_seed_candidates  # noqa: E402
from srs_topic_family_depth_audit_markdown import render_markdown  # noqa: E402
from srs_topic_source_policy_en_es import (  # noqa: E402
    raw_topic_tokens,
    seed_info as source_seed_info,
    trusted_labels_for_seed,
    trusted_source_exclusion,
    trusted_source_exclusions,
    trusted_source_mappings,
)
from srs_topic_signal_inventory_en_es import load_kaikki_topic_signal_index  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Measure trusted topic-family coverage and difficulty depth for the en-es "
            "SRS preference taxonomy. Read-only; does not write overlays or mutate SRS state."
        )
    )
    parser.add_argument("--taxonomy-json", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--kaikki-forward-db", type=Path, default=DEFAULT_KAIKKI_FORWARD_DB)
    parser.add_argument(
        "--frontier",
        action="append",
        default=[],
        help="Candidate frontier as LABEL=PATH. May be repeated. Defaults to current CDE plus the prior SPALEX research path if known.",
    )
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument(
        "--difficulty-ranking-csv",
        type=Path,
        default=DEFAULT_DIFFICULTY_RANKING_CSV,
        help=(
            "Optional final learner-difficulty ranking CSV with lemma and score columns. "
            "When present, topic depth bands use that calibrated score instead of "
            "1 - admission_weight."
        ),
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    frontiers = (
        [_parse_frontier_arg(value) for value in args.frontier]
        if args.frontier
        else _default_frontiers()
    )
    report = build_report(
        taxonomy_path=args.taxonomy_json,
        kaikki_forward_db=args.kaikki_forward_db,
        difficulty_ranking_csv=args.difficulty_ranking_csv,
        frontiers=frontiers,
        top_n=max(1, int(args.top_n)),
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
    taxonomy_path: Path = DEFAULT_TAXONOMY,
    kaikki_forward_db: Path | None = None,
    difficulty_ranking_csv: Path | None = None,
    frontiers: Sequence[tuple[str, Path, bool]] | None = None,
    top_n: int = DEFAULT_TOP_N,
    generated_at: str | None = None,
) -> dict[str, object]:
    signal_db = kaikki_forward_db or DEFAULT_KAIKKI_FORWARD_DB
    taxonomy = _load_json(taxonomy_path)
    family_rows = _taxonomy_families(taxonomy)
    source_mappings = trusted_source_mappings(taxonomy)
    source_exclusions = trusted_source_exclusions(taxonomy)
    signal_index = load_kaikki_topic_signal_index(signal_db)
    difficulty_index = _load_difficulty_ranking_index(difficulty_ranking_csv)
    frontier_specs = list(frontiers) if frontiers is not None else _default_frontiers()
    audits = [
        audit_frontier(
            label=label,
            frequency_db=path,
            required=required,
            family_rows=family_rows,
            source_mappings=source_mappings,
            source_exclusions=source_exclusions,
            signal_index=signal_index,
            difficulty_scores=_as_mapping(difficulty_index.get("_scores")),
            top_n=top_n,
        )
        for label, path, required in frontier_specs
    ]
    findings = _build_findings(audits=audits, signal_index=signal_index)
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_topic_family_depth_audit_completed"
            if status == "ok"
            else "srs_topic_family_depth_audit_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "inputs": {
            "taxonomy_json": str(Path(taxonomy_path).expanduser().resolve(strict=False)),
            "kaikki_forward_db": str(Path(signal_db).expanduser().resolve(strict=False)),
            "difficulty_ranking_csv": str(
                Path(difficulty_ranking_csv).expanduser().resolve(strict=False)
            )
            if difficulty_ranking_csv is not None
            else "",
            "top_n": int(top_n),
            "frontiers": [
                {"label": label, "frequency_db": str(path), "required": required}
                for label, path, required in frontier_specs
            ],
        },
        "methodology": {
            "runtime_policy_change": "none",
            "helper_state_mutation": "none",
            "source_download": "none",
            "trusted_topic_policy": "taxonomy source_label_mappings over Kaikki/Wiktionary sense_topics and pack topic columns, minus taxonomy source-topic exclusions",
            "register_policy": "review-only allowlisted tag/category inventory; no admission lift",
            "difficulty_source": str(difficulty_index.get("source") or "admission_weight_proxy"),
            "difficulty_proxy": str(difficulty_index.get("proxy") or "1_minus_admission_weight"),
        },
        "taxonomy": {
            "taxonomy_id": str(taxonomy.get("taxonomy_id") or ""),
            "family_count": len(family_rows),
            "families": list(family_rows.values()),
        },
        "signal_source": {
            "path": str(Path(signal_db).expanduser().resolve(strict=False)),
            "exists": bool(signal_index.get("exists")),
        },
        "difficulty_ranking": {
            key: value for key, value in difficulty_index.items() if not key.startswith("_")
        },
        "frontiers": audits,
        "findings": findings,
        "summary": _summary(audits, findings),
        "limitations": [
            "This audit is read-only and does not create overlays, mutate packs, or publish SRS sets.",
            "Trusted family coverage uses explicit sense-topic-style evidence only.",
            "Register/style rows are inventoried as review-only candidates and are not profile-admission proof.",
            (
                "Difficulty depth uses the final learner-difficulty ranking when "
                "a ranking CSV is available; otherwise it falls back to the "
                "admission-weight proxy."
            ),
            "Optional research frontiers are reported as unavailable if their local SQLite path is absent; the audit does not download or rebuild them.",
        ],
    }


def audit_frontier(
    *,
    label: str,
    frequency_db: Path,
    required: bool,
    family_rows: Mapping[str, Mapping[str, object]],
    source_mappings: Mapping[str, Sequence[Mapping[str, object]]],
    source_exclusions: Sequence[Mapping[str, object]],
    signal_index: Mapping[str, object],
    difficulty_scores: Mapping[str, object],
    top_n: int,
) -> dict[str, object]:
    resolved = Path(frequency_db).expanduser().resolve(strict=False)
    if not resolved.exists():
        return {
            "label": label,
            "frequency_db": str(resolved),
            "required": required,
            "exists": False,
            "status": "missing_required" if required else "missing_optional",
            "seed_count": 0,
            "unique_lemma_count": 0,
            "families": _empty_family_reports(family_rows),
        }
    seeds = build_seed_candidates(
        frequency_db=resolved,
        config=SeedSelectionConfig(
            language_pair="en-es",
            top_n=max(1, int(top_n)),
            require_jmdict=False,
            source_label=label,
            sort_by_admission_weight=True,
        ),
    )
    by_channel = _as_mapping(signal_index.get("_by_channel"))
    difficulty_source_counts: Counter[str] = Counter()
    family_accumulators = {
        family_id: _new_family_accumulator(family) for family_id, family in family_rows.items()
    }
    for seed_index, seed in enumerate(seeds, start=1):
        seed_info = _seed_info_with_difficulty(
            seed,
            seed_index,
            difficulty_scores=difficulty_scores,
        )
        difficulty_source_counts[str(seed_info.get("difficulty_source") or "unknown")] += 1
        lemma = seed_info["lemma"]
        trusted_labels = trusted_labels_for_seed(seed, lemma=lemma, by_channel=by_channel)
        trusted_matches_by_family: dict[str, dict[str, object]] = {}
        for label_token in trusted_labels:
            for mapping in source_mappings.get(label_token, ()):
                family_id = str(mapping.get("target_family") or "")
                if family_id not in family_accumulators:
                    continue
                exclusion = trusted_source_exclusion(
                    source_exclusions,
                    lemma=lemma,
                    seed_info=seed_info,
                    source_label=label_token,
                    target_family=family_id,
                )
                if exclusion:
                    _add_excluded_family_match(
                        family_accumulators[family_id],
                        seed_info=seed_info,
                        source_label=label_token,
                        reason=str(exclusion.get("reason") or ""),
                    )
                    continue
                score = _float(mapping.get("weight")) * _float(mapping.get("confidence"))
                match = trusted_matches_by_family.setdefault(
                    family_id,
                    {"score": 0.0, "source_labels": []},
                )
                match["score"] = max(_float(match.get("score")), score)
                source_labels = match.get("source_labels")
                if isinstance(source_labels, list) and label_token not in source_labels:
                    source_labels.append(label_token)
        for family_id, match in trusted_matches_by_family.items():
            source_labels = [
                str(label) for label in match.get("source_labels", []) if str(label).strip()
            ]
            if source_labels:
                _add_trusted_family_hit(
                    family_accumulators[family_id],
                    seed_info=seed_info,
                    source_labels=source_labels,
                    score=_float(match.get("score")),
                )
        for family_id, channel_rules in REGISTER_REVIEW_LABELS.items():
            if family_id not in family_accumulators:
                continue
            matches = _register_review_matches(
                lemma=lemma,
                channel_rules=channel_rules,
                by_channel=by_channel,
            )
            for source_channel, source_label in matches:
                _add_review_only_family_hit(
                    family_accumulators[family_id],
                    seed_info=seed_info,
                    source_channel=source_channel,
                    source_label=source_label,
                )
    family_reports = [
        _finalize_family_report(accumulator, total_candidates=len(seeds))
        for accumulator in family_accumulators.values()
    ]
    family_reports.sort(
        key=lambda row: (
            _axis_sort(row.get("axis")),
            -int(row.get("trusted_candidate_count") or 0),
            -int(row.get("review_only_candidate_count") or 0),
            str(row.get("family") or ""),
        )
    )
    return {
        "label": label,
        "frequency_db": str(resolved),
        "required": required,
        "exists": True,
        "status": "ok",
        "seed_count": len(seeds),
        "unique_lemma_count": len({str(getattr(seed, "lemma", "") or "") for seed in seeds}),
        "difficulty_source_counts": dict(difficulty_source_counts),
        "families": family_reports,
    }


def _taxonomy_families(taxonomy: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    families: dict[str, Mapping[str, object]] = {}
    for row in _mapping_rows(taxonomy.get("families")):
        family_id = normalize_topic_token(row.get("id"))
        if not family_id:
            continue
        families[family_id] = {
            "family": family_id,
            "display_name": str(row.get("display_name") or family_id),
            "axis": normalize_topic_token(row.get("axis")) or "topic",
            "ux_group": normalize_topic_token(row.get("ux_group")) or "",
            "pair_scope": str(row.get("pair_scope") or ""),
            "product_priority": str(row.get("product_priority") or ""),
            "readiness_state": str(row.get("readiness_state") or ""),
            "data_strategy": str(row.get("data_strategy") or ""),
        }
    return families


def _new_family_accumulator(family: Mapping[str, object]) -> dict[str, object]:
    return {
        "family": family,
        "trusted_lemmas": set(),
        "trusted_source_counter": Counter(),
        "trusted_excluded_counter": Counter(),
        "trusted_excluded_examples": [],
        "trusted_hits": [],
        "trusted_bands": [
            _new_band(label, lower, upper) for label, lower, upper in DIFFICULTY_BANDS
        ],
        "review_lemmas": set(),
        "review_source_counter": Counter(),
        "review_hits": [],
        "review_bands": [
            _new_band(label, lower, upper) for label, lower, upper in DIFFICULTY_BANDS
        ],
    }


def _add_excluded_family_match(
    accumulator: dict[str, object],
    *,
    seed_info: Mapping[str, object],
    source_label: str,
    reason: str,
) -> None:
    counter = accumulator.get("trusted_excluded_counter")
    if isinstance(counter, Counter):
        counter[source_label] += 1
    examples = accumulator.get("trusted_excluded_examples")
    if isinstance(examples, list) and len(examples) < 12:
        examples.append(
            {
                "lemma": seed_info.get("lemma"),
                "seed_rank": seed_info.get("seed_rank"),
                "difficulty": seed_info.get("difficulty"),
                "pos_bucket": seed_info.get("pos_bucket"),
                "source_label": source_label,
                "reason": reason,
            }
        )


def _new_band(label: str, lower: float, upper: float) -> dict[str, object]:
    return {"band": label, "lower": lower, "upper": upper, "count": 0, "examples": []}


def _add_trusted_family_hit(
    accumulator: dict[str, object],
    *,
    seed_info: Mapping[str, object],
    source_labels: Sequence[str],
    score: float,
) -> None:
    lemma = str(seed_info.get("lemma") or "")
    if not lemma:
        return
    trusted_lemmas = accumulator["trusted_lemmas"]
    if not isinstance(trusted_lemmas, set):
        return
    trusted_lemmas.add(lemma)
    counter = accumulator["trusted_source_counter"]
    if isinstance(counter, Counter):
        for source_label in source_labels:
            counter[source_label] += 1
    hit = dict(seed_info)
    hit["source_labels"] = list(source_labels)
    hit["score"] = round(score, 6)
    _append_unique_hit(accumulator["trusted_hits"], hit)
    _increment_band(
        accumulator["trusted_bands"],
        seed_info,
        source_label=",".join(source_labels),
    )


def _add_review_only_family_hit(
    accumulator: dict[str, object],
    *,
    seed_info: Mapping[str, object],
    source_channel: str,
    source_label: str,
) -> None:
    lemma = str(seed_info.get("lemma") or "")
    if not lemma:
        return
    review_lemmas = accumulator["review_lemmas"]
    if not isinstance(review_lemmas, set):
        return
    review_lemmas.add(lemma)
    counter = accumulator["review_source_counter"]
    if isinstance(counter, Counter):
        counter[f"{source_channel}:{source_label}"] += 1
    hit = dict(seed_info)
    hit["source_labels"] = [f"{source_channel}:{source_label}"]
    _append_unique_hit(accumulator["review_hits"], hit)
    _increment_band(
        accumulator["review_bands"],
        seed_info,
        source_label=f"{source_channel}:{source_label}",
    )


def _append_unique_hit(target: object, hit: Mapping[str, object]) -> None:
    if not isinstance(target, list):
        return
    lemma = str(hit.get("lemma") or "")
    existing = next((row for row in target if row.get("lemma") == lemma), None)
    if isinstance(existing, dict):
        existing_labels = list(existing.get("source_labels") or [])
        for label in hit.get("source_labels") or []:
            if label not in existing_labels:
                existing_labels.append(label)
        existing["source_labels"] = existing_labels
        existing["score"] = max(_float(existing.get("score")), _float(hit.get("score")))
        return
    target.append(dict(hit))


def _increment_band(
    bands: object,
    seed_info: Mapping[str, object],
    *,
    source_label: str,
) -> None:
    if not isinstance(bands, list):
        return
    difficulty = _float(seed_info.get("difficulty"))
    index = _band_index(difficulty)
    band = bands[index]
    band["count"] = int(band.get("count") or 0) + 1
    examples = band.get("examples")
    if isinstance(examples, list) and len(examples) < 5:
        examples.append(
            {
                "lemma": seed_info.get("lemma"),
                "difficulty": seed_info.get("difficulty"),
                "source_label": source_label,
            }
        )


def _finalize_family_report(
    accumulator: Mapping[str, object],
    *,
    total_candidates: int,
) -> dict[str, object]:
    family = _as_mapping(accumulator.get("family"))
    trusted_hits = _mapping_rows(accumulator.get("trusted_hits"))
    review_hits = _mapping_rows(accumulator.get("review_hits"))
    trusted_hits.sort(
        key=lambda row: (
            -_float(row.get("score")),
            _float(row.get("difficulty")),
            int(row.get("seed_rank") or 0),
        )
    )
    review_hits.sort(
        key=lambda row: (_float(row.get("difficulty")), int(row.get("seed_rank") or 0))
    )
    trusted_lemmas = accumulator.get("trusted_lemmas")
    review_lemmas = accumulator.get("review_lemmas")
    trusted_count = len(trusted_lemmas) if isinstance(trusted_lemmas, set) else 0
    review_count = len(review_lemmas) if isinstance(review_lemmas, set) else 0
    trusted_bands = _finalize_bands(accumulator.get("trusted_bands"))
    review_bands = _finalize_bands(accumulator.get("review_bands"))
    trusted_max_difficulty = (
        max((_float(row.get("difficulty")) for row in trusted_hits), default=None)
        if trusted_hits
        else None
    )
    return {
        **family,
        "trusted_candidate_count": trusted_count,
        "trusted_candidate_share": _ratio(trusted_count, total_candidates),
        "trusted_nonempty_band_count": sum(1 for row in trusted_bands if int(row["count"]) > 0),
        "trusted_max_difficulty": (
            round(float(trusted_max_difficulty), 6) if trusted_max_difficulty is not None else None
        ),
        "trusted_bands": trusted_bands,
        "trusted_top_source_labels": _counter_rows(accumulator.get("trusted_source_counter")),
        "trusted_excluded_source_labels": _counter_rows(
            accumulator.get("trusted_excluded_counter")
        ),
        "trusted_excluded_examples": _mapping_rows(accumulator.get("trusted_excluded_examples")),
        "trusted_top_examples": [_public_hit(row) for row in trusted_hits[:8]],
        "trusted_hardest_examples": [
            _public_hit(row)
            for row in sorted(trusted_hits, key=lambda row: -_float(row.get("difficulty")))[:8]
        ],
        "review_only_candidate_count": review_count,
        "review_only_candidate_share": _ratio(review_count, total_candidates),
        "review_only_bands": review_bands,
        "review_only_top_labels": _counter_rows(accumulator.get("review_source_counter")),
        "review_only_examples": [_public_hit(row) for row in review_hits[:8]],
        "coverage_posture": _coverage_posture(
            family=family,
            trusted_count=trusted_count,
            review_count=review_count,
            nonempty_band_count=sum(1 for row in trusted_bands if int(row["count"]) > 0),
            trusted_max_difficulty=trusted_max_difficulty,
        ),
    }


def _coverage_posture(
    *,
    family: Mapping[str, object],
    trusted_count: int,
    review_count: int,
    nonempty_band_count: int,
    trusted_max_difficulty: float | None,
) -> str:
    axis = str(family.get("axis") or "")
    if axis == "register":
        if review_count > 0:
            return "review_only_signal_available"
        return "review_only_signal_absent"
    if trusted_count <= 0:
        return "no_trusted_coverage"
    if trusted_count < 10:
        return "thin_trusted_coverage"
    if nonempty_band_count <= 1 or (
        trusted_max_difficulty is not None and trusted_max_difficulty < 0.4
    ):
        return "shallow_difficulty_depth"
    return "measurable_trusted_coverage"


def _register_review_matches(
    *,
    lemma: str,
    channel_rules: Mapping[str, Sequence[str]],
    by_channel: Mapping[str, object],
) -> list[tuple[str, str]]:
    matches: list[tuple[str, str]] = []
    for channel, allowed_labels in channel_rules.items():
        allowed = {normalize_topic_token(label) for label in allowed_labels}
        lemma_signals = _as_mapping(by_channel.get(channel))
        labels = raw_topic_tokens(lemma_signals.get(lemma))
        for label in labels:
            if label in allowed:
                matches.append((channel, label))
    return sorted(dict.fromkeys(matches))


def _finalize_bands(value: object) -> list[dict[str, object]]:
    bands = value if isinstance(value, list) else []
    return [
        {
            "band": str(row.get("band") or ""),
            "lower": _float(row.get("lower")),
            "upper": _float(row.get("upper")),
            "count": int(row.get("count") or 0),
            "examples": _mapping_rows(row.get("examples")),
        }
        for row in _mapping_rows(bands)
    ]


def _empty_family_reports(
    family_rows: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    return [
        _finalize_family_report(_new_family_accumulator(family), total_candidates=0)
        for family in family_rows.values()
    ]


def _seed_info_with_difficulty(
    seed: object,
    seed_rank: int,
    *,
    difficulty_scores: Mapping[str, object],
) -> dict[str, object]:
    seed_info = source_seed_info(seed, seed_rank)
    lemma = _normalize_lemma(seed_info.get("lemma"))
    calibrated = _optional_float(difficulty_scores.get(lemma))
    if calibrated is None:
        seed_info["difficulty_source"] = "admission_weight_proxy"
        return seed_info
    seed_info["admission_difficulty"] = seed_info.get("difficulty")
    seed_info["difficulty"] = round(max(0.0, min(1.0, calibrated)), 6)
    seed_info["difficulty_source"] = "corrected_learner_difficulty_ranking"
    return seed_info


def _load_difficulty_ranking_index(path: Path | None) -> dict[str, object]:
    if path is None:
        return {
            "source": "admission_weight_proxy",
            "proxy": "1_minus_admission_weight",
            "exists": False,
            "path": "",
            "score_count": 0,
            "_scores": {},
        }
    resolved = Path(path).expanduser().resolve(strict=False)
    if not resolved.exists():
        return {
            "source": "admission_weight_proxy",
            "proxy": "1_minus_admission_weight",
            "exists": False,
            "path": str(resolved),
            "score_count": 0,
            "_scores": {},
        }
    scores: dict[str, float] = {}
    malformed_rows = 0
    with resolved.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            lemma = _normalize_lemma(row.get("lemma"))
            score = _optional_float(row.get("score"))
            if not lemma or score is None:
                malformed_rows += 1
                continue
            scores[lemma] = max(0.0, min(1.0, score))
    return {
        "source": "corrected_learner_difficulty_ranking",
        "proxy": "final_ranking_score",
        "exists": True,
        "path": str(resolved),
        "score_count": len(scores),
        "malformed_row_count": malformed_rows,
        "_scores": scores,
    }


def _build_findings(
    *,
    audits: Sequence[Mapping[str, object]],
    signal_index: Mapping[str, object],
) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    if signal_index.get("exists"):
        findings.append(
            _finding(
                "PASS", "kaikki_signal_source_available", "Kaikki/Wiktionary signal DB exists."
            )
        )
    else:
        findings.append(
            _finding(
                "FAIL", "kaikki_signal_source_missing", "Kaikki/Wiktionary signal DB is missing."
            )
        )
    for audit in audits:
        label = str(audit.get("label") or "frontier")
        if not audit.get("exists"):
            level = "FAIL" if audit.get("required") else "WARN"
            findings.append(
                _finding(
                    level,
                    f"frontier_missing:{label}",
                    "Candidate frontier SQLite is missing.",
                )
            )
            continue
        families = _mapping_rows(audit.get("families"))
        trusted_with_rows = [
            row
            for row in families
            if row.get("axis") == "topic" and int(row.get("trusted_candidate_count") or 0) > 0
        ]
        if trusted_with_rows:
            findings.append(
                _finding(
                    "PASS",
                    f"trusted_topic_families_available:{label}",
                    "At least one topic family has trusted candidate coverage.",
                )
            )
        else:
            findings.append(
                _finding(
                    "WARN",
                    f"trusted_topic_families_absent:{label}",
                    "No topic family has trusted candidate coverage.",
                )
            )
        register_rows = [
            row
            for row in families
            if row.get("axis") == "register"
            and int(row.get("review_only_candidate_count") or 0) > 0
        ]
        if register_rows:
            findings.append(
                _finding(
                    "PASS",
                    f"register_review_signals_available:{label}",
                    "Register/style has review-only candidate signals.",
                )
            )
        else:
            findings.append(
                _finding(
                    "WARN",
                    f"register_review_signals_absent:{label}",
                    "No register/style review-only signals were found.",
                )
            )
    return findings


def _summary(
    audits: Sequence[Mapping[str, object]],
    findings: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    family_postures = Counter()
    for audit in audits:
        if not audit.get("exists"):
            continue
        for family in _mapping_rows(audit.get("families")):
            family_postures[str(family.get("coverage_posture") or "")] += 1
    return {
        "frontier_count": len(audits),
        "available_frontier_count": sum(1 for audit in audits if audit.get("exists")),
        "missing_optional_frontier_count": sum(
            1 for audit in audits if not audit.get("exists") and not audit.get("required")
        ),
        "finding_counts": dict(Counter(str(row.get("level") or "") for row in findings)),
        "family_posture_counts": dict(family_postures),
        "issues": [row.get("code") for row in findings if row.get("level") == "FAIL"],
        "warnings": [row.get("code") for row in findings if row.get("level") == "WARN"],
    }


def _default_frontiers() -> list[tuple[str, Path, bool]]:
    frontiers = [("current_cde", DEFAULT_CURRENT_FREQUENCY_DB, True)]
    expansion_path = _prior_expansion_frequency_db()
    if expansion_path is not None:
        frontiers.append(("spalex_10k_research", expansion_path, False))
    return frontiers


def _prior_expansion_frequency_db() -> Path | None:
    if not DEFAULT_PRIOR_EXPANSION_AUDIT.exists():
        return None
    try:
        payload = json.loads(DEFAULT_PRIOR_EXPANSION_AUDIT.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    path_text = str(_as_mapping(payload.get("inputs")).get("frequency_db") or "").strip()
    return Path(path_text) if path_text else None


def _parse_frontier_arg(value: str) -> tuple[str, Path, bool]:
    text = str(value or "").strip()
    required = True
    if text.startswith("optional:"):
        required = False
        text = text.removeprefix("optional:")
    if "=" in text:
        label, path_text = text.split("=", 1)
        return label.strip() or Path(path_text).stem, Path(path_text).expanduser(), required
    path = Path(text).expanduser()
    return path.stem, path, required


def _load_json(path: Path) -> Mapping[str, object]:
    return _as_mapping(json.loads(Path(path).expanduser().read_text(encoding="utf-8")))


def _band_index(difficulty: float) -> int:
    for index, (_label, lower, upper) in enumerate(DIFFICULTY_BANDS):
        if index == len(DIFFICULTY_BANDS) - 1:
            if lower <= difficulty <= upper:
                return index
        elif lower <= difficulty < upper:
            return index
    return len(DIFFICULTY_BANDS) - 1


def _public_hit(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "lemma": row.get("lemma"),
        "seed_rank": row.get("seed_rank"),
        "difficulty": row.get("difficulty"),
        "difficulty_source": row.get("difficulty_source"),
        "admission_difficulty": row.get("admission_difficulty"),
        "admission_weight": row.get("admission_weight"),
        "pos_bucket": row.get("pos_bucket"),
        "source_labels": list(row.get("source_labels") or []),
        "score": row.get("score"),
    }


def _axis_sort(value: object) -> int:
    return {"topic": 0, "register": 1}.get(str(value or ""), 9)


def _counter_rows(value: object, *, limit: int = 12) -> list[dict[str, object]]:
    if not isinstance(value, Counter):
        return []
    return [
        {"label": label, "count": count} for label, count in value.most_common(max(1, int(limit)))
    ]


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _float(value: object) -> float:
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return 0.0
    return 0.0


def _optional_float(value: object) -> float | None:
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _normalize_lemma(value: object) -> str:
    return str(value or "").strip().lower()


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
