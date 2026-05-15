#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
GUI_SRC = PROJECT_ROOT / "apps" / "gui" / "src"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
for candidate in (CORE_ROOT, GUI_SRC):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)

from language_packs_catalog import build_pack_catalogs  # noqa: E402


DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "pack_lifecycle_source_identity_plan_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "pack_lifecycle_source_identity_plan_latest.md"

CLASSIFICATIONS = (
    "safe_to_write",
    "label_only",
    "needs_policy",
    "source_bundle_needed",
    "unknown",
)

_RELEASE_TAG_RE = re.compile(r"/releases/download/([^/]+)/")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Classify catalog pack source-version/source-dump identity candidates. "
            "The command is read-only: it does not write provenance sidecars or "
            "promote any candidate value into durable source identity."
        )
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_source_identity_plan()
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_source_identity_plan_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_source_identity_plan(*, generated_at: str | None = None) -> dict[str, object]:
    catalogs = build_pack_catalogs()
    rows: list[dict[str, object]] = []
    for family, packs in (
        ("language", catalogs.language_packs),
        ("frequency", catalogs.frequency_packs),
        ("embedding", catalogs.embedding_packs),
        ("embedding", catalogs.cross_embedding_packs),
    ):
        for pack in packs:
            rows.append(_classify_pack(family=family, pack=pack))

    summary = _summary(rows)
    return {
        "schema_version": 1,
        "generated_at": generated_at or _utc_now(),
        "status": "review" if summary["needs_decision_count"] else "ok",
        "decision": (
            "source_identity_classification_needs_review"
            if summary["needs_decision_count"]
            else "source_identity_candidates_classified"
        ),
        "mutation": "none",
        "runtime_policy_change": "none",
        "summary": summary,
        "packs": rows,
        "boundaries": [
            "does_not_write_source_version_or_source_dump",
            "does_not_approve_source_licenses",
            "does_not_pin_rolling_remote_sources",
            "does_not_change_pack_catalogs_or_runtime_defaults",
        ],
    }


def render_source_identity_plan_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# Pack Lifecycle Source Identity Plan",
        "",
        f"- Generated at: `{report.get('generated_at')}`",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Mutation: `{report.get('mutation')}`",
        f"- Runtime policy change: `{report.get('runtime_policy_change')}`",
        f"- Safe to write: `{summary.get('safe_to_write_count')}`",
        f"- Needs decision: `{summary.get('needs_decision_count')}`",
        "",
        "## Classification Summary",
        "",
        "| Classification | Count |",
        "| --- | --- |",
    ]
    classification_counts = _as_mapping(summary.get("classification_counts"))
    for classification in CLASSIFICATIONS:
        lines.append(f"| `{classification}` | `{classification_counts.get(classification, 0)}` |")
    lines.extend(
        [
            "",
            "## Pack Candidates",
            "",
            "| Family | Pack | Classification | Field | Candidate | Rationale | Recommended Action |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in _mapping_rows(report.get("packs")):
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('family') or ''))}`",
                    f"`{_escape_md(str(row.get('pack_id') or ''))}`",
                    f"`{_escape_md(str(row.get('classification') or ''))}`",
                    f"`{_escape_md(str(row.get('candidate_field') or ''))}`",
                    f"`{_escape_md(str(row.get('candidate_value') or ''))}`",
                    _escape_md(str(row.get("rationale") or "")),
                    _escape_md(str(row.get("recommended_action") or "")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Boundaries", ""])
    lines.extend(f"- `{item}`" for item in _string_sequence(report.get("boundaries")))
    return "\n".join(lines) + "\n"


def _classify_pack(*, family: str, pack: object) -> dict[str, object]:
    pack_id = _text(getattr(pack, "pack_id", ""))
    filename = _text(getattr(pack, "source_filename", "")) or _text(getattr(pack, "filename", ""))
    source_name = _text(getattr(pack, "source", ""))
    source_url = _text(getattr(pack, "url", ""))
    build_mode = _text(getattr(pack, "build_mode", "download_only")) or "download_only"
    candidate = _artifact_identity(filename)

    if build_mode == "de_frequency_pipeline":
        return _row(
            family=family,
            pack=pack,
            candidate_field="source_bundle",
            candidate_value="deu_news_2023_1M + LanguageTool POS pipeline",
            classification="source_bundle_needed",
            rationale=(
                "Generated pipeline output depends on a downloaded Leipzig corpus plus "
                "pipeline/POS dependencies, not a single source_version field."
            ),
            recommended_action="design_source_bundle_lineage_before_writing_identity",
        )

    if pack_id in {"jp-wordnet", "jp-wordnet-sqlite"}:
        release = _release_tag(source_url)
        return _row(
            family=family,
            pack=pack,
            candidate_field="source_version",
            candidate_value=f"wnja-{release}" if release else candidate,
            classification="safe_to_write" if release else "needs_policy",
            rationale=(
                "Catalog URL points at a GitHub release tag."
                if release
                else "Japanese WordNet catalog entry lacks an explicit release tag."
            ),
            recommended_action=(
                "eligible_for_future_source_version_writer"
                if release
                else "confirm_release_identity_before_writing_source_version"
            ),
        )

    if source_name.lower() == "freedict" or filename.startswith("freedict-"):
        return _row(
            family=family,
            pack=pack,
            candidate_field="source_version",
            candidate_value=candidate,
            classification="safe_to_write",
            rationale="FreeDict source archive filename and URL carry the dictionary release id.",
            recommended_action="eligible_for_future_source_version_writer",
        )

    if pack_id == "wordnet-en":
        return _row(
            family=family,
            pack=pack,
            candidate_field="source_version",
            candidate_value=candidate,
            classification="safe_to_write",
            rationale="WordNet catalog filename includes the source package year/id.",
            recommended_action="eligible_for_future_source_version_writer",
        )

    if pack_id == "freq-ja-bccwj":
        return _row(
            family=family,
            pack=pack,
            candidate_field="source_version",
            candidate_value="BCCWJ_frequencylist_suw_ver1_0",
            classification="safe_to_write",
            rationale="BCCWJ archive/source filename carries an explicit ver1_0 identifier.",
            recommended_action="eligible_for_future_source_version_writer",
        )

    if source_name.lower() == "kaikki":
        return _row(
            family=family,
            pack=pack,
            candidate_field="source_dump",
            candidate_value="enwiktionary",
            classification="needs_policy",
            rationale=(
                "Catalog identifies the Wiktextract dump family, but the shared raw dump URL "
                "does not pin a dated dump."
            ),
            recommended_action="pin_or_record_dump_date_before_writing_source_dump",
        )

    if source_name.lower() == "fasttext":
        return _row(
            family=family,
            pack=pack,
            candidate_field="source_label",
            candidate_value=candidate,
            classification="needs_policy",
            rationale="fastText artifact filename identifies model family/language but not a release.",
            recommended_action="confirm_fasttext_release_or_snapshot_before_writing_source_version",
        )

    if pack_id in {"freq-en-coca", "freq-es-cde"}:
        return _row(
            family=family,
            pack=pack,
            candidate_field="source_label",
            candidate_value=candidate,
            classification="label_only",
            rationale="Filename is a useful sample/artifact label, not clearly a source release.",
            recommended_action="keep_as_label_until_source_policy_defines_version_semantics",
        )

    if pack_id in {"moby-en", "jmdict-ja-en", "cc-cedict-zh-en"}:
        return _row(
            family=family,
            pack=pack,
            candidate_field="source_label",
            candidate_value=candidate,
            classification="needs_policy",
            rationale="Catalog filename is useful, but release/snapshot semantics need source policy.",
            recommended_action="confirm_release_or_snapshot_semantics_before_writing_source_version",
        )

    if "refs/heads/" in source_url or "/raw/master/" in source_url:
        return _row(
            family=family,
            pack=pack,
            candidate_field="source_label",
            candidate_value=candidate,
            classification="needs_policy",
            rationale="Catalog URL follows a branch/head rather than a pinned source release.",
            recommended_action="pin_source_commit_or_snapshot_before_writing_source_version",
        )

    return _row(
        family=family,
        pack=pack,
        candidate_field="source_label" if candidate else "",
        candidate_value=candidate,
        classification="unknown",
        rationale="No safe source-version or source-dump rule matched this catalog entry.",
        recommended_action="manual_source_identity_review_required",
    )


def _row(
    *,
    family: str,
    pack: object,
    candidate_field: str,
    candidate_value: str,
    classification: str,
    rationale: str,
    recommended_action: str,
) -> dict[str, object]:
    return {
        "family": family,
        "pack_id": _text(getattr(pack, "pack_id", "")),
        "source_name": _text(getattr(pack, "source", "")),
        "build_mode": _text(getattr(pack, "build_mode", "download_only")) or "download_only",
        "filename": _text(getattr(pack, "filename", "")),
        "source_filename": _text(getattr(pack, "source_filename", "")),
        "source_url": _text(getattr(pack, "url", "")),
        "candidate_field": candidate_field,
        "candidate_value": candidate_value,
        "classification": classification,
        "rationale": rationale,
        "recommended_action": recommended_action,
    }


def _summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    counts = {classification: 0 for classification in CLASSIFICATIONS}
    for row in rows:
        classification = str(row.get("classification") or "unknown")
        counts[classification] = counts.get(classification, 0) + 1
    needs_decision = sum(
        counts.get(classification, 0)
        for classification in ("label_only", "needs_policy", "source_bundle_needed", "unknown")
    )
    return {
        "pack_count": len(rows),
        "classification_counts": counts,
        "safe_to_write_count": counts.get("safe_to_write", 0),
        "needs_decision_count": needs_decision,
    }


def _artifact_identity(filename: str) -> str:
    value = _text(filename)
    for suffix in (
        ".src.tar.xz",
        ".tar.xz",
        ".tar.gz",
        ".jsonl.gz",
        ".tab.gz",
        ".db.gz",
        ".vec.gz",
        ".txt",
        ".zip",
        ".gz",
        ".u8",
    ):
        if value.lower().endswith(suffix):
            return value[: -len(suffix)]
    return Path(value).stem if value else ""


def _release_tag(url: str) -> str:
    match = _RELEASE_TAG_RE.search(str(url or ""))
    return match.group(1) if match else ""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _string_sequence(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [str(item) for item in value]


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
