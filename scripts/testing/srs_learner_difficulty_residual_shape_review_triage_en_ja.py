#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_proficiency_ordering_en_ja import (  # noqa: E402
    _escape,
    _load_json,
    _mapping,
    _optional_float,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _utc_now,
)


PAIR = "en-ja"
DEFAULT_REVIEW_PACK_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_residual_shape_review_pack_en_ja_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_residual_shape_review_triage_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_residual_shape_review_triage_en_ja_latest.md"
)

LOW_FREQUENCY_DIFFICULTY_MAX = 0.80
TAIL_FREQUENCY_DIFFICULTY_MIN = 0.95
HIGH_JMDICT_PRIORITY_RISK_MIN = 0.75
HIGH_WRITTEN_BURDEN_MIN = 0.70
HIGH_KANJI_BURDEN_MIN = 0.85
HIGH_WAGO_EASE_MIN = 0.75
HIGH_RARE_WAGO_TAIL_MIN = 0.70
HIGH_MARKED_RISK_MIN = 0.75

DOMAIN_GLOSS_KEYWORDS = (
    "aboard a warship",
    "branchial",
    "castle town",
    "chemistry",
    "civil war",
    "dew point",
    "electricity",
    "family register",
    "fief",
    "geisha",
    "gill",
    "indigo",
    "leprosy",
    "nevus",
    "papal",
    "photophobia",
    "president",
    "rhododendron",
    "russia",
    "sexagenary",
    "sleigh",
    "taxonomical",
    "temple",
    "warship",
    "warring states",
    "wheat gluten",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Triage the residual-shape blind review pack into source-supported "
            "review routes. This does not create calibration labels."
        )
    )
    parser.add_argument("--review-pack-json", type=Path, default=DEFAULT_REVIEW_PACK_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    review_pack_path = _resolve_path(args.review_pack_json)
    report = build_report(review_pack_path=review_pack_path)
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    return 0


def build_report(*, review_pack_path: Path) -> dict[str, object]:
    review_pack = _load_json(review_pack_path)
    rows = [
        _triage_row(index, _mapping(row))
        for index, row in enumerate(
            review_pack.get("review_rows") or (),
            start=1,
        )
    ]
    by_route = Counter(str(row["review_route"]) for row in rows)
    by_tag = Counter(str(tag["tag"]) for row in rows for tag in row.get("triage_tags") or ())
    by_bucket_route: dict[str, dict[str, int]] = defaultdict(dict)
    for row in rows:
        bucket = str(row.get("review_bucket") or "")
        route = str(row.get("review_route") or "")
        by_bucket_route[bucket][route] = by_bucket_route[bucket].get(route, 0) + 1
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "calibration_labels_changed": False,
        "method": {
            "purpose": (
                "Route the blind review rows into source-supported questions that "
                "map directly to model-shape decisions after human labels arrive."
            ),
            "important_limit": (
                "Routes are deterministic triage hints from existing source "
                "signals and JMDict text. They are not target difficulty labels."
            ),
        },
        "inputs": {
            "review_pack_json": _repo_or_home_path(review_pack_path),
            "review_rows": len(rows),
        },
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={"review_pack_json": review_pack_path},
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "review_pack": SCRIPT_DIR
                / "srs_learner_difficulty_residual_shape_review_pack_en_ja.py",
            },
            version_constants={},
            argv=sys.argv,
        ),
        "counts": {
            "review_rows": len(rows),
            "by_route": dict(sorted(by_route.items())),
            "by_tag": dict(sorted(by_tag.items())),
            "by_bucket_route": {
                bucket: dict(sorted(routes.items()))
                for bucket, routes in sorted(by_bucket_route.items())
            },
        },
        "review_questions": _review_questions(),
        "triage_rows": rows,
    }


def _triage_row(index: int, row: Mapping[str, object]) -> dict[str, object]:
    tags = _triage_tags(row)
    route = _review_route(tags)
    return {
        "row_number": index,
        "review_bucket": row.get("review_bucket"),
        "lemma": row.get("lemma"),
        "reading": row.get("reading"),
        "gloss": "; ".join(str(value) for value in row.get("jmdict_glosses") or ()),
        "pos": "; ".join(str(value) for value in row.get("jmdict_pos") or ()),
        "jmdict_match": row.get("jmdict_match"),
        "jlpt_vocab_level": row.get("jlpt_vocab_level"),
        "source_signals": row.get("source_signals") or {},
        "triage_tags": tags,
        "review_route": route,
        "review_priority": _review_priority(route, tags),
        "model_question": _model_question(route),
    }


def _triage_tags(row: Mapping[str, object]) -> list[dict[str, object]]:
    signals = _mapping(row.get("source_signals"))
    gloss = " ".join(str(value) for value in row.get("jmdict_glosses") or ())
    lower_gloss = gloss.lower()
    tags = []
    if str(row.get("jmdict_match") or "") != "exact_reading":
        tags.append(
            _tag(
                "source_reading_mismatch",
                f"JMDict match is `{row.get('jmdict_match')}`.",
            )
        )
    jlpt = _optional_float(row.get("jlpt_vocab_level"))
    if jlpt is not None:
        tags.append(_tag("known_curriculum_word", f"JLPT vocabulary level `{_rounded(jlpt)}`."))
    frequency = _signal(signals, "frequency")
    if frequency is not None and frequency <= LOW_FREQUENCY_DIFFICULTY_MAX:
        tags.append(
            _tag(
                "low_frequency_difficulty_signal",
                f"frequency difficulty signal `{_rounded(frequency)}`.",
            )
        )
    if frequency is not None and frequency >= TAIL_FREQUENCY_DIFFICULTY_MIN:
        tags.append(
            _tag(
                "tail_frequency_difficulty_signal",
                f"frequency difficulty signal `{_rounded(frequency)}`.",
            )
        )
    jmdict_priority = _signal(signals, "jmdict_priority")
    if jmdict_priority is not None and jmdict_priority >= HIGH_JMDICT_PRIORITY_RISK_MIN:
        tags.append(
            _tag(
                "low_jmdict_priority_signal",
                f"JMDict priority risk signal `{_rounded(jmdict_priority)}`.",
            )
        )
    wtype_wago = _signal(signals, "wtype_wago_ease")
    rare_wago = _signal(signals, "rare_wago_tail_risk")
    written_burden = _signal(signals, "max_written_form_burden")
    kanji_burden = _signal(signals, "max_kanji_burden")
    if (
        wtype_wago is not None
        and wtype_wago >= HIGH_WAGO_EASE_MIN
        and rare_wago is not None
        and rare_wago >= HIGH_RARE_WAGO_TAIL_MIN
    ):
        tags.append(
            _tag(
                "rare_wago_orthography",
                "wago ease is high and rare-wago-tail risk is high.",
            )
        )
    if (
        wtype_wago is not None
        and wtype_wago >= HIGH_WAGO_EASE_MIN
        and written_burden is not None
        and written_burden >= HIGH_WRITTEN_BURDEN_MIN
    ):
        tags.append(
            _tag(
                "wago_written_form_stress",
                f"wago ease plus max written-form burden `{_rounded(written_burden)}`.",
            )
        )
    if (
        _signal(signals, "wtype_kango_risk") is not None
        and _signal(signals, "wtype_kango_risk") >= HIGH_JMDICT_PRIORITY_RISK_MIN
        and written_burden is not None
        and written_burden >= HIGH_WRITTEN_BURDEN_MIN
    ):
        tags.append(
            _tag(
                "kango_written_form_stress",
                f"kango risk plus max written-form burden `{_rounded(written_burden)}`.",
            )
        )
    if kanji_burden is not None and kanji_burden >= HIGH_KANJI_BURDEN_MIN:
        tags.append(
            _tag(
                "high_kanji_burden",
                f"max kanji burden `{_rounded(kanji_burden)}`.",
            )
        )
    for signal_name in ("jmdict_marked_usage_risk", "jmdict_register_marked_risk"):
        marked = _signal(signals, signal_name)
        if marked is not None and marked >= HIGH_MARKED_RISK_MIN:
            tags.append(_tag("marked_usage_or_register", f"{signal_name}=`{_rounded(marked)}`."))
            break
    domain_hits = [keyword for keyword in DOMAIN_GLOSS_KEYWORDS if keyword in lower_gloss]
    if domain_hits:
        tags.append(
            _tag(
                "domain_or_topic_gloss",
                f"gloss keyword(s): {', '.join(domain_hits[:3])}.",
            )
        )
    if not tags:
        tags.append(_tag("ordinary_shape_probe", "No special triage signal fired."))
    return tags


def _tag(tag: str, evidence: str) -> dict[str, object]:
    return {"tag": tag, "evidence": evidence}


def _review_route(tags: Sequence[Mapping[str, object]]) -> str:
    tag_names = {str(tag.get("tag") or "") for tag in tags}
    if "source_reading_mismatch" in tag_names:
        return "source_review_first"
    if "known_curriculum_word" in tag_names and "low_frequency_difficulty_signal" in tag_names:
        return "possible_overhard_general_vocab"
    if "rare_wago_orthography" in tag_names or "wago_written_form_stress" in tag_names:
        return "wago_form_policy_review"
    if "marked_usage_or_register" in tag_names:
        return "usage_register_policy_review"
    if (
        "tail_frequency_difficulty_signal" in tag_names
        and "low_jmdict_priority_signal" in tag_names
    ) or "domain_or_topic_gloss" in tag_names:
        return "tail_topic_or_omit_review"
    if "kango_written_form_stress" in tag_names or "high_kanji_burden" in tag_names:
        return "burden_shape_review"
    return "ordinary_shape_review"


def _review_priority(route: str, tags: Sequence[Mapping[str, object]]) -> str:
    tag_names = {str(tag.get("tag") or "") for tag in tags}
    if route in {
        "possible_overhard_general_vocab",
        "source_review_first",
        "wago_form_policy_review",
    }:
        return "high"
    if route == "tail_topic_or_omit_review" and "tail_frequency_difficulty_signal" in tag_names:
        return "high"
    if route in {"usage_register_policy_review", "burden_shape_review"}:
        return "medium"
    return "low"


def _model_question(route: str) -> str:
    return {
        "source_review_first": (
            "Should the source reading/form be normalized before this item is rankable?"
        ),
        "possible_overhard_general_vocab": (
            "Should curriculum/frequency evidence cap high written-form or kanji burden?"
        ),
        "wago_form_policy_review": (
            "Should rare written-form burden be separated from core word familiarity for wago?"
        ),
        "usage_register_policy_review": (
            "Should marked usage/register move the item out of ordinary rankable vocab?"
        ),
        "tail_topic_or_omit_review": (
            "Should this be late vocab, topic-only, or omitted rather than globally ranked?"
        ),
        "burden_shape_review": ("Should high written/kanji burden alone move this region later?"),
        "ordinary_shape_review": ("Does this row confirm or reject the current bucket placement?"),
    }.get(route, "Does this row confirm or reject the current bucket placement?")


def _review_questions() -> list[dict[str, object]]:
    return [
        {
            "route": "possible_overhard_general_vocab",
            "decision_if_reviewers_score_low": (
                "Add a bounded downshift or cap when curriculum/frequency says the word is common."
            ),
        },
        {
            "route": "wago_form_policy_review",
            "decision_if_reviewers_split": (
                "Separate word familiarity from rare displayed spelling or preferred-form effects."
            ),
        },
        {
            "route": "tail_topic_or_omit_review",
            "decision_if_reviewers_choose_topic_or_omit": (
                "Improve admission/classification gates before trying another numeric scalar."
            ),
        },
        {
            "route": "source_review_first",
            "decision_if_confirmed": (
                "Fix reading/form normalization before using the row as learner-difficulty evidence."
            ),
        },
    ]


def _signal(signals: Mapping[str, object], name: str) -> float | None:
    return _optional_float(signals.get(name))


def render_markdown(report: Mapping[str, object]) -> str:
    counts = _mapping(report.get("counts"))
    lines = [
        "# en-ja Residual-Shape Review Triage",
        "",
        (
            "This artifact routes the blind review rows into source-supported "
            "review questions. It is not a calibration file and does not assign "
            "target difficulty values."
        ),
        "",
        "## Summary",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Review rows: `{_escape(counts.get('review_rows'))}`",
        "- Calibration labels changed: `False`",
        "",
        "## Route Counts",
        "",
        "| Route | Count |",
        "| --- | ---: |",
    ]
    for route, count in _mapping(counts.get("by_route")).items():
        lines.append(f"| `{_escape(route)}` | `{_escape(count)}` |")
    lines.extend(
        [
            "",
            "## What Review Decides",
            "",
            "| Route | If reviewers agree, next model action |",
            "| --- | --- |",
        ]
    )
    for question in report.get("review_questions") or ():
        row = _mapping(question)
        lines.append(
            "| "
            f"`{_escape(row.get('route'))}` | "
            f"{_escape(row.get('decision_if_reviewers_score_low') or row.get('decision_if_reviewers_split') or row.get('decision_if_reviewers_choose_topic_or_omit') or row.get('decision_if_confirmed'))} |"
        )
    lines.extend(
        [
            "",
            "## Rows",
            "",
            _rows_table(report.get("triage_rows") or ()),
            "",
        ]
    )
    return "\n".join(lines)


def _rows_table(rows: Sequence[Mapping[str, object]]) -> str:
    header = (
        "| # | bucket | lemma | reading | route | priority | tags | model question |\n"
        "|---:|---|---|---|---|---|---|---|"
    )
    body = []
    for row in rows:
        tags = "; ".join(str(tag.get("tag") or "") for tag in row.get("triage_tags") or ())
        body.append(
            "| "
            + " | ".join(
                [
                    _escape(row.get("row_number")),
                    _escape(row.get("review_bucket")),
                    _escape(row.get("lemma")),
                    _escape(row.get("reading")),
                    _escape(row.get("review_route")),
                    _escape(row.get("review_priority")),
                    _escape(tags),
                    _escape(row.get("model_question")),
                ]
            )
            + " |"
        )
    return "\n".join([header, *body])


if __name__ == "__main__":
    raise SystemExit(main())
