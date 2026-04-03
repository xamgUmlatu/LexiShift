# Reverse-Check Rollout Matrix

Status: active rollout matrix
Last updated: 2026-03-13

Purpose:
- Make reverse-check pair coverage explicit without reconstructing it from pair modules, helper plumbing, and benchmark artifacts.
- Separate `wired`, `benchmarked`, and `default-on` so rollout maturity is easy to recover.

## Status Vocabulary

- `unsupported`: pair has no reverse-check path or no rulegen surface.
- `wired`: pair code emits reverse metadata and ranking can consume it.
- `benchmarked`: committed benchmark evidence exists for the pair.
- `default-on`: pair defaults enable reverse-check in normal behavior.

## Pair Matrix

| Pair | Rulegen | Reverse Resources | Metadata Emitted | Ranking Hooked | Benchmarked | Default-On | Current State | Primary Evidence | Main Blocker |
|---|---|---|---|---|---|---|---|---|---|
| `en-es` | yes | yes | yes | yes | yes | no | `wired`, `benchmarked` | `core/lexishift_core/rulegen/pairs/en_es.py`; `docs/rulegen/reverse_check_en_es_case_review_2026-03-13.md`; `docs/rulegen/reverse_check_en_es_failure_traits_2026-03-13.md`; `docs/test_outputs/rulegen_benchmark_en_es_reverse_latest.md`; `docs/test_outputs/rulegen_benchmark_triage_en_es_reverse_latest.md`; `docs/test_outputs/rulegen_probe_en_es_reverse_far_hit_experiment_2026-03-13.json` | Rank-aware far-hit scoring plus top-3 hygiene now reduces the reverse-lane triage to one item (`cuadro`), but default rollout is still off and the remaining non-reverse failure class needs a different signal. |
| `es-en` | yes | yes | yes | yes | no committed pair artifact | no | `wired` | `core/lexishift_core/rulegen/pairs/es_en.py`; `core/tests/rulegen/test_rulegen_reverse_check_metadata.py` | No committed benchmark/gate/triage artifact showing pair-level win or safe default rollout. |
| `en-de` | yes | yes | yes | yes | no committed pair artifact | no | `wired` | `core/lexishift_core/rulegen/pairs/en_de.py`; `core/lexishift_core/rulegen/adapters.py`; `scripts/testing/rulegen_probe_words.py`; `core/tests/rulegen/test_rulegen_adapters.py` | First local Kaikki reverse experiment is now possible, but the tested `rev=on` setting did not beat `rev=off`, and no committed pair artifact establishes rollout maturity yet. |
| `en-ja` | yes (via `en_ja` mode) | no | no | no | no | no | `unsupported` | `core/lexishift_core/rulegen/pairs/en_ja.py`; `core/lexishift_core/helper/lp_capabilities.py` | Current JMdict-backed path has no reverse-check phase-1 design or plumbing. |
| `ja-ja` | no | n/a | n/a | n/a | no | no | `unsupported` | `core/lexishift_core/helper/lp_capabilities.py` | No rulegen mode. |
| `en-en` | no | n/a | n/a | n/a | no | no | `unsupported` | `core/lexishift_core/helper/lp_capabilities.py` | No rulegen mode. |
| `de-en` | yes | no | no | no | no | no | `unsupported` | `core/lexishift_core/rulegen/pairs/de_en.py`; `core/lexishift_core/helper/lp_capabilities.py` | Baseline rulegen mode exists now, but the pair has no reverse-path config or reverse metadata emission yet. |
| `es-es` | no | n/a | n/a | n/a | no | no | `unsupported` | `core/lexishift_core/helper/lp_capabilities.py` | No rulegen mode. |
| `de-de` | no | n/a | n/a | n/a | no | no | `unsupported` | `core/lexishift_core/helper/lp_capabilities.py` | No rulegen mode. |
| `en-zh` | no | n/a | n/a | n/a | no | no | `unsupported` | `core/lexishift_core/helper/lp_capabilities.py` | No rulegen mode. |

## Formulaic Rollout Pattern

For a new pair, reverse-check rollout is complete only when all of these are true:

1. Pair capability exposes a rulegen mode.
2. Helper resource resolution can find the reverse dictionary path.
3. Pair config accepts reverse path + reverse scoring config.
4. Pair candidate generation emits reverse metadata.
5. Ranking mechanism receives reverse scoring config.
6. Helper job / engine overrides surface the tuning knobs.
7. Unit tests cover metadata and ranking behavior.
8. Committed benchmark/gate/triage artifacts prove pair-level value.
9. Pair defaults enable the feature only after benchmark acceptance.

## Still Unimplemented

1. No first-class capability field such as `supports_reverse_check`; support is inferred indirectly from pair modules and helper resource resolution.
2. `core/lexishift_core/helper/lp_capabilities.py` still uses the misleading field name `requires_freedict_de_en_for_rulegen` for non-DE FreeDict-backed pairs.
3. No committed `es-en` benchmark/gate/triage artifacts establish rollout maturity.
4. No pair defaults currently enable reverse-check in `core/lexishift_core/rulegen/tuning.py`.
5. Phase 1 remains scoring-only:
   - no hard blocking
   - no sense-qualifier integration
   - no multi-source agreement bonus
   - no context-aware disambiguation

## Immediate Priority

1. `en-es`
   - best evidence exists
   - hard-case breadth is now explicit
   - named reverse lane now gives a stable benchmark/gate/triage surface for the workstream
   - remaining blocker is no longer generic reverse scoring; it is the single non-reverse failure class (`cuadro`)
2. `es-en`
   - code is wired, but artifact evidence is thin
3. `en-de` / `en-ja`
   - only worth touching after `en-es` proves the scoring model is actually strong enough to justify further pair rollout
