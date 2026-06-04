#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_INPUTS_ROOT = DOCS_ROOT / "test_inputs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
for candidate in (str(CORE_ROOT), str(Path(__file__).resolve().parent)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_example_frame_source_adapter_support import text_list  # noqa: E402
from semantic_veto_full_family_representative_sample_en_es import (  # noqa: E402
    DEFAULT_WORDNET_DIR,
)
from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _escape_md,
    _load_json,
    _repo_path,
    _resolve_repo_path,
)
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


DEFAULT_SAMPLE_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_representative_sample_en_es_latest.json"
)
DEFAULT_DATASET_OUT = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_full_family_representative_manual_v1.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_manual_packet_authoring_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_manual_packet_authoring_en_es_latest.md"
)
DEFAULT_DATASET_ID = "en_es_full_family_representative_manual_v1"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize the frozen full-family representative sample into an "
            "agent-draft sentence-veto dataset. Research-only; human review pending."
        )
    )
    parser.add_argument("--sample-json", type=Path, default=DEFAULT_SAMPLE_JSON)
    parser.add_argument("--wordnet-dir", type=Path, default=DEFAULT_WORDNET_DIR)
    parser.add_argument("--dataset-out", type=Path, default=DEFAULT_DATASET_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    sample_path = _resolve_repo_path(args.sample_json)
    wordnet_dir = _resolve_repo_path(args.wordnet_dir)
    dataset_path = _resolve_repo_path(args.dataset_out)
    report_path = _resolve_repo_path(args.json_out)
    markdown_path = _resolve_repo_path(args.markdown_out)
    report, dataset = build_full_family_manual_packet_authoring_report(
        sample_payload=_load_json(sample_path),
        wordnet_index=WordNetIndex.load(wordnet_dir),
        sample_path=sample_path,
        wordnet_dir=wordnet_dir,
        dataset_path=dataset_path,
    )
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    dataset_path.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_full_family_manual_packet_markdown(report), encoding="utf-8")
    print(f"Wrote dataset artifact to {dataset_path}")
    print(f"Wrote JSON artifact to {report_path}")
    print(f"Wrote Markdown artifact to {markdown_path}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_full_family_manual_packet_authoring_report(
    *,
    sample_payload: Mapping[str, object],
    wordnet_index: WordNetIndex | None = None,
    sense_rows_by_source: Mapping[str, Sequence[Mapping[str, object]]] | None = None,
    sample_path: Path | None = None,
    wordnet_dir: Path | None = None,
    dataset_path: Path | None = None,
    generated_at: str | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    generated_at = generated_at or _utc_now()
    sample_rows = _mapping_rows(sample_payload.get("manual_authoring_queue"))
    families = [
        _family_from_sample_row(
            row=row,
            wordnet_index=wordnet_index,
            sense_rows_by_source=sense_rows_by_source,
        )
        for row in sample_rows
    ]
    dataset = {
        "schema_version": 1,
        "pair": str(sample_payload.get("pair") or "en-es"),
        "dataset_id": DEFAULT_DATASET_ID,
        "description": (
            "Agent-draft manual sentence-veto packet for the frozen full-family "
            "representative en-es sample. Research-only; human review pending."
        ),
        "families": families,
    }
    case_rows = [case for family in families for case in _mapping_rows(family.get("cases"))]
    case_type_counts = Counter(
        str(_as_mapping(case.get("slice_dimensions")).get("manual_case_type", [""])[0])
        for case in case_rows
    )
    shadow_contract_counts = Counter(
        str(_as_mapping(case.get("slice_dimensions")).get("shadow_contract", [""])[0])
        for case in case_rows
    )
    source_band_counts = Counter(
        str(_as_mapping(case.get("slice_dimensions")).get("source_zipf_band_en", [""])[0])
        for case in case_rows
    )
    summary = {
        "sampled_family_count": len(sample_rows),
        "dataset_family_count": len(families),
        "dataset_case_count": len(case_rows),
        "case_type_counts": dict(sorted(case_type_counts.items())),
        "shadow_contract_case_counts": dict(sorted(shadow_contract_counts.items())),
        "source_band_case_counts": dict(sorted(source_band_counts.items())),
        "active_positive_count": case_type_counts.get("positive_active", 0),
        "shadow_negative_count": case_type_counts.get("shadow_negative", 0),
        "phrase_no_winner_count": case_type_counts.get("phrase_no_winner", 0),
        "draft_review_state": "agent_draft_human_review_pending",
        "dataset_fingerprint": _fingerprint_dataset(dataset),
    }
    checks = _checks(sample_rows=sample_rows, dataset=dataset)
    issues = [key for key, value in checks.items() if not value]
    report = {
        "schema_version": 1,
        "pair": str(dataset.get("pair") or "en-es"),
        "status": "review" if issues else "ok",
        "decision": (
            "full_family_manual_packet_ready_for_scoring"
            if not issues
            else "full_family_manual_packet_needs_review"
        ),
        "generated_at": generated_at,
        "inputs": {
            "sample_path": _repo_path(sample_path),
            "sample_decision": str(sample_payload.get("decision") or ""),
            "wordnet_dir": _repo_path(wordnet_dir),
            "wordnet_source_file_count": int(wordnet_index.source_file_count)
            if wordnet_index is not None
            else None,
        },
        "outputs": {
            "dataset_path": _repo_path(dataset_path),
            "dataset_id": DEFAULT_DATASET_ID,
            "dataset_fingerprint": summary["dataset_fingerprint"],
        },
        "methodology": {
            "runtime_policy_change": "none",
            "llm_generation": "none",
            "source_selection": "frozen_full_family_representative_sample",
            "manual_review_state": "agent_draft_human_review_pending",
            "authoring_policy": (
                "Use exact or source-adapted WordNet examples before definition fallbacks; "
                "do not duplicate shadow-negative rows when only one real alternate "
                "context is available; keep missing or single-sense shadows as not_applicable."
            ),
            "promotion_rule": (
                "This dataset may be scored as a research lane but cannot support "
                "promotion claims until reviewed or replaced by human-approved cases."
            ),
        },
        "summary": summary,
        "e2e_checks": checks,
        "family_rows": [_family_report_row(family) for family in families],
        "limitations": [
            "agent_draft_sentences_are_not_human_locked_evaluation_rows",
            "wordnet_first_sense_may_not_match_the_dictionary_source_target_sense",
            "automated_phrase_no_winner_rows_are_diagnostic_not_browser_distribution",
            "shadow_negative_rows_depend_on_available_wordnet_alternate_senses",
        ],
        "next_steps": [
            "Run TF-IDF and sentence-transformer sentence-veto scoring as a diagnostic lane.",
            "Inspect failures and questionable authored rows before any promotion claim.",
            "Use source-band and polysemy breakdowns to decide whether mid and rare bands are easier.",
            "Replace weak draft rows with human-reviewed contexts if the curve signal is promising or ambiguous.",
        ],
    }
    return report, dataset


def render_full_family_manual_packet_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Full-Family Manual Packet Authoring",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{_as_mapping(report.get('outputs')).get('dataset_path', '')}`",
        f"- Families: `{summary.get('dataset_family_count', 0)}`",
        f"- Cases: `{summary.get('dataset_case_count', 0)}`",
        f"- Review state: `{summary.get('draft_review_state', '')}`",
        "",
        "## Methodology",
        "",
        str(_as_mapping(report.get("methodology")).get("authoring_policy") or ""),
        "",
        "The source-target family sample remains frozen. This pass only fills the "
        "sentence-veto dataset shape so the current veto algorithm can be measured "
        "against the representative queue.",
        "",
        "## Counts",
        "",
        _summary_table(summary),
        "",
        "## Families",
        "",
        _family_table(report.get("family_rows")),
        "",
        "## Guardrails",
        "",
        "| Check | Value |",
        "| --- | --- |",
    ]
    for key, value in _as_mapping(report.get("e2e_checks")).items():
        lines.append(f"| `{_escape_md(key)}` | `{value}` |")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _family_from_sample_row(
    *,
    row: Mapping[str, object],
    wordnet_index: WordNetIndex | None,
    sense_rows_by_source: Mapping[str, Sequence[Mapping[str, object]]] | None,
) -> dict[str, object]:
    source = str(row.get("source") or "").strip().lower()
    target = str(row.get("target") or "").strip()
    family_id = f"en-es:full-family-representative:{_slug(source)}:{_slug(target)}"
    active_id = f"{family_id}:active"
    sense_rows = _sense_rows_for_source(
        source=source,
        wordnet_index=wordnet_index,
        sense_rows_by_source=sense_rows_by_source,
    )
    active_sense = sense_rows[0] if sense_rows else _fallback_sense(source=source)
    shadow_contract = str(_as_mapping(row.get("manual_packet")).get("shadow_contract") or "")
    shadow_candidates = sense_rows[1:3] if shadow_contract == "candidate_polysemic" else []
    shadows = [
        _shadow_payload(
            family_id=family_id,
            index=index,
            source=source,
            sense=sense,
        )
        for index, sense in enumerate(shadow_candidates, start=1)
    ]
    cases = _case_payloads(
        family_id=family_id,
        source=source,
        target=target,
        active_id=active_id,
        active_sense=active_sense,
        shadows=shadows,
        shadow_senses=shadow_candidates,
        sample_row=row,
    )
    return {
        "family_id": family_id,
        "trigger": source,
        "active": {
            "sense_id": active_id,
            "target_lemma": target,
            "canonical_pos": _canonical_pos(active_sense),
            "evidence_views": _evidence_views(
                sense_label=f"{source} -> {target}",
                gloss_text=str(active_sense.get("definition") or f"{source} in the {target} sense"),
                examples=_example_texts(active_sense),
            ),
        },
        "shadows": shadows,
        "cases": cases,
    }


def _case_payloads(
    *,
    family_id: str,
    source: str,
    target: str,
    active_id: str,
    active_sense: Mapping[str, object],
    shadows: Sequence[Mapping[str, object]],
    shadow_senses: Sequence[Mapping[str, object]],
    sample_row: Mapping[str, object],
) -> list[dict[str, object]]:
    cases: list[dict[str, object]] = []
    case_index = 1
    seen_sentences: set[str] = set()
    active_sentences = _positive_sentences(source=source, sense=active_sense)
    for sentence, sentence_note in active_sentences[:2]:
        if _normalized_sentence(sentence) in seen_sentences:
            continue
        seen_sentences.add(_normalized_sentence(sentence))
        cases.append(
            _case(
                family_id=family_id,
                index=case_index,
                source=source,
                sentence=sentence,
                gold_winner=active_id,
                gold_decision="replace",
                manual_case_type="positive_active",
                sample_row=sample_row,
                notes=sentence_note,
            )
        )
        case_index += 1
    for shadow, shadow_sense in zip(shadows, shadow_senses):
        sentence, sentence_note = _shadow_sentence(source=source, sense=shadow_sense)
        normalized = _normalized_sentence(sentence)
        if normalized in seen_sentences:
            continue
        seen_sentences.add(normalized)
        cases.append(
            _case(
                family_id=family_id,
                index=case_index,
                source=source,
                sentence=sentence,
                gold_winner=str(shadow.get("sense_id") or ""),
                gold_decision="abstain",
                manual_case_type="shadow_negative",
                sample_row=sample_row,
                notes=sentence_note,
            )
        )
        case_index += 1
    no_winner_sentence = _phrase_no_winner_sentence(source=source)
    cases.append(
        _case(
            family_id=family_id,
            index=case_index,
            source=source,
            sentence=no_winner_sentence,
            gold_winner="none",
            gold_decision="abstain",
            manual_case_type="phrase_no_winner",
            sample_row=sample_row,
            notes="draft browser-like phrase/no-winner context",
        )
    )
    return cases


def _case(
    *,
    family_id: str,
    index: int,
    source: str,
    sentence: str,
    gold_winner: str,
    gold_decision: str,
    manual_case_type: str,
    sample_row: Mapping[str, object],
    notes: str,
) -> dict[str, object]:
    source_band = str(sample_row.get("source_zipf_band_en") or "missing")
    target_band = str(sample_row.get("target_zipf_band_es") or "missing")
    polysemy = str(sample_row.get("wordnet_polysemy_band") or "missing")
    pos_shape = str(sample_row.get("wordnet_pos_shape") or "missing")
    shadow_contract = str(_as_mapping(sample_row.get("manual_packet")).get("shadow_contract") or "")
    return {
        "case_id": f"{family_id}:{index:03d}",
        "sentence": sentence,
        "source_phrase": source,
        "gold_winner": gold_winner,
        "gold_decision": gold_decision,
        "slice_tags": [
            DEFAULT_DATASET_ID,
            "full_family_representative_manual_v1",
            "agent_draft_human_review_pending",
            f"source_zipf:{source_band}",
            f"target_zipf:{target_band}",
            f"polysemy:{polysemy}",
            f"pos_shape:{pos_shape}",
            manual_case_type,
            f"shadow_contract:{shadow_contract}",
        ],
        "slice_dimensions": {
            "dataset_lane": [DEFAULT_DATASET_ID],
            "manual_review_state": ["agent_draft_human_review_pending"],
            "source_zipf_band_en": [source_band],
            "target_zipf_band_es": [target_band],
            "polysemy_band": [polysemy],
            "pos_shape": [pos_shape],
            "manual_case_type": [manual_case_type],
            "shadow_contract": [shadow_contract],
        },
        "notes": notes,
    }


def _shadow_payload(
    *,
    family_id: str,
    index: int,
    source: str,
    sense: Mapping[str, object],
) -> dict[str, object]:
    sense_id = f"{family_id}:shadow:{index}:{_slug(str(sense.get('synset_id') or index))}"
    return {
        "sense_id": sense_id,
        "target_lemma": f"{source} alternate sense {index}",
        "canonical_pos": _canonical_pos(sense),
        "evidence_views": _evidence_views(
            sense_label=f"{source} alternate sense {index}",
            gloss_text=str(sense.get("definition") or f"alternate sense of {source}"),
            examples=_example_texts(sense),
        ),
    }


def _evidence_views(
    *,
    sense_label: str,
    gloss_text: str,
    examples: Sequence[str],
) -> dict[str, str]:
    example_text = " | ".join(str(example).strip() for example in examples if str(example).strip())
    all_parts = [sense_label, gloss_text]
    all_evidence = " | ".join(part for part in all_parts if part)
    views = {
        "sense_label": sense_label,
        "gloss_text": gloss_text,
        "sense_gloss_bundle": f"{sense_label} | {gloss_text}",
        "all_evidence_text": all_evidence,
    }
    if example_text:
        views["source_examples_text"] = example_text
    return views


def _positive_sentences(
    *,
    source: str,
    sense: Mapping[str, object],
) -> list[tuple[str, str]]:
    examples = _example_candidates(source=source, sense=sense)
    if examples:
        return examples[:2]
    definition = str(sense.get("definition") or "").strip()
    if definition:
        return [
            (
                f"The article used {source} to describe {definition}.",
                "draft active-positive definition fallback; needs independent-context rewrite",
            )
        ]
    return [
        (
            f"The article used {source} in a sentence that still needs human authoring.",
            "draft active-positive placeholder; needs independent-context rewrite",
        )
    ]


def _shadow_sentence(
    *,
    source: str,
    sense: Mapping[str, object],
) -> tuple[str, str]:
    examples = _example_candidates(source=source, sense=sense)
    if examples:
        return examples[0]
    definition = str(sense.get("definition") or "").strip() or "an alternate meaning"
    return (
        f"In this sentence, {source} referred to {definition}, not the target replacement.",
        "draft shadow-negative definition fallback; needs independent-context rewrite",
    )


def _phrase_no_winner_sentence(*, source: str) -> str:
    variants = [
        f'The download list included a file named "{source}_notes.txt".',
        f'The sidebar showed "{source}" as a saved search query.',
        f'A navigation tab labeled "{source}" opened an empty archive page.',
        f'The spreadsheet column was titled "{source}" in the exported report.',
    ]
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    return variants[int(digest[:2], 16) % len(variants)]


def _example_candidates(
    *,
    source: str,
    sense: Mapping[str, object],
) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    for example in _example_texts(sense):
        if _contains_source(example, source):
            candidates.append((example, "draft context from exact WordNet example"))
            continue
        adapted = _adapt_example_to_source(
            example=example,
            source=source,
            members=[str(item) for item in _sequence(sense.get("members"))],
        )
        if adapted:
            candidates.append((adapted, "draft context from source-adapted WordNet example"))
    return _unique_sentence_rows(candidates)


def _adapt_example_to_source(
    *,
    example: str,
    source: str,
    members: Sequence[str],
) -> str:
    source = str(source or "").strip()
    if not source:
        return ""
    for member in members:
        member = str(member or "").strip()
        if not member or member.lower() == source.lower():
            continue
        pattern = re.compile(rf"(?<!\w){re.escape(member)}(?!\w)", flags=re.IGNORECASE)
        if pattern.search(example):
            return pattern.sub(source, example, count=1)
    return ""


def _sense_rows_for_source(
    *,
    source: str,
    wordnet_index: WordNetIndex | None,
    sense_rows_by_source: Mapping[str, Sequence[Mapping[str, object]]] | None,
) -> list[Mapping[str, object]]:
    if sense_rows_by_source is not None:
        return [dict(row) for row in sense_rows_by_source.get(source, [])]
    if wordnet_index is None:
        return []
    entry = wordnet_index.entries_by_word.get(source)
    if not isinstance(entry, Mapping):
        return []
    rows: list[Mapping[str, object]] = []
    for pos_key, section in entry.items():
        if not isinstance(section, Mapping):
            continue
        for sense_rank, raw_sense in enumerate(_sequence(section.get("sense")), start=1):
            if not isinstance(raw_sense, Mapping):
                continue
            synset_id = str(raw_sense.get("synset") or "").strip()
            synset = wordnet_index.synsets_by_id.get(synset_id)
            if not isinstance(synset, Mapping):
                continue
            definitions = text_list(synset.get("definition"))
            examples = [*text_list(synset.get("example")), *text_list(raw_sense.get("sent"))]
            rows.append(
                {
                    "synset_id": synset_id,
                    "pos": str(pos_key or ""),
                    "sense_rank": sense_rank,
                    "definition": definitions[0] if definitions else "",
                    "examples": examples,
                    "members": text_list(synset.get("members")),
                }
            )
    return sorted(rows, key=lambda row: (int(row.get("sense_rank") or 999), str(row.get("pos"))))


def _fallback_sense(*, source: str) -> Mapping[str, object]:
    return {
        "synset_id": "",
        "pos": "",
        "definition": f"the intended dictionary sense of {source}",
        "examples": (),
        "members": (),
    }


def _family_report_row(family: Mapping[str, object]) -> dict[str, object]:
    cases = _mapping_rows(family.get("cases"))
    active = _as_mapping(family.get("active"))
    return {
        "family_id": str(family.get("family_id") or ""),
        "trigger": str(family.get("trigger") or ""),
        "target": str(active.get("target_lemma") or ""),
        "shadow_count": len(_mapping_rows(family.get("shadows"))),
        "case_count": len(cases),
        "case_type_counts": dict(Counter(_case_type(case) for case in cases)),
    }


def _checks(
    *,
    sample_rows: Sequence[Mapping[str, object]],
    dataset: Mapping[str, object],
) -> dict[str, bool]:
    families = _mapping_rows(dataset.get("families"))
    cases = [case for family in families for case in _mapping_rows(family.get("cases"))]
    case_ids = [str(case.get("case_id") or "") for case in cases]
    return {
        "sample_rows_available": bool(sample_rows),
        "one_family_per_sample_row": len(families) == len(sample_rows),
        "case_ids_unique": len(case_ids) == len(set(case_ids)),
        "all_cases_have_review_state": all(
            "agent_draft_human_review_pending"
            in _as_mapping(case.get("slice_dimensions")).get("manual_review_state", [])
            for case in cases
        ),
        "active_positive_cases_present": any(
            _case_type(case) == "positive_active" for case in cases
        ),
        "phrase_no_winner_cases_present": any(
            _case_type(case) == "phrase_no_winner" for case in cases
        ),
        "mid_cases_present": any(
            "zipf_3_to_4_mid"
            in _as_mapping(case.get("slice_dimensions")).get("source_zipf_band_en", [])
            for case in cases
        ),
        "rare_cases_present": any(
            "zipf_below_3_rare"
            in _as_mapping(case.get("slice_dimensions")).get("source_zipf_band_en", [])
            for case in cases
        ),
    }


def _case_type(case: Mapping[str, object]) -> str:
    values = _as_mapping(case.get("slice_dimensions")).get("manual_case_type", [])
    return str(values[0] if values else "")


def _canonical_pos(sense: Mapping[str, object]) -> str:
    pos = str(sense.get("pos") or "").strip().lower()
    return {
        "n": "noun",
        "v": "verb",
        "a": "adjective",
        "s": "adjective",
        "r": "adverb",
    }.get(pos, "")


def _example_texts(sense: Mapping[str, object]) -> list[str]:
    examples = [
        str(value).strip() for value in _sequence(sense.get("examples")) if str(value).strip()
    ]
    return examples[:4]


def _contains_source(sentence: str, source: str) -> bool:
    source = str(source or "").strip()
    if not source:
        return False
    return bool(re.search(rf"(?<!\w){re.escape(source)}(?!\w)", str(sentence or ""), re.I))


def _unique_sentence_rows(rows: Sequence[tuple[str, str]]) -> list[tuple[str, str]]:
    unique_rows: list[tuple[str, str]] = []
    seen: set[str] = set()
    for sentence, note in rows:
        normalized = _normalized_sentence(sentence)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique_rows.append((sentence, note))
    return unique_rows


def _normalized_sentence(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _summary_table(value: Mapping[str, object]) -> str:
    lines = ["| Key | Value |", "| --- | --- |"]
    for key, raw in value.items():
        if isinstance(raw, (dict, list, tuple)):
            rendered = json.dumps(raw, ensure_ascii=False, sort_keys=True)
        else:
            rendered = str(raw)
        lines.append(f"| `{_escape_md(str(key))}` | `{_escape_md(rendered)}` |")
    return "\n".join(lines)


def _family_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No family rows._"
    lines = [
        "| Trigger | Target | Shadows | Cases | Case Mix |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('trigger') or ''))}`",
                    f"`{_escape_md(str(row.get('target') or ''))}`",
                    str(int(row.get("shadow_count") or 0)),
                    str(int(row.get("case_count") or 0)),
                    _escape_md(json.dumps(row.get("case_type_counts") or {}, sort_keys=True)),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _fingerprint_dataset(dataset: Mapping[str, object]) -> str:
    payload = json.dumps(dataset, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _mapping_rows(value: object) -> list[dict[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [dict(row) for row in value if isinstance(row, Mapping)]


def _sequence(value: object) -> list[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return list(value)


def _slug(value: str) -> str:
    return (
        str(value or "")
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
        .replace(">", "to")
        .replace(":", "_")
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
