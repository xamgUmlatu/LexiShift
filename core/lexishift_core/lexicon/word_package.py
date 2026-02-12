from __future__ import annotations

from typing import Mapping, Optional

from lexishift_core.resources.japanese_script import (
    contains_kana,
    contains_kanji,
    kana_to_romaji,
)


WORD_PACKAGE_VERSION = 1


def resolve_language_tag_from_pair(pair: str) -> str:
    normalized = str(pair or "").strip().lower()
    if not normalized:
        return ""
    parts = normalized.split("-", 1)
    if len(parts) < 2:
        return ""
    return normalize_language_tag(parts[1])


def normalize_language_tag(value: object, *, fallback: str = "") -> str:
    text = str(value or "").strip().lower().replace("_", "-")
    if not text:
        text = str(fallback or "").strip().lower().replace("_", "-")
    return text


def normalize_reading(value: object, *, language_tag: str) -> str:
    text = _extract_primary_variant(str(value or "").strip())
    if not text:
        return ""
    if normalize_language_tag(language_tag).startswith("ja"):
        return _katakana_to_hiragana(text)
    return text


def normalize_script_forms(value: object) -> Optional[dict[str, str]]:
    if not isinstance(value, Mapping):
        return None
    normalized: dict[str, str] = {}
    for key, raw in dict(value).items():
        script = str(key or "").strip().lower()
        text = str(raw or "").strip()
        if not script or not text:
            continue
        normalized[script] = text
    return normalized or None


def merge_script_forms(
    primary: Optional[Mapping[str, str]],
    fallback: Optional[Mapping[str, str]],
) -> Optional[dict[str, str]]:
    primary_forms = normalize_script_forms(primary) or {}
    fallback_forms = normalize_script_forms(fallback) or {}
    merged = dict(primary_forms)
    for key, value in fallback_forms.items():
        if key not in merged and value:
            merged[key] = value
    return merged or None


def build_word_package(
    *,
    language_pair: str,
    surface: str,
    reading: object,
    source_provider: str,
    script_forms: Optional[Mapping[str, object]] = None,
    source_extra: Optional[Mapping[str, object]] = None,
    pos: Optional[object] = None,
    wtype: Optional[object] = None,
    sublemma: Optional[object] = None,
    core_rank: Optional[object] = None,
    pmw: Optional[object] = None,
    lform_raw: Optional[object] = None,
    row_index: Optional[object] = None,
    row_rank: Optional[object] = None,
) -> Optional[dict[str, object]]:
    source: dict[str, object] = {"provider": str(source_provider or "").strip()}
    for key, raw in dict(source_extra or {}).items():
        cleaned_key = str(key or "").strip()
        if not cleaned_key:
            continue
        cleaned_value = _normalize_scalar(raw)
        if cleaned_value is not None:
            source[cleaned_key] = cleaned_value
    package: dict[str, object] = {
        "version": WORD_PACKAGE_VERSION,
        "language_tag": resolve_language_tag_from_pair(language_pair),
        "surface": str(surface or "").strip(),
        "reading": reading,
        "script_forms": script_forms,
        "source": source,
        "pos": pos,
        "wtype": wtype,
        "sublemma": sublemma,
        "core_rank": core_rank,
        "pmw": pmw,
        "lform_raw": lform_raw,
        "row_index": row_index,
        "row_rank": row_rank,
    }
    return normalize_word_package(
        package,
        fallback_surface=surface,
        fallback_language_tag=resolve_language_tag_from_pair(language_pair),
        fallback_provider=source_provider,
    )


def normalize_word_package(
    value: object,
    *,
    fallback_surface: str = "",
    fallback_language_tag: str = "",
    fallback_provider: str = "",
) -> Optional[dict[str, object]]:
    if not isinstance(value, Mapping):
        return None
    raw = dict(value)
    version = _to_int(raw.get("version"), default=WORD_PACKAGE_VERSION)
    if version != WORD_PACKAGE_VERSION:
        return None

    language_tag = normalize_language_tag(raw.get("language_tag"), fallback=fallback_language_tag)
    surface = str(raw.get("surface") or fallback_surface or "").strip()
    if not language_tag or not surface:
        return None

    reading = normalize_reading(raw.get("reading"), language_tag=language_tag)
    base_script_forms = normalize_script_forms(raw.get("script_forms"))
    if language_tag.startswith("ja"):
        if base_script_forms and "kana" in base_script_forms:
            base_script_forms["kana"] = normalize_reading(
                base_script_forms.get("kana"),
                language_tag=language_tag,
            )
        base_script_forms = merge_script_forms(
            base_script_forms,
            _build_default_script_forms(
                surface=surface,
                reading=reading,
                language_tag=language_tag,
            ),
        )
    elif base_script_forms is None:
        base_script_forms = _build_default_script_forms(
            surface=surface,
            reading=reading,
            language_tag=language_tag,
        )

    script_forms = normalize_script_forms(base_script_forms)
    if not reading:
        if language_tag.startswith("ja"):
            reading = normalize_reading(
                script_forms.get("kana") if isinstance(script_forms, Mapping) else "",
                language_tag=language_tag,
            )
        if not reading:
            reading = surface

    if not reading:
        return None
    if not script_forms:
        return None

    source = _normalize_source(raw.get("source"), fallback_provider=fallback_provider)
    if source is None:
        return None

    normalized: dict[str, object] = {
        "version": version,
        "language_tag": language_tag,
        "surface": surface,
        "reading": reading,
        "script_forms": script_forms,
        "source": source,
    }

    optional_text_fields = ("pos", "wtype", "sublemma", "lform_raw")
    for field in optional_text_fields:
        text = str(raw.get(field) or "").strip()
        if text:
            normalized[field] = text

    optional_float_fields = ("core_rank", "pmw", "row_rank")
    for field in optional_float_fields:
        value_float = _to_float(raw.get(field))
        if value_float is not None:
            normalized[field] = value_float

    row_index = _to_int(raw.get("row_index"), default=None)
    if row_index is not None:
        normalized["row_index"] = row_index

    return normalized


def extract_script_forms_from_word_package(value: object) -> Optional[dict[str, str]]:
    package = normalize_word_package(value)
    if package is None:
        return None
    return normalize_script_forms(package.get("script_forms"))


def _extract_primary_variant(text: str) -> str:
    if not text:
        return ""
    candidate = text
    for separator in (";", ",", "/", "|"):
        if separator in candidate:
            candidate = candidate.split(separator, 1)[0]
    return candidate.strip()


def _katakana_to_hiragana(text: str) -> str:
    out: list[str] = []
    for ch in text:
        code = ord(ch)
        if 0x30A1 <= code <= 0x30F6:
            out.append(chr(code - 0x60))
            continue
        if ch == "ヵ":
            out.append("か")
            continue
        if ch == "ヶ":
            out.append("け")
            continue
        out.append(ch)
    return "".join(out)


def _build_default_script_forms(
    *,
    surface: str,
    reading: str,
    language_tag: str,
) -> Optional[dict[str, str]]:
    forms: dict[str, str] = {}
    normalized_language_tag = normalize_language_tag(language_tag)
    normalized_reading = normalize_reading(reading, language_tag=normalized_language_tag)
    if normalized_language_tag.startswith("ja"):
        if contains_kanji(surface):
            forms["kanji"] = surface
        if normalized_reading and contains_kana(normalized_reading):
            forms["kana"] = normalized_reading
        elif contains_kana(surface):
            forms["kana"] = _katakana_to_hiragana(surface)
        kana_value = forms.get("kana")
        if kana_value:
            romaji = kana_to_romaji(kana_value)
            if romaji:
                forms["romaji"] = romaji
        if not forms:
            forms["surface"] = surface
        return forms

    if surface:
        forms["surface"] = surface
    return forms or None


def _normalize_source(
    value: object,
    *,
    fallback_provider: str,
) -> Optional[dict[str, object]]:
    source = dict(value) if isinstance(value, Mapping) else {}
    provider = str(source.get("provider") or fallback_provider or "").strip()
    if not provider:
        return None
    normalized: dict[str, object] = {"provider": provider}
    for key, raw in source.items():
        cleaned_key = str(key or "").strip()
        if not cleaned_key or cleaned_key == "provider":
            continue
        cleaned_value = _normalize_scalar(raw)
        if cleaned_value is not None:
            normalized[cleaned_key] = cleaned_value
    return normalized


def _normalize_scalar(value: object) -> Optional[object]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    text = str(value).strip()
    return text or None


def _to_float(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, (str, bytes, bytearray)):
        text = str(value).strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    return None


def _to_int(value: object, *, default: Optional[int]) -> Optional[int]:
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, (str, bytes, bytearray)):
        text = str(value).strip()
        if not text:
            return default
        try:
            return int(float(text))
        except ValueError:
            return default
    return default


__all__ = [
    "WORD_PACKAGE_VERSION",
    "build_word_package",
    "extract_script_forms_from_word_package",
    "merge_script_forms",
    "normalize_language_tag",
    "normalize_reading",
    "normalize_script_forms",
    "normalize_word_package",
    "resolve_language_tag_from_pair",
]
