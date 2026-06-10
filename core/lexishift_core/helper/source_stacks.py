from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceStackResource:
    role: str
    family: str
    pack_id: str
    label_key: str = ""
    required_for: tuple[str, ...] = ()
    optional_for: tuple[str, ...] = ()
    pair_setup: bool = False
    wired: bool = True
    joins_on: str = ""
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "family": self.family,
            "pack_id": self.pack_id,
            "label_key": self.label_key or None,
            "required_for": list(self.required_for),
            "optional_for": list(self.optional_for),
            "pair_setup": self.pair_setup,
            "wired": self.wired,
            "joins_on": self.joins_on or None,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class PairSourceStack:
    pair: str
    stack_id: str
    label_key: str
    resources: tuple[SourceStackResource, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "pair": self.pair,
            "stack_id": self.stack_id,
            "label_key": self.label_key,
            "resources": [resource.as_dict() for resource in self.resources],
        }

    def pair_setup_resources(self) -> tuple[SourceStackResource, ...]:
        return tuple(
            resource
            for resource in self.resources
            if resource.pair_setup
            and resource.family in {"frequency", "language", "pos_overlay", "semantic_pack"}
        )


_SOURCE_STACKS: dict[str, PairSourceStack] = {
    "en-ja": PairSourceStack(
        pair="en-ja",
        stack_id="en-ja-default-v1",
        label_key="language_packs.learning_pairs.pairs.en_ja",
        resources=(
            SourceStackResource(
                role="target_frequency",
                family="frequency",
                pack_id="freq-ja-bccwj",
                label_key="language_packs.learning_pairs.resources.freq_ja_bccwj",
                required_for=("srs_admission", "srs_bootstrap"),
                pair_setup=True,
                joins_on="target_lemma",
                notes=("manual_supply_quality_preferred",),
            ),
            SourceStackResource(
                role="forward_translation",
                family="language",
                pack_id="jmdict-ja-en",
                label_key="language_packs.learning_pairs.resources.jmdict_ja_en",
                required_for=("srs_seed_validation", "rulegen", "semantic_publication"),
                pair_setup=True,
                joins_on="target_headword",
            ),
            SourceStackResource(
                role="source_frequency_prior",
                family="frequency",
                pack_id="freq-en-leipzig-default",
                label_key="language_packs.learning_pairs.resources.freq_en_leipzig_default",
                optional_for=("rulegen_source_frequency_prior_experiment",),
                wired=False,
                joins_on="source_lemma",
                notes=(
                    "en_ja_adapter_does_not_wire_sqlite_source_prior_yet",
                    "current_probe_no_ordering_gain",
                ),
            ),
            SourceStackResource(
                role="target_monolingual_wordnet",
                family="language",
                pack_id="jp-wordnet-sqlite",
                label_key="language_packs.learning_pairs.resources.jp_wordnet_sqlite",
                optional_for=("semantic_evidence_enrichment_experiment",),
                wired=False,
                joins_on="target_lemma",
                notes=("candidate_overlay_not_in_default_algorithm",),
            ),
        ),
    ),
    "en-de": PairSourceStack(
        pair="en-de",
        stack_id="en-de-default-v1",
        label_key="language_packs.learning_pairs.pairs.en_de",
        resources=(
            SourceStackResource(
                role="target_frequency",
                family="frequency",
                pack_id="freq-de-default",
                label_key="language_packs.learning_pairs.resources.freq_de_default",
                required_for=("srs_admission", "srs_bootstrap"),
                pair_setup=True,
                joins_on="target_lemma",
            ),
            SourceStackResource(
                role="source_frequency_prior",
                family="frequency",
                pack_id="freq-en-leipzig-default",
                label_key="language_packs.learning_pairs.resources.freq_en_leipzig_default",
                required_for=("rulegen_source_frequency_prior",),
                pair_setup=True,
                joins_on="source_lemma",
                notes=("fallback_pack_id:freq-en-coca",),
            ),
            SourceStackResource(
                role="forward_translation",
                family="language",
                pack_id="freedict-de-en",
                label_key="language_packs.learning_pairs.resources.freedict_de_en",
                required_for=("rulegen", "semantic_publication"),
                pair_setup=True,
                joins_on="target_headword",
            ),
            SourceStackResource(
                role="reverse_translation",
                family="language",
                pack_id="freedict-en-de",
                label_key="language_packs.learning_pairs.resources.freedict_en_de",
                required_for=("rulegen_reverse_check",),
                pair_setup=True,
                joins_on="source_headword",
            ),
            SourceStackResource(
                role="semantic_reference_pack",
                family="semantic_pack",
                pack_id="en-de-semantic-reference-pending",
                label_key="language_packs.learning_pairs.resources.semantic_en_de_pending",
                optional_for=("semantic_admission_reference",),
                pair_setup=True,
                wired=False,
                joins_on="source_replacement_family",
                notes=("no_default_semantic_reference_pack_declared",),
            ),
            SourceStackResource(
                role="target_monolingual_thesaurus",
                family="language",
                pack_id="openthesaurus-de",
                optional_for=("semantic_evidence_enrichment_experiment",),
                wired=False,
                joins_on="target_lemma",
                notes=("candidate_overlay_not_in_default_algorithm",),
            ),
            SourceStackResource(
                role="target_monolingual_wordnet",
                family="language",
                pack_id="odenet-de",
                optional_for=("semantic_evidence_enrichment_experiment",),
                wired=False,
                joins_on="target_lemma",
                notes=("candidate_overlay_not_in_default_algorithm",),
            ),
        ),
    ),
    "en-es": PairSourceStack(
        pair="en-es",
        stack_id="en-es-default-v2",
        label_key="language_packs.learning_pairs.pairs.en_es",
        resources=(
            SourceStackResource(
                role="target_frequency",
                family="frequency",
                pack_id="freq-es-spalex-v1",
                label_key="language_packs.learning_pairs.resources.freq_es_spalex",
                required_for=("srs_admission", "srs_bootstrap"),
                pair_setup=True,
                joins_on="target_word_form",
            ),
            SourceStackResource(
                role="target_pos_overlay",
                family="pos_overlay",
                pack_id="pos-es-ud-ancora-v1",
                label_key="language_packs.learning_pairs.resources.pos_es_ud_ancora",
                optional_for=("srs_admission_pos_recovery",),
                pair_setup=True,
                joins_on="target_word_form",
            ),
            SourceStackResource(
                role="forward_translation",
                family="language",
                pack_id="wiktionary-es-en",
                label_key="language_packs.learning_pairs.resources.wiktionary_es_en",
                required_for=("rulegen", "semantic_publication"),
                pair_setup=True,
                joins_on="target_headword",
            ),
            SourceStackResource(
                role="fallback_forward_translation",
                family="language",
                pack_id="freedict-es-en",
                label_key="language_packs.learning_pairs.resources.freedict_es_en",
                required_for=("rulegen_fallback",),
                pair_setup=True,
                joins_on="target_headword",
            ),
            SourceStackResource(
                role="semantic_reference_pack",
                family="semantic_pack",
                pack_id="en-es-active-only-combined-full-v1-tranche-011",
                label_key="language_packs.learning_pairs.resources.semantic_en_es_sentence_veto",
                optional_for=("semantic_admission_reference",),
                pair_setup=True,
                joins_on="source_replacement_family",
            ),
            SourceStackResource(
                role="reverse_translation",
                family="language",
                pack_id="wiktionary-en-es",
                required_for=("rulegen_reverse_check",),
                joins_on="source_headword",
            ),
            SourceStackResource(
                role="fallback_reverse_translation",
                family="language",
                pack_id="freedict-en-es",
                optional_for=("rulegen_reverse_check_fallback",),
                joins_on="source_headword",
            ),
        ),
    ),
}


def normalize_pair_key(pair: str | None) -> str:
    return str(pair or "").strip().lower()


def source_stack_for_pair(pair: str | None) -> PairSourceStack | None:
    return _SOURCE_STACKS.get(normalize_pair_key(pair))


def source_stack_payload(pair: str | None) -> dict[str, object] | None:
    stack = source_stack_for_pair(pair)
    return stack.as_dict() if stack is not None else None


def available_source_stacks() -> tuple[PairSourceStack, ...]:
    return tuple(_SOURCE_STACKS[pair] for pair in sorted(_SOURCE_STACKS))
