# en-es Semantic Veto LLM Data Priority Target-Family Construction

- Status: `ok`
- Decision: `target_family_construction_queue_established`
- Generated: `2026-05-05T20:07:04+00:00`
- Attempts: `34`
- Source-ready family drafts: `3`
- Weak diagnostic family drafts: `25`
- Blocked rows: `6`

## Goal

Move top inventory-only rows one stage forward by constructing Spanish target/shadow family drafts before any LLM active/shadow/phrase row spend.

This report still does not generate active/shadow/phrase LLM rows. It only moves rows from English-only inventory toward reviewed en-es target families.

## Stage Counts

| Stage | Count |
| --- | ---: |
| `construction_blocked` | 6 |
| `source_supported_family_draft_needs_review` | 3 |
| `weak_family_draft_needs_source_support` | 25 |

## Construction Attempts

| Rank | Trigger | Bridge rank | Stage | Strategy | Active | Shadows | Reason |
| ---: | --- | ---: | --- | --- | --- | --- | --- |
| 1 | `flush` | 17 | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `rico (adjective)` | `color (noun)` | `constructed_family` |
| 2 | `rough` | 18 | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 3 | `home` | 19 | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `hogar (noun)` | `patria (noun), en casa (adverb)` | `constructed_family` |
| 4 | `out` | 20 | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `afuera (adverb)` | `sacar del armario (verb)` | `constructed_family` |
| 5 | `true` | 21 | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 6 | `better` | 22 | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `mejor (adjective)` | `mejorar (verb)` | `constructed_family` |
| 7 | `flash` | 23 | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `flash (noun)` | `periquete (noun), destellar (verb)` | `constructed_family` |
| 8 | `level` | 24 | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `nivel (noun)` | `nivelar (verb)` | `constructed_family` |
| 9 | `separate` | 25 | `source_supported_family_draft_needs_review` | `any_cross_pos_supported_source_linked` | `separado (adjective)` | `separar (verb)` | `constructed_family` |
| 10 | `bound` | 26 | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `límite (noun)` | `cota (noun), limitar (verb)` | `constructed_family` |
| 11 | `slack` | 27 | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `flojo (adjective)` | `carbonilla (noun)` | `constructed_family` |
| 12 | `split` | 28 | `source_supported_family_draft_needs_review` | `any_cross_pos_supported_source_linked` | `partido (adjective)` | `escisión (noun)` | `constructed_family` |
| 13 | `white` | 29 | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `blanco (adjective)` | `blanquiñoso (noun)` | `constructed_family` |
| 14 | `blue` | 30 | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `azul (noun)` | `azular (verb)` | `constructed_family` |
| 15 | `fit` | 31 | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `idóneo (adjective)` | `caber (verb)` | `constructed_family` |
| 16 | `smash` | 32 | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 17 | `fine` | 33 | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `multa (noun)` | `multar (verb)` | `constructed_family` |
| 18 | `cross` | 34 | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `cruce (noun)` | `contrariar (verb)` | `constructed_family` |
| 19 | `color` | 35 | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `en color (adjective)` | `colorar (verb)` | `constructed_family` |
| 20 | `side` | 36 | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 21 | `subject` | 37 | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `sujeto (noun)` | `materia (noun), someter (verb)` | `constructed_family` |
| 22 | `control` | 38 | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `administración (noun)` | `mando (noun), controlar (verb)` | `constructed_family` |
| 23 | `rule` | 39 | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `regla (noun)` | `laudar (verb)` | `constructed_family` |
| 24 | `strain` | 40 | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `cepa (noun)` | `variedad (noun), esforzar (verb)` | `constructed_family` |
| 25 | `spare` | 41 | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `repuesto (noun)` | `apiadarse de (verb)` | `constructed_family` |
| 26 | `burn` | 42 | `source_supported_family_draft_needs_review` | `noun_verb_supported_source_linked` | `quemadura (noun)` | `arder (verb)` | `constructed_family` |
| 27 | `spot` | 43 | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `mancha (noun)` | `grano (noun), divisar (verb)` | `constructed_family` |
| 28 | `strip` | 44 | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `franja (noun)` | `remover (verb)` | `constructed_family` |
| 29 | `bar` | 45 | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `abogacía (noun)` | `barrear (verb)` | `constructed_family` |
| 30 | `figure` | 46 | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `figura (noun)` | `cifra (noun), ocurrírsele (verb)` | `constructed_family` |
| 31 | `force` | 47 | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `fuerza (noun)` | `descerrajar (verb)` | `constructed_family` |
| 32 | `hang` | 48 | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 33 | `number` | 49 | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `número (noun)` | `cantidad (noun), numerar (verb)` | `constructed_family` |
| 34 | `position` | 50 | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |

## Guardrails

| Check | Value |
| --- | --- |
| `attempts_are_bridge_inventory_only_rows` | `True` |
| `no_llm_packets_emitted` | `True` |
| `source_ready_rows_have_source_supported_strategy` | `True` |
| `weak_rows_not_marked_source_ready` | `True` |
| `selected_families_have_distinct_visible_targets` | `True` |

## Limitations

- `constructed_families_are_drafts_and_need_review_before_locked_eval_claims`
- `source_ready_here_means_ready_for_scored_probe_not_runtime_promotion`
- `diagnostic_translation_only_families_are_not_scored_probe_inputs`
- `no_active_shadow_phrase_llm_rows_are_generated_by_this_harness`

## Next Steps

- Review the source-ready target/shadow family drafts for visible-target and sense quality.
- Run scored context probes only for reviewed source-ready families.
- Return reviewed probe rows to the LLM data priority scan before spending on active/shadow/phrase examples.
