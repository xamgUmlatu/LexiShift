from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
from pathlib import Path
import re
from typing import Mapping


SOURCE_IDENTITY_CLASSIFICATIONS = (
    "safe_to_write",
    "label_only",
    "needs_policy",
    "source_bundle_needed",
    "unknown",
)

_RELEASE_TAG_RE = re.compile(r"/releases/download/([^/]+)/")
_DATED_DUMP_RE = re.compile(r"(?<!\d)((?:19|20)\d{2})[-_]?([01]\d)[-_]?([0-3]\d)(?!\d)")
_GIT_COMMIT_RE = re.compile(r"(?<![0-9a-fA-F])([0-9a-fA-F]{40})(?![0-9a-fA-F])")
_KAIKKI_DUMP_FAMILY = "enwiktionary"


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
    explicit_source_version = _text(getattr(pack, "source_version", ""))
    explicit_source_dump = _text(getattr(pack, "source_dump", ""))
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
        dated_dump = _dated_dump_identity((explicit_source_dump, source_url, filename))
        if explicit_source_dump:
            return PackSourceIdentityDecision(
                candidate_field="source_dump",
                candidate_value=dated_dump or explicit_source_dump,
                classification="safe_to_write" if dated_dump else "needs_policy",
                rationale=(
                    "Catalog carries an explicit dated Wiktextract dump identity."
                    if dated_dump
                    else (
                        "Catalog carries source_dump, but it is not a dated "
                        "Wiktextract dump identity."
                    )
                ),
                recommended_action=(
                    "eligible_for_future_source_dump_writer"
                    if dated_dump
                    else "record_dated_wiktextract_dump_before_writing_source_dump"
                ),
            )
        return PackSourceIdentityDecision(
            candidate_field="source_dump",
            candidate_value=dated_dump or _KAIKKI_DUMP_FAMILY,
            classification="safe_to_write" if dated_dump else "needs_policy",
            rationale=(
                "Catalog identifies a dated Wiktextract dump identity."
                if dated_dump
                else (
                    "Catalog identifies the Wiktextract dump family, but the shared raw dump "
                    "URL does not pin a dated dump."
                )
            ),
            recommended_action=(
                "eligible_for_future_source_dump_writer"
                if dated_dump
                else "record_dated_wiktextract_dump_before_writing_source_dump"
            ),
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

    if pack_id == "freq-en-leipzig-default":
        return PackSourceIdentityDecision(
            candidate_field="source_label",
            candidate_value=candidate or "eng_news_2025_1M",
            classification="source_bundle_needed",
            rationale=(
                "Leipzig corpus filename identifies the source corpus, but source-bundle "
                "metadata should carry URL/checksum lineage for generated SQLite artifacts."
            ),
            recommended_action="record_source_bundle_for_generated_pack",
        )

    if pack_id == "freq-es-spalex-v1":
        return PackSourceIdentityDecision(
            candidate_field="source_version",
            candidate_value=explicit_source_version or "10.6084/m9.figshare.5924794.v4",
            classification="safe_to_write",
            rationale="SPALEX catalog entry pins the Figshare dataset DOI/version.",
            recommended_action="eligible_for_future_source_version_writer",
        )

    if pack_id in {"moby-en", "jmdict-ja-en", "cc-cedict-zh-en"}:
        return PackSourceIdentityDecision(
            candidate_field="source_label",
            candidate_value=candidate,
            classification="needs_policy",
            rationale="Catalog filename is useful, but release/snapshot semantics need source policy.",
            recommended_action="confirm_release_or_snapshot_semantics_before_writing_source_version",
        )

    if _is_branch_source_url(source_url):
        if explicit_source_version:
            pinned_source_version = _pinned_git_source_version(explicit_source_version)
            return PackSourceIdentityDecision(
                candidate_field="source_version",
                candidate_value=pinned_source_version or explicit_source_version,
                classification="safe_to_write" if pinned_source_version else "needs_policy",
                rationale=(
                    "Catalog carries an explicit source_version with a pinned commit hash."
                    if pinned_source_version
                    else (
                        "Catalog carries source_version for a branch/head source, but it "
                        "does not include a pinned commit hash."
                    )
                ),
                recommended_action=(
                    "eligible_for_future_source_version_writer"
                    if pinned_source_version
                    else "pin_source_commit_or_snapshot_before_writing_source_version"
                ),
            )
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


def source_bundle_fields_for_pack(
    pack: object,
    *,
    component_paths: Mapping[str, Path] | None = None,
) -> dict[str, Mapping[str, object]]:
    build_mode = _text(getattr(pack, "build_mode", "download_only")) or "download_only"
    if build_mode == "de_frequency_pipeline":
        return {"source_bundle": _de_frequency_source_bundle(pack, component_paths=component_paths)}
    if build_mode == "en_frequency_pipeline":
        return {"source_bundle": _en_frequency_source_bundle(pack, component_paths=component_paths)}
    return {}


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


def _is_branch_source_url(url: str) -> bool:
    source_url = str(url or "")
    return "refs/heads/" in source_url or "/raw/master/" in source_url


def _pinned_git_source_version(value: str) -> str:
    text = _text(value)
    if _GIT_COMMIT_RE.search(text):
        return text
    return ""


def _dated_dump_identity(values: tuple[str, ...]) -> str:
    for value in values:
        match = _DATED_DUMP_RE.search(str(value or ""))
        if match:
            normalized_date = _normalized_date_match(match)
            if normalized_date:
                return f"{_KAIKKI_DUMP_FAMILY}:{normalized_date}"
    return ""


def _de_frequency_source_bundle(
    pack: object,
    *,
    component_paths: Mapping[str, Path] | None = None,
) -> dict[str, object]:
    from lexishift_core.frequency.de import pipeline as de_pipeline

    pack_id = _text(getattr(pack, "pack_id", "")) or "freq-de-default"
    corpus_filename = _text(getattr(pack, "source_filename", "")) or _text(
        getattr(pack, "filename", "")
    )
    components: list[dict[str, object]] = [
        {
            "role": "corpus",
            "source_name": _text(getattr(pack, "source", "")) or "Leipzig Wortschatz",
            "source_url": _text(getattr(pack, "url", "")) or de_pipeline.LEIPZIG_CORPUS_URL,
            "filename": corpus_filename or Path(de_pipeline.LEIPZIG_CORPUS_URL).name,
        },
        {
            "role": "lexicon_whitelist",
            "source_name": "FreeDict DE-EN",
            "source_url": de_pipeline.FREEDICT_DE_EN_URL,
            "filename": Path(de_pipeline.FREEDICT_DE_EN_URL).name,
        },
        {
            "role": "lexicon_whitelist",
            "source_name": "OdeNet",
            "source_url": de_pipeline.ODENET_URL,
            "filename": "odenet_oneline.xml",
        },
        {
            "role": "lexicon_whitelist",
            "source_name": "OpenThesaurus",
            "source_url": de_pipeline.OPENTHESAURUS_URL,
            "filename": "openthesaurus.txt",
        },
        {
            "role": "pos_lexicon_primary",
            "source_name": "german-pos-dict german.dict",
            "source_url": de_pipeline.GERMAN_POS_DICT_URL,
            "filename": "german.dict",
        },
        {
            "role": "pos_lexicon_primary_metadata",
            "source_name": "german-pos-dict german.info",
            "source_url": de_pipeline.GERMAN_POS_INFO_URL,
            "filename": "german.info",
        },
        {
            "role": "pos_lexicon_fallback",
            "source_name": "german-pos-dict EIG",
            "source_url": de_pipeline.GERMAN_POS_EIG_URL,
            "filename": "EIG.txt",
        },
        {
            "role": "pos_lexicon_fallback",
            "source_name": "german-pos-dict sonstige",
            "source_url": de_pipeline.GERMAN_POS_SONSTIGE_URL,
            "filename": "sonstige.txt",
        },
    ]
    for filename, url in sorted(de_pipeline.MORFOLOGIK_TOOLS.items()):
        components.append(
            {
                "role": "pos_tooling",
                "source_name": "Morfologik tools",
                "source_url": url,
                "filename": filename,
            }
        )
    checked_components = [
        _with_component_checksum(component, component_paths or {}) for component in components
    ]
    return {
        "bundle_id": f"{pack_id}:de_frequency_pipeline",
        "bundle_kind": "generated_frequency_pipeline",
        "lineage_status": "component_urls_recorded",
        "components": checked_components,
        "notes": [
            "source_bundle_is_not_license_approval",
            "de_pos_source_auto_prefers_german_dict_then_eig_sonstige",
        ],
    }


def _en_frequency_source_bundle(
    pack: object,
    *,
    component_paths: Mapping[str, Path] | None = None,
) -> dict[str, object]:
    from lexishift_core.frequency.en import pipeline as en_pipeline

    pack_id = _text(getattr(pack, "pack_id", "")) or "freq-en-leipzig-default"
    corpus_filename = _text(getattr(pack, "source_filename", "")) or _text(
        getattr(pack, "filename", "")
    )
    source_url = _text(getattr(pack, "url", "")) or en_pipeline.LEIPZIG_EN_CORPUS_URL
    components: list[dict[str, object]] = [
        {
            "role": "corpus",
            "source_name": _text(getattr(pack, "source", "")) or "Leipzig Wortschatz",
            "source_url": source_url,
            "filename": corpus_filename or Path(source_url).name,
        },
    ]
    checked_components = [
        _with_component_checksum(component, component_paths or {}) for component in components
    ]
    return {
        "bundle_id": f"{pack_id}:en_frequency_pipeline",
        "bundle_kind": "generated_frequency_pipeline",
        "lineage_status": "component_urls_recorded",
        "components": checked_components,
        "notes": [
            "source_bundle_is_not_license_approval",
            "english_leipzig_pipeline_uses_source_frequency_only_no_pos_overlay",
        ],
    }


def _normalized_date_match(match: re.Match[str]) -> str:
    year, month, day = (int(value) for value in match.groups())
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return ""


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _with_component_checksum(
    component: Mapping[str, object],
    component_paths: Mapping[str, Path],
) -> dict[str, object]:
    item = dict(component)
    filename = _text(item.get("filename"))
    source_path = component_paths.get(filename) if filename else None
    checksums = _file_checksums(source_path) if source_path is not None else {}
    item.update(checksums)
    return item


def _file_checksums(path: Path) -> dict[str, str]:
    file_path = Path(path)
    if not file_path.is_file():
        return {}
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()
    with file_path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            sha1.update(chunk)
            sha256.update(chunk)
    return {
        "sha1": sha1.hexdigest(),
        "sha256": sha256.hexdigest(),
    }
