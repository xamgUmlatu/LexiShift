# Reverse-Check EN-ES Case Review (2026-03-13)

Purpose:
- record the first reverse-check-focused `en-es` benchmark expansion slice
- keep the proposed Green / Gray / Red intent explicit for manual review
- tie each new case to observed current output, not just intuition

Artifacts:
- Benchmark: `docs/test_outputs/rulegen_benchmark_en_es_latest.json`
- Triage: `docs/test_outputs/rulegen_benchmark_triage_latest.json`
- Probe (`rev=off`): `docs/test_outputs/rulegen_probe_en_es_reverse_off_latest.json`
- Probe (`rev=on`): `docs/test_outputs/rulegen_probe_en_es_reverse_on_latest.json`
- Reverse-specific experiment benchmark: `docs/test_outputs/rulegen_benchmark_en_es_reverse_far_hit_experiment_2026-03-13.json`
- Reverse-specific experiment triage: `docs/test_outputs/rulegen_benchmark_triage_en_es_reverse_far_hit_experiment_2026-03-13.json`
- Reverse-specific experiment probe: `docs/test_outputs/rulegen_probe_en_es_reverse_far_hit_experiment_2026-03-13.json`

## Proposed Slice

| Bucket | Target | Current `rev=off` top outputs | Current `rev=on` top outputs | Proposed benchmark intent |
|---|---|---|---|---|
| Red | `madre` | `bed`, `watercourse`, `mother` | `bed`, `mother`, `watercourse` | keep as anchor failure; rare senses must not outrank `mother` / `mom` |
| Red | `planta` | `sole`, `plant` | `sole`, `plant` | accept `plant` / `floor`; block `sole` as top-1 |
| Red | `derecho` | `claim`, `presumption`, `pretence` | `claim`, `presumption`, `right` | accept `right` / `law`; reject low-value legal gloss drift |
| Red | `cuadro` | `bed`, `picture` | `bed`, `picture` | accept `picture` / `painting` / `chart` / `table`; reject `bed` |
| Gray | `fondo` | `background` | `background` | allow `background` / `bottom` / `fund` without hard-forcing one sense |
| Gray | `medio` | `half`, `agent`, `tool` | `half`, `average`, `mean` | advisory ambiguity case; watch ranking movement without forcing a single output |
| Green | `banco` | `bank`, `bench` | `bank`, `bench` | stable polysemy anchor; both common noun senses acceptable |
| Green | `capital` | `capital`, `metropolis` | `capital`, `metropolis` | stable anchor; keep city-related readings from regressing |
| Green | `luz` | `light` | `light` | one-to-one anchor for collateral regression checks |

## Notes

1. The new benchmark cases were added to `docs/test_inputs/rulegen_benchmark_cases.json`.
2. `madre` already existed and remains the anchor failure case.
3. `fondo` and `medio` are intentionally advisory in spirit, but the current benchmark schema only supports the existing `smoke` / `hard` tiering. Their labels therefore remain broad and permissive.
4. The strongest immediate product questions remain the Red cases:
   - can reverse-check stop obviously bad top-1 outputs?
   - can it do that without damaging the Green anchors?
5. The canonical benchmark artifact and the reverse-specific experiment now diverge in an important way:
   - the canonical latest benchmark still defaults to `rev=off` because `scripts/testing/rulegen_benchmark.py` only sweeps `--reverse-check-enabled-values false` unless explicitly overridden
   - the reverse-specific experiment is therefore the relevant artifact for this workstream
6. Current reverse-specific experiment evidence says rank-aware reverse scoring is useful, but still partial:
   - best `en-es` experiment run has `rev=on`
   - top-1 improves to `95.83%`
   - triage drops from `4` failing items to `3`
   - `madre`, `planta`, and `derecho` all move to acceptable top-1 outputs
   - but `madre` / `derecho` still retain forbidden candidates in top-3, and `cuadro` still fails outright
