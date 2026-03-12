# Reverse-Check Scoring (Phase 1) Specification

Status: implemented (configurable, conservative defaults)
Last updated: 2026-03-13

## Goal

Improve rulegen precision for polysemic terms by scoring candidate mappings with reverse-dictionary consistency:

1. Forward candidate exists: `target -> source`.
2. Reverse evidence check: `source -> target`.
3. Boost candidates with strong reverse support; demote one-way/sense-misaligned candidates.

Primary immediate target:

1. `en-es`
2. `es-en`

## Problem Statement

Current ranking is mostly based on dictionary gloss order + existing scoring signals.
This allows cases where a low-congruity forward gloss survives if listed early.

Reverse-check scoring is designed to reduce these failures without adding sentence-level context.

## Scope (Phase 1)

In scope:

1. Add reverse-evidence metadata to pair candidate generation for FreeDict-backed pairs.
2. Add ranking bonus/penalty hooks using reverse evidence.
3. Keep behavior graceful when reverse dictionary is unavailable.
4. Keep all logic pair-aware and configurable for future LP expansion.

Out of scope (Phase 1):

1. Context-aware runtime disambiguation.
2. Probability/entropy features from aligned corpora.
3. Hard blocking of candidates (this phase is scoring-only, not strict filtering).

## Data Dependencies

For `en-es`:

1. Forward dictionary: `spa-eng` (target ES -> source EN)
2. Reverse dictionary: `eng-spa` (source EN -> target ES)

For `es-en`:

1. Forward dictionary: `eng-spa` (target EN -> source ES)
2. Reverse dictionary: `spa-eng` (source ES -> target EN)

Fallback behavior:

1. If reverse dictionary is missing, reverse-check is treated as unsupported for that candidate.
2. Unsupported reverse-check must not throw or hard-fail rulegen.

## Touchpoints

Pair candidate metadata generation:

1. `core/lexishift_core/rulegen/pairs/en_es.py`
2. `core/lexishift_core/rulegen/pairs/es_en.py`

Dictionary loading:

1. `core/lexishift_core/resources/dict_loaders.py`

Ranking logic:

1. `core/lexishift_core/rulegen/ranking.py`
2. `core/lexishift_core/rulegen/generation.py` (already consumes ranking mechanism)

Adapter/config plumbing:

1. `core/lexishift_core/rulegen/adapters.py`
2. `core/lexishift_core/helper/rulegen.py`
3. `core/lexishift_core/helper/use_cases/rulegen_job.py`
4. `core/lexishift_core/rulegen/tuning.py`
5. `core/lexishift_core/helper/lp_capabilities.py` (reverse-path resolution helper)
6. `core/lexishift_core/helper/pair_resources.py`

## Metadata Contract (Candidate-Level)

Each candidate may carry:

1. `reverse_check_supported` (`bool`)
2. `reverse_check_hit` (`bool`)
3. `reverse_check_rank` (`int | null`)
4. `reverse_check_total` (`int | null`)
5. `reverse_check_source_dict` (`str`)
6. `reverse_check_target_norm` (`str`) - normalized target used for matching
7. `reverse_check_source_norm` (`str`) - normalized source used for lookup

Normalization rule (Phase 1):

1. Use the same gloss sanitization policy used for forward candidates (`sanitize_dictionary_gloss`, lowercased).
2. Match on exact normalized form only (no morphology/context expansion in this phase).

## Scoring Model (Phase 1)

Base score remains current dictionary-order score with semantic demotion applied.

Reverse delta is then applied:

1. Supported + exact hit: add `match_bonus`.
2. Supported + near hit (`rank <= near_rank_max`): add `near_bonus`.
3. Supported + farther hit: apply a far-hit penalty scaled by the reverse-rank position when `reverse_check_total` is available.
4. Supported + miss: apply penalty.
5. Unsupported: no delta.

Recommended initial constants:

1. `reverse_match_bonus = +0.20` (rank 0)
2. `reverse_near_bonus = +0.10` (rank <= `reverse_near_rank_max`)
3. `reverse_near_rank_max = 2`
4. `reverse_far_hit_penalty = 0.00` (optional; when enabled, acts as the maximum far-hit penalty; actual penalty scales with `rank / (total - 1)` when reverse totals are known)
5. `reverse_miss_penalty = -0.20`

Score clamp:

1. Clamp final ranking score to `[0.0, 1.0]`.

## Configuration Surface

Add pair-tunable knobs (default disabled globally):

1. `reverse_check_enabled` (`bool`)
2. `reverse_match_bonus` (`float`)
3. `reverse_near_bonus` (`float`)
4. `reverse_near_rank_max` (`int`)
5. `reverse_far_hit_penalty` (`float`)
6. `reverse_miss_penalty` (`float`)

Rollout defaults (current):

1. Global default: disabled.
2. Pair-level tuning and runtime overrides are fully wired (`rulegen/tuning.py`, helper job config, benchmark sweep).
3. Enable for benchmark experiments on `en-es` and `es-en`.
4. Promote to production pair defaults only after benchmark/triage acceptance.

## Implementation Steps

1. Add reverse path resolution:
   - Introduce resolver utility for reverse FreeDict path per pair.
   - Thread optional reverse path through helper/adapters/pair configs.
2. Load reverse records:
   - Build reverse index by normalized source headword -> normalized translations list.
3. Attach reverse metadata:
   - In pair candidate source generation, compute reverse evidence per candidate and attach metadata fields.
4. Ranking integration:
   - Extend `DictionaryEntryOrderRankingMechanism` with reverse-check scoring hooks.
   - Keep mechanism deterministic and metadata-driven.
5. Tuning exposure:
   - Add overrides and pair defaults in `rulegen/tuning.py`.
   - Ensure diagnostics payload includes effective reverse-check config.
6. Guardrails:
   - Feature remains non-fatal when reverse path/data is unavailable.

## Testing Plan

Unit tests:

1. `core/tests/rulegen/test_rulegen_ranking.py`
   - bonus/penalty/no-support behavior
   - clamping and rank-threshold behavior
2. `core/tests/rulegen/test_rulegen_adapters.py`
   - reverse path plumbed into pair configs
3. New/extended pair generation tests:
   - reverse metadata present and correct for `en-es` and `es-en`
   - graceful behavior when reverse dictionary missing

Quality loop (required for scoring changes):

1. Benchmark sweep (touched pairs):
   - `python3 scripts/testing/rulegen_benchmark.py --pairs en-es ...`
2. Quality gate:
   - `python3 scripts/testing/rulegen_quality_gate.py ...`
3. Triage extraction:
   - `python3 scripts/testing/rulegen_benchmark_triage.py ...`

## Acceptance Criteria (Phase 1)

1. Reverse metadata is emitted for candidates when reverse resources are available.
2. Ranking behavior changes only when reverse-check is enabled.
3. No runtime crashes when reverse resources are missing.
4. Unit tests pass.
5. Benchmark/quality gate evidence shows net precision gain (or at minimum no regression) for enabled pairs.

## Current Known Unresolved Cases

1. `en-es:madre` may still fail with FreeDict-first senses (`bed`, `watercourse`) when reverse-check is disabled.
2. This remains a tracked benchmark/triage item and is intentionally unresolved in default production tuning until pair-level reverse-check rollout is validated.

## Risks and Mitigations

Risk:

1. Dictionary asymmetry and sparse entries can over-penalize valid translations.

Mitigation:

1. Start with moderate penalties.
2. Keep feature toggleable and pair-tuned.
3. Validate via benchmark + manual triage before production defaults.

Risk:

1. More configuration complexity.

Mitigation:

1. Centralize controls in `rulegen/tuning.py`.
2. Keep default behavior unchanged until explicit pair enablement.

## Future Phase Hooks

After Phase 1:

1. Integrate sense qualifiers into reverse-check confidence beyond raw reverse rank/percentile.
2. Combine reverse-check with multi-source agreement bonus.
3. Optional runtime abstain synergy for low-margin, high-risk candidates.
