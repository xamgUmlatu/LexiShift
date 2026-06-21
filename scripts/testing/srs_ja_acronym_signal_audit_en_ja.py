#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(CORE_ROOT))
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from lexishift_core.helper.lp_capabilities import (  # noqa: E402
    default_frequency_db_path,
    default_jmdict_path,
    default_jmnedict_path,
)
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.resources.japanese_learner_signals import (  # noqa: E402
    JAPANESE_LEARNER_SIGNALS_VERSION,
    JA_ACRONYM_SIGNAL_VERSION,
    JMDICT_LEXICAL_INDEX_VERSION,
)
from lexishift_core.srs.candidate_classification import (  # noqa: E402
    CANDIDATE_CLASSIFICATION_VERSION,
)
from lexishift_core.srs.seed import SeedSelectionConfig, build_seed_candidates  # noqa: E402


PAIR = "en-ja"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_ja_acronym_signal_audit_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_ja_acronym_signal_audit_latest.md"
)
MAX_EXAMPLES_PER_GROUP = 16


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit en-ja acronym/code learner signals without changing admission "
            "behavior. The report shows recommended classes/states from "
            "learner-signal metadata only."
        )
    )
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument("--jmdict", type=Path)
    parser.add_argument("--jmnedict", type=Path)
    parser.add_argument(
        "--top-n",
        type=int,
        default=None,
        help="Optional finite seed frontier. Omit to audit all available rows.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        frequency_db=args.frequency_db,
        jmdict_path=args.jmdict,
        jmnedict_path=args.jmnedict,
        top_n=max(1, int(args.top_n)) if args.top_n is not None else None,
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    return 0


def build_report(
    *,
    frequency_db: Path | None,
    jmdict_path: Path | None,
    jmnedict_path: Path | None,
    top_n: int | None,
) -> dict[str, object]:
    paths = build_helper_paths()
    frequency_db = frequency_db or default_frequency_db_path(
        PAIR,
        frequency_packs_dir=paths.frequency_packs_dir,
    )
    jmdict_path = jmdict_path or default_jmdict_path(
        PAIR,
        language_packs_dir=paths.language_packs_dir,
    )
    jmnedict_path = jmnedict_path or default_jmnedict_path(
        PAIR,
        language_packs_dir=paths.language_packs_dir,
    )
    if frequency_db is None or not Path(frequency_db).is_file():
        raise FileNotFoundError(f"Missing en-ja frequency DB: {frequency_db}")
    if jmdict_path is None or not Path(jmdict_path).is_file():
        raise FileNotFoundError(f"Missing en-ja JMDict path: {jmdict_path}")

    seeds = build_seed_candidates(
        frequency_db=Path(frequency_db),
        config=SeedSelectionConfig(
            language_pair=PAIR,
            top_n=top_n,
            jmdict_path=Path(jmdict_path),
            jmnedict_path=Path(jmnedict_path) if jmnedict_path else None,
        ),
    )
    rows = [_acronym_row(seed) for seed in seeds]
    acronym_rows = [row for row in rows if row is not None]
    class_counts = Counter(str(row["recommended_acronym_class"]) for row in acronym_rows)
    state_counts = Counter(str(row["recommended_candidate_state"]) for row in acronym_rows)
    reason_counts: Counter[str] = Counter()
    for row in acronym_rows:
        reason_counts.update(str(reason) for reason in row.get("reasons", ()))
    evidence_flag_counts: Counter[str] = Counter()
    for row in acronym_rows:
        for flag in (
            "has_exact_identity",
            "has_initialism_expansion",
            "has_jmdict_domain_field",
            "has_proper_name_signal",
            "domain_from_distribution_only",
        ):
            if row.get(flag):
                evidence_flag_counts[flag] += 1
    examples_by_class: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in sorted(acronym_rows, key=_example_sort_key):
        key = str(row.get("recommended_acronym_class") or "unknown")
        if len(examples_by_class[key]) < MAX_EXAMPLES_PER_GROUP:
            examples_by_class[key].append(row)
    provenance = build_artifact_provenance(
        producer_script=Path(__file__),
        input_paths={
            "frequency_db": Path(frequency_db),
            "jmdict": Path(jmdict_path),
            "jmnedict": Path(jmnedict_path) if jmnedict_path else None,
        },
        code_paths=_core_code_paths(),
        version_constants={
            "candidate_classification": CANDIDATE_CLASSIFICATION_VERSION,
            "japanese_learner_signals": JAPANESE_LEARNER_SIGNALS_VERSION,
            "jmdict_lexical_index": JMDICT_LEXICAL_INDEX_VERSION,
            "ja_acronym_signal": JA_ACRONYM_SIGNAL_VERSION,
        },
        argv=sys.argv,
    )
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "provenance": provenance,
        "frequency_db": str(frequency_db),
        "jmdict_path": str(jmdict_path),
        "jmnedict_path": str(jmnedict_path) if jmnedict_path else "",
        "top_n": top_n,
        "seed_count": len(seeds),
        "acronym_signal_count": len(acronym_rows),
        "acronym_signal_rate": _rounded(len(acronym_rows) / len(seeds) if seeds else 0.0),
        "class_counts": dict(sorted(class_counts.items())),
        "state_counts": dict(sorted(state_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
        "evidence_flag_counts": dict(sorted(evidence_flag_counts.items())),
        "examples_by_class": {key: examples for key, examples in sorted(examples_by_class.items())},
    }


def _acronym_row(seed: object) -> dict[str, object] | None:
    metadata = _mapping(getattr(seed, "metadata", None))
    learner_signals = _mapping(metadata.get("learner_signals"))
    signal = _mapping(learner_signals.get("ja_acronym"))
    if not signal:
        return None
    has_exact_identity = _float(signal.get("identity_gloss_confidence")) >= 0.8
    has_initialism_expansion = _float(signal.get("expanded_gloss_confidence")) >= 0.8
    has_jmdict_domain_field = _float(signal.get("field_domain_confidence")) >= 0.8
    has_proper_name_signal = _float(signal.get("proper_name_risk")) >= 0.7
    domain_from_distribution_only = (
        _float(signal.get("domain_concentration")) >= 0.75 and not has_jmdict_domain_field
    )
    return {
        "lemma": str(getattr(seed, "lemma", "") or ""),
        "reading": _word_package_value(seed, "reading") or metadata.get("lform_raw") or "",
        "pos": str(getattr(seed, "pos", "") or ""),
        "wtype": _word_package_value(seed, "wtype"),
        "rank": _rounded_or_none(getattr(seed, "core_rank", None)),
        "pmw": _rounded_or_none(getattr(seed, "pmw", None)),
        "normalized_ascii_surface": signal.get("normalized_ascii_surface"),
        "recommended_acronym_class": signal.get("recommended_acronym_class"),
        "recommended_candidate_state": signal.get("recommended_candidate_state"),
        "recommended_admission_suitability": signal.get("recommended_admission_suitability"),
        "surface_confidence": signal.get("surface_confidence"),
        "reading_spellout_confidence": signal.get("reading_spellout_confidence"),
        "identity_gloss_confidence": signal.get("identity_gloss_confidence"),
        "japanese_specific_usage_confidence": signal.get("japanese_specific_usage_confidence"),
        "domain_concentration": signal.get("domain_concentration"),
        "field_domain_confidence": signal.get("field_domain_confidence"),
        "proper_name_risk": signal.get("proper_name_risk"),
        "real_usage_confidence": signal.get("real_usage_confidence"),
        "has_exact_identity": has_exact_identity,
        "has_initialism_expansion": has_initialism_expansion,
        "has_jmdict_domain_field": has_jmdict_domain_field,
        "has_proper_name_signal": has_proper_name_signal,
        "domain_from_distribution_only": domain_from_distribution_only,
        "reasons": list(signal.get("reasons", ()) or ()),
    }


def render_markdown(report: Mapping[str, object]) -> str:
    lines: list[str] = [
        "# en-ja Acronym Signal Audit",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Producer: `{_escape(_producer_path(report))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Seed count: `{_escape(report.get('seed_count'))}`",
        f"- Acronym/code signal count: `{_escape(report.get('acronym_signal_count'))}`",
        f"- Acronym/code signal rate: `{_escape(report.get('acronym_signal_rate'))}`",
        "",
        "## Recommended Classes",
        "",
        _counter_table(report.get("class_counts")),
        "",
        "## Recommended States",
        "",
        _counter_table(report.get("state_counts")),
        "",
        "## Reasons",
        "",
        _counter_table(report.get("reason_counts")),
        "",
        "## Evidence Flags",
        "",
        _counter_table(report.get("evidence_flag_counts")),
        "",
        "## Examples By Class",
        "",
    ]
    examples_by_class = _mapping(report.get("examples_by_class"))
    for class_name, raw_examples in examples_by_class.items():
        examples = raw_examples if isinstance(raw_examples, Sequence) else ()
        lines.extend(
            [
                f"### `{_escape(class_name)}`",
                "",
                (
                    "| Lemma | Reading | State | Rank | Spellout | Identity | "
                    "Japanese-specific | Domain | Proper | Reasons |"
                ),
                "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for raw_example in examples:
            example = _mapping(raw_example)
            domain_signal = max(
                _float(example.get("domain_concentration")),
                _float(example.get("field_domain_confidence")),
            )
            reasons = ", ".join(str(item) for item in example.get("reasons", ()) or ())
            lines.append(
                "| "
                f"`{_escape(example.get('lemma'))}` | "
                f"`{_escape(example.get('reading'))}` | "
                f"`{_escape(example.get('recommended_candidate_state'))}` | "
                f"`{_escape(example.get('rank'))}` | "
                f"`{_escape(example.get('reading_spellout_confidence'))}` | "
                f"`{_escape(example.get('identity_gloss_confidence'))}` | "
                f"`{_escape(example.get('japanese_specific_usage_confidence'))}` | "
                f"`{_escape(domain_signal)}` | "
                f"`{_escape(example.get('proper_name_risk'))}` | "
                f"{_escape(reasons)} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _counter_table(value: object) -> str:
    counts = _mapping(value)
    if not counts:
        return "_None._"
    lines = ["| Key | Count |", "| --- | ---: |"]
    for key, count in counts.items():
        lines.append(f"| `{_escape(key)}` | `{_escape(count)}` |")
    return "\n".join(lines)


def _word_package_value(seed: object, key: str) -> object:
    word_package = getattr(seed, "word_package", None)
    if isinstance(word_package, Mapping):
        value = word_package.get(key)
        if value not in (None, ""):
            return value
        source = word_package.get("source")
        if isinstance(source, Mapping):
            return source.get(key)
    return ""


def _example_sort_key(row: Mapping[str, object]) -> tuple[float, str]:
    rank = _float(row.get("rank"))
    if rank <= 0.0:
        rank = float("inf")
    return rank, str(row.get("lemma") or "")


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def _core_code_paths() -> dict[str, Path]:
    return {
        "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
        "seed": CORE_ROOT / "lexishift_core" / "srs" / "seed.py",
        "candidate_classification": (
            CORE_ROOT / "lexishift_core" / "srs" / "candidate_classification.py"
        ),
        "japanese_learner_signals": (
            CORE_ROOT / "lexishift_core" / "resources" / "japanese_learner_signals.py"
        ),
    }


def _rounded(value: float) -> float:
    return round(float(value), 6)


def _rounded_or_none(value: object) -> float | None:
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return None


def _float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _escape(value: object) -> str:
    return str(value if value is not None else "").replace("|", "\\|")


def _producer_path(report: Mapping[str, object]) -> object:
    provenance = _mapping(report.get("provenance"))
    producer = _mapping(provenance.get("producer"))
    return producer.get("path")


if __name__ == "__main__":
    raise SystemExit(main())
