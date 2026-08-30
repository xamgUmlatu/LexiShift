#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import gzip
import json
from pathlib import Path
from typing import Any, Mapping, Sequence
import unicodedata
import xml.etree.ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RANKING_CSV = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_final_ranking_corrected_en_ja_latest.csv"
)
DEFAULT_JMDICT = (
    Path.home()
    / "Library"
    / "Application Support"
    / "LexiShift"
    / "LexiShift"
    / "language_packs"
    / "jmdict-ja-en"
    / "JMdict_e"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_jmdict_family_admission_review_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_jmdict_family_admission_review_en_ja_latest.md"
)
NORMAL_ADMISSION = "normal_vocab"
SUPPRESSIBLE_ACTIONS = frozenset({"safe_family_representative", "caution_family_representative"})


@dataclass(frozen=True)
class JmdictPair:
    surface: str
    reading: str
    pair_kind: str
    surface_info: tuple[str, ...] = ()
    reading_info: tuple[str, ...] = ()
    reading_restricted: bool = False
    no_kanji: bool = False


@dataclass(frozen=True)
class JmdictFamily:
    ent_seq: str
    kanji_forms: tuple[str, ...]
    reading_forms: tuple[str, ...]
    pairs: tuple[JmdictPair, ...]
    glosses: tuple[str, ...]
    pos_values: tuple[str, ...]
    misc_values: tuple[str, ...]
    field_values: tuple[str, ...]
    sense_restriction_count: int
    has_marked_form: bool


@dataclass(frozen=True)
class PairMatch:
    family_id: str
    ent_seq: str
    pair_kind: str
    surface_info: tuple[str, ...]
    reading_info: tuple[str, ...]
    reading_restricted: bool
    no_kanji: bool


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a JMDict-entry family review over the corrected en-ja learner "
            "difficulty ranking. This is a source-backed grouping diagnostic only."
        )
    )
    parser.add_argument("--ranking-csv", type=Path, default=DEFAULT_RANKING_CSV)
    parser.add_argument("--jmdict", type=Path, default=DEFAULT_JMDICT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--visible-top-n", type=int, default=5000)
    parser.add_argument("--group-limit", type=int, default=80)
    parser.add_argument("--ambiguous-limit", type=int, default=40)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        ranking_csv=_resolve_path(args.ranking_csv),
        jmdict_path=_resolve_path(args.jmdict),
        visible_top_n=max(1, int(args.visible_top_n)),
        group_limit=max(0, int(args.group_limit)),
        ambiguous_limit=max(0, int(args.ambiguous_limit)),
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    return 0


def build_report(
    *,
    ranking_csv: Path,
    jmdict_path: Path,
    visible_top_n: int,
    group_limit: int,
    ambiguous_limit: int,
) -> dict[str, Any]:
    ranking_rows = load_ranking_rows(ranking_csv)
    families = load_jmdict_families(jmdict_path)
    pair_lookup = build_pair_lookup(families)
    family_rows: dict[str, list[dict[str, Any]]] = {}
    ambiguous_rows: list[dict[str, Any]] = []
    unmapped_visible_rows: list[dict[str, Any]] = []
    mapped_count = 0

    for row in ranking_rows:
        matches = pair_lookup.get(pair_key(row["lemma"], row["reading"]), ())
        ent_seqs = sorted({match.ent_seq for match in matches})
        if len(ent_seqs) == 1:
            match = matches[0]
            row["jmdict_family_id"] = match.family_id
            row["jmdict_ent_seq"] = match.ent_seq
            row["jmdict_pair_kind"] = match.pair_kind
            row["jmdict_pair_marked"] = bool(match.surface_info or match.reading_info)
            row["jmdict_pair_reading_restricted"] = bool(match.reading_restricted)
            row["jmdict_pair_no_kanji"] = bool(match.no_kanji)
            family_rows.setdefault(match.family_id, []).append(row)
            mapped_count += 1
        elif matches:
            row["jmdict_ambiguous_ent_seqs"] = ent_seqs
            if row["rank"] <= visible_top_n:
                ambiguous_rows.append(ambiguous_row(row, matches=matches))
        elif row["rank"] <= visible_top_n:
            unmapped_visible_rows.append(sample_row(row))

    group_reports = [
        build_group_report(
            family_id=family_id,
            rows=rows,
            family=families[family_id],
            visible_top_n=visible_top_n,
        )
        for family_id, rows in family_rows.items()
        if len(rows) > 1
    ]
    group_reports.sort(key=group_sort_key)
    visible_group_reports = [
        group for group in group_reports if int(group["visible_row_count"]) > 1
    ]
    same_surface_different_entry = same_surface_different_entry_rows(
        ranking_rows,
        visible_top_n=visible_top_n,
        limit=group_limit,
    )
    summary = {
        "ranking_rows": len(ranking_rows),
        "jmdict_family_count": len(families),
        "mapped_rows": mapped_count,
        "unmapped_visible_rows": len(unmapped_visible_rows),
        "ambiguous_visible_rows": len(ambiguous_rows),
        "multirow_family_count": len(group_reports),
        "visible_multirow_family_count": len(visible_group_reports),
        "safe_visible_family_count": sum(
            1 for group in visible_group_reports if group["action"] == "safe_family_representative"
        ),
        "caution_visible_family_count": sum(
            1
            for group in visible_group_reports
            if group["action"] == "caution_family_representative"
        ),
        "review_only_visible_family_count": sum(
            1 for group in visible_group_reports if group["action"] == "review_only"
        ),
        "visible_suppressed_sibling_count": sum(
            int(group["visible_suppressible_sibling_count"])
            for group in visible_group_reports
            if group["action"] in SUPPRESSIBLE_ACTIONS
        ),
    }
    return {
        "schema_version": 1,
        "language_pair": "en-ja",
        "runtime_behavior_changed": False,
        "scores_changed": False,
        "purpose": (
            "Source-backed JMDict entry-family review for possible admission "
            "representative selection. Rows are grouped only when their "
            "surface+reading pair maps unambiguously to one JMDict ent_seq."
        ),
        "inputs": {
            "ranking_csv": repo_path(ranking_csv),
            "jmdict": str(jmdict_path),
            "visible_top_n": visible_top_n,
        },
        "policy": {
            "family_source": "JMDict ent_seq",
            "no_heuristic_merge": True,
            "ambiguous_pair_behavior": "report_only_no_family_assignment",
            "same_surface_different_entry_behavior": "report_only_do_not_merge",
            "representative_selection": (
                "prefer normal admission and topic-stretchable rows, then lower "
                "final score, stronger exact commonness, lower core rank, and lower rank"
            ),
        },
        "summary": summary,
        "visible_multirow_families": visible_group_reports[:group_limit],
        "all_multirow_family_examples": group_reports[:group_limit],
        "ambiguous_visible_rows": ambiguous_rows[:ambiguous_limit],
        "same_surface_different_entry_examples": same_surface_different_entry,
        "unmapped_visible_examples": unmapped_visible_rows[:ambiguous_limit],
    }


def load_ranking_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    parsed_rows: list[dict[str, Any]] = []
    for row in rows:
        parsed = dict(row)
        parsed["rank"] = int(row["rank"])
        parsed["score"] = optional_float(row.get("score")) or 0.0
        parsed["model_score"] = optional_float(row.get("model_score"))
        parsed["core_rank"] = optional_float(row.get("core_rank"))
        parsed["exact_commonness"] = optional_float(row.get("exact_commonness")) or 0.0
        topic_stretch_allowed = str(row.get("topic_stretch_allowed") or "").strip()
        parsed["topic_stretch_allowed_bool"] = (
            topic_stretch_allowed == "True" if topic_stretch_allowed else None
        )
        parsed_rows.append(parsed)
    return parsed_rows


def load_jmdict_families(path: Path) -> dict[str, JmdictFamily]:
    families: dict[str, JmdictFamily] = {}
    with xml_text_stream(path) as source:
        context = ET.iterparse(source, events=("end",))
        for _event, elem in context:
            if local_name(elem.tag) != "entry":
                continue
            family = parse_jmdict_family(elem)
            if family is not None:
                families[f"jmdict:{family.ent_seq}"] = family
            elem.clear()
    return families


def parse_jmdict_family(elem: ET.Element) -> JmdictFamily | None:
    ent_seq = node_text(elem.find("ent_seq"))
    if not ent_seq:
        return None
    kanji_entries = [
        {
            "surface": node_text(k_ele.find("keb")),
            "info": collect_texts(k_ele.findall("ke_inf")),
        }
        for k_ele in elem.findall("k_ele")
    ]
    kanji_entries = [entry for entry in kanji_entries if entry["surface"]]
    reading_entries = [
        {
            "reading": node_text(r_ele.find("reb")),
            "info": collect_texts(r_ele.findall("re_inf")),
            "restrictions": tuple(
                value for value in (node_text(node) for node in r_ele.findall("re_restr")) if value
            ),
            "no_kanji": bool(r_ele.findall("re_nokanji")),
        }
        for r_ele in elem.findall("r_ele")
    ]
    reading_entries = [entry for entry in reading_entries if entry["reading"]]
    pairs: list[JmdictPair] = []
    for reading_entry in reading_entries:
        reading = str(reading_entry["reading"])
        restrictions = {
            str(value) for value in reading_entry.get("restrictions", ()) if str(value).strip()
        }
        no_kanji = bool(reading_entry.get("no_kanji"))
        if restrictions:
            compatible_kanji = [
                entry for entry in kanji_entries if str(entry["surface"]) in restrictions
            ]
        elif kanji_entries and not no_kanji:
            compatible_kanji = kanji_entries
        else:
            compatible_kanji = []
        for kanji_entry in compatible_kanji:
            pairs.append(
                JmdictPair(
                    surface=str(kanji_entry["surface"]),
                    reading=reading,
                    pair_kind="kanji_reading",
                    surface_info=tuple(kanji_entry.get("info", ()) or ()),
                    reading_info=tuple(reading_entry.get("info", ()) or ()),
                    reading_restricted=bool(restrictions),
                    no_kanji=no_kanji,
                )
            )
        # The kana reading itself is source-backed as a form of the entry, but
        # it will only be assigned to a family if this surface+reading pair is
        # unambiguous across JMDict.
        pairs.append(
            JmdictPair(
                surface=reading,
                reading=reading,
                pair_kind="reading_form",
                reading_info=tuple(reading_entry.get("info", ()) or ()),
                reading_restricted=bool(restrictions),
                no_kanji=no_kanji,
            )
        )
    return JmdictFamily(
        ent_seq=ent_seq,
        kanji_forms=tuple(sorted({str(entry["surface"]) for entry in kanji_entries})),
        reading_forms=tuple(sorted({str(entry["reading"]) for entry in reading_entries})),
        pairs=tuple(dict.fromkeys(pairs)),
        glosses=tuple(collect_texts(elem.findall("sense/gloss"))[:8]),
        pos_values=tuple(collect_texts(elem.findall("sense/pos"))),
        misc_values=tuple(collect_texts(elem.findall("sense/misc"))),
        field_values=tuple(collect_texts(elem.findall("sense/field"))),
        sense_restriction_count=len(elem.findall("sense/stagk")) + len(elem.findall("sense/stagr")),
        has_marked_form=bool(elem.findall("k_ele/ke_inf") or elem.findall("r_ele/re_inf")),
    )


def build_pair_lookup(
    families: Mapping[str, JmdictFamily],
) -> dict[tuple[str, str], tuple[PairMatch, ...]]:
    lookup: dict[tuple[str, str], list[PairMatch]] = {}
    for family_id, family in families.items():
        for pair in family.pairs:
            key = pair_key(pair.surface, pair.reading)
            lookup.setdefault(key, []).append(
                PairMatch(
                    family_id=family_id,
                    ent_seq=family.ent_seq,
                    pair_kind=pair.pair_kind,
                    surface_info=pair.surface_info,
                    reading_info=pair.reading_info,
                    reading_restricted=pair.reading_restricted,
                    no_kanji=pair.no_kanji,
                )
            )
    return {
        key: tuple(sorted(matches, key=lambda match: (match.ent_seq, match.pair_kind)))
        for key, matches in lookup.items()
    }


def build_group_report(
    *,
    family_id: str,
    rows: Sequence[dict[str, Any]],
    family: JmdictFamily,
    visible_top_n: int,
) -> dict[str, Any]:
    sorted_rows = sorted(rows, key=representative_sort_key)
    representative = sorted_rows[0]
    visible_rows = [row for row in sorted_rows if int(row["rank"]) <= visible_top_n]
    visible_siblings = [row for row in visible_rows if row_key(row) != row_key(representative)]
    caution_reasons = group_caution_reasons(family=family, rows=sorted_rows)
    action = "safe_family_representative"
    if caution_reasons:
        action = "caution_family_representative"
    if not is_admission_normal(representative):
        action = "review_only"
        caution_reasons = (*caution_reasons, "representative_not_normal_admission")
    return {
        "family_id": family_id,
        "ent_seq": family.ent_seq,
        "action": action,
        "caution_reasons": list(dict.fromkeys(caution_reasons)),
        "row_count": len(sorted_rows),
        "visible_row_count": len(visible_rows),
        "visible_suppressible_sibling_count": (
            len(visible_siblings) if action in SUPPRESSIBLE_ACTIONS else 0
        ),
        "representative": sample_row(representative),
        "rows": [sample_row(row) for row in sorted_rows],
        "visible_rows": [sample_row(row) for row in visible_rows],
        "suppressed_sibling_preview": [sample_row(row) for row in visible_siblings[:8]],
        "jmdict": {
            "kanji_forms": list(family.kanji_forms[:12]),
            "reading_forms": list(family.reading_forms[:12]),
            "glosses": list(family.glosses[:6]),
            "pos_values": list(family.pos_values[:8]),
            "misc_values": list(family.misc_values[:8]),
            "field_values": list(family.field_values[:8]),
            "sense_restriction_count": family.sense_restriction_count,
            "has_marked_form": family.has_marked_form,
        },
    }


def group_caution_reasons(
    *,
    family: JmdictFamily,
    rows: Sequence[Mapping[str, Any]],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if family.sense_restriction_count > 0:
        reasons.append("jmdict_sense_restrictions")
    if family.has_marked_form:
        reasons.append("jmdict_marked_form_or_reading")
    if any(bool(row.get("jmdict_pair_reading_restricted")) for row in rows):
        reasons.append("jmdict_reading_restrictions")
    if any(not is_admission_normal(row) for row in rows):
        reasons.append("contains_restricted_or_non_normal_sibling")
    if len({str(row.get("reading") or "") for row in rows}) > 1:
        reasons.append("multiple_readings")
    return tuple(reasons)


def same_surface_different_entry_rows(
    rows: Sequence[dict[str, Any]],
    *,
    visible_top_n: int,
    limit: int,
) -> list[dict[str, Any]]:
    by_surface: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row["rank"] > visible_top_n:
            continue
        family_id = str(row.get("jmdict_family_id") or "")
        if not family_id:
            continue
        by_surface.setdefault(str(row.get("lemma") or ""), []).append(row)
    examples: list[dict[str, Any]] = []
    for surface, surface_rows in sorted(by_surface.items()):
        family_ids = sorted({str(row.get("jmdict_family_id") or "") for row in surface_rows})
        if len(family_ids) <= 1:
            continue
        examples.append(
            {
                "surface": surface,
                "family_count": len(family_ids),
                "families": family_ids[:8],
                "rows": [
                    sample_row(row)
                    for row in sorted(surface_rows, key=lambda item: int(item["rank"]))[:12]
                ],
            }
        )
    examples.sort(key=lambda item: int(item["rows"][0]["rank"]) if item["rows"] else 999999999)
    return examples[:limit]


def ambiguous_row(row: Mapping[str, Any], *, matches: Sequence[PairMatch]) -> dict[str, Any]:
    sampled = sample_row(row)
    sampled["ambiguous_ent_seqs"] = sorted({match.ent_seq for match in matches})[:12]
    sampled["ambiguous_family_count"] = len({match.ent_seq for match in matches})
    return sampled


def sample_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "rank": int(row.get("rank") or 0),
        "score": rounded(optional_float(row.get("score")) or 0.0),
        "model_score": rounded(optional_float(row.get("model_score"))),
        "lemma": str(row.get("lemma") or ""),
        "reading": str(row.get("reading") or ""),
        "display": str(row.get("display_form") or row.get("lemma") or ""),
        "admission": admission_class(row),
        "topic_stretch_allowed": topic_stretch_allowed(row),
        "correction_types": split_flags(str(row.get("correction_types") or "")),
        "review_flags": split_flags(str(row.get("review_flags") or "")),
        "core_rank": rounded(optional_float(row.get("core_rank"))),
        "exact_commonness": rounded(optional_float(row.get("exact_commonness"))),
        "jmdict_family_id": str(row.get("jmdict_family_id") or ""),
        "jmdict_ent_seq": str(row.get("jmdict_ent_seq") or ""),
        "jmdict_pair_kind": str(row.get("jmdict_pair_kind") or ""),
        "jmdict_pair_marked": bool(row.get("jmdict_pair_marked")),
        "jmdict_pair_reading_restricted": bool(row.get("jmdict_pair_reading_restricted")),
    }


def representative_sort_key(
    row: Mapping[str, Any],
) -> tuple[float, float, float, float, int, str, str]:
    admission_penalty = 0.0
    if not is_admission_normal(row):
        admission_penalty += 10.0
    if "display_only" in split_flags(str(row.get("correction_types") or "")):
        admission_penalty -= 0.1
    exact_commonness = optional_float(row.get("exact_commonness")) or 0.0
    core_rank = optional_float(row.get("core_rank"))
    if core_rank is None:
        core_rank = 999999999.0
    return (
        admission_penalty,
        optional_float(row.get("score")) or 1.0,
        -exact_commonness,
        core_rank,
        int(row.get("rank") or 0),
        str(row.get("lemma") or ""),
        str(row.get("reading") or ""),
    )


def group_sort_key(group: Mapping[str, Any]) -> tuple[int, int, float, int, str]:
    representative = group.get("representative")
    rep = representative if isinstance(representative, Mapping) else {}
    return (
        0 if int(group.get("visible_row_count") or 0) > 1 else 1,
        -int(group.get("visible_suppressible_sibling_count") or 0),
        optional_float(rep.get("score")) or 1.0,
        int(rep.get("rank") or 999999999),
        str(group.get("family_id") or ""),
    )


def render_markdown(report: Mapping[str, Any]) -> str:
    summary = mapping(report.get("summary"))
    lines = [
        "# en-ja JMDict Family Admission Review",
        "",
        "This is a sidecar diagnostic only. It does not change ranking scores, "
        "manual corrections, admission, or runtime behavior.",
        "",
        f"Ranking CSV: `{mapping(report.get('inputs')).get('ranking_csv')}`",
        f"JMDict path: `{mapping(report.get('inputs')).get('jmdict')}`",
        f"Visible cutoff: top `{mapping(report.get('inputs')).get('visible_top_n')}` rows",
        "",
        "## Policy",
        "",
        "- Family source: JMDict `ent_seq`.",
        "- No heuristic same-surface or same-reading merging.",
        "- A row is assigned to a family only when its surface+reading pair maps "
        "unambiguously to one JMDict entry.",
        "- Ambiguous pairs and same-surface different-entry rows are reported only.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key in (
        "ranking_rows",
        "jmdict_family_count",
        "mapped_rows",
        "unmapped_visible_rows",
        "ambiguous_visible_rows",
        "multirow_family_count",
        "visible_multirow_family_count",
        "safe_visible_family_count",
        "caution_visible_family_count",
        "review_only_visible_family_count",
        "visible_suppressed_sibling_count",
    ):
        lines.append(f"| `{key}` | `{summary.get(key, 0)}` |")
    lines.extend(
        [
            "",
            "## Visible Multirow Families",
            "",
        ]
    )
    render_groups(lines, sequence(report.get("visible_multirow_families")))
    lines.extend(
        [
            "",
            "## Same Surface, Different JMDict Entries",
            "",
            "These are explicit non-merges: JMDict maps the visible rows to different entries.",
            "",
        ]
    )
    render_same_surface_examples(
        lines, sequence(report.get("same_surface_different_entry_examples"))
    )
    lines.extend(
        [
            "",
            "## Ambiguous Visible Rows",
            "",
            "These rows matched multiple JMDict entries for the same surface+reading pair, "
            "so no family assignment was made.",
            "",
        ]
    )
    render_ambiguous_rows(lines, sequence(report.get("ambiguous_visible_rows")))
    return "\n".join(lines) + "\n"


def render_groups(lines: list[str], groups: Sequence[object]) -> None:
    if not groups:
        lines.append("No visible multirow JMDict families found.")
        return
    for group_obj in groups:
        group = mapping(group_obj)
        rep = mapping(group.get("representative"))
        lines.extend(
            [
                f"### `{group.get('family_id')}`",
                "",
                f"- Action: `{group.get('action')}`",
                f"- Caution reasons: `{', '.join(sequence(group.get('caution_reasons'))) or 'none'}`",
                (
                    "- Representative: "
                    f"`{rep.get('lemma')}/{rep.get('reading')}` "
                    f"score `{rep.get('score')}` admission `{rep.get('admission')}`"
                ),
                f"- Visible suppressible siblings: `{group.get('visible_suppressible_sibling_count')}`",
                "",
                "| Rank | Score | Row | Display | Admission | Pair | Flags |",
                "| ---: | ---: | --- | --- | --- | --- | --- |",
            ]
        )
        for row_obj in sequence(group.get("visible_rows")):
            row = mapping(row_obj)
            flags = ",".join(sequence(row.get("correction_types")))
            lines.append(
                "| "
                f"{row.get('rank')} | "
                f"{row.get('score')} | "
                f"`{row.get('lemma')}/{row.get('reading')}` | "
                f"`{row.get('display')}` | "
                f"`{row.get('admission')}` | "
                f"`{row.get('jmdict_pair_kind')}` | "
                f"{flags or ''} |"
            )
        jmdict = mapping(group.get("jmdict"))
        glosses = "; ".join(str(value) for value in sequence(jmdict.get("glosses"))[:4])
        readings = ", ".join(str(value) for value in sequence(jmdict.get("reading_forms"))[:8])
        kanji = ", ".join(str(value) for value in sequence(jmdict.get("kanji_forms"))[:8])
        lines.extend(
            [
                "",
                f"JMDict forms: kanji `{kanji or '-'}`, readings `{readings or '-'}`.",
                f"Glosses: {glosses or '-'}",
                "",
            ]
        )


def render_same_surface_examples(lines: list[str], examples: Sequence[object]) -> None:
    if not examples:
        lines.append("No same-surface different-entry examples inside the visible cutoff.")
        return
    for example_obj in examples[:40]:
        example = mapping(example_obj)
        lines.append(f"### `{example.get('surface')}`")
        lines.append("")
        lines.append("| Rank | Score | Row | JMDict family | Admission |")
        lines.append("| ---: | ---: | --- | --- | --- |")
        for row_obj in sequence(example.get("rows")):
            row = mapping(row_obj)
            lines.append(
                "| "
                f"{row.get('rank')} | "
                f"{row.get('score')} | "
                f"`{row.get('lemma')}/{row.get('reading')}` | "
                f"`{row.get('jmdict_family_id')}` | "
                f"`{row.get('admission')}` |"
            )
        lines.append("")


def render_ambiguous_rows(lines: list[str], rows: Sequence[object]) -> None:
    if not rows:
        lines.append("No ambiguous visible rows found.")
        return
    lines.append("| Rank | Score | Row | Ambiguous entries | Admission |")
    lines.append("| ---: | ---: | --- | --- | --- |")
    for row_obj in rows[:80]:
        row = mapping(row_obj)
        entries = ", ".join(str(value) for value in sequence(row.get("ambiguous_ent_seqs"))[:8])
        lines.append(
            "| "
            f"{row.get('rank')} | "
            f"{row.get('score')} | "
            f"`{row.get('lemma')}/{row.get('reading')}` | "
            f"`{entries}` | "
            f"`{row.get('admission')}` |"
        )


def xml_text_stream(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def node_text(node: ET.Element | None) -> str:
    if node is None or node.text is None:
        return ""
    return str(node.text).strip()


def collect_texts(nodes: Sequence[ET.Element]) -> list[str]:
    return sorted({text for text in (node_text(node) for node in nodes) if text})


def local_name(value: object) -> str:
    text = str(value or "")
    if "}" in text:
        return text.rsplit("}", 1)[-1]
    return text


def pair_key(surface: object, reading: object) -> tuple[str, str]:
    return normalize_surface(surface), normalize_reading(reading)


def normalize_surface(value: object) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).strip()


def normalize_reading(value: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).strip()
    return "".join(katakana_to_hiragana(char) for char in normalized)


def katakana_to_hiragana(char: str) -> str:
    codepoint = ord(char)
    if 0x30A1 <= codepoint <= 0x30F6:
        return chr(codepoint - 0x60)
    return char


def is_admission_normal(row: Mapping[str, Any]) -> bool:
    if "exclude_standalone_srs" in split_flags(str(row.get("correction_types") or "")):
        return False
    if "restricted_admission" in split_flags(str(row.get("correction_types") or "")):
        return False
    return admission_class(row) == NORMAL_ADMISSION and topic_stretch_allowed(row)


def admission_class(row: Mapping[str, Any]) -> str:
    admission = str(row.get("admission_override") or "").strip()
    if admission:
        return admission
    return str(row.get("candidate_state") or NORMAL_ADMISSION).strip() or NORMAL_ADMISSION


def topic_stretch_allowed(row: Mapping[str, Any]) -> bool:
    raw = row.get("topic_stretch_allowed_bool")
    if isinstance(raw, bool):
        return raw
    text = str(row.get("topic_stretch_allowed") or "").strip()
    if not text:
        return admission_class(row) == NORMAL_ADMISSION
    return text == "True"


def row_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return str(row.get("lemma") or ""), str(row.get("reading") or "")


def split_flags(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def optional_float(value: object) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def rounded(value: object) -> float | None:
    numeric = optional_float(value)
    return round(float(numeric), 6) if numeric is not None else None


def mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def sequence(value: object) -> Sequence[Any]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
