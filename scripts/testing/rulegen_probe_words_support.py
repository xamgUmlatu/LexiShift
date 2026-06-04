from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping, Optional

from lexishift_core.helper.frequency_packs import build_frequency_pack_ref
from lexishift_core.helper.translation_packs import (
    FORWARD_PACK_DIRECTION,
    REVERSE_PACK_DIRECTION,
    build_translation_pack_ref,
)
from lexishift_core.lexicon.word_package import build_word_package, normalize_word_package
from lexishift_core.rulegen.generation import RuleGenerationResult
from lexishift_core.rulegen.ranking import (
    CandidateRankingContext,
    DictionaryEntryOrderRankingMechanism,
    build_ranking_sort_key,
)
from lexishift_core.srs import SrsStore, load_srs_store


def parse_csv_words(value: str) -> list[str]:
    words = [item.strip() for item in str(value or "").split(",")]
    return [word for word in words if word]


def parse_reading_overrides(value: str) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for chunk in str(value or "").split(","):
        part = chunk.strip()
        if not part or "=" not in part:
            continue
        lemma, reading = part.split("=", 1)
        lemma_text = lemma.strip()
        reading_text = reading.strip()
        if not lemma_text or not reading_text:
            continue
        overrides[lemma_text] = reading_text
    return overrides


def resolve_required_file(label: str, path: Optional[Path]) -> Path:
    if path is None:
        raise FileNotFoundError(f"Could not resolve {label} path.")
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    return path


def load_store(path: Path) -> SrsStore:
    if not path.exists():
        return SrsStore()
    return load_srs_store(path)


def source_frequency_pair_for_probe(pair: str) -> Optional[str]:
    normalized = str(pair or "").strip().lower()
    source_lang = normalized.split("-", 1)[0] if "-" in normalized else ""
    if not source_lang:
        return None
    return f"{source_lang}-{source_lang}"


def build_pair_resources_payload(
    *,
    pair: str,
    jmdict_path: Optional[Path],
    translation_dict_path: Optional[Path],
    reverse_translation_dict_path: Optional[Path],
    source_frequency_db_path: Optional[Path] = None,
) -> dict[str, object]:
    if (
        jmdict_path is None
        and translation_dict_path is None
        and reverse_translation_dict_path is None
        and source_frequency_db_path is None
    ):
        return {}
    translation_pack = build_translation_pack_ref(
        pair,
        translation_dict_path,
        direction=FORWARD_PACK_DIRECTION,
    )
    reverse_translation_pack = build_translation_pack_ref(
        pair,
        reverse_translation_dict_path,
        direction=REVERSE_PACK_DIRECTION,
    )
    source_frequency_pair = source_frequency_pair_for_probe(pair)
    source_frequency_pack = build_frequency_pack_ref(
        source_frequency_pair or pair,
        source_frequency_db_path,
    )
    return {
        "jmdict_path": str(jmdict_path) if jmdict_path else None,
        "translation_dict_path": str(translation_dict_path) if translation_dict_path else None,
        "translation_pack_id": (translation_pack.pack_id if translation_pack is not None else None),
        "translation_pack_provider": (
            translation_pack.provider if translation_pack is not None else None
        ),
        "translation_pack_pos_source_profile": (
            translation_pack.pos_source_profile if translation_pack is not None else None
        ),
        "reverse_translation_dict_path": (
            str(reverse_translation_dict_path) if reverse_translation_dict_path else None
        ),
        "reverse_translation_pack_id": (
            reverse_translation_pack.pack_id if reverse_translation_pack is not None else None
        ),
        "reverse_translation_pack_provider": (
            reverse_translation_pack.provider if reverse_translation_pack is not None else None
        ),
        "reverse_translation_pack_pos_source_profile": (
            reverse_translation_pack.pos_source_profile
            if reverse_translation_pack is not None
            else None
        ),
        "source_frequency_db_path": (
            str(source_frequency_db_path) if source_frequency_db_path else None
        ),
        "source_frequency_pack_id": (
            source_frequency_pack.pack_id if source_frequency_pack is not None else None
        ),
        "source_frequency_pack_provider": (
            source_frequency_pack.provider if source_frequency_pack is not None else None
        ),
        "source_frequency_pack_pos_source_profile": (
            source_frequency_pack.pos_source_profile if source_frequency_pack is not None else None
        ),
    }


def print_pack_identity(
    *,
    label: str,
    pack_id: Optional[str],
    provider: Optional[str],
    pos_source_profile: Optional[str],
    path: Optional[str],
) -> None:
    if not any((pack_id, provider, pos_source_profile, path)):
        return
    print(
        f"  {label}: "
        f"id={pack_id or '-'} "
        f"provider={provider or '-'} "
        f"pos_profile={pos_source_profile or '-'} "
        f"path={path or '-'}"
    )


def print_resource_identity_block(
    resource_payload: Mapping[str, Mapping[str, object]],
) -> None:
    print(
        "  resource_identity: installed-pack metadata is reported below; "
        "raw paths above are execution details/manual overrides."
    )
    en_es = resource_payload.get("en-es", {})
    en_de = resource_payload.get("en-de", {})
    print_pack_identity(
        label="translation_pack_en_es",
        pack_id=_optional_text(en_es.get("translation_pack_id")),
        provider=_optional_text(en_es.get("translation_pack_provider")),
        pos_source_profile=_optional_text(en_es.get("translation_pack_pos_source_profile")),
        path=_optional_text(en_es.get("translation_dict_path")),
    )
    print_pack_identity(
        label="translation_pack_es_en_reverse",
        pack_id=_optional_text(en_es.get("reverse_translation_pack_id")),
        provider=_optional_text(en_es.get("reverse_translation_pack_provider")),
        pos_source_profile=_optional_text(en_es.get("reverse_translation_pack_pos_source_profile")),
        path=_optional_text(en_es.get("reverse_translation_dict_path")),
    )
    print_pack_identity(
        label="translation_pack_en_de",
        pack_id=_optional_text(en_de.get("translation_pack_id")),
        provider=_optional_text(en_de.get("translation_pack_provider")),
        pos_source_profile=_optional_text(en_de.get("translation_pack_pos_source_profile")),
        path=_optional_text(en_de.get("translation_dict_path")),
    )
    print_pack_identity(
        label="translation_pack_de_en_reverse",
        pack_id=_optional_text(en_de.get("reverse_translation_pack_id")),
        provider=_optional_text(en_de.get("reverse_translation_pack_provider")),
        pos_source_profile=_optional_text(en_de.get("reverse_translation_pack_pos_source_profile")),
        path=_optional_text(en_de.get("reverse_translation_dict_path")),
    )
    print_pack_identity(
        label="source_frequency_pack_en_de",
        pack_id=_optional_text(en_de.get("source_frequency_pack_id")),
        provider=_optional_text(en_de.get("source_frequency_pack_provider")),
        pos_source_profile=_optional_text(en_de.get("source_frequency_pack_pos_source_profile")),
        path=_optional_text(en_de.get("source_frequency_db_path")),
    )


def build_ja_word_packages(
    *,
    targets: Iterable[str],
    store: SrsStore,
    reading_overrides: Mapping[str, str],
) -> tuple[dict[str, Mapping[str, object]], list[str], list[str]]:
    target_set = {str(target).strip() for target in targets if str(target).strip()}
    by_target: dict[str, Mapping[str, object]] = {}
    notes: list[str] = []

    for item in store.items:
        if item.language_pair != "en-ja":
            continue
        lemma = str(item.lemma or "").strip()
        if lemma not in target_set:
            continue
        normalized = normalize_word_package(
            item.word_package,
            fallback_surface=lemma,
            fallback_language_tag="ja",
            fallback_provider=item.source_type or "srs",
        )
        if normalized is None:
            continue
        by_target[lemma] = normalized

    missing = [lemma for lemma in sorted(target_set) if lemma not in by_target]
    for lemma in list(missing):
        reading = str(reading_overrides.get(lemma) or "").strip()
        if not reading:
            continue
        package = build_word_package(
            language_pair="en-ja",
            surface=lemma,
            reading=reading,
            source_provider="rulegen_probe_words",
        )
        if package is None:
            continue
        by_target[lemma] = package
        missing.remove(lemma)
        notes.append(f"Using reading override for '{lemma}' -> '{reading}'.")

    return by_target, missing, notes


def serialize_result(
    result: RuleGenerationResult,
    *,
    mechanism: DictionaryEntryOrderRankingMechanism,
) -> dict[str, object]:
    context = CandidateRankingContext(
        source_phrase=result.candidate.source_phrase,
        replacement=result.candidate.replacement,
        metadata=result.candidate.metadata,
        confidence=result.confidence,
    )
    rank_score = mechanism.score(context)
    bucket = mechanism.bucket_key(context)
    sort_key = build_ranking_sort_key(context, score=rank_score)
    morphology = result.candidate.metadata.get("morphology")
    morphology_map = morphology if isinstance(morphology, Mapping) else {}
    return {
        "target": result.rule.replacement,
        "source_phrase": result.rule.source_phrase,
        "confidence": float(result.confidence),
        "rank_score": float(rank_score),
        "bucket_key": str(bucket),
        "sort_key": sort_key,
        "gloss_index": result.candidate.metadata.get("gloss_index"),
        "gloss_total": result.candidate.metadata.get("gloss_total"),
        "variant": result.candidate.metadata.get("variant"),
        "source_form": morphology_map.get("source_form"),
        "target_surface": morphology_map.get("target_surface"),
        "reverse_check_supported": result.candidate.metadata.get("reverse_check_supported"),
        "reverse_check_hit": result.candidate.metadata.get("reverse_check_hit"),
        "reverse_check_rank": result.candidate.metadata.get("reverse_check_rank"),
        "reverse_check_total": result.candidate.metadata.get("reverse_check_total"),
        "semantic_demotion": result.candidate.metadata.get("semantic_demotion"),
        "semantic_demotion_reason": result.candidate.metadata.get("semantic_demotion_reason"),
        "source_frequency_prior": result.candidate.metadata.get("source_frequency_prior"),
        "cleaner_later_competition_present": result.candidate.metadata.get(
            "cleaner_later_competition_present"
        ),
        "cleaner_later_competitor_phrase": result.candidate.metadata.get(
            "cleaner_later_competitor_phrase"
        ),
        "cleaner_later_competitor_prior": result.candidate.metadata.get(
            "cleaner_later_competitor_prior"
        ),
        "kaikki_family_names": result.candidate.metadata.get("kaikki_family_names"),
        "dictionary_record_views": result.candidate.metadata.get("dictionary_record_views"),
        "kaikki_policy_shadow": result.candidate.metadata.get("kaikki_policy_shadow"),
    }


def collect_rows_for_target(
    results: Iterable[RuleGenerationResult],
    *,
    target: str,
    mechanism: DictionaryEntryOrderRankingMechanism,
) -> list[dict[str, object]]:
    rows = [
        serialize_result(item, mechanism=mechanism)
        for item in results
        if str(item.rule.replacement) == str(target)
    ]
    rows.sort(key=lambda row: row["sort_key"])
    return rows


def print_target_block(
    *,
    pair: str,
    target: str,
    uncapped_rows: list[dict[str, object]],
    capped_rows: list[dict[str, object]],
) -> None:
    selected_buckets = {str(row["bucket_key"]) for row in capped_rows}
    selected_definitions = len(selected_buckets)
    print(f"\n[{pair}] target='{target}'")
    print(
        f"  uncapped_rules={len(uncapped_rows)} "
        f"capped_rules={len(capped_rows)} "
        f"selected_definitions={selected_definitions}"
    )
    if not uncapped_rows:
        print("  (no rules)")
        return

    print("  uncapped:")
    for index, row in enumerate(uncapped_rows, start=1):
        bucket = str(row["bucket_key"])
        marker = "*" if bucket in selected_buckets else " "
        gloss_index = row.get("gloss_index")
        variant = str(row.get("variant") or "-")
        source_form = str(row.get("source_form") or "-")
        target_surface = str(row.get("target_surface") or "-")
        reverse_supported = bool(row.get("reverse_check_supported"))
        reverse_hit = bool(row.get("reverse_check_hit"))
        reverse_rank = row.get("reverse_check_rank")
        reverse_total = row.get("reverse_check_total")
        reverse_note = ""
        if reverse_supported:
            if reverse_hit:
                reverse_note = f" reverse=hit@{reverse_rank}/{reverse_total}"
            else:
                reverse_note = f" reverse=miss/{reverse_total}"
        semantic_demotion = row.get("semantic_demotion")
        semantic_note = ""
        if semantic_demotion not in (None, 0, 0.0):
            semantic_note = f" semdem={float(semantic_demotion):.4f}"
        source_frequency_prior = row.get("source_frequency_prior")
        source_frequency_note = ""
        if source_frequency_prior not in (None, 0, 0.0):
            source_frequency_note = f" sfreq={float(source_frequency_prior):.4f}"
        competition_note = ""
        if bool(row.get("cleaner_later_competition_present")):
            competitor_phrase = str(row.get("cleaner_later_competitor_phrase") or "").strip()
            competitor_prior = row.get("cleaner_later_competitor_prior")
            competition_note = " clcmp=on"
            if competitor_phrase:
                competition_note += f":{competitor_phrase}"
            if competitor_prior not in (None, 0, 0.0):
                competition_note += f"@{float(competitor_prior):.4f}"
        kaikki_note = ""
        family_names = row.get("kaikki_family_names")
        if isinstance(family_names, list):
            normalized_families = [
                str(value).strip() for value in family_names if str(value).strip()
            ]
        elif isinstance(family_names, tuple):
            normalized_families = [
                str(value).strip() for value in family_names if str(value).strip()
            ]
        else:
            normalized_families = []
        if normalized_families:
            kaikki_note = f" kfam={'+'.join(normalized_families)}"
        print(
            f"    {index:02d}. [{marker}] src='{row['source_phrase']}' "
            f"conf={float(row['confidence']):.4f} rank={float(row['rank_score']):.4f} "
            f"bucket={bucket} gloss_index={gloss_index} "
            f"variant={variant} source_form={source_form} target_surface={target_surface}"
            f"{reverse_note}{semantic_note}{source_frequency_note}{competition_note}{kaikki_note}"
        )

    print("  capped:")
    for index, row in enumerate(capped_rows, start=1):
        bucket = str(row["bucket_key"])
        gloss_index = row.get("gloss_index")
        reverse_supported = bool(row.get("reverse_check_supported"))
        reverse_hit = bool(row.get("reverse_check_hit"))
        reverse_rank = row.get("reverse_check_rank")
        reverse_total = row.get("reverse_check_total")
        reverse_note = ""
        if reverse_supported:
            if reverse_hit:
                reverse_note = f" reverse=hit@{reverse_rank}/{reverse_total}"
            else:
                reverse_note = f" reverse=miss/{reverse_total}"
        semantic_demotion = row.get("semantic_demotion")
        semantic_note = ""
        if semantic_demotion not in (None, 0, 0.0):
            semantic_note = f" semdem={float(semantic_demotion):.4f}"
        source_frequency_prior = row.get("source_frequency_prior")
        source_frequency_note = ""
        if source_frequency_prior not in (None, 0, 0.0):
            source_frequency_note = f" sfreq={float(source_frequency_prior):.4f}"
        competition_note = ""
        if bool(row.get("cleaner_later_competition_present")):
            competitor_phrase = str(row.get("cleaner_later_competitor_phrase") or "").strip()
            competitor_prior = row.get("cleaner_later_competitor_prior")
            competition_note = " clcmp=on"
            if competitor_phrase:
                competition_note += f":{competitor_phrase}"
            if competitor_prior not in (None, 0, 0.0):
                competition_note += f"@{float(competitor_prior):.4f}"
        kaikki_note = ""
        family_names = row.get("kaikki_family_names")
        if isinstance(family_names, list):
            normalized_families = [
                str(value).strip() for value in family_names if str(value).strip()
            ]
        elif isinstance(family_names, tuple):
            normalized_families = [
                str(value).strip() for value in family_names if str(value).strip()
            ]
        else:
            normalized_families = []
        if normalized_families:
            kaikki_note = f" kfam={'+'.join(normalized_families)}"
        print(
            f"    {index:02d}. src='{row['source_phrase']}' "
            f"conf={float(row['confidence']):.4f} rank={float(row['rank_score']):.4f} "
            f"bucket={bucket} gloss_index={gloss_index}"
            f"{reverse_note}{semantic_note}{source_frequency_note}{competition_note}{kaikki_note}"
        )


def _optional_text(value: object) -> Optional[str]:
    text = str(value or "").strip()
    return text or None
