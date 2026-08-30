from __future__ import annotations

from pathlib import Path
from typing import Mapping, Optional, Sequence

from lexishift_core.helper.translation_packs import (
    FORWARD_PACK_DIRECTION,
    REVERSE_PACK_DIRECTION,
    build_translation_pack_ref,
)
from lexishift_core.rulegen.adapters import RulegenAdapterRequest


def build_rulegen_adapter_request(
    *,
    pair: str,
    targets: Sequence[str],
    rulegen_config: object,
    jmdict_path: Optional[Path],
    translation_dict_path: Optional[Path],
    resolved_reverse_translation_dict_path: Optional[Path],
    source_frequency_db_path: Optional[Path] = None,
    word_packages_by_target: Optional[Mapping[str, Mapping[str, object]]] = None,
) -> RulegenAdapterRequest:
    return RulegenAdapterRequest(
        pair=pair,
        targets=targets,
        language_pair=str(getattr(rulegen_config, "language_pair", pair)),
        confidence_threshold=float(getattr(rulegen_config, "confidence_threshold", 0.0)),
        max_definitions_per_target=getattr(rulegen_config, "max_definitions_per_target", None),
        max_rules_per_target=getattr(rulegen_config, "max_rules_per_target", None),
        semantic_demotion_scale=float(getattr(rulegen_config, "semantic_demotion_scale", 1.0)),
        include_variants=bool(getattr(rulegen_config, "include_variants", True)),
        allow_multiword_glosses=bool(getattr(rulegen_config, "allow_multiword_glosses", False)),
        scoring=getattr(rulegen_config, "scoring"),
        reverse_check=getattr(rulegen_config, "reverse_check"),
        gloss_decay=getattr(rulegen_config, "gloss_decay"),
        enable_exact_gloss_demotions=bool(
            getattr(rulegen_config, "enable_exact_gloss_demotions", False)
        ),
        jmdict_path=jmdict_path,
        translation_pack=build_translation_pack_ref(
            pair,
            translation_dict_path,
            direction=FORWARD_PACK_DIRECTION,
        ),
        translation_dict_path=translation_dict_path,
        reverse_translation_pack=build_translation_pack_ref(
            pair,
            resolved_reverse_translation_dict_path,
            direction=REVERSE_PACK_DIRECTION,
        ),
        reverse_translation_dict_path=resolved_reverse_translation_dict_path,
        enable_source_frequency_prior=bool(
            getattr(rulegen_config, "enable_source_frequency_prior", False)
        ),
        source_frequency_db_path=source_frequency_db_path,
        word_packages_by_target=word_packages_by_target,
    )
