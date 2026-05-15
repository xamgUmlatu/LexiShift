from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


SOURCE_IDENTITY_CLASSIFICATIONS = (
    "safe_to_write",
    "label_only",
    "needs_policy",
    "source_bundle_needed",
    "unknown",
)

_RELEASE_TAG_RE = re.compile(r"/releases/download/([^/]+)/")


@dataclass(frozen=True)
class PackSourceIdentityDecision:
    candidate_field: str
    candidate_value: str
    classification: str
    rationale: str
    recommended_action: str


def classify_pack_source_identity(pack: object) -> PackSourceIdentityDecision:
    pack_id = _text(getattr(pack, "pack_id", ""))
    filename = _text(getattr(pack, "source_filename", "")) or _text(getattr(pack, "filename", ""))
    source_name = _text(getattr(pack, "source", ""))
    source_url = _text(getattr(pack, "url", ""))
    build_mode = _text(getattr(pack, "build_mode", "download_only")) or "download_only"
    candidate = _artifact_identity(filename)

    if build_mode == "de_frequency_pipeline":
        return PackSourceIdentityDecision(
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
        return PackSourceIdentityDecision(
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
        return PackSourceIdentityDecision(
            candidate_field="source_version",
            candidate_value=candidate,
            classification="safe_to_write",
            rationale="FreeDict source archive filename and URL carry the dictionary release id.",
            recommended_action="eligible_for_future_source_version_writer",
        )

    if pack_id == "wordnet-en":
        return PackSourceIdentityDecision(
            candidate_field="source_version",
            candidate_value=candidate,
            classification="safe_to_write",
            rationale="WordNet catalog filename includes the source package year/id.",
            recommended_action="eligible_for_future_source_version_writer",
        )

    if pack_id == "freq-ja-bccwj":
        return PackSourceIdentityDecision(
            candidate_field="source_version",
            candidate_value="BCCWJ_frequencylist_suw_ver1_0",
            classification="safe_to_write",
            rationale="BCCWJ archive/source filename carries an explicit ver1_0 identifier.",
            recommended_action="eligible_for_future_source_version_writer",
        )

    if source_name.lower() == "kaikki":
        return PackSourceIdentityDecision(
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
        return PackSourceIdentityDecision(
            candidate_field="source_label",
            candidate_value=candidate,
            classification="needs_policy",
            rationale="fastText artifact filename identifies model family/language but not a release.",
            recommended_action="confirm_fasttext_release_or_snapshot_before_writing_source_version",
        )

    if pack_id in {"freq-en-coca", "freq-es-cde"}:
        return PackSourceIdentityDecision(
            candidate_field="source_label",
            candidate_value=candidate,
            classification="label_only",
            rationale="Filename is a useful sample/artifact label, not clearly a source release.",
            recommended_action="keep_as_label_until_source_policy_defines_version_semantics",
        )

    if pack_id in {"moby-en", "jmdict-ja-en", "cc-cedict-zh-en"}:
        return PackSourceIdentityDecision(
            candidate_field="source_label",
            candidate_value=candidate,
            classification="needs_policy",
            rationale="Catalog filename is useful, but release/snapshot semantics need source policy.",
            recommended_action="confirm_release_or_snapshot_semantics_before_writing_source_version",
        )

    if "refs/heads/" in source_url or "/raw/master/" in source_url:
        return PackSourceIdentityDecision(
            candidate_field="source_label",
            candidate_value=candidate,
            classification="needs_policy",
            rationale="Catalog URL follows a branch/head rather than a pinned source release.",
            recommended_action="pin_source_commit_or_snapshot_before_writing_source_version",
        )

    return PackSourceIdentityDecision(
        candidate_field="source_label" if candidate else "",
        candidate_value=candidate,
        classification="unknown",
        rationale="No safe source-version or source-dump rule matched this catalog entry.",
        recommended_action="manual_source_identity_review_required",
    )


def safe_pack_source_identity_fields(pack: object) -> dict[str, str]:
    decision = classify_pack_source_identity(pack)
    if decision.classification != "safe_to_write" or not decision.candidate_value:
        return {}
    if decision.candidate_field not in {"source_version", "source_dump"}:
        return {}
    return {decision.candidate_field: decision.candidate_value}


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


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()
