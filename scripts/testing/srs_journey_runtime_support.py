from __future__ import annotations

from typing import Mapping, Sequence

from srs_journey_installed_support import is_role_ref


def finding(
    *,
    level: str,
    code: str,
    message: str,
    details: str | None = None,
    phase: str | None = None,
) -> dict[str, object]:
    return {
        "level": level,
        "code": code,
        "message": message,
        "details": details,
        "phase": phase,
    }


def summarize_findings(findings: Sequence[Mapping[str, object]]) -> dict[str, object]:
    pass_count = 0
    warn_count = 0
    fail_count = 0
    for item in findings:
        level = str(item.get("level") or "").upper()
        if level == "PASS":
            pass_count += 1
        elif level == "WARN":
            warn_count += 1
        elif level == "FAIL":
            fail_count += 1
    status = "FAIL" if fail_count else "WARN" if warn_count else "PASS"
    return {
        "status": status,
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "should_fail": fail_count > 0,
    }


def snapshot_item(snapshot: Mapping[str, object] | None, lemma: str) -> Mapping[str, object] | None:
    if not isinstance(snapshot, Mapping):
        return None
    items = snapshot.get("items")
    if not isinstance(items, list):
        return None
    for item in items:
        if isinstance(item, Mapping) and str(item.get("lemma") or "") == lemma:
            return item
    return None


def cohort_for_resolved_ref(
    *,
    ref: str,
    lemma: str,
    cohort_by_lemma: Mapping[str, str],
) -> str:
    if is_role_ref(ref):
        if ref.startswith("@stable_"):
            return "stable"
        if ref.startswith("@difficult_"):
            return "difficult"
        return "frontier"
    return cohort_by_lemma.get(lemma, "frontier")


def resolve_feedback_plan_events(
    events: Sequence[tuple[str, str]],
    *,
    role_assignments: Mapping[str, str],
    cohort_by_lemma: Mapping[str, str],
) -> list[dict[str, str]]:
    resolved: list[dict[str, str]] = []
    for ref, rating in events:
        lemma = str(role_assignments.get(ref, ref) or "").strip()
        if is_role_ref(ref) and not lemma:
            raise ValueError(f"Unresolved SRS journey role reference: {ref}")
        resolved.append(
            {
                "ref": ref,
                "lemma": lemma,
                "rating": rating,
                "cohort": cohort_for_resolved_ref(
                    ref=ref,
                    lemma=lemma,
                    cohort_by_lemma=cohort_by_lemma,
                ),
            }
        )
    return resolved


def resolve_exposure_plan_events(
    events: Sequence[str],
    *,
    role_assignments: Mapping[str, str],
    cohort_by_lemma: Mapping[str, str],
) -> list[dict[str, str]]:
    resolved: list[dict[str, str]] = []
    for ref in events:
        lemma = str(role_assignments.get(ref, ref) or "").strip()
        if is_role_ref(ref) and not lemma:
            raise ValueError(f"Unresolved SRS journey role reference: {ref}")
        resolved.append(
            {
                "ref": ref,
                "lemma": lemma,
                "cohort": cohort_for_resolved_ref(
                    ref=ref,
                    lemma=lemma,
                    cohort_by_lemma=cohort_by_lemma,
                ),
            }
        )
    return resolved
