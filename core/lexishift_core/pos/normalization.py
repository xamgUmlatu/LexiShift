from __future__ import annotations

from dataclasses import dataclass
import re

CANONICAL_POS_NOUN = "noun"
CANONICAL_POS_ADJECTIVE = "adjective"
CANONICAL_POS_VERB = "verb"
CANONICAL_POS_ADVERB = "adverb"
CANONICAL_POS_PRONOUN = "pronoun"
CANONICAL_POS_DETERMINER = "determiner"
CANONICAL_POS_ADPOSITION = "adposition"
CANONICAL_POS_CONJUNCTION = "conjunction"
CANONICAL_POS_INTERJECTION = "interjection"
CANONICAL_POS_NUMERAL = "numeral"
CANONICAL_POS_PUNCTUATION = "punctuation"
CANONICAL_POS_OTHER = "other"

CANONICAL_POS_TAGS = (
    CANONICAL_POS_NOUN,
    CANONICAL_POS_ADJECTIVE,
    CANONICAL_POS_VERB,
    CANONICAL_POS_ADVERB,
    CANONICAL_POS_PRONOUN,
    CANONICAL_POS_DETERMINER,
    CANONICAL_POS_ADPOSITION,
    CANONICAL_POS_CONJUNCTION,
    CANONICAL_POS_INTERJECTION,
    CANONICAL_POS_NUMERAL,
    CANONICAL_POS_PUNCTUATION,
    CANONICAL_POS_OTHER,
)

POS_BUCKET_TAGS = (
    CANONICAL_POS_NOUN,
    CANONICAL_POS_ADJECTIVE,
    CANONICAL_POS_VERB,
    CANONICAL_POS_ADVERB,
    CANONICAL_POS_OTHER,
)

PROFILE_BCCWJ = "bccwj"
PROFILE_FREQ_ES_CDE = "freq-es-cde"
PROFILE_SPALEX_ONLY = "spalex_only_v1"
PROFILE_FREQ_DE_DEFAULT = "freq-de-default"
PROFILE_UNIVERSAL_DEPENDENCIES = "universal-dependencies"
PROFILE_COMPACT_LATIN = "compact-latin"
PROFILE_FREEDICT = "freedict"
PROFILE_WIKTIONARY = "wiktionary"
PROFILE_GENERIC = "generic"

KNOWN_SOURCE_PROFILES = (
    PROFILE_BCCWJ,
    PROFILE_FREQ_ES_CDE,
    PROFILE_SPALEX_ONLY,
    PROFILE_FREQ_DE_DEFAULT,
    PROFILE_UNIVERSAL_DEPENDENCIES,
    PROFILE_COMPACT_LATIN,
    PROFILE_FREEDICT,
    PROFILE_WIKTIONARY,
    PROFILE_GENERIC,
)

_LEXICAL_PRIORITY = {
    CANONICAL_POS_NOUN: 0,
    CANONICAL_POS_ADJECTIVE: 1,
    CANONICAL_POS_VERB: 2,
    CANONICAL_POS_ADVERB: 3,
}

_TOKEN_SPLIT_PATTERN = re.compile(r"[:|+_\-/\s,.;]+")

_COMPACT_ONE_CHAR_MAP = {
    "n": CANONICAL_POS_NOUN,
    "j": CANONICAL_POS_ADJECTIVE,
    "a": CANONICAL_POS_ADJECTIVE,
    "v": CANONICAL_POS_VERB,
    "r": CANONICAL_POS_ADVERB,
    "p": CANONICAL_POS_PRONOUN,
    "d": CANONICAL_POS_DETERMINER,
    "l": CANONICAL_POS_DETERMINER,
    "e": CANONICAL_POS_ADPOSITION,
    "c": CANONICAL_POS_CONJUNCTION,
    "i": CANONICAL_POS_INTERJECTION,
    "m": CANONICAL_POS_NUMERAL,
    # COCA sample data includes "u" as a residual class; treat as mapped-other.
    "u": CANONICAL_POS_OTHER,
    "-": CANONICAL_POS_PUNCTUATION,
}

_PENN_MAP = {
    "nn": CANONICAL_POS_NOUN,
    "nns": CANONICAL_POS_NOUN,
    "nnp": CANONICAL_POS_NOUN,
    "nnps": CANONICAL_POS_NOUN,
    "jj": CANONICAL_POS_ADJECTIVE,
    "jjr": CANONICAL_POS_ADJECTIVE,
    "jjs": CANONICAL_POS_ADJECTIVE,
    "vb": CANONICAL_POS_VERB,
    "vbd": CANONICAL_POS_VERB,
    "vbg": CANONICAL_POS_VERB,
    "vbn": CANONICAL_POS_VERB,
    "vbp": CANONICAL_POS_VERB,
    "vbz": CANONICAL_POS_VERB,
    "rb": CANONICAL_POS_ADVERB,
    "rbr": CANONICAL_POS_ADVERB,
    "rbs": CANONICAL_POS_ADVERB,
    "prp": CANONICAL_POS_PRONOUN,
    "prp$": CANONICAL_POS_PRONOUN,
    "dt": CANONICAL_POS_DETERMINER,
    "in": CANONICAL_POS_ADPOSITION,
    "cc": CANONICAL_POS_CONJUNCTION,
    "uh": CANONICAL_POS_INTERJECTION,
    "cd": CANONICAL_POS_NUMERAL,
}

_GENERIC_SUBSTRING_RULES = (
    ("noun", CANONICAL_POS_NOUN, "generic_substring:noun"),
    ("substantiv", CANONICAL_POS_NOUN, "generic_substring:substantiv"),
    ("subst", CANONICAL_POS_NOUN, "generic_substring:subst"),
    ("adjective", CANONICAL_POS_ADJECTIVE, "generic_substring:adjective"),
    ("adjektiv", CANONICAL_POS_ADJECTIVE, "generic_substring:adjektiv"),
    ("adj", CANONICAL_POS_ADJECTIVE, "generic_substring:adj"),
    ("verb", CANONICAL_POS_VERB, "generic_substring:verb"),
    ("adverb", CANONICAL_POS_ADVERB, "generic_substring:adverb"),
    ("adv", CANONICAL_POS_ADVERB, "generic_substring:adv"),
    ("pronoun", CANONICAL_POS_PRONOUN, "generic_substring:pronoun"),
    ("pronomen", CANONICAL_POS_PRONOUN, "generic_substring:pronomen"),
    ("pron", CANONICAL_POS_PRONOUN, "generic_substring:pron"),
    ("determiner", CANONICAL_POS_DETERMINER, "generic_substring:determiner"),
    ("article", CANONICAL_POS_DETERMINER, "generic_substring:article"),
    ("artikel", CANONICAL_POS_DETERMINER, "generic_substring:artikel"),
    ("det", CANONICAL_POS_DETERMINER, "generic_substring:det"),
    ("adposition", CANONICAL_POS_ADPOSITION, "generic_substring:adposition"),
    ("preposition", CANONICAL_POS_ADPOSITION, "generic_substring:preposition"),
    ("präposition", CANONICAL_POS_ADPOSITION, "generic_substring:präposition"),
    ("prep", CANONICAL_POS_ADPOSITION, "generic_substring:prep"),
    ("adp", CANONICAL_POS_ADPOSITION, "generic_substring:adp"),
    ("conjunction", CANONICAL_POS_CONJUNCTION, "generic_substring:conjunction"),
    ("konjunktion", CANONICAL_POS_CONJUNCTION, "generic_substring:konjunktion"),
    ("conj", CANONICAL_POS_CONJUNCTION, "generic_substring:conj"),
    ("interjection", CANONICAL_POS_INTERJECTION, "generic_substring:interjection"),
    ("interjektion", CANONICAL_POS_INTERJECTION, "generic_substring:interjektion"),
    ("intj", CANONICAL_POS_INTERJECTION, "generic_substring:intj"),
    ("numeral", CANONICAL_POS_NUMERAL, "generic_substring:numeral"),
    ("zahl", CANONICAL_POS_NUMERAL, "generic_substring:zahl"),
    ("num", CANONICAL_POS_NUMERAL, "generic_substring:num"),
    ("punct", CANONICAL_POS_PUNCTUATION, "generic_substring:punct"),
)


@dataclass(frozen=True)
class NormalizedPos:
    raw: str
    canonical: str
    bucket: str
    matched_rule: str
    source_profile: str
    mapped: bool


def normalize_pos(
    raw_pos: object,
    *,
    language_pair: str = "",
    source_provider: str = "",
    source_kind: str = "",
    target_language: str = "",
    source_profile: str = "",
) -> NormalizedPos:
    raw_text = str(raw_pos or "").strip()
    resolved_profile = resolve_pos_source_profile(
        language_pair=language_pair,
        source_provider=source_provider,
        source_kind=source_kind,
        target_language=target_language,
        source_profile=source_profile,
    )
    if not raw_text:
        return NormalizedPos(
            raw=raw_text,
            canonical=CANONICAL_POS_OTHER,
            bucket=CANONICAL_POS_OTHER,
            matched_rule="empty",
            source_profile=resolved_profile,
            mapped=False,
        )
    if resolved_profile == PROFILE_BCCWJ:
        canonical, rule, mapped = _normalize_bccwj(raw_text)
    elif resolved_profile == PROFILE_FREQ_ES_CDE:
        canonical, rule, mapped = _normalize_compact_latin(raw_text, rule_prefix="freq-es-cde")
    elif resolved_profile == PROFILE_FREQ_DE_DEFAULT:
        canonical, rule, mapped = _normalize_de_frequency(raw_text)
    elif resolved_profile == PROFILE_UNIVERSAL_DEPENDENCIES:
        canonical, rule, mapped = _normalize_universal_dependencies(raw_text)
    elif resolved_profile == PROFILE_FREEDICT:
        canonical, rule, mapped = _normalize_freedict(raw_text)
    elif resolved_profile == PROFILE_WIKTIONARY:
        canonical, rule, mapped = _normalize_wiktionary(raw_text)
    elif resolved_profile == PROFILE_COMPACT_LATIN:
        canonical, rule, mapped = _normalize_compact_latin(raw_text, rule_prefix="compact")
    else:
        canonical, rule, mapped = _normalize_generic(raw_text)
    canonical_resolved = canonical if canonical in CANONICAL_POS_TAGS else CANONICAL_POS_OTHER
    bucket = canonical_pos_to_bucket(canonical_resolved)
    return NormalizedPos(
        raw=raw_text,
        canonical=canonical_resolved,
        bucket=bucket,
        matched_rule=rule,
        source_profile=resolved_profile,
        mapped=bool(mapped),
    )


def canonical_pos_to_bucket(canonical_pos: object) -> str:
    normalized = str(canonical_pos or "").strip().lower()
    if normalized in _LEXICAL_PRIORITY:
        return normalized
    return CANONICAL_POS_OTHER


def normalize_source_profile_name(value: object) -> str:
    text = str(value or "").strip().lower().replace("_", "-")
    if text in KNOWN_SOURCE_PROFILES:
        return text
    return ""


def resolve_pos_source_profile(
    *,
    language_pair: str = "",
    source_provider: str = "",
    source_kind: str = "",
    target_language: str = "",
    source_profile: str = "",
) -> str:
    explicit = normalize_source_profile_name(source_profile)
    if explicit:
        return explicit

    provider = str(source_provider or "").strip().lower()
    kind = str(source_kind or "").strip().lower()
    target = _resolve_target_language(language_pair=language_pair, target_language=target_language)

    if "freq-ja-bccwj" in provider or "bccwj" in provider:
        return PROFILE_BCCWJ
    if "freq-es-cde" in provider:
        return PROFILE_FREQ_ES_CDE
    if "spalex" in provider:
        return PROFILE_SPALEX_ONLY
    if "freq-de-default" in provider:
        return PROFILE_FREQ_DE_DEFAULT
    if "universaldependencies" in provider or "universal-dependencies" in provider:
        return PROFILE_UNIVERSAL_DEPENDENCIES
    if "ud-ancora" in provider or "ud_ancora" in provider:
        return PROFILE_UNIVERSAL_DEPENDENCIES
    if "freq-en-coca" in provider:
        return PROFILE_COMPACT_LATIN
    if "freedict" in provider:
        return PROFILE_FREEDICT
    if "wiktionary" in provider or "kaikki" in provider:
        return PROFILE_WIKTIONARY

    if "freedict" in kind:
        return PROFILE_FREEDICT
    if "wiktionary" in kind:
        return PROFILE_WIKTIONARY
    if kind in {"pos-overlay", "pos_overlay"} and target == "es":
        return PROFILE_UNIVERSAL_DEPENDENCIES
    if "frequency" in kind:
        if target == "ja":
            return PROFILE_BCCWJ
        if target == "es":
            return PROFILE_FREQ_ES_CDE
        if target == "de":
            return PROFILE_FREQ_DE_DEFAULT
        if target == "en":
            return PROFILE_COMPACT_LATIN

    if target == "ja":
        return PROFILE_BCCWJ
    if target == "de":
        return PROFILE_FREQ_DE_DEFAULT
    return PROFILE_GENERIC


def _resolve_target_language(*, language_pair: str, target_language: str) -> str:
    explicit = str(target_language or "").strip().lower()
    if explicit:
        return explicit
    pair = str(language_pair or "").strip().lower()
    if "-" not in pair:
        return ""
    _source, _sep, target = pair.partition("-")
    return target


def _normalize_bccwj(raw: str) -> tuple[str, str, bool]:
    if "数詞" in raw:
        return CANONICAL_POS_NUMERAL, "bccwj_contains:数詞", True
    head = raw.split("-", 1)[0].strip()
    mapping = {
        "名詞": CANONICAL_POS_NOUN,
        "代名詞": CANONICAL_POS_PRONOUN,
        "形容詞": CANONICAL_POS_ADJECTIVE,
        "形状詞": CANONICAL_POS_ADJECTIVE,
        "連体詞": CANONICAL_POS_DETERMINER,
        "動詞": CANONICAL_POS_VERB,
        "助動詞": CANONICAL_POS_VERB,
        "副詞": CANONICAL_POS_ADVERB,
        "助詞": CANONICAL_POS_ADPOSITION,
        "接続詞": CANONICAL_POS_CONJUNCTION,
        "感動詞": CANONICAL_POS_INTERJECTION,
        "記号": CANONICAL_POS_PUNCTUATION,
        "補助記号": CANONICAL_POS_PUNCTUATION,
        # BCCWJ affix classes are non-lexical for our buckets; map explicitly to other.
        "接頭辞": CANONICAL_POS_OTHER,
        "接尾辞": CANONICAL_POS_OTHER,
    }
    canonical = mapping.get(head)
    if canonical:
        return canonical, f"bccwj_head:{head}", True
    return CANONICAL_POS_OTHER, f"bccwj_unmapped:{head or raw}", False


def _normalize_de_frequency(raw: str) -> tuple[str, str, bool]:
    tokens = _split_tokens(raw, lower=False)
    hits: list[tuple[str, str, int]] = []
    for index, token_raw in enumerate(tokens):
        token = token_raw.upper()
        if token in {"SUB", "NOUN", "NOMEN", "NN"} or token.startswith("NN"):
            hits.append((CANONICAL_POS_NOUN, f"de_token:{token}", index))
            continue
        if token in {"ADJ", "ADJA", "ADJD"} or token.startswith("ADJ"):
            hits.append((CANONICAL_POS_ADJECTIVE, f"de_token:{token}", index))
            continue
        if token in {"VER", "VERB"} or token.startswith(("VV", "VA", "VM")):
            hits.append((CANONICAL_POS_VERB, f"de_token:{token}", index))
            continue
        if token in {"ADV", "NEG"}:
            hits.append((CANONICAL_POS_ADVERB, f"de_token:{token}", index))
            continue
        if token in {
            "PRO",
            "PRON",
            "PPER",
            "PDS",
            "PDAT",
            "PIS",
            "PIAT",
            "PIDAT",
            "PPOSAT",
            "PRELS",
            "PRELAT",
            "PRF",
            "PWS",
            "PWAT",
            "PWAV",
        }:
            hits.append((CANONICAL_POS_PRONOUN, f"de_token:{token}", index))
            continue
        if token in {"ART", "DET"}:
            hits.append((CANONICAL_POS_DETERMINER, f"de_token:{token}", index))
            continue
        if token in {"APPR", "APPO", "APZR", "PREP", "PRP", "ADP"}:
            hits.append((CANONICAL_POS_ADPOSITION, f"de_token:{token}", index))
            continue
        if token in {"KON", "KOUS", "KOUI", "CONJ"}:
            hits.append((CANONICAL_POS_CONJUNCTION, f"de_token:{token}", index))
            continue
        if token in {"ITJ", "INTJ"}:
            hits.append((CANONICAL_POS_INTERJECTION, f"de_token:{token}", index))
            continue
        if token in {"CARD", "NUM", "ZAL"}:
            hits.append((CANONICAL_POS_NUMERAL, f"de_token:{token}", index))
            continue
        if token in {"PUNCT", "$.", "$,", "$("} or token.startswith("$"):
            hits.append((CANONICAL_POS_PUNCTUATION, f"de_token:{token}", index))
            continue
    return _select_hit(hits, fallback_rule=f"de_unmapped:{raw}")


def _normalize_universal_dependencies(raw: str) -> tuple[str, str, bool]:
    tokens = _split_tokens(raw, lower=False)
    if not tokens and raw.strip():
        tokens = [raw.strip()]
    hits: list[tuple[str, str, int]] = []
    mapping = {
        "ADJ": CANONICAL_POS_ADJECTIVE,
        "ADP": CANONICAL_POS_ADPOSITION,
        "ADV": CANONICAL_POS_ADVERB,
        "AUX": CANONICAL_POS_VERB,
        "CCONJ": CANONICAL_POS_CONJUNCTION,
        "DET": CANONICAL_POS_DETERMINER,
        "INTJ": CANONICAL_POS_INTERJECTION,
        "NOUN": CANONICAL_POS_NOUN,
        "NUM": CANONICAL_POS_NUMERAL,
        "PART": CANONICAL_POS_OTHER,
        "PRON": CANONICAL_POS_PRONOUN,
        "PROPN": CANONICAL_POS_NOUN,
        "PUNCT": CANONICAL_POS_PUNCTUATION,
        "SCONJ": CANONICAL_POS_CONJUNCTION,
        "SYM": CANONICAL_POS_PUNCTUATION,
        "VERB": CANONICAL_POS_VERB,
        "X": CANONICAL_POS_OTHER,
    }
    for index, token_raw in enumerate(tokens):
        token = token_raw.upper()
        canonical = mapping.get(token)
        if canonical:
            hits.append((canonical, f"ud_upos:{token}", index))
    return _select_hit(hits, fallback_rule=f"ud_unmapped:{raw}")


def _normalize_compact_latin(raw: str, *, rule_prefix: str) -> tuple[str, str, bool]:
    tokens = _split_tokens(raw, lower=True)
    if not tokens and raw.strip():
        token = raw.strip().lower()
        tokens = [token]
    hits: list[tuple[str, str, int]] = []
    for index, token in enumerate(tokens):
        canonical = _COMPACT_ONE_CHAR_MAP.get(token)
        if canonical:
            hits.append((canonical, f"{rule_prefix}_compact:{token}", index))
            continue
        penn = _PENN_MAP.get(token)
        if penn:
            hits.append((penn, f"{rule_prefix}_penn:{token}", index))
    return _select_hit(hits, fallback_rule=f"{rule_prefix}_unmapped:{raw}")


def _normalize_freedict(raw: str) -> tuple[str, str, bool]:
    hits = _collect_generic_hits(raw, rule_prefix="freedict")
    return _select_hit(hits, fallback_rule=f"freedict_unmapped:{raw}")


def _normalize_wiktionary(raw: str) -> tuple[str, str, bool]:
    compact_hits = _collect_compact_hits(raw, rule_prefix="wiktionary")
    generic_hits = _collect_generic_hits(raw, rule_prefix="wiktionary")
    return _select_hit(
        [*compact_hits, *generic_hits],
        fallback_rule=f"wiktionary_unmapped:{raw}",
    )


def _normalize_generic(raw: str) -> tuple[str, str, bool]:
    compact_hits = _collect_compact_hits(raw, rule_prefix="generic")
    generic_hits = _collect_generic_hits(raw, rule_prefix="generic")
    return _select_hit(
        [*compact_hits, *generic_hits],
        fallback_rule=f"generic_unmapped:{raw}",
    )


def _collect_compact_hits(raw: str, *, rule_prefix: str) -> list[tuple[str, str, int]]:
    tokens = _split_tokens(raw, lower=True)
    if not tokens and raw.strip():
        tokens = [raw.strip().lower()]
    hits: list[tuple[str, str, int]] = []
    for index, token in enumerate(tokens):
        canonical = _COMPACT_ONE_CHAR_MAP.get(token)
        if canonical:
            hits.append((canonical, f"{rule_prefix}_compact:{token}", index))
            continue
        penn = _PENN_MAP.get(token)
        if penn:
            hits.append((penn, f"{rule_prefix}_penn:{token}", index))
    return hits


def _collect_generic_hits(raw: str, *, rule_prefix: str) -> list[tuple[str, str, int]]:
    lowered = raw.lower()
    hits: list[tuple[str, str, int]] = []
    for index, (needle, canonical, _rule_name) in enumerate(_GENERIC_SUBSTRING_RULES):
        if needle in lowered:
            hits.append((canonical, f"{rule_prefix}_substring:{needle}", index))
    return hits


def _select_hit(
    hits: list[tuple[str, str, int]],
    *,
    fallback_rule: str,
) -> tuple[str, str, bool]:
    if not hits:
        return CANONICAL_POS_OTHER, fallback_rule, False
    lexical = [item for item in hits if item[0] in _LEXICAL_PRIORITY]
    candidates = lexical or hits
    best = min(
        candidates,
        key=lambda item: (
            _LEXICAL_PRIORITY.get(item[0], 99),
            item[2],
        ),
    )
    canonical, rule, _index = best
    return canonical, rule, True


def _split_tokens(raw: str, *, lower: bool) -> list[str]:
    parts = _TOKEN_SPLIT_PATTERN.split(str(raw or "").strip())
    tokens = [part for part in parts if part]
    if lower:
        return [item.lower() for item in tokens]
    return tokens


__all__ = [
    "CANONICAL_POS_TAGS",
    "KNOWN_SOURCE_PROFILES",
    "NormalizedPos",
    "POS_BUCKET_TAGS",
    "canonical_pos_to_bucket",
    "normalize_pos",
    "normalize_source_profile_name",
    "resolve_pos_source_profile",
]
