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
- Named reverse lane benchmark: `docs/test_outputs/rulegen_benchmark_en_es_reverse_latest.json`
- Named reverse lane triage: `docs/test_outputs/rulegen_benchmark_triage_en_es_reverse_latest.json`
- Named reverse lane summaries:
  - `docs/test_outputs/rulegen_benchmark_en_es_reverse_summary_latest.md`
  - `docs/test_outputs/rulegen_quality_gate_en_es_reverse_summary_latest.md`
  - `docs/test_outputs/rulegen_benchmark_triage_en_es_reverse_summary_latest.md`
- Run matrix: `docs/test_outputs/rulegen_reverse_en_es_run_matrix_latest.md`
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

## Second Expansion

- A second, more aggressive `en-es` expansion pass added 14 more cases.
- Review artifact: `docs/rulegen/reverse_check_en_es_aggressive_expansion_2026-03-13.md`
- The `en-es` benchmark slice now totals 38 cases before the next tuning pass.

## Notes

1. The new benchmark cases were added to `docs/test_inputs/rulegen_benchmark_cases/en_es.json`.
2. `madre` already existed and remains the anchor failure case.
3. `fondo` and `medio` are intentionally advisory in spirit, but the current benchmark schema only supports the existing `smoke` / `hard` tiering. Their labels therefore remain broad and permissive.
4. The strongest immediate product questions remain the Red cases:
   - can reverse-check stop obviously bad top-1 outputs?
   - can it do that without damaging the Green anchors?
5. The canonical benchmark artifact and the reverse-specific experiment now diverge in an important way:
   - the canonical latest benchmark still defaults to `rev=off` because `scripts/testing/rulegen_benchmark.py` only sweeps `--reverse-check-enabled-values false` unless explicitly overridden
   - the reverse-specific experiment is therefore the relevant artifact for this workstream
6. The named reverse lane now captures the current best practical state for this workstream:
   - best `en-es` run has `rev=on`
   - on the widened 38-case slice, top-1 improves to `97.37%`
   - `forbidden_any_rate` improves to `2.63%`
   - the remaining triage set drops to one item: `cuadro`
7. There are two relevant reverse-lane operating points:
   - objective winner: `mr=1`, which yields `top1=97.37%`, `top3=97.37%`, and leaves only `cuadro`
   - near-winner: `mr=none`, which keeps `top3=100.00%` while still leaving only `cuadro`
8. The practical reverse-check story for `en-es` is now much better:
   - `madre`, `planta`, `derecho`, `cargo`, `masa`, `caso`, and `vista` all move to acceptable top-1 outputs in the reverse lane
   - top-3 hygiene also cleans the forbidden-any tail for the newly added red cases
   - `cuadro` remains the only visible non-reverse failure class
