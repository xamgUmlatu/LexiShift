#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
EXAMPLE_FRAME_BATCH_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_example_frame_batches"
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.helper.paths import resolve_data_root  # noqa: E402
from semantic_phrase_containment_support import (  # noqa: E402
    match_phrase_containment_examples,
)
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402
from semantic_source_heldout_validation_en_es import _load_json  # noqa: E402
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


DEFAULT_DATASET = (
    TEST_OUTPUTS_ROOT
    / "experiments"
    / "semantic_non_v10_wave_drafts"
    / "en_es_source_non_v10_wave5_anypos_source_portfolio_materialized_v1_dataset.json"
)
DEFAULT_HELDOUT_CASES = (
    DOCS_ROOT
    / "test_inputs"
    / "semantic_routing_cases"
    / "en_es_source_non_v10_wave5_portfolio_phrase_cases_v1.json"
)
DEFAULT_PREFIX = "semantic_wordnet_phrase_control_non_v10_wave5_portfolio_latest"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / f"{DEFAULT_PREFIX}.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / f"{DEFAULT_PREFIX}.md"
DEFAULT_BATCH_OUT = (
    EXAMPLE_FRAME_BATCH_ROOT
    / "en-es-wordnet-phrase-control-non-v10-wave5-portfolio-latest_normalized_evidence.json"
)
DEFAULT_BATCH_ID = "en-es:wordnet-phrase-control:non-v10-wave5-portfolio-v1"
DEFAULT_SOURCE_ID = "wordnet_phrase_control_non_v10_wave5_portfolio_v1"
_TOKEN_RE = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ']+")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Mine source-backed phrase-control containment rows from WordNet examples for "
            "phrase/no-winner held-out cases. This is a failure-analysis probe, not broad "
            "automatic phrase generation."
        )
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--heldout-cases", type=Path, default=DEFAULT_HELDOUT_CASES)
    parser.add_argument("--wordnet-dir", type=Path, default=None)
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--max-rows-per-family", type=int, default=1)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--batch-out", type=Path, default=DEFAULT_BATCH_OUT)
    return parser.parse_args()


def build_wordnet_phrase_control_miner_bundle(
    *,
    dataset_payload: Mapping[str, object],
    heldout_case_payload: Mapping[str, object],
    wordnet_index: WordNetIndex,
    batch_id: str = DEFAULT_BATCH_ID,
    source_id: str = DEFAULT_SOURCE_ID,
    max_rows_per_family: int = 1,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    family_lookup = {
        str(family.get("family_id") or "").strip(): family
        for family in dataset_payload.get("families", ())
        if isinstance(family, Mapping) and str(family.get("family_id") or "").strip()
    }
    wordnet_examples = _wordnet_example_rows(wordnet_index)
    rows: list[dict[str, object]] = []
    case_rows: list[dict[str, object]] = []
    rows_by_family: dict[str, int] = {}
    for heldout_family in heldout_case_payload.get("families", ()):
        if not isinstance(heldout_family, Mapping):
            continue
        family_id = str(heldout_family.get("family_id") or "").strip()
        family = family_lookup.get(family_id)
        if not isinstance(family, Mapping):
            continue
        for case in heldout_family.get("cases", ()):
            if not isinstance(case, Mapping) or str(case.get("gold_decision") or "") != "abstain":
                continue
            if rows_by_family.get(family_id, 0) >= max(0, int(max_rows_per_family)):
                continue
            match_row = _first_source_match(
                family=family,
                case=case,
                wordnet_examples=wordnet_examples,
            )
            if not match_row:
                case_rows.append(_case_result_row(family=family, case=case, matched=False))
                continue
            row = _phrase_control_row(
                family=family,
                case=case,
                source_example=match_row,
                batch_id=batch_id,
                source_id=source_id,
                generated_at=generated_at,
            )
            rows.append(row)
            rows_by_family[family_id] = rows_by_family.get(family_id, 0) + 1
            case_rows.append(
                _case_result_row(
                    family=family,
                    case=case,
                    matched=True,
                    source_example=match_row,
                    evidence_row=row,
                )
            )
    batch = _batch_payload(
        rows=rows,
        batch_id=batch_id,
        source_id=source_id,
        generated_at=generated_at,
    )
    report = _report_payload(
        dataset_payload=dataset_payload,
        heldout_case_payload=heldout_case_payload,
        batch=batch,
        case_rows=case_rows,
        wordnet_index=wordnet_index,
        generated_at=generated_at,
    )
    return {"report": report, "batch": batch}


def render_wordnet_phrase_control_miner_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es WordNet Phrase-Control Miner",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{report.get('dataset_id', '')}`",
        f"- Held-out case scope: `{report.get('heldout_case_scope', '')}`",
        f"- Phrase rows: `{summary.get('phrase_control_row_count', 0)}`",
        f"- Matched held-out cases: `{summary.get('matched_case_count', 0)}` / `{summary.get('eligible_case_count', 0)}`",
        "",
        "## Matches",
        "",
        "| Case | Family | Pattern | Source example | Synset |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report.get("case_rows", ()):
        if not isinstance(row, Mapping) or not bool(row.get("matched")):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('case_id', '')}`",
                    f"`{row.get('family_id', '')}`",
                    f"`{row.get('phrase_containment_pattern', '')}`",
                    str(row.get("source_example", "")).replace("|", "\\|"),
                    f"`{row.get('wordnet_synset_id', '')}`",
                ]
            )
            + " |"
        )
    if not any(
        isinstance(row, Mapping) and bool(row.get("matched")) for row in report.get("case_rows", ())
    ):
        lines.append("| `none` | `n/a` | `n/a` | `n/a` | `n/a` |")
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- `failure_driven_phrase_probe_not_broad_generation`",
            "- `wordnet_examples_only`",
            "- `phrase_rows_are_containment_only_not_semantic_competitors`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_wordnet_phrase_control_miner_bundle(
    *,
    bundle: Mapping[str, object],
    json_out: Path,
    markdown_out: Path,
    batch_out: Path,
) -> None:
    _write_json(batch_out, _as_mapping(bundle.get("batch")))
    report = dict(_as_mapping(bundle.get("report")))
    report["artifacts"] = {**_as_mapping(report.get("artifacts")), "batch_json": str(batch_out)}
    _write_json(json_out, report)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.write_text(render_wordnet_phrase_control_miner_markdown(report), encoding="utf-8")


def _first_source_match(
    *,
    family: Mapping[str, object],
    case: Mapping[str, object],
    wordnet_examples: Sequence[Mapping[str, object]],
) -> Mapping[str, object]:
    trigger = str(family.get("trigger") or "").strip()
    sentence = str(case.get("sentence") or "").strip()
    source_phrase = str(case.get("source_phrase") or trigger).strip()
    source_tokens = set(_tokens(source_phrase or trigger))
    if not source_tokens:
        return {}
    for example_row in wordnet_examples:
        example = str(example_row.get("example") or "").strip()
        if not source_tokens.issubset(set(_tokens(example))):
            continue
        match = match_phrase_containment_examples(
            sentence=sentence,
            source_phrase=source_phrase,
            trigger=trigger,
            phrase_examples=[example],
        )
        if match.hit:
            return {**dict(example_row), "phrase_match": match}
    return {}


def _phrase_control_row(
    *,
    family: Mapping[str, object],
    case: Mapping[str, object],
    source_example: Mapping[str, object],
    batch_id: str,
    source_id: str,
    generated_at: str,
) -> dict[str, object]:
    family_id = str(family.get("family_id") or "").strip()
    trigger = str(family.get("trigger") or "").strip()
    active = _as_mapping(family.get("active"))
    match = source_example.get("phrase_match")
    pattern = str(getattr(match, "pattern_text", "")).strip()
    evidence_text = str(source_example.get("example") or "").strip()
    row_id = f"{_slug(family_id)}:phrase-control-wordnet-{_slug(pattern or evidence_text)}"
    row = {
        "evidence_id": _stable_id(
            "semantic-evidence",
            source_id,
            row_id,
            family_id,
            evidence_text,
        ),
        "dedupe_key": _stable_id(
            "dedupe", family_id, "phrase_control_example", pattern, evidence_text
        ),
        "batch_id": batch_id,
        "row_id": row_id,
        "pair": "en-es",
        "source_type": "external",
        "source_id": source_id,
        "source_family": "external_sense_graph",
        "roles": ["phrase_containment"],
        "relation_type": "phrase_control_example",
        "trigger": trigger,
        "normalized_trigger": trigger.lower(),
        "active_target": str(active.get("target_lemma") or "").strip(),
        "normalized_active_target": str(active.get("target_lemma") or "").strip().lower(),
        "candidate_target": "phrase_control",
        "normalized_candidate_target": "phrase_control",
        "is_multiword": True,
        "evidence_text": evidence_text,
        "review_state": "source_mined_phrase_probe",
        "promotion_state": "proposed",
        "linkage_status": "partially_linked",
        "runtime_publishable": False,
        "active_sense_hint": {
            "provider": "sentence_veto_dataset",
            "locator_kind": "sense_id",
            "target_key": str(active.get("sense_id") or "").strip(),
            "canonical_pos": str(active.get("canonical_pos") or "").strip(),
            "note": "phrase_control_anchor",
        },
        "candidate_sense_hint": {
            "provider": "wordnet_en_json",
            "locator_kind": "synset_id",
            "target_key": str(source_example.get("synset_id") or "").strip(),
            "canonical_pos": str(source_example.get("part_of_speech") or "").strip(),
            "note": "wordnet_phrase_control_example",
        },
        "metadata": {
            "family_id": family_id,
            "active_sense_id": str(active.get("sense_id") or "").strip(),
            "candidate_sense_id": "phrase_control",
            "example_bucket": "phrase_control",
            "case_id": str(case.get("case_id") or "").strip(),
            "source_view": "wordnet_synset_example",
            "wordnet_synset_id": str(source_example.get("synset_id") or "").strip(),
            "wordnet_members": list(source_example.get("members") or ()),
            "wordnet_source_file_count": int(source_example.get("source_file_count") or 0),
            "phrase_containment_pattern": pattern,
            "phrase_containment_reason_code": str(getattr(match, "reason_code", "")).strip(),
        },
        "provenance": {
            "source_type": "external",
            "source_id": source_id,
            "source_family": "external_sense_graph",
            "batch_id": batch_id,
            "row_id": row_id,
            "model_id": "none",
            "prompt_version": "wordnet-phrase-control-miner-v1",
            "generated_at": generated_at,
            "ingested_at": generated_at,
            "normalization_version": "semantic_evidence_manual_v1",
        },
    }
    return row


def _case_result_row(
    *,
    family: Mapping[str, object],
    case: Mapping[str, object],
    matched: bool,
    source_example: Mapping[str, object] | None = None,
    evidence_row: Mapping[str, object] | None = None,
) -> dict[str, object]:
    match = (
        (source_example or {}).get("phrase_match") if isinstance(source_example, Mapping) else None
    )
    return {
        "case_id": str(case.get("case_id") or "").strip(),
        "family_id": str(family.get("family_id") or "").strip(),
        "trigger": str(family.get("trigger") or "").strip(),
        "sentence": str(case.get("sentence") or "").strip(),
        "matched": bool(matched),
        "row_id": str((evidence_row or {}).get("row_id") or "").strip()
        if isinstance(evidence_row, Mapping)
        else "",
        "source_example": str((source_example or {}).get("example") or "").strip()
        if isinstance(source_example, Mapping)
        else "",
        "wordnet_synset_id": str((source_example or {}).get("synset_id") or "").strip()
        if isinstance(source_example, Mapping)
        else "",
        "phrase_containment_pattern": str(getattr(match, "pattern_text", "")).strip(),
        "phrase_containment_reason_code": str(getattr(match, "reason_code", "")).strip(),
    }


def _wordnet_example_rows(wordnet_index: WordNetIndex) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for synset_id, synset in sorted(wordnet_index.synsets_by_id.items()):
        if not isinstance(synset, Mapping):
            continue
        for example in _text_list(synset.get("example")):
            rows.append(
                {
                    "synset_id": synset_id,
                    "part_of_speech": str(synset.get("partOfSpeech") or "").strip(),
                    "members": _text_list(synset.get("members")),
                    "example": example,
                    "source_file_count": wordnet_index.source_file_count,
                }
            )
    return rows


def _batch_payload(
    *,
    rows: Sequence[Mapping[str, object]],
    batch_id: str,
    source_id: str,
    generated_at: str,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "normalization_version": "semantic_evidence_manual_v1",
        "batch_id": str(batch_id or "").strip() or DEFAULT_BATCH_ID,
        "pair": "en-es",
        "source_type": "external",
        "source_id": str(source_id or "").strip() or DEFAULT_SOURCE_ID,
        "source_family": "external_sense_graph",
        "roles": ["phrase_containment"],
        "generated_at": generated_at,
        "ingested_at": generated_at,
        "review_state": "source_mined_phrase_probe",
        "model_id": "none",
        "prompt_version": "wordnet-phrase-control-miner-v1",
        "row_count": len(rows),
        "rows": [dict(row) for row in rows],
        "provenance": {
            "method": "wordnet_example_phrase_containment_probe",
            "failure_driven": True,
        },
    }


def _report_payload(
    *,
    dataset_payload: Mapping[str, object],
    heldout_case_payload: Mapping[str, object],
    batch: Mapping[str, object],
    case_rows: Sequence[Mapping[str, object]],
    wordnet_index: WordNetIndex,
    generated_at: str,
) -> dict[str, object]:
    eligible_count = sum(
        1
        for family in heldout_case_payload.get("families", ())
        if isinstance(family, Mapping)
        for case in family.get("cases", ())
        if isinstance(case, Mapping) and str(case.get("gold_decision") or "") == "abstain"
    )
    matched_count = sum(1 for row in case_rows if bool(row.get("matched")))
    matched_family_count = len(
        {str(row.get("family_id") or "").strip() for row in case_rows if bool(row.get("matched"))}
    )
    target_family_count = sum(
        1 for family in heldout_case_payload.get("families", ()) if isinstance(family, Mapping)
    )
    status = "ok" if int(batch.get("row_count") or 0) > 0 else "review"
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": status,
        "decision": "phrase_control_rows_mined"
        if status == "ok"
        else "no_phrase_control_rows_mined",
        "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
        "heldout_case_scope": str(heldout_case_payload.get("case_scope") or "").strip(),
        "batch_id": str(batch.get("batch_id") or "").strip(),
        "source_id": str(batch.get("source_id") or "").strip(),
        "summary": {
            "source_family_count": matched_family_count,
            "target_family_count": target_family_count,
            "row_count": int(batch.get("row_count") or 0),
            "eligible_case_count": eligible_count,
            "matched_case_count": matched_count,
            "phrase_control_row_count": int(batch.get("row_count") or 0),
            "families_with_phrase_control_examples": matched_family_count,
            "phrase_contract_complete_family_count": matched_family_count,
            "wordnet_synset_count": len(wordnet_index.synsets_by_id),
            "wordnet_source_file_count": wordnet_index.source_file_count,
        },
        "case_rows": [dict(row) for row in case_rows],
        "artifacts": {},
        "limitations": [
            "failure_driven_phrase_probe_not_broad_generation",
            "wordnet_examples_only",
            "phrase_rows_are_containment_only_not_semantic_competitors",
        ],
    }


def _tokens(text: str) -> list[str]:
    return [match.lower() for match in _TOKEN_RE.findall(str(text or ""))]


def _text_list(value: object) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [_text_item(item) for item in value if _text_item(item)]
    return [_text_item(value)] if _text_item(value) else []


def _text_item(value: object) -> str:
    if isinstance(value, Mapping):
        return str(value.get("text") or value.get("value") or "").strip()
    if str(value or "").strip():
        return str(value).strip()
    return ""


def _stable_id(prefix: str, *parts: object) -> str:
    digest = hashlib.sha1(
        json.dumps([str(part) for part in parts], sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    return f"{prefix}:{digest}"


def _slug(value: object) -> str:
    slug = re.sub(r"[^0-9A-Za-z]+", "-", str(value or "").strip().lower()).strip("-")
    return slug or "unknown"


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    args = _parse_args()
    data_root = Path(resolve_data_root())
    wordnet_dir = args.wordnet_dir or data_root / "language_packs" / "english-wordnet-2025-json"
    bundle = build_wordnet_phrase_control_miner_bundle(
        dataset_payload=load_sentence_veto_dataset(args.dataset),
        heldout_case_payload=_load_json(args.heldout_cases),
        wordnet_index=WordNetIndex.load(wordnet_dir),
        batch_id=args.batch_id,
        source_id=args.source_id,
        max_rows_per_family=args.max_rows_per_family,
    )
    write_wordnet_phrase_control_miner_bundle(
        bundle=bundle,
        json_out=args.json_out,
        markdown_out=args.markdown_out,
        batch_out=args.batch_out,
    )
    print(f"Wrote WordNet phrase-control miner report to {args.json_out}")
    print(f"Wrote WordNet phrase-control batch to {args.batch_out}")


if __name__ == "__main__":
    main()
