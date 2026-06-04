# Rulegen `en-es` Seam Map

Status: active plan
Role: Planning / WIP
Last updated: 2026-04-16
Last verified: 2026-04-16 code-structure audit of `core/lexishift_core/rulegen/pairs/en_es.py`, `core/lexishift_core/rulegen/pairs/en_es_support.py`, `core/lexishift_core/rulegen/adapters.py`, `core/tests/rulegen/test_rulegen_en_es_compiled_resources.py`, and `core/tests/dev/test_rulegen_benchmark.py`
Purpose: identify the verified extraction seams inside `core/lexishift_core/rulegen/pairs/en_es.py` so Wave F can reduce project-health risk without drifting the current `en-es` rulegen contract
Source-of-truth: planning doc only; executable truth still lives in `core/lexishift_core/rulegen/pairs/en_es.py` and the owning tests/scripts
Verification: F1 is a docs-only seam map; follow-on slices `F2` through `F4` still need the backlog validation bundles (`V0`, `V1`, `V4`)

## Scope

This note is for `F1` only.
It does not change behavior.

Its job is to answer four questions before any extraction starts:

1. which parts of `en_es.py` are natural seams rather than arbitrary chunks,
2. which names are already part of the effective public/tooling contract,
3. which dependencies make a naive split risky,
4. what order keeps `F2`, `F3`, and `F4` disciplined.

## Current External Contract To Preserve

There are two different contract surfaces today.

### Runtime contract

The runtime-facing pair contract is small:

- `lexishift_core.rulegen.pairs.__init__` re-exports:
  - `EnEsRulegenConfig`
  - `generate_en_es_results`
  - `generate_en_es_rules`
- `core/lexishift_core/rulegen/adapters.py` builds `EnEsRulegenConfig` and calls `generate_en_es_results(...)`

This is the contract that must still be simple when `F4` is done.

### Tooling and test contract

The benchmark and verification surfaces already import more than the runtime does:

- `scripts/testing/rulegen_benchmark_resources.py`
  - `build_en_es_compiled_resources`
- `scripts/testing/rulegen_benchmark_sweep.py`
  - `build_en_es_compiled_selected_row_table`
  - `prepare_en_es_compiled_benchmark_sweep_tables`
- `core/tests/rulegen/test_rulegen_en_es_compiled_resources.py`
  - direct imports of the compiled-resource builders, pipeline builder, benchmark-table builders, and several private helper functions
- `core/tests/dev/test_rulegen_benchmark.py`
  - direct imports of compiled-resource and selected-row helpers

Implication:

- `F2` and `F3` should preserve the current import path from `en_es.py`
- move implementations first
- keep compatibility re-exports or thin wrappers in `en_es.py`
- only reduce the top-level surface in `F4`, after the new internal modules are stable

## Verified Structural Seams

The file is large because several real seams are physically interleaved.
The extraction plan should follow the conceptual seams, not the current line order.

### 1. Existing support seam: gloss/provenance helpers

Current home:

- `core/lexishift_core/rulegen/pairs/en_es_support.py` (`840` lines as of this audit)

Current responsibilities:

- gloss sanitation and fragmentation
- reverse-token normalization
- gloss/sense/target provenance shaping
- Kaikki-family shadow and demotion helpers

Important constraint:

- this file is already on the project-health watchlist
- `F2` through `F4` should not keep appending new compiled-pipeline logic here
- use new focused modules instead of turning `en_es_support.py` into a second hotspot

### 2. Compiled inventory and provenance assembly seam

Current anchors inside `en_es.py`:

- `build_en_es_compiled_resources(...)`
- `_build_static_candidate_inventory(...)`
- `_build_static_candidate_metadata(...)`
- `_extract_kaikki_family_names(...)`
- `_build_definition_bucket_ids(...)`
- `_build_family_marker_ids(...)`
- `_build_compiled_candidate_fact(...)`
- `_build_compiled_candidate_table(...)`
- `_finalize_compiled_target_contexts(...)`
- `EnEsCompiledCandidateFact`
- `EnEsCompiledCandidateTable`
- `EnEsCompiledTargetContext`
- `EnEsCompiledResources`

Current responsibilities:

- turn ordered translation-gloss records plus optional reverse records and word packages into:
  - base `RuleCandidate` rows
  - stable metadata keys
  - target contexts
  - compiled candidate facts/tables
  - cache-tokened compiled resources

Why this is the first extraction seam:

- it is mostly shaping and indexing, not score math
- it already behaves like a support layer consumed by the rest of the file
- it is the cleanest `F2` move that reduces line/function pressure without changing ranking behavior

Recommended home:

- `core/lexishift_core/rulegen/pairs/en_es_compiled_inventory.py`

Guardrails:

- keep `compiled_candidate_id`, `compiled_target_id`, `compiled_definition_bucket_id`, and related metadata keys unchanged
- keep `EnEsCompiledResources` and `EnEsCompiledTargetContext` shapes stable
- do not rename benchmark-facing fields while moving this seam

### 3. Compiled scoring and ranking seam

Current anchors inside `en_es.py`:

- `EnEsCompiledSignalProvider`
- `EnEsCompiledCandidateScoreTable`
- `EnEsCompiledRankingMechanism`
- `_EnEsCompiledScoreBatchProjection`
- `_EnEsCompiledScoreConfigMatrix`
- `_resolve_compiled_score_backend(...)`
- `_build_compiled_candidate_score_table_for_table(...)`
- `_build_compiled_candidate_score_tables_for_table(...)`
- `_materialize_compiled_candidate_score_table_batch(...)`
- `_resolve_vectorized_frequency_weight_matrix(...)`
- `_resolve_vectorized_pos_match_matrix(...)`
- `_vectorized_reverse_check_delta_matrix(...)`
- `_vectorized_reverse_check_strength_matrix(...)`
- `_compute_confidence_and_ranking_matrices_torch(...)`
- `_build_compiled_overlay_demotion_rows(...)`
- `_resolve_compiled_overlay_demotion_rows(...)`
- `_build_compiled_score_table_cache_key(...)`
- `_build_compiled_score_selected_row_signature(...)`

Current responsibilities:

- materialize cached confidence/ranking tables from compiled candidate rows
- apply gloss decay, POS match, semantic demotion, and reverse-check scoring
- preserve row ordering/signatures used by the benchmark sweep path
- optionally switch to the CUDA batch backend

Why this is the second extraction seam:

- it is the densest algorithmic block in the file
- it owns most of the function-count pressure
- it has a tight dependency graph that is easier to move intact than to nibble piecemeal

Recommended home:

- `core/lexishift_core/rulegen/pairs/en_es_compiled_scoring.py`

Guardrails:

- preserve cache-key inputs exactly
- preserve tuple ordering and row-sort behavior exactly
- preserve score-table field names and shapes because tests and benchmark scripts inspect them directly
- treat this as `V4` work even if the intent is behavior-preserving, because it sits directly on scoring/ranking semantics

### 4. Compiled filtering, selected-row, and benchmark projection seam

Current anchors inside `en_es.py`:

- `EnEsCompiledCandidateFilterTable`
- `EnEsCompiledSelectedRowTable`
- `EnEsCompiledBenchmarkEvaluationTables`
- `EnEsCompiledBenchmarkSweepTables`
- `EnEsCompiledDefinitionRowGroup`
- `build_en_es_compiled_candidate_filter_table(...)`
- `_build_compiled_candidate_filter_table_for_table(...)`
- `_compiled_non_empty_accepts(...)`
- `_compiled_gloss_shape_accepts(...)`
- `_compiled_length_accepts(...)`
- `_compiled_possessive_accepts(...)`
- `_compiled_stopword_accepts(...)`
- `_compiled_inflection_artifact_accepts(...)`
- `_build_compiled_benchmark_variant_candidate_table(...)`
- `_resolve_compiled_benchmark_candidate_table(...)`
- `prepare_en_es_compiled_benchmark_evaluation_tables(...)`
- `prepare_en_es_compiled_benchmark_sweep_tables(...)`
- `build_en_es_compiled_selected_row_table(...)`
- `_build_or_resolve_compiled_selected_row_table(...)`
- `_build_en_es_compiled_selected_row_table_from_target_context_rows(...)`
- `_limit_compiled_result_row_ids(...)`
- `_limit_compiled_definition_row_ids(...)`
- `_build_compiled_definition_sorted_row_ids_by_group(...)`
- `_build_compiled_definition_row_group(...)`
- `_apply_compiled_reverse_definition_hygiene(...)`
- `_flatten_compiled_definition_groups(...)`
- `_limit_compiled_rule_count_row_ids(...)`

Current responsibilities:

- normalize/filter compiled rows
- build benchmark-time variant tables
- select accepted rows per target
- apply definition/rule limits and reverse-definition hygiene
- expose the precomputed tables consumed by benchmark tooling

Why this is the third extraction seam:

- it depends on the compiled inventory and scoring seams
- it is still behavior-sensitive because filtering and top-row selection change visible outputs
- moving it after the inventory/scoring split keeps the dependency direction clean

Recommended home:

- `core/lexishift_core/rulegen/pairs/en_es_compiled_selection.py`

Guardrails:

- preserve filter order
- preserve definition-group bucketing and interleave behavior
- preserve selected-row signatures because benchmark caching depends on them
- keep this under `V4`; the backlog already treats `F3` and `F4` as full rulegen validation work

### 5. Pair orchestration and live-source seam

Current anchors inside `en_es.py`:

- `EnEsRulegenConfig`
- `build_en_es_pipeline(...)`
- `generate_en_es_results(...)`
- `generate_en_es_rules(...)`
- `FreedictCandidateSource`
- `_build_filters(...)`
- `_build_gloss_base_forms(...)`
- `_resolve_gloss_records(...)`
- `_coerce_gloss_records(...)`
- `_resolve_reverse_gloss_records(...)`
- `_records_to_gloss_mapping(...)`
- small pair-local filter primitives such as:
  - `_should_expand_english(...)`
  - `_resolve_spanish_target_surface(...)`
  - `_pluralize_spanish_noun(...)`
  - `EnEsGlossShapeFilter`
  - `EnEsStopwordFilter`
  - `ShadowedInterjectionFilter`

Current responsibilities:

- keep the runtime pair API stable
- choose live-vs-compiled generation paths
- load or coerce translation records
- wire filters, expanders, scorer, and ranking into `RuleGenerationPipeline`

Why this should move last:

- it is the real façade for the pair
- it depends on every other seam
- moving it early would create circular-import risk and widen the blast radius for no immediate health gain

Recommended home after `F2` and `F3`:

- keep `en_es.py` as the façade
- optionally move `FreedictCandidateSource` and record-loading helpers into a focused support module only during `F4`

Guardrails:

- preserve the `EnEsRulegenConfig`, `generate_en_es_results`, and `generate_en_es_rules` import path
- keep `build_en_es_pipeline(...)` callable from tests and tooling until the new internal layout has settled

## Physical Ordering Problem To Fix Carefully

The current file order is not the same as the conceptual architecture.

Examples:

- `build_en_es_compiled_resources(...)` appears early, but it depends on inventory/fact builders defined much later
- the benchmark-table and selected-row helpers sit far away from the score-table builders they depend on
- passive dataclasses, filters, score math, and façade entry points are mixed near the top of the file

Implication:

- each follow-on slice should move a whole seam, not isolated helper fragments
- compatibility wrappers in `en_es.py` are preferable to partial half-splits that introduce circular imports

## Recommended `F2` Through `F4` Sequence

### `F2`: extract compiled inventory/provenance support

Target:

- move the compiled inventory/provenance seam into `en_es_compiled_inventory.py`

Include in this move:

- compiled resource/context/fact/table dataclasses that are passive inventory models
- the builders that materialize them
- the metadata-shaping helpers tied directly to compiled-resource creation

Keep in `en_es.py` for now:

- public `build_en_es_compiled_resources(...)` as a thin wrapper or re-export
- `EnEsRulegenConfig`
- the façade generation entry points

Do not do in `F2`:

- scoring changes
- filter-order changes
- benchmark selection rewrites

### `F3`: extract compiled scoring plus compiled selection

Target:

- move the compiled scoring seam first
- then move the compiled filter/selection/benchmark seam once the scoring imports are stable

Preferred shape:

- `en_es_compiled_scoring.py`
- `en_es_compiled_selection.py`

Fallback if circular-import pressure appears:

- one temporary `en_es_compiled_runtime.py` module is acceptable
- but only if it still clearly separates:
  - score-table materialization
  - filter/selected-row logic

Do not do in `F3`:

- change cache semantics
- rename score/filter table fields
- move the public pair façade yet

### `F4`: reduce `en_es.py` to the façade

Target end state:

- `en_es.py` should mostly hold:
  - public config
  - public entry points
  - thin composition glue
  - compatibility re-exports needed by scripts/tests

Anything not tied to the façade should already live in the extracted support modules by the time `F4` lands.

## Explicit Risks To Keep Visible

1. `en_es_support.py` is already near the watchlist threshold.
   Do not solve `en_es.py` by merely moving the hotspot sideways.

2. Benchmark and test code import private helpers directly.
   Each extraction must either:
   - keep `en_es.py` re-exports, or
   - update the direct imports in the same slice.
   Do not mix both strategies inconsistently.

3. Compiled-row metadata is an implicit contract.
   Selection tables, benchmark scripts, and parity tests all depend on stable metadata keys and tuple ordering.

4. The compiled and live paths must stay behavior-aligned.
   `build_en_es_pipeline(...)`, `generate_en_es_results(...)`, compiled selected-row tables, and benchmark sweeps are cross-checking the same pair logic from different entry points.

## Bottom Line

`en_es.py` is not one indivisible blob.
It contains four real seams:

1. compiled inventory/provenance assembly,
2. compiled scoring/ranking,
3. compiled filtering/selection/benchmark projections,
4. pair façade plus live-source orchestration.

The safest cleanup path is:

1. move the inventory seam first,
2. move the scoring/selection seams next,
3. collapse `en_es.py` to façade/orchestration last,
4. keep compatibility exports in place until the benchmark and test surfaces are intentionally rewired.
