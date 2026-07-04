from __future__ import annotations

from typing import Mapping

from lexishift_core.persistence.storage import VocabDataset, dataset_from_dict, dataset_to_dict
from lexishift_core.replacement.builder import BuildOptions, expand_vocab_rules
from lexishift_core.replacement.core import RuleMetadata, VocabRule
from lexishift_core.replacement.inflect import FORM_PLURAL, InflectionSpec


_ENGLISH_NOUN_PLURAL_SPEC = InflectionSpec(forms=frozenset({FORM_PLURAL}))


def build_runtime_ruleset_payload(
    payload: Mapping[str, object],
    *,
    pair: str,
) -> dict[str, object]:
    """Return the ruleset shape served to browser runtimes.

    SRS publication stores one canonical source phrase per selected rule. Browser
    replacement needs a small, safe source-language expansion layer so a selected
    noun like `company -> 会社` can still match `companies` on the page.
    """

    dataset = dataset_from_dict(payload)
    rules = tuple(dataset.rules)
    if _source_language(pair) != "en":
        return dict(payload)

    plural_specs = {
        rule.source_phrase: _ENGLISH_NOUN_PLURAL_SPEC for rule in rules if _rule_targets_noun(rule)
    }
    if not plural_specs:
        return dict(payload)

    expanded = expand_vocab_rules(
        rules,
        options=BuildOptions(
            inflection_spec=None,
            inflection_overrides=plural_specs,
            include_generated_tag=True,
            generated_tag="generated_source_plural",
        ),
    )
    return dataset_to_dict(
        VocabDataset(
            rules=tuple(expanded),
            meaning_rules=dataset.meaning_rules,
            synonyms=dataset.synonyms,
            version=dataset.version,
            settings=dataset.settings,
        )
    )


def _source_language(pair: str) -> str:
    return str(pair or "").strip().lower().split("-", 1)[0]


def _rule_targets_noun(rule: VocabRule) -> bool:
    metadata = rule.metadata
    if metadata is None:
        return False

    word_package = metadata.word_package if isinstance(metadata.word_package, Mapping) else {}
    if _canonical_pos_is_noun(word_package.get("pos_canonical")):
        return True

    pos = metadata.pos if isinstance(metadata.pos, Mapping) else {}
    target_pos = pos.get("target")
    if isinstance(target_pos, Mapping) and _canonical_pos_is_noun(target_pos.get("canonical")):
        return True

    return _source_pos_is_noun(metadata)


def _canonical_pos_is_noun(value: object) -> bool:
    return str(value or "").strip().lower() == "noun"


def _source_pos_is_noun(metadata: RuleMetadata) -> bool:
    pos = metadata.pos if isinstance(metadata.pos, Mapping) else {}
    source_pos = pos.get("source")
    if isinstance(source_pos, Mapping):
        raw = str(source_pos.get("raw") or "").strip().lower()
        if raw.startswith("noun") or "|noun" in raw:
            return True

    dictionary_pos = pos.get("dictionary")
    if isinstance(dictionary_pos, Mapping):
        raw = str(dictionary_pos.get("raw") or "").strip().lower()
        return raw.startswith("noun") or "|noun" in raw
    return False
