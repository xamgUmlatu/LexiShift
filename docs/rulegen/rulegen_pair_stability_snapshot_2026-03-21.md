# Rulegen Pair Stability Snapshot (2026-03-21)

Status: dated advisory snapshot
Role: Planning / WIP
Last updated: 2026-03-21
Source-of-truth: dated multi-pair benchmark, quality-gate, and triage artifacts only; this snapshot does not change required gate policy.

Purpose:
- keep one dated view of rulegen quality across active language pairs
- catch shared regressions while `en-es` remains the only active tuning lane
- separate "needs active tuning now" from "needs advisory monitoring only"

Artifacts:
- Benchmark summary: `docs/test_outputs/experiments/rulegen_pair_stability_snapshot_20260321/rulegen_benchmark_all_pairs_summary_2026-03-21.md`
- Quality gate summary: `docs/test_outputs/experiments/rulegen_pair_stability_snapshot_20260321/rulegen_quality_gate_all_pairs_2026-03-21.md`
- Triage summary: `docs/test_outputs/experiments/rulegen_pair_stability_snapshot_20260321/rulegen_benchmark_triage_all_pairs_summary_2026-03-21.md`
- Benchmark JSON: `docs/test_outputs/experiments/rulegen_pair_stability_snapshot_20260321/rulegen_benchmark_all_pairs_2026-03-21.json`
- Quality gate JSON: `docs/test_outputs/experiments/rulegen_pair_stability_snapshot_20260321/rulegen_quality_gate_all_pairs_2026-03-21.json`
- Triage JSON: `docs/test_outputs/experiments/rulegen_pair_stability_snapshot_20260321/rulegen_benchmark_triage_all_pairs_2026-03-21.json`

Policy note:
- `en-es` remains the only required hard-gated rulegen tuning lane.
- `en-ja`, `en-de`, and `es-en` are still advisory surfaces until they become active development lanes again.
- The purpose of this snapshot is visibility and regression detection, not policy expansion.

## Pair Readout

| Pair | Current read | Best advisory result | Triage shape | Immediate interpretation |
| --- | --- | --- | --- | --- |
| `en-es` | active red lane | top1 `78.95%`, top3 `78.95%`, forbidden-any `13.16%` | `8` FAIL | canonical lane remains unhealthy; continue active tuning here |
| `en-ja` | advisory green | top1 `94.12%`, top3 `100.00%`, forbidden-any `0.00%` | `1` REVIEW | currently stable enough to monitor rather than tune |
| `en-de` | advisory yellow | top1 `75.00%`, top3 `100.00%`, forbidden-any `0.00%` | `4` REVIEW | not policy-ready, but drift looks reviewable rather than catastrophic |
| `es-en` | advisory red | top1 `75.00%`, top3 `75.00%`, forbidden-any `0.00%` | `4` FAIL | materially lagging, but not the current active surgery lane |

## Notable Cases

### `en-es`

Canonical advisory lane remains red:
- `madre -> bed`
- `planta -> sole`
- `derecho -> claim`
- `cuadro -> bed`
- `cargo -> accusal`
- `masa -> lump`

Read:
- this confirms the known picture from the `2026-03-13` reverse-check work
- the canonical `rev=off` lane is still not healthy
- keep `en-es` as the only active tuning lane after this snapshot

### `en-ja`

Single advisory review item:
- `en-ja:世界` top1=`society`

Read:
- `en-ja` currently clears its floor and does not show broad instability
- this pair is a good regression sentinel while shared rulegen code changes continue

### `en-de`

Current review items:
- `Haus -> establishment`
- `Schule -> pod`
- `Weg -> alley`
- `Zeit -> spell`

Read:
- `en-de` is not healthy enough for hard policy promotion
- the failure shape is mostly "unexpected top1" rather than forbidden/noisy-tail explosion
- keep monitoring it when shared ranking/scoring layers change

### `es-en`

Current fail items:
- `house -> casalicio`
- `love -> cero`
- `money -> pasta`
- `time -> mes`

Read:
- `es-en` is the clearest non-`en-es` cavity in the advisory snapshot
- do not expand policy around it yet, but treat it as a standing regression-risk surface

## Cross-Pair Read

1. Current instability is not evenly distributed.
   - `en-ja` looks serviceable.
   - `en-de` is behind on top1 precision but not obviously overrun by forbidden candidates.
   - `es-en` is materially behind on current benchmark expectations.
   - `en-es` remains the active quality problem.

2. The current sweep knobs are low-sensitivity across all pairs.
   - Every pair emitted saturation warnings in the all-pairs gate.
   - Treat this as a measurement note, not a reason to widen tuning scope immediately.

3. This snapshot supports a narrow operating rule.
   - keep active tuning focused on `en-es`
   - use `en-ja`, `en-de`, and `es-en` as advisory regression monitors when shared rulegen code changes

## Immediate Next Step

Return to `en-es` tuning with this standing constraint:
- when changing shared rulegen layers, re-run the dated all-pairs advisory snapshot or an equivalent multi-pair benchmark pass before closing the change
- when changing `en-es`-specific ranking logic, keep the reverse-check evidence and the all-pairs advisory snapshot separate so the canonical lane remains easy to compare against the reverse lane
