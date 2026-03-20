# Reverse-Check EN-ES Failure Traits (2026-03-13)

Purpose:
- classify the current `en-es` hard cases after widening the benchmark slice
- separate "tunable with current reverse-check model" from "needs a different signal"
- give a quicker feel for how product-critical these cases are
- keep the raw reverse-rank positions explicit for manual review

Method:
- canonical benchmark/triage state from `docs/test_outputs/rulegen_benchmark_en_es_latest.json`
- reverse-specific experiment state from:
  - `docs/test_outputs/rulegen_benchmark_en_es_reverse_far_hit_experiment_2026-03-13.json`
  - `docs/test_outputs/rulegen_benchmark_triage_en_es_reverse_far_hit_experiment_2026-03-13.md`
- reverse metadata from `docs/test_outputs/rulegen_probe_en_es_reverse_on_latest.json`
- rough Spanish commonness from `wordfreq` Zipf scores (`es`)
- tuned experiment check from:
  - `docs/test_outputs/rulegen_benchmark_en_es_reverse_far_hit_experiment_2026-03-13.json`
  - `docs/test_outputs/rulegen_benchmark_triage_en_es_reverse_far_hit_experiment_2026-03-13.md`
  - `docs/test_outputs/rulegen_probe_en_es_reverse_far_hit_experiment_2026-03-13.json`

Aggressive expansion note:
- a second pass added 14 more `en-es` cases; see `docs/rulegen/reverse_check_en_es_aggressive_expansion_2026-03-13.md`
- the named reverse lane on the widened 38-case slice now reaches:
  - top-1: `97.37%`
  - top-3: `97.37%` (objective winner) / `100.00%` (`mr=none` comparison row)
  - forbidden-any: `2.63%`
  - remaining triage count: `1` (`cuadro`)
- the tables below still focus on the original anchor red cases that shaped the reverse-check scoring changes

Interpretation of Zipf:
- `~6`: extremely common everyday word
- `~5`: common core vocabulary
- `~4`: still fairly common, but less dominant

## Red Cases

| Target | Zipf (es) | Forward gloss count | Current top candidates (`rev=on`) | Reverse rank snapshot | Failure class | What it suggests |
|---|---:|---:|---|---|---|---|
| `madre` | `5.45` | `3` | `bed`, `mother`, `watercourse` | `bed`: miss (`13` reverse entries), `mother`: `0 / 1`, `watercourse`: miss (`2` reverse entries) | reverse-miss vs exact-hit | Product-critical common word. Bad early glosses are reverse misses; expected sense is an exact reverse hit. Current penalties are too weak relative to gloss-order priority. |
| `planta` | `4.81` | `2` | `sole`, `plant` | `sole`: `3 / 8`, `plant`: `0 / 10` | competing reverse hits | Both bad and good senses have reverse support. This is not a simple hit/miss problem. The raw reverse position matters: `plant` is the first reverse sense, while `sole` only appears later. |
| `derecho` | `5.44` | `6` | `claim`, `presumption`, `right` | `claim`: miss (`20` reverse entries), `presumption`: miss (`0`), `right`: `5 / 23` | reverse-miss vs far-hit | Product-critical common word. Expected sense gets into top-3 once reverse-check is active, but remains below two misses. This is tunable, but the raw reverse position is not near-top. |
| `cuadro` | `4.52` | `3` | `bed`, `picture` | `bed`: miss (`13` reverse entries), `picture`: miss (`4`) | no reverse separation | Both bad and good senses miss in the reverse dictionary. Reverse-check alone cannot separate them. This case likely needs another signal or should be treated as a non-reverse-check lexical-quality case. |

## Green Anchors

| Target | Zipf (es) | Forward gloss count | Current top candidates (`rev=on`) | Reverse rank snapshot | Why it matters |
|---|---:|---:|---|---|---|
| `banco` | `5.04` | `2` | `bank`, `bench` | `bank`: `3 / 24`, `bench`: `0 / 8` | Common polysemy anchor. Useful for checking that stronger penalties do not overcorrect a case where multiple senses remain acceptable. It also shows why raw rank position matters: `bank` is later than `bench`, but still fairly early within a much larger reverse list. |
| `capital` | `5.25` | `3` | `capital`, `metropolis` | `capital`: `0 / 4`, `metropolis`: miss (`3`) | Stable exact-hit case. Good regression guard for obvious one-to-one or dominant-sense behavior. |
| `luz` | `5.25` | `1` | `light` | `light`: `12 / 23` | Simple one-candidate anchor. Helps detect collateral damage from broader ranking changes, especially when the reverse hit exists but is not near the top. |

## Practical Read

1. The failing cases are not fringe vocabulary.
   - All four red targets are roughly Zipf `4.5+`.
   - `madre` and `derecho` are especially common.

2. The red set is not one phenomenon.
   - `madre`: exact reverse rescue blocked by gloss-order dominance.
   - `derecho`: far reverse support helps, but not enough.
   - `planta`: both senses have reverse support, so hit/miss is too coarse.
   - `cuadro`: reverse dictionary gives no useful separation at all.

3. This means reverse-check work should split into two tracks.
   - Track A: improve how reverse evidence competes with gloss order (`madre`, `derecho`).
   - Track B: keep a record of cases reverse-check cannot realistically solve alone (`planta`, `cuadro`).

## Promising Structural Experiment

Config tested:
- `reverse_match_bonus = 0.6`
- `reverse_near_bonus = 0.1`
- `reverse_near_rank_max = 2`
- `reverse_far_hit_penalty = 0.05`
- `reverse_miss_penalty = 0.8`
- `include_variants = false`

Observed benchmark result:
- top-1: `95.83%`
- top-3: `100.00%`
- forbidden top-1: `4.17%`
- failing triage items: `3`

What it fixed:
- `madre` top-1 becomes `mother`
- `planta` top-1 becomes `plant`
- `derecho` top-1 becomes `right`

What still remains:
- `cuadro` still fails because reverse evidence does not separate `bed` from `picture`
- forbidden-any remains high because `madre` and `derecho` still keep forbidden candidates in the visible top-3

## Immediate Conclusion

1. The raw reverse-rank position matters, and the current slice shows why.
   - `plant` is `0 / 10` while `sole` is `3 / 8`
   - `right` is only `5 / 23`
   - `bank` is later than `bench`, but still early within a much larger reverse list (`3 / 24` vs `0 / 8`)

2. The current reverse model now handles the reverse-solvable cases well enough.
   - Named reverse lane result:
     - top-1: `97.37%`
     - objective-best forbidden-any: `2.63%`
     - remaining triage count: `1`
   - Reverse-solvable cases now clean up as expected:
     - `madre` -> `mother`
     - `planta` -> `plant`
     - `derecho` -> `right`
     - `cargo` -> `function`
     - `masa` -> `dough`
     - `caso` -> `case`
     - `vista` -> `sight`

3. The remaining blocker is now concentrated.
   - `cuadro` is the only remaining hard failure in the named reverse lane.
   - That is strong evidence that the next product step should not be “more reverse tuning everywhere”; it should be a different signal for the non-reverse class.
