from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Mapping, Sequence


@dataclass(frozen=True)
class QualityFinding:
    level: str  # PASS | WARN | FAIL
    code: str
    message: str
    details: str | None = None


@dataclass(frozen=True)
class QualityReport:
    benchmark_json: str
    policy_json: str
    baseline_json: str | None
    dataset_json: str | None
    pos_probe_json: str | None
    pos_inventory_json: str | None
    strict_saturation: bool
    fail_on_warn: bool
    summary: dict[str, object]
    findings: list[QualityFinding]

    def to_dict(self) -> dict[str, object]:
        return {
            "benchmark_json": self.benchmark_json,
            "policy_json": self.policy_json,
            "baseline_json": self.baseline_json,
            "dataset_json": self.dataset_json,
            "pos_probe_json": self.pos_probe_json,
            "pos_inventory_json": self.pos_inventory_json,
            "strict_saturation": self.strict_saturation,
            "fail_on_warn": self.fail_on_warn,
            "summary": self.summary,
            "findings": [asdict(item) for item in self.findings],
        }


def read_json(path: Path) -> Mapping[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def as_float(value: object, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def as_int(value: object, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def metric_vector_key(run: Mapping[str, object]) -> tuple[float, float, float, float, float, float]:
    summary = run.get("summary")
    if not isinstance(summary, Mapping):
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    return (
        as_float(summary.get("objective_score")),
        as_float(summary.get("top1_accuracy")),
        as_float(summary.get("top3_recall")),
        as_float(summary.get("forbidden_top1_rate")),
        as_float(summary.get("forbidden_any_rate")),
        as_float(summary.get("avg_rules_per_target")),
    )


def pair_best_summary(benchmark_payload: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    pairs = benchmark_payload.get("pairs")
    if not isinstance(pairs, Mapping):
        return {}
    result: dict[str, Mapping[str, object]] = {}
    for pair, pair_payload in pairs.items():
        if not isinstance(pair_payload, Mapping):
            continue
        best_run = pair_payload.get("best_run")
        if not isinstance(best_run, Mapping):
            continue
        summary = best_run.get("summary")
        if not isinstance(summary, Mapping):
            continue
        result[str(pair)] = summary
    return result


def dataset_from_payload(
    benchmark_payload: Mapping[str, object],
    explicit_dataset: Path | None,
    *,
    project_root: Path,
) -> Path | None:
    if explicit_dataset is not None:
        return explicit_dataset
    dataset_path = str(benchmark_payload.get("dataset_path") or "").strip()
    if not dataset_path:
        return None
    path = Path(dataset_path)
    candidates: list[Path] = []
    if path.is_absolute() or dataset_path.startswith(("/", "\\")):
        candidates.append(path)
        parts = list(path.parts)
        if "docs" in parts:
            docs_index = parts.index("docs")
            candidates.append((project_root / Path(*parts[docs_index:])).resolve())
        candidates.append((project_root / "docs" / "test_inputs" / path.name).resolve())
    else:
        candidates.append((project_root / path).resolve())

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists():
            return resolved
    return candidates[0] if candidates else None


def record(
    findings: list[QualityFinding],
    *,
    level: str,
    code: str,
    message: str,
    details: str | None = None,
) -> None:
    findings.append(QualityFinding(level=level, code=code, message=message, details=details))


def summarize_findings(
    findings: Sequence[QualityFinding],
    *,
    fail_on_warn: bool,
) -> dict[str, object]:
    fail_count = sum(1 for item in findings if item.level == "FAIL")
    warn_count = sum(1 for item in findings if item.level == "WARN")
    pass_count = sum(1 for item in findings if item.level == "PASS")
    should_fail = fail_count > 0 or (bool(fail_on_warn) and warn_count > 0)
    status = "FAIL" if should_fail else "WARN" if warn_count > 0 else "PASS"
    return {
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "status": status,
        "should_fail": should_fail,
    }


def print_findings(findings: Sequence[QualityFinding]) -> None:
    for finding in findings:
        print(f"[{finding.level}] {finding.code}: {finding.message}")
        if finding.details:
            for line in str(finding.details).splitlines():
                print(f"  {line}")
