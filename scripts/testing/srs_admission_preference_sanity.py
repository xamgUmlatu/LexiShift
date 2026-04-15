#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import types
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REPORT_VERSION = "srs_admission_preference_sanity_v1"
SYNTHETIC_PAIR = "en-en"


def _load_profile_bootstrap_module() -> object:
    core_root = PROJECT_ROOT / "core" / "lexishift_core"
    srs_root = core_root / "srs"

    lexishift_core_pkg = sys.modules.get("lexishift_core")
    if lexishift_core_pkg is None:
        lexishift_core_pkg = types.ModuleType("lexishift_core")
        lexishift_core_pkg.__path__ = [str(core_root)]  # type: ignore[attr-defined]
        sys.modules["lexishift_core"] = lexishift_core_pkg

    srs_pkg = sys.modules.get("lexishift_core.srs")
    if srs_pkg is None:
        srs_pkg = types.ModuleType("lexishift_core.srs")
        srs_pkg.__path__ = [str(srs_root)]  # type: ignore[attr-defined]
        sys.modules["lexishift_core.srs"] = srs_pkg

    for module_name in ("admission_features", "selector", "profile_bootstrap"):
        full_name = f"lexishift_core.srs.{module_name}"
        if full_name in sys.modules:
            continue
        module_path = srs_root / f"{module_name}.py"
        spec = importlib.util.spec_from_file_location(full_name, module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to load module spec for {full_name}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[full_name] = module
        setattr(srs_pkg, module_name, module)
        spec.loader.exec_module(module)
    return sys.modules["lexishift_core.srs.profile_bootstrap"]


rerank_seed_words_for_profile = _load_profile_bootstrap_module().rerank_seed_words_for_profile


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed(
    *,
    lemma: str,
    admission_weight: float,
    pos_bucket: str = "noun",
    sense_topics: Sequence[str] = (),
) -> SimpleNamespace:
    return SimpleNamespace(
        lemma=lemma,
        language_pair=SYNTHETIC_PAIR,
        admission_weight=admission_weight,
        pos_bucket=pos_bucket,
        metadata={"sense_topics": list(sense_topics)},
    )


def build_seed_pool() -> list[SimpleNamespace]:
    return [
        _seed(lemma="money", admission_weight=0.80, sense_topics=("finance",)),
        _seed(lemma="home", admission_weight=0.76, sense_topics=("daily_life",)),
        _seed(lemma="case", admission_weight=0.72, sense_topics=("general",)),
        _seed(
            lemma="funny", admission_weight=0.66, pos_bucket="adjective", sense_topics=("comedy",)
        ),
        _seed(
            lemma="livestream",
            admission_weight=0.63,
            sense_topics=("streaming", "media"),
        ),
        _seed(lemma="dog", admission_weight=0.60, sense_topics=("animals", "pets")),
        _seed(lemma="elephant", admission_weight=0.56, sense_topics=("animals",)),
        _seed(lemma="fur", admission_weight=0.53, sense_topics=("animals", "body")),
    ]


def _finding(
    *,
    level: str,
    code: str,
    message: str,
    details: str | None = None,
) -> dict[str, Any]:
    return {
        "level": level,
        "code": code,
        "message": message,
        "details": details,
    }


def summarize_findings(findings: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    pass_count = 0
    warn_count = 0
    fail_count = 0
    for item in findings:
        level = str(item.get("level") or "").upper()
        if level == "PASS":
            pass_count += 1
        elif level == "WARN":
            warn_count += 1
        elif level == "FAIL":
            fail_count += 1
    status = "FAIL" if fail_count else "WARN" if warn_count else "PASS"
    return {
        "status": status,
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
    }


def _rank_map(ranked: Sequence[object]) -> dict[str, int]:
    return {
        str(getattr(seed, "lemma", "") or "").strip(): index + 1
        for index, seed in enumerate(ranked)
        if str(getattr(seed, "lemma", "") or "").strip()
    }


def _average_rank(rank_map: Mapping[str, int], lemmas: Sequence[str]) -> float | None:
    values = [rank_map[lemma] for lemma in lemmas if lemma in rank_map]
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def _build_scenario(
    *,
    name: str,
    description: str,
    profile_context: Mapping[str, object],
    focus_lemmas: Sequence[str],
    seeds: Sequence[object],
    preview_limit: int,
) -> dict[str, Any]:
    reranked, diagnostics = rerank_seed_words_for_profile(
        seeds,
        profile_context=profile_context,
        preview_limit=preview_limit,
    )
    rank_map = _rank_map(reranked)
    top_lemmas = [
        str(getattr(seed, "lemma", "") or "").strip() for seed in reranked[:preview_limit]
    ]
    return {
        "name": name,
        "description": description,
        "profile_context": diagnostics["profile_context"],
        "selection_weights": diagnostics["selection_weights"],
        "policy": diagnostics["policy"],
        "focus_lemmas": list(focus_lemmas),
        "top_lemmas": top_lemmas,
        "average_focus_rank": _average_rank(rank_map, focus_lemmas),
        "ranking_preview": diagnostics["ranking_preview"],
    }


def build_report(*, preview_limit: int = 5) -> dict[str, Any]:
    seeds = build_seed_pool()
    base_order = [seed.lemma for seed in seeds]

    scenarios = [
        _build_scenario(
            name="neutral",
            description="No profile signals. Ranking should stay near neutral frequency order.",
            profile_context={},
            focus_lemmas=(),
            seeds=seeds,
            preview_limit=preview_limit,
        ),
        _build_scenario(
            name="explicit_animals",
            description="Explicit `animals` interest should promote animal-related vocabulary.",
            profile_context={"interests": ["animals"]},
            focus_lemmas=("dog", "elephant", "fur"),
            seeds=seeds,
            preview_limit=preview_limit,
        ),
        _build_scenario(
            name="implicit_streaming_comedy",
            description=(
                "Derived implicit topic weights should promote media-related vocabulary "
                "without introducing a new planner contract."
            ),
            profile_context={
                "empirical_trends": {
                    "topic_bias": {
                        "streaming": 0.8,
                        "comedy": 0.65,
                    }
                }
            },
            focus_lemmas=("livestream", "funny"),
            seeds=seeds,
            preview_limit=preview_limit,
        ),
    ]
    scenario_by_name = {scenario["name"]: scenario for scenario in scenarios}

    neutral = scenario_by_name["neutral"]
    explicit_animals = scenario_by_name["explicit_animals"]
    implicit_media = scenario_by_name["implicit_streaming_comedy"]

    neutral_animal_rank = _average_rank(
        _rank_map(seeds),
        explicit_animals["focus_lemmas"],
    )
    animals_rank = explicit_animals["average_focus_rank"]
    neutral_media_rank = _average_rank(
        _rank_map(seeds),
        implicit_media["focus_lemmas"],
    )
    media_rank = implicit_media["average_focus_rank"]

    comparisons = {
        "explicit_animals_vs_neutral": {
            "focus_lemmas": list(explicit_animals["focus_lemmas"]),
            "baseline_average_rank": neutral_animal_rank,
            "scenario_average_rank": animals_rank,
            "average_rank_gain": round((neutral_animal_rank or 0.0) - (animals_rank or 0.0), 6),
        },
        "implicit_streaming_comedy_vs_neutral": {
            "focus_lemmas": list(implicit_media["focus_lemmas"]),
            "baseline_average_rank": neutral_media_rank,
            "scenario_average_rank": media_rank,
            "average_rank_gain": round((neutral_media_rank or 0.0) - (media_rank or 0.0), 6),
        },
    }

    findings: list[dict[str, Any]] = []
    if neutral["top_lemmas"] == base_order[:preview_limit]:
        findings.append(
            _finding(
                level="PASS",
                code="NEUTRAL_ORDER_STABLE",
                message="Neutral profile preserved the neutral seed order.",
                details=", ".join(neutral["top_lemmas"]),
            )
        )
    else:
        findings.append(
            _finding(
                level="FAIL",
                code="NEUTRAL_ORDER_DRIFT",
                message="Neutral profile changed the neutral seed order unexpectedly.",
                details=", ".join(neutral["top_lemmas"]),
            )
        )

    if comparisons["explicit_animals_vs_neutral"]["average_rank_gain"] > 0.0:
        findings.append(
            _finding(
                level="PASS",
                code="EXPLICIT_INTEREST_LIFTS_TOPIC_MATCHES",
                message="Explicit `animals` interest promoted animal-related candidates.",
                details=(
                    "gain=" f"{comparisons['explicit_animals_vs_neutral']['average_rank_gain']}"
                ),
            )
        )
    else:
        findings.append(
            _finding(
                level="FAIL",
                code="EXPLICIT_INTEREST_NO_EFFECT",
                message="Explicit `animals` interest did not improve animal-candidate rank.",
                details=json.dumps(comparisons["explicit_animals_vs_neutral"]),
            )
        )

    explicit_preview = explicit_animals["ranking_preview"][0]
    if "topic_affinity" in str(explicit_preview.get("explanation") or "").lower():
        findings.append(
            _finding(
                level="PASS",
                code="EXPLICIT_PREVIEW_EXPLAINS_TOPIC_BIAS",
                message="Preview explanation surfaced topic-affinity-driven reranking.",
                details=str(explicit_preview.get("explanation") or ""),
            )
        )
    else:
        findings.append(
            _finding(
                level="FAIL",
                code="EXPLICIT_PREVIEW_MISSING_TOPIC_EXPLANATION",
                message="Preview explanation did not surface the topic-affinity lift.",
                details=str(explicit_preview.get("explanation") or ""),
            )
        )

    if comparisons["implicit_streaming_comedy_vs_neutral"]["average_rank_gain"] > 0.0:
        findings.append(
            _finding(
                level="PASS",
                code="IMPLICIT_TOPIC_BIAS_LIFTS_MATCHES",
                message="Derived implicit topic weights promoted media-related candidates.",
                details=(
                    "gain="
                    f"{comparisons['implicit_streaming_comedy_vs_neutral']['average_rank_gain']}"
                ),
            )
        )
    else:
        findings.append(
            _finding(
                level="FAIL",
                code="IMPLICIT_TOPIC_BIAS_NO_EFFECT",
                message="Derived implicit topic weights did not improve media-candidate rank.",
                details=json.dumps(comparisons["implicit_streaming_comedy_vs_neutral"]),
            )
        )

    implicit_source = implicit_media["profile_context"].get("signal_sources", {}).get("interests")
    if implicit_source == "empirical_trends.topic_bias":
        findings.append(
            _finding(
                level="PASS",
                code="IMPLICIT_SIGNAL_SOURCE_IS_DERIVED",
                message="Implicit scenario routed through derived topic-bias normalization.",
                details=implicit_source,
            )
        )
    else:
        findings.append(
            _finding(
                level="FAIL",
                code="IMPLICIT_SIGNAL_SOURCE_UNEXPECTED",
                message="Implicit scenario did not route through the expected normalization seam.",
                details=str(implicit_source),
            )
        )

    findings.append(
        _finding(
            level="PASS",
            code="LIVE_METADATA_COVERAGE_AUDIT_AVAILABLE",
            message=(
                "Synthetic sanity passes the scoring seam, and live frequency-source topic "
                "coverage is now tracked by the dedicated frontier audit."
            ),
        )
    )

    summary = summarize_findings(findings)
    return {
        "version": REPORT_VERSION,
        "generated_at": _now_iso_utc(),
        "pair": SYNTHETIC_PAIR,
        "seed_pool": {
            "size": len(seeds),
            "neutral_order": base_order,
        },
        "scenarios": scenarios,
        "comparisons": comparisons,
        "findings": findings,
        "summary": summary,
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# SRS Admission Preference Sanity",
        "",
        f"- status: {report['summary']['status']}",
        f"- pass_count: {report['summary']['pass_count']}",
        f"- warn_count: {report['summary']['warn_count']}",
        f"- fail_count: {report['summary']['fail_count']}",
        f"- pair: {report['pair']}",
        "",
        "## Findings",
    ]
    for finding in report["findings"]:
        details = f" ({finding['details']})" if finding.get("details") else ""
        lines.append(f"- {finding['level']} `{finding['code']}`: {finding['message']}{details}")

    lines.append("")
    lines.append("## Scenario previews")
    for scenario in report["scenarios"]:
        signal_sources = scenario["profile_context"].get("signal_sources", {})
        active_signals = scenario["profile_context"].get("active_signals", [])
        lines.extend(
            [
                "",
                f"### {scenario['name']}",
                f"- description: {scenario['description']}",
                f"- active_signals: {', '.join(active_signals) if active_signals else 'none'}",
                (
                    "- signal_sources: "
                    f"{json.dumps(signal_sources, ensure_ascii=False, sort_keys=True)}"
                ),
                f"- top_lemmas: {', '.join(scenario['top_lemmas'])}",
                f"- average_focus_rank: {scenario['average_focus_rank']}",
            ]
        )
        for preview in scenario["ranking_preview"][:3]:
            lines.append(
                "- "
                f"{preview['lemma']} [delta={preview['rank_delta']:+}, "
                f"score={preview['profile_score']}]: {preview['explanation']}"
            )
    return "\n".join(lines) + "\n"


def _write_json(path: Path | None, payload: Mapping[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"json_out: {path}")


def _write_markdown(path: Path | None, content: str) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"markdown_out: {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render a deterministic sanity report for neutral and preference-biased "
            "SRS admission reranking."
        )
    )
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--markdown-out", type=Path, default=None)
    parser.add_argument("--preview-limit", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(preview_limit=max(1, int(args.preview_limit)))
    markdown = render_markdown(report)
    _write_json(args.json_out, report)
    _write_markdown(args.markdown_out, markdown)
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 1 if int(report["summary"]["fail_count"]) > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
