from __future__ import annotations

from copy import deepcopy
import re
from typing import Mapping, Sequence


PRODUCT_SCOPE_BROWSER_SOFT_ASSIST = "browser_soft_assist"
DIAGNOSTIC_LABEL_PRESERVATION = "diagnostic_label_preservation"

_INTERNAL_PROJECT_CODE_RE = re.compile(
    r"^the dashboard listed .+ as an internal project code\.?$",
    re.IGNORECASE,
)


def classify_semantic_veto_product_scope(row: Mapping[str, object]) -> dict[str, object]:
    sentence = _normalize_sentence(str(row.get("sentence") or row.get("context_text") or ""))
    if _INTERNAL_PROJECT_CODE_RE.match(sentence):
        return {
            "scope_id": DIAGNOSTIC_LABEL_PRESERVATION,
            "include_in_product_scope": False,
            "reason_code": "synthetic_internal_project_code_label",
        }
    return {
        "scope_id": PRODUCT_SCOPE_BROWSER_SOFT_ASSIST,
        "include_in_product_scope": True,
        "reason_code": "",
    }


def filter_sentence_veto_dataset_for_product_scope(
    dataset_payload: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    filtered = deepcopy(dict(dataset_payload))
    filtered_families: list[dict[str, object]] = []
    excluded_cases: list[dict[str, object]] = []
    retained_case_count = 0
    original_case_count = 0

    for raw_family in _mapping_rows(dataset_payload.get("families")):
        family = deepcopy(dict(raw_family))
        retained_cases: list[dict[str, object]] = []
        for raw_case in _mapping_rows(family.get("cases")):
            original_case_count += 1
            scope = classify_semantic_veto_product_scope(raw_case)
            if bool(scope["include_in_product_scope"]):
                retained_cases.append(deepcopy(dict(raw_case)))
                retained_case_count += 1
            else:
                excluded_cases.append(
                    {
                        "case_id": str(raw_case.get("case_id") or ""),
                        "family_id": str(family.get("family_id") or ""),
                        "trigger": str(
                            family.get("trigger") or raw_case.get("source_phrase") or ""
                        ),
                        "gold_decision": str(raw_case.get("gold_decision") or ""),
                        "scope_id": scope["scope_id"],
                        "reason_code": scope["reason_code"],
                        "sentence": str(raw_case.get("sentence") or ""),
                    }
                )
        if retained_cases:
            family["cases"] = retained_cases
            filtered_families.append(family)

    filtered["families"] = filtered_families
    filtered["dataset_id"] = f"{dataset_payload.get('dataset_id') or 'dataset'}_product_scope"
    filtered["product_scope_filter"] = {
        "scope_id": PRODUCT_SCOPE_BROWSER_SOFT_ASSIST,
        "excluded_scope_ids": [DIAGNOSTIC_LABEL_PRESERVATION],
        "reason": (
            "Synthetic label-preservation rows are diagnostic for internal-label behavior, "
            "but product soft-assist evaluation should not count them as bad replacements."
        ),
    }
    summary = {
        "scope_id": PRODUCT_SCOPE_BROWSER_SOFT_ASSIST,
        "original_case_count": original_case_count,
        "retained_case_count": retained_case_count,
        "excluded_case_count": len(excluded_cases),
        "excluded_scope_counts": {
            DIAGNOSTIC_LABEL_PRESERVATION: len(excluded_cases),
        },
        "excluded_cases": excluded_cases,
    }
    return filtered, summary


def _normalize_sentence(value: str) -> str:
    return " ".join(str(value or "").strip().split())


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]
