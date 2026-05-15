from __future__ import annotations

import json
import os
import re
from pathlib import Path
import tempfile
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
        _validate_build(build, errors)

    artifact = _required_mapping(payload, "artifact", "artifact", errors)
    if artifact is not None:
        _validate_artifact(artifact, "artifact", errors)

    return tuple(errors)


def write_app_managed_pack_provenance(
    *,
    pack_root: Path,
    pack_id: str,
    pack_kind: str,
    provider: str,
    source_name: str,
    source_url: str,
    build_mode: str,
    artifact_path: Path,
    source_filename: str | None = None,
    sqlite_filename: str | None = None,
    required_files: Sequence[str] = (),
    wayback_url: str | None = None,
    license_status: str = "requires_review",
    build_command: str | None = None,
    converter_version: str | None = None,
    parser_profile: str | None = None,
    parser_config: Mapping[str, object] | None = None,
    source_version: str | None = None,
    source_dump: str | None = None,
    raw_artifact_sha1: str | None = None,
    raw_artifact_sha256: str | None = None,
) -> Path:
    target_root = Path(pack_root)
    artifact = Path(artifact_path)
    payload = build_app_managed_pack_provenance_payload(
        pack_root=target_root,
        pack_id=pack_id,
        pack_kind=pack_kind,
        provider=provider,
        source_name=source_name,
        source_url=source_url,
        build_mode=build_mode,
        artifact_path=artifact,
        source_filename=source_filename,
        sqlite_filename=sqlite_filename,
        required_files=required_files,
        wayback_url=wayback_url,
        license_status=license_status,
        build_command=build_command,
        converter_version=converter_version,
        parser_profile=parser_profile,
        parser_config=parser_config,
        source_version=source_version,
        source_dump=source_dump,
        raw_artifact_sha1=raw_artifact_sha1,
        raw_artifact_sha256=raw_artifact_sha256,
    )
    provenance_path = target_root / PACK_PROVENANCE_FILENAME
    _write_json(provenance_path, payload)
    return provenance_path


def build_app_managed_pack_provenance_payload(
    *,
    pack_root: Path,
    pack_id: str,
    pack_kind: str,
    provider: str,
    source_name: str,
    source_url: str,
    build_mode: str,
    artifact_path: Path,
    source_filename: str | None = None,
    sqlite_filename: str | None = None,
    required_files: Sequence[str] = (),
    wayback_url: str | None = None,
    license_status: str = "requires_review",
    build_command: str | None = None,
    converter_version: str | None = None,
    parser_profile: str | None = None,
    parser_config: Mapping[str, object] | None = None,
    source_version: str | None = None,
    source_dump: str | None = None,
    raw_artifact_sha1: str | None = None,
    raw_artifact_sha256: str | None = None,
) -> dict[str, object]:
    raw_filename = _optional_text(source_filename) or Path(source_url).name or str(pack_id)
    artifact_relpath = _artifact_relpath(Path(pack_root), Path(artifact_path))
    raw_artifact: dict[str, object] = {"filename": raw_filename}
    if raw_sha1_text := _optional_text(raw_artifact_sha1):
        raw_artifact["sha1"] = raw_sha1_text
    if raw_sha256_text := _optional_text(raw_artifact_sha256):
        raw_artifact["sha256"] = raw_sha256_text
    source: dict[str, object] = {
        "source_name": _optional_text(source_name) or _optional_text(provider) or str(pack_id),
        "source_url": str(source_url or "").strip(),
        "license_status": str(license_status or "requires_review").strip(),
        "raw_artifacts": [raw_artifact],
    }
    if wayback_url_text := _optional_text(wayback_url):
        source["wayback_url"] = wayback_url_text
    if source_version_text := _optional_text(source_version):
        source["source_version"] = source_version_text
    if source_dump_text := _optional_text(source_dump):
        source["source_dump"] = source_dump_text
    build: dict[str, object] = {
        "build_mode": str(build_mode or "").strip() or "download_only",
    }
    if build_command_text := _optional_text(build_command):
        build["command"] = build_command_text
    if converter_version_text := _optional_text(converter_version):
        build["converter_version"] = converter_version_text
    if parser_profile_text := _optional_text(parser_profile):
        build["parser_profile"] = parser_profile_text
    if parser_config:
        build["parser_config"] = dict(parser_config)
    if sqlite_filename_text := _optional_text(sqlite_filename):
        build["sqlite_filename"] = sqlite_filename_text
    required_file_values = tuple(
        str(item or "").strip() for item in required_files if str(item or "").strip()
    )
    if required_file_values:
        build["required_files"] = list(required_file_values)
    return {
        "schema_version": PACK_PROVENANCE_SCHEMA_VERSION,
        "pack_id": str(pack_id or "").strip(),
        "pack_kind": str(pack_kind or "").strip(),
        "provider": str(provider or "").strip(),
        "source": source,
        "build": build,
        "artifact": {
            "artifact_relpath": artifact_relpath,
            "artifact_kind": _infer_artifact_kind(Path(artifact_path)),
            "sha1": _sha1_file(Path(artifact_path)) if Path(artifact_path).is_file() else None,
        },
    }


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
    _optional_text_field(source, "source_version", "source.source_version", errors)
    _optional_text_field(source, "source_dump", "source.source_dump", errors)
    if not _optional_text(source.get("source_url")) and not _optional_text(
        source.get("local_source_path")
    ):
        errors.append("source must include source_url or local_source_path")
    raw_artifacts = source.get("raw_artifacts")
    if raw_artifacts is not None:
        _validate_artifact_list(raw_artifacts, "source.raw_artifacts", errors)


def _validate_build(build: Mapping[str, object], errors: list[str]) -> None:
    _required_text(build, "build_mode", "build.build_mode", errors)
    _optional_text_field(build, "command", "build.command", errors)
    _optional_text_field(build, "converter_version", "build.converter_version", errors)
    _optional_text_field(build, "parser_profile", "build.parser_profile", errors)
    parser_config = build.get("parser_config")
    if parser_config is not None and not isinstance(parser_config, Mapping):
        errors.append("build.parser_config must be a JSON object")


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


def _optional_text_field(
    payload: Mapping[str, object],
    key: str,
    field_path: str,
    errors: list[str],
) -> None:
    if key in payload and not _optional_text(payload.get(key)):
        errors.append(f"{field_path} must not be blank when present")


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


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    _write_text_atomic(
        path,
        json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if temp_name and Path(temp_name).exists():
            Path(temp_name).unlink()


def _sha1_file(path: Path) -> str:
    from hashlib import sha1

    return sha1(path.read_bytes()).hexdigest()


def _artifact_relpath(pack_root: Path, artifact_path: Path) -> str:
    resolved_root = pack_root.resolve()
    resolved_artifact = artifact_path.resolve()
    if resolved_artifact == resolved_root:
        return "."
    try:
        return resolved_artifact.relative_to(resolved_root).as_posix()
    except ValueError:
        return artifact_path.name


def _infer_artifact_kind(path: Path) -> str:
    if path.is_dir():
        return "directory"
    suffix = path.suffix.lower()
    if suffix in {".sqlite", ".sqlite3", ".db"}:
        return "sqlite"
    if suffix in {".vec", ".bin"}:
        return "embedding"
    return "file"
