from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Mapping, Sequence


PACK_PROVENANCE_FILENAME = "provenance.json"
PACK_PROVENANCE_SCHEMA_VERSION = 1
LICENSE_STATUS_VALUES = frozenset(
    {
        "confirmed",
        "requires_review",
        "unknown",
        "not_redistributable",
        "internal_only",
    }
)
ARTIFACT_KIND_VALUES = frozenset(
    {
        "file",
        "directory",
        "sqlite",
        "embedding",
        "semantic_inventory",
        "other",
    }
)

_HEX_RE = re.compile(r"^[0-9a-fA-F]+$")


def validate_pack_provenance_file(path: Path) -> tuple[str, ...]:
    candidate = Path(path)
    if not candidate.exists() or not candidate.is_file():
        return (f"{candidate} is missing",)
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return (f"{candidate} is not valid JSON: {exc}",)
    return validate_pack_provenance_payload(payload)


def validate_pack_provenance_payload(payload: object) -> tuple[str, ...]:
    if not isinstance(payload, Mapping):
        return ("payload must be a JSON object",)

    errors: list[str] = []
    _validate_schema_version(payload, errors)
    _required_text(payload, "pack_id", "pack_id", errors)
    _required_text(payload, "pack_kind", "pack_kind", errors)
    _required_text(payload, "provider", "provider", errors)

    source = _required_mapping(payload, "source", "source", errors)
    if source is not None:
        _validate_source(source, errors)

    build = _required_mapping(payload, "build", "build", errors)
    if build is not None:
        _required_text(build, "build_mode", "build.build_mode", errors)

    artifact = _required_mapping(payload, "artifact", "artifact", errors)
    if artifact is not None:
        _validate_artifact(artifact, "artifact", errors)

    return tuple(errors)


def _validate_schema_version(payload: Mapping[str, object], errors: list[str]) -> None:
    schema_version = payload.get("schema_version")
    if isinstance(schema_version, bool) or schema_version != PACK_PROVENANCE_SCHEMA_VERSION:
        errors.append(
            f"schema_version must be {PACK_PROVENANCE_SCHEMA_VERSION}, got {schema_version!r}"
        )


def _validate_source(source: Mapping[str, object], errors: list[str]) -> None:
    _required_text(source, "source_name", "source.source_name", errors)
    license_status = _required_text(source, "license_status", "source.license_status", errors)
    if license_status and license_status not in LICENSE_STATUS_VALUES:
        allowed = ", ".join(sorted(LICENSE_STATUS_VALUES))
        errors.append(f"source.license_status must be one of: {allowed}")
    if not _optional_text(source.get("source_url")) and not _optional_text(
        source.get("local_source_path")
    ):
        errors.append("source must include source_url or local_source_path")
    raw_artifacts = source.get("raw_artifacts")
    if raw_artifacts is not None:
        _validate_artifact_list(raw_artifacts, "source.raw_artifacts", errors)


def _validate_artifact(
    artifact: Mapping[str, object],
    field_path: str,
    errors: list[str],
) -> None:
    _required_text(artifact, "artifact_relpath", f"{field_path}.artifact_relpath", errors)
    artifact_kind = _required_text(artifact, "artifact_kind", f"{field_path}.artifact_kind", errors)
    if artifact_kind and artifact_kind not in ARTIFACT_KIND_VALUES:
        allowed = ", ".join(sorted(ARTIFACT_KIND_VALUES))
        errors.append(f"{field_path}.artifact_kind must be one of: {allowed}")
    _validate_checksums(artifact, field_path, errors)
    metrics = artifact.get("metrics")
    if metrics is not None:
        if not isinstance(metrics, Mapping):
            errors.append(f"{field_path}.metrics must be a JSON object")
        else:
            _validate_metrics(metrics, f"{field_path}.metrics", errors)


def _validate_artifact_list(value: object, field_path: str, errors: list[str]) -> None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        errors.append(f"{field_path} must be a list")
        return
    for index, item in enumerate(value):
        item_path = f"{field_path}[{index}]"
        if not isinstance(item, Mapping):
            errors.append(f"{item_path} must be a JSON object")
            continue
        _required_text(item, "filename", f"{item_path}.filename", errors)
        _validate_checksums(item, item_path, errors)


def _validate_metrics(
    metrics: Mapping[str, object],
    field_path: str,
    errors: list[str],
) -> None:
    row_count = _optional_non_negative_int(metrics, "row_count", field_path, errors)
    distinct_lemma_count = _optional_non_negative_int(
        metrics,
        "distinct_lemma_count",
        field_path,
        errors,
    )
    pos_rows = _optional_non_negative_int(metrics, "pos_rows", field_path, errors)
    topic_domain_rows = _optional_non_negative_int(
        metrics,
        "topic_domain_rows",
        field_path,
        errors,
    )
    if (
        row_count is not None
        and distinct_lemma_count is not None
        and distinct_lemma_count > row_count
    ):
        errors.append(f"{field_path}.distinct_lemma_count cannot exceed row_count")
    if row_count is not None and pos_rows is not None and pos_rows > row_count:
        errors.append(f"{field_path}.pos_rows cannot exceed row_count")
    if row_count is not None and topic_domain_rows is not None and topic_domain_rows > row_count:
        errors.append(f"{field_path}.topic_domain_rows cannot exceed row_count")


def _validate_checksums(
    payload: Mapping[str, object],
    field_path: str,
    errors: list[str],
) -> None:
    _validate_checksum(payload.get("sha1"), f"{field_path}.sha1", expected_length=40, errors=errors)
    _validate_checksum(
        payload.get("sha256"),
        f"{field_path}.sha256",
        expected_length=64,
        errors=errors,
    )


def _validate_checksum(
    value: object,
    field_path: str,
    *,
    expected_length: int,
    errors: list[str],
) -> None:
    if value is None:
        return
    text = _optional_text(value)
    if not text:
        errors.append(f"{field_path} must not be blank when present")
        return
    if len(text) != expected_length or _HEX_RE.fullmatch(text) is None:
        errors.append(f"{field_path} must be {expected_length} hex characters")


def _required_mapping(
    payload: Mapping[str, object],
    key: str,
    field_path: str,
    errors: list[str],
) -> Mapping[str, object] | None:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        errors.append(f"{field_path} must be a JSON object")
        return None
    return value


def _required_text(
    payload: Mapping[str, object],
    key: str,
    field_path: str,
    errors: list[str],
) -> str:
    text = _optional_text(payload.get(key))
    if not text:
        errors.append(f"{field_path} is required")
        return ""
    return text


def _optional_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _optional_non_negative_int(
    payload: Mapping[str, object],
    key: str,
    field_path: str,
    errors: list[str],
) -> int | None:
    if key not in payload or payload.get(key) is None:
        return None
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append(f"{field_path}.{key} must be a non-negative integer")
        return None
    if value < 0:
        errors.append(f"{field_path}.{key} must be a non-negative integer")
        return None
    return value
