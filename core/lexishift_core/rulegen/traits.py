from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Sequence


@dataclass(frozen=True)
class RulegenRouterTraitSummary:
    target_length: int
    target_token_count: int
    candidate_row_count: int
    candidate_definition_bucket_count: int
    candidate_phrase_count: int
    candidate_variant_count: int
    candidate_reverse_supported_count: int
    candidate_reverse_hit_count: int
    candidate_interjection_shadow_count: int
    candidate_late_sense_count: int
    candidate_target_pos_canonicals: tuple[str, ...]
    candidate_family_names: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "target_length": int(self.target_length),
            "target_token_count": int(self.target_token_count),
            "candidate_row_count": int(self.candidate_row_count),
            "candidate_definition_bucket_count": int(self.candidate_definition_bucket_count),
            "candidate_phrase_count": int(self.candidate_phrase_count),
            "candidate_variant_count": int(self.candidate_variant_count),
            "candidate_reverse_supported_count": int(self.candidate_reverse_supported_count),
            "candidate_reverse_hit_count": int(self.candidate_reverse_hit_count),
            "candidate_interjection_shadow_count": int(self.candidate_interjection_shadow_count),
            "candidate_late_sense_count": int(self.candidate_late_sense_count),
            "candidate_target_pos_canonicals": list(self.candidate_target_pos_canonicals),
            "candidate_family_names": list(self.candidate_family_names),
        }


@dataclass(frozen=True)
class RulegenResultShapeTraitSummary:
    selected_source_count: int
    selected_multiword_count: int
    top1_source_token_count: int
    top1_multiword: bool
    variant_rule_count: int
    top1_is_variant: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "selected_source_count": int(self.selected_source_count),
            "selected_multiword_count": int(self.selected_multiword_count),
            "top1_source_token_count": int(self.top1_source_token_count),
            "top1_multiword": bool(self.top1_multiword),
            "variant_rule_count": int(self.variant_rule_count),
            "top1_is_variant": bool(self.top1_is_variant),
        }


def build_family_name_by_marker_id(
    family_marker_ids_by_name: object,
) -> dict[int, str]:
    if not isinstance(family_marker_ids_by_name, Mapping):
        return {}
    return {
        int(marker_id): str(name)
        for name, marker_id in family_marker_ids_by_name.items()
        if str(name).strip()
    }


def build_rulegen_router_trait_summary(
    *,
    target: object,
    candidate_table: object | None = None,
    candidate_row_ids: Sequence[int] = (),
    family_name_by_marker_id: Optional[Mapping[int, str]] = None,
) -> RulegenRouterTraitSummary:
    target_text = str(target or "").strip()
    target_tokens = tuple(token for token in target_text.split() if token)

    if candidate_table is None:
        return RulegenRouterTraitSummary(
            target_length=len(target_text),
            target_token_count=len(target_tokens),
            candidate_row_count=0,
            candidate_definition_bucket_count=0,
            candidate_phrase_count=0,
            candidate_variant_count=0,
            candidate_reverse_supported_count=0,
            candidate_reverse_hit_count=0,
            candidate_interjection_shadow_count=0,
            candidate_late_sense_count=0,
            candidate_target_pos_canonicals=(),
            candidate_family_names=(),
        )

    candidate_ids = getattr(candidate_table, "candidate_ids", ())
    row_ids = tuple(
        int(row_id)
        for row_id in candidate_row_ids
        if isinstance(row_id, int) and 0 <= int(row_id) < len(candidate_ids)
    )
    family_names = family_name_by_marker_id or {}
    definition_bucket_ids = getattr(candidate_table, "definition_bucket_ids", ())
    phrase_flags = getattr(candidate_table, "phrase_flags", ())
    variant_flags = getattr(candidate_table, "variant_flags", ())
    reverse_supported_flags = getattr(candidate_table, "reverse_check_supported_flags", ())
    reverse_hit_flags = getattr(candidate_table, "reverse_check_hit_flags", ())
    interjection_shadowed_flags = getattr(candidate_table, "interjection_shadowed_flags", ())
    current_sense_positions = getattr(candidate_table, "current_sense_positions", ())
    target_pos_canonicals = getattr(candidate_table, "target_pos_canonicals", ())
    family_marker_id_rows = getattr(candidate_table, "family_marker_id_rows", ())

    return RulegenRouterTraitSummary(
        target_length=len(target_text),
        target_token_count=len(target_tokens),
        candidate_row_count=len(row_ids),
        candidate_definition_bucket_count=len(
            {int(definition_bucket_ids[row_id]) for row_id in row_ids}
        ),
        candidate_phrase_count=sum(bool(phrase_flags[row_id]) for row_id in row_ids),
        candidate_variant_count=sum(bool(variant_flags[row_id]) for row_id in row_ids),
        candidate_reverse_supported_count=sum(
            bool(reverse_supported_flags[row_id]) for row_id in row_ids
        ),
        candidate_reverse_hit_count=sum(bool(reverse_hit_flags[row_id]) for row_id in row_ids),
        candidate_interjection_shadow_count=sum(
            bool(interjection_shadowed_flags[row_id]) for row_id in row_ids
        ),
        candidate_late_sense_count=sum(
            int(current_sense_positions[row_id]) > 1 for row_id in row_ids
        ),
        candidate_target_pos_canonicals=tuple(
            sorted(
                {
                    str(target_pos_canonicals[row_id]).strip()
                    for row_id in row_ids
                    if str(target_pos_canonicals[row_id]).strip()
                }
            )
        ),
        candidate_family_names=tuple(
            sorted(
                {
                    family_names[int(marker_id)]
                    for row_id in row_ids
                    for marker_id in family_marker_id_rows[row_id]
                    if int(marker_id) in family_names
                }
            )
        ),
    )


def build_rulegen_result_shape_trait_summary(
    *,
    all_sources: Sequence[object],
    top1_source: object,
    variant_rule_count: int,
    top1_is_variant: bool,
) -> RulegenResultShapeTraitSummary:
    normalized_sources = tuple(
        str(source).strip() for source in all_sources if str(source or "").strip()
    )
    top1_text = str(top1_source or "").strip()
    return RulegenResultShapeTraitSummary(
        selected_source_count=len(normalized_sources),
        selected_multiword_count=sum(" " in source for source in normalized_sources),
        top1_source_token_count=len(tuple(token for token in top1_text.split() if token)),
        top1_multiword=bool(top1_text and " " in top1_text),
        variant_rule_count=int(variant_rule_count),
        top1_is_variant=bool(top1_is_variant),
    )
