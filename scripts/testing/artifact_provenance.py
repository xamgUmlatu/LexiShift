from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HASH_SIZE_LIMIT_BYTES = 64 * 1024 * 1024


def build_artifact_provenance(
    *,
    producer_script: Path,
    input_paths: Mapping[str, Path | None] | Sequence[Path | None] = (),
    code_paths: Mapping[str, Path | None] | Sequence[Path | None] = (),
    version_constants: Mapping[str, object] | None = None,
    argv: Sequence[str] | None = None,
    project_root: Path = PROJECT_ROOT,
    input_hash_size_limit_bytes: int = DEFAULT_HASH_SIZE_LIMIT_BYTES,
) -> dict[str, object]:
    """Build provenance for generated testing artifacts.

    This is intentionally about generated test-output freshness, not third-party
    data licensing or pack lineage.
    """

    resolved_project_root = project_root.resolve()
    producer = _file_record(
        producer_script,
        label="producer_script",
        project_root=resolved_project_root,
        require_hash=True,
        hash_size_limit_bytes=input_hash_size_limit_bytes,
    )
    dependencies = [
        _file_record(
            path,
            label=label,
            project_root=resolved_project_root,
            require_hash=True,
            hash_size_limit_bytes=input_hash_size_limit_bytes,
        )
        for label, path in _named_paths(code_paths)
        if path is not None and Path(path).resolve() != Path(producer_script).resolve()
    ]
    inputs = [
        _file_record(
            path,
            label=label,
            project_root=resolved_project_root,
            require_hash=False,
            hash_size_limit_bytes=input_hash_size_limit_bytes,
        )
        for label, path in _named_paths(input_paths)
        if path is not None
    ]
    return {
        "schema_version": 1,
        "kind": "testing_artifact_provenance",
        "generated_at": utc_now(),
        "cwd": str(Path.cwd()),
        "command": _shell_join(tuple(argv if argv is not None else sys.argv)),
        "project_root": str(resolved_project_root),
        "git": _git_info(resolved_project_root),
        "producer": producer,
        "code_dependencies": dependencies,
        "inputs": inputs,
        "version_constants": dict(version_constants or {}),
        "hash_policy": {
            "code": "sha256_required",
            "inputs": (
                f"sha256_if_size_lte_{int(input_hash_size_limit_bytes)}_else_size_and_mtime"
            ),
        },
    }


def attach_provenance_to_npz_metadata(
    arrays: Mapping[str, object],
    provenance: Mapping[str, object],
) -> dict[str, object]:
    updated = dict(arrays)
    metadata_raw = updated.get("metadata_json")
    metadata_text = _metadata_text(metadata_raw)
    metadata = json.loads(metadata_text) if metadata_text else {}
    metadata["provenance"] = dict(provenance)
    updated["metadata_json"] = json.dumps(
        metadata,
        ensure_ascii=False,
        sort_keys=True,
    )
    return updated


def validate_artifact_freshness(
    artifact_path: Path,
    *,
    project_root: Path = PROJECT_ROOT,
    input_hash_size_limit_bytes: int = DEFAULT_HASH_SIZE_LIMIT_BYTES,
    _depth: int = 0,
) -> dict[str, object]:
    artifact = artifact_path.resolve()
    payload = _load_artifact_payload(artifact)
    provenance = payload.get("provenance") if isinstance(payload, Mapping) else None
    if not isinstance(provenance, Mapping):
        return {
            "artifact": _path_display(artifact, project_root=project_root.resolve()),
            "status": "stale",
            "fresh": False,
            "failures": ["missing_provenance"],
            "warnings": [],
        }

    failures: list[str] = []
    warnings: list[str] = []

    producer = provenance.get("producer")
    if isinstance(producer, Mapping):
        failures.extend(
            _compare_file_record(
                producer,
                project_root=project_root,
                hash_size_limit_bytes=input_hash_size_limit_bytes,
                nested_artifact_depth=_depth + 1,
            )
        )
    else:
        failures.append("missing_producer_record")

    for category in ("code_dependencies", "inputs"):
        records = provenance.get(category)
        if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
            failures.append(f"missing_{category}")
            continue
        for record in records:
            if not isinstance(record, Mapping):
                failures.append(f"invalid_{category}_record")
                continue
            failures.extend(
                _compare_file_record(
                    record,
                    project_root=project_root,
                    hash_size_limit_bytes=input_hash_size_limit_bytes,
                    nested_artifact_depth=_depth + 1,
                )
            )

    current_git = _git_info(project_root.resolve())
    recorded_git = provenance.get("git")
    if isinstance(recorded_git, Mapping):
        if recorded_git.get("head") != current_git.get("head"):
            warnings.append("git_head_changed")
        if recorded_git.get("branch") != current_git.get("branch"):
            warnings.append("git_branch_changed")

    status = "fresh" if not failures else "stale"
    return {
        "artifact": _path_display(artifact, project_root=project_root.resolve()),
        "status": status,
        "fresh": status == "fresh",
        "generated_at": provenance.get("generated_at"),
        "producer": _record_display(producer),
        "failures": failures,
        "warnings": warnings,
    }


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _file_record(
    path: Path | str,
    *,
    label: str,
    project_root: Path,
    require_hash: bool,
    hash_size_limit_bytes: int,
) -> dict[str, object]:
    resolved = _resolve_path(Path(path), project_root=project_root)
    record: dict[str, object] = {
        "label": str(label),
        "path": _path_display(resolved, project_root=project_root),
        "absolute_path": str(resolved),
        "repo_path": _repo_relative(resolved, project_root=project_root),
    }
    if not resolved.exists():
        record.update(
            {
                "exists": False,
                "sha256_status": "missing",
            }
        )
        return record
    stat = resolved.stat()
    record.update(
        {
            "exists": True,
            "size_bytes": int(stat.st_size),
            "mtime_ns": int(stat.st_mtime_ns),
            "mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
        }
    )
    if resolved.is_file() and (require_hash or stat.st_size <= int(hash_size_limit_bytes)):
        record["sha256"] = _sha256_file(resolved)
        record["sha256_status"] = "computed"
    elif resolved.is_file():
        record["sha256_status"] = "skipped_large"
    else:
        record["sha256_status"] = "not_file"
    return record


def _compare_file_record(
    record: Mapping[str, object],
    *,
    project_root: Path,
    hash_size_limit_bytes: int,
    nested_artifact_depth: int,
) -> list[str]:
    label = str(record.get("label") or record.get("path") or "unknown")
    path = _path_from_record(record, project_root=project_root.resolve())
    current = _file_record(
        path,
        label=label,
        project_root=project_root.resolve(),
        require_hash=record.get("sha256_status") == "computed",
        hash_size_limit_bytes=hash_size_limit_bytes,
    )
    failures: list[str] = []
    if not current.get("exists"):
        return [f"{label}:missing_current_file"]
    if record.get("exists") is False:
        failures.append(f"{label}:was_missing_now_exists")
    if record.get("sha256_status") == "computed":
        if current.get("sha256") != record.get("sha256"):
            failures.append(f"{label}:sha256_changed")
    else:
        for key in ("size_bytes", "mtime_ns"):
            if record.get(key) != current.get(key):
                failures.append(f"{label}:{key}_changed")
    nested_failure = _nested_artifact_failure(
        path,
        label=label,
        project_root=project_root,
        hash_size_limit_bytes=hash_size_limit_bytes,
        depth=nested_artifact_depth,
    )
    if nested_failure:
        failures.append(nested_failure)
    return failures


def _load_artifact_payload(path: Path) -> Mapping[str, object]:
    if path.suffix == ".npz":
        import numpy as np

        data = np.load(path)
        metadata_text = _metadata_text(data["metadata_json"]) if "metadata_json" in data else ""
        return json.loads(metadata_text) if metadata_text else {}
    return json.loads(path.read_text(encoding="utf-8"))


def _metadata_text(value: object) -> str:
    if value is None:
        return ""
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def _nested_artifact_failure(
    path: Path,
    *,
    label: str,
    project_root: Path,
    hash_size_limit_bytes: int,
    depth: int,
) -> str:
    if depth > 2:
        return ""
    repo_path = _repo_relative(path, project_root=project_root)
    if not repo_path.startswith("docs/test_outputs/"):
        return ""
    if path.suffix not in {".json", ".npz"}:
        return ""
    nested = validate_artifact_freshness(
        path,
        project_root=project_root,
        input_hash_size_limit_bytes=hash_size_limit_bytes,
        _depth=depth,
    )
    if nested.get("fresh"):
        return ""
    failures = ", ".join(str(item) for item in nested.get("failures", ()) or ())
    return f"{label}:input_artifact_stale[{failures}]"


def _named_paths(
    paths: Mapping[str, Path | None] | Sequence[Path | None],
) -> list[tuple[str, Path | None]]:
    if isinstance(paths, Mapping):
        return [(str(label), path) for label, path in paths.items()]
    return [(str(index), path) for index, path in enumerate(paths)]


def _path_from_record(record: Mapping[str, object], *, project_root: Path) -> Path:
    repo_path = record.get("repo_path")
    if isinstance(repo_path, str) and repo_path:
        return project_root / repo_path
    absolute_path = record.get("absolute_path")
    if isinstance(absolute_path, str) and absolute_path:
        return Path(absolute_path)
    path = str(record.get("path") or "")
    if path.startswith("~/"):
        return Path.home() / path[2:]
    return _resolve_path(Path(path), project_root=project_root)


def _resolve_path(path: Path, *, project_root: Path) -> Path:
    if path.is_absolute():
        return path.resolve()
    return (project_root / path).resolve()


def _path_display(path: Path, *, project_root: Path) -> str:
    repo_path = _repo_relative(path, project_root=project_root)
    if repo_path:
        return repo_path
    try:
        home_path = path.resolve().relative_to(Path.home().resolve())
        return f"~/{home_path}"
    except ValueError:
        return str(path)


def _repo_relative(path: Path, *, project_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return ""


def _record_display(record: object) -> str:
    if not isinstance(record, Mapping):
        return ""
    return str(record.get("path") or record.get("absolute_path") or "")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_info(project_root: Path) -> dict[str, object]:
    return {
        "branch": _git_output(project_root, ("branch", "--show-current")),
        "head": _git_output(project_root, ("rev-parse", "HEAD")),
        "dirty": bool(_git_output(project_root, ("status", "--porcelain"))),
    }


def _git_output(project_root: Path, args: Sequence[str]) -> str:
    try:
        completed = subprocess.run(
            ("git", *args),
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return completed.stdout.strip()


def _shell_join(argv: Sequence[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in argv)
