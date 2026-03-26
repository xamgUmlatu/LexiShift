# Rulegen PC Sweep Handoff

Status: Active handoff
Role: Runbook / operational
Purpose: Make the current `en-es` Kaikki rulegen benchmark state portable and replayable on a higher-end PC for broader experiment sweeps.
Last updated: 2026-03-26
Last verified: 2026-03-26
Verification:
- `scripts/testing/rulegen_benchmark.py`
- `scripts/testing/rulegen_benchmark_bundle.py`
- `docs/test_outputs/rulegen_benchmark_en_es_latest.json`
- `docs/test_outputs/rulegen_quality_gate_latest.json`
- `docs/test_outputs/rulegen_benchmark_triage_latest.json`

## Scope

This runbook is for the current Kaikki-backed `en-es` rulegen workstream only.

Current intended use:

- export a frozen benchmark bundle from the source machine
- transfer it to the PC
- replay the exact canonical run on the PC
- run larger sweep methodologies against the frozen bundle inputs
- compare results without depending on the live local SRS store

For the broader ordering of the whole workstream, see:

- `docs/developer/rulegen_workstream_execution_order.md`

## Current Known-Good State

Canonical source commit before this handoff doc:

- `ddd601aa40a8153fff60d8efd60f15fefddf6923`

Canonical benchmark methodology:

- preset: `en_es_canonical_matrix`
- source preset file: `docs/test_inputs/rulegen_benchmark_presets.json`

Current canonical `en-es` benchmark result:

- `Top1`: `91.23%`
- `Top3`: `98.25%`
- `ForbidTop1`: `0.00%`
- `ForbidAny`: `3.51%`
- `AvgRules`: `2.98`
- objective: `129.474`

Current best config label:

- `md=3 mr=none thr=0.000 sd=1.00 var=off pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`

Current triage targets:

- `derecho`
- `cuadro`
- `cuenta`
- `red`
- `sacar`

Important interpretation:

- `cuadro` is still the only clear hard algorithmic miss in the canonical lane.
- `derecho`, `cuenta`, `red`, and `sacar` are closer to review / preference / phrase-policy questions.
- reverse-check is part of the current best config.
- exact-hit ambiguity penalty is implemented but still off in the current best config.
- Kaikki live demotion is implemented but still off in the current best config.

## What Is Frozen Now

The current portability work means the benchmark can now be replayed from frozen inputs.

What is frozen in the bundle:

- benchmark dataset JSON
- copied source benchmark JSON
- exact resolved dictionary resources used by the run
- SHA-256 checksums for copied resources
- per-pair frozen `word_package` snapshot
- preset metadata used by the source benchmark
- source commit metadata

What is no longer required for replay:

- the source machine's live SRS store
- the source machine's helper data root

Current remaining ergonomic gap:

- bundle transfer is directory-based, not single-file archive-based

## Source-Machine Export

Recommended export command:

```bash
python3 scripts/testing/rulegen_benchmark_bundle.py export \
  --benchmark-json docs/test_outputs/rulegen_benchmark_en_es_latest.json \
  --output-dir /tmp/lexishift_rulegen_bundle_en_es_2026-03-26
```

Optional archive step if directory transfer is annoying:

```bash
tar -C /tmp -czf /tmp/lexishift_rulegen_bundle_en_es_2026-03-26.tar.gz \
  lexishift_rulegen_bundle_en_es_2026-03-26
```

Bundle contents should include:

- `bundle_manifest.json`
- `inputs/rulegen_benchmark_cases.json`
- `inputs/word_package_snapshots.json`
- `inputs/rulegen_benchmark_presets.json`
- `resources/en-es/wiktionary-es-en.sqlite`
- `resources/en-es/wiktionary-en-es.sqlite`
- `source/rulegen_benchmark_en_es_latest.json`

## PC Setup

Recommended PC-side assumptions:

- same repo checkout, ideally at the same commit or a later descendant that preserves the same benchmark/bundle code paths
- `python3` available
- `npm` available

Recommended first step after checkout:

```bash
git rev-parse HEAD
```

If the code on the PC has diverged materially from the source machine, regenerate the bundle from the newer code instead of trusting old replay equivalence.

## Replay On The PC

First validate the bundle:

```bash
python3 scripts/testing/rulegen_benchmark_bundle.py validate \
  --bundle-dir /path/to/lexishift_rulegen_bundle_en_es_2026-03-26
```

Then replay the exact canonical benchmark from frozen inputs:

```bash
python3 scripts/testing/rulegen_benchmark_bundle.py run \
  --bundle-dir /path/to/lexishift_rulegen_bundle_en_es_2026-03-26 \
  --json-output /path/to/pc_outputs/replay.json \
  --markdown-output /path/to/pc_outputs/replay.md \
  --html-output /path/to/pc_outputs/replay.html
```

Expected replay result:

- `Top1`: `91.23%`
- `Top3`: `98.25%`
- objective: `129.474`

If the replay does not match those numbers exactly, stop and inspect:

- wrong bundle directory
- stale or modified resources
- different code path than expected
- accidental rerun against live local resources instead of the bundle

Important note:

- because the benchmark dataset has now been expanded from `48` to `57` `en-es` cases, refresh/export the portable bundle again before the broad PC sweep so replay expectations match the current canonical suite

## Gate And Triage On The PC

After replay, regenerate the standard downstream artifacts from the replay JSON:

```bash
python3 scripts/testing/rulegen_quality_gate.py \
  --benchmark-json /path/to/pc_outputs/replay.json \
  --policy-json docs/test_inputs/rulegen_quality_policy.json \
  --baseline-json docs/test_outputs/baselines/rulegen_quality_baseline.json \
  --pos-probe-json docs/test_outputs/phase6_pos_inventory/phase6_pos_probe_2026-02-23_final.json \
  --pos-inventory-json docs/test_outputs/phase6_pos_inventory/phase6_pos_inventory_2026-02-23_final.json

python3 scripts/testing/rulegen_benchmark_triage.py \
  --benchmark-json /path/to/pc_outputs/replay.json \
  --json-out /path/to/pc_outputs/replay_triage.json \
  --markdown-out /path/to/pc_outputs/replay_triage.md
```

The quality gate is expected to remain red at current quality:

- quality floor breach on `en-es`
- delta budget breach on `en-es`

That is not a portability problem. It is the current known model-quality state.

## Running Broader Sweeps On The PC

The bundle runner is currently optimized for exact replay of the source methodology.

For broader PC-side sweeps, use `rulegen_benchmark.py` directly with the bundle inputs:

```bash
python3 scripts/testing/rulegen_benchmark.py \
  --preset-file docs/test_inputs/rulegen_benchmark_presets.json \
  --preset en_es_policy_hypothesis_matrix \
  --dataset /path/to/lexishift_rulegen_bundle_en_es_2026-03-26/inputs/rulegen_benchmark_cases.json \
  --word-package-snapshot-json /path/to/lexishift_rulegen_bundle_en_es_2026-03-26/inputs/word_package_snapshots.json \
  --translation-dict-en-es /path/to/lexishift_rulegen_bundle_en_es_2026-03-26/resources/en-es/wiktionary-es-en.sqlite \
  --translation-dict-es-en /path/to/lexishift_rulegen_bundle_en_es_2026-03-26/resources/en-es/wiktionary-en-es.sqlite \
  --json-output /path/to/pc_outputs/hypothesis_matrix.json \
  --markdown-output /path/to/pc_outputs/hypothesis_matrix.md \
  --html-output /path/to/pc_outputs/hypothesis_matrix.html
```

Recommended methodology rule:

- do not overwrite canonical `*_latest` artifacts on the PC during exploratory sweeps
- write dated or experiment-specific output files
- only refresh canonical artifacts after deciding a result is worth bringing back

Recommended preset discipline:

- keep `en_es_canonical_matrix` stable
- keep `en_es_policy_hypothesis_matrix` small and interpretable
- if you need a truly broad PC-only sweep, create a separate preset file rather than mutating the canonical one first

## What I Would Focus On Next

If the goal is raw sweep throughput, the PC is ready now.

If the goal is best signal-per-compute, I would prioritize:

1. expanding the benchmark dataset before trusting fine-grained parameter tuning
2. adding more lexical-polysemy cases around:
   - `cuadro`
   - `cuenta`
   - `red`
3. adding more short verb-phrase cases around:
   - `sacar`
4. keeping `derecho` separate as a likely preference/label question rather than a pure algorithm problem

Current model observations that matter for PC experiments:

- reverse on is currently part of the best run
- Kaikki demotion infrastructure exists, but current best is still `kdem=off`
- exact-hit ambiguity infrastructure exists, but current best is still `xamb=off`
- this suggests the next broad sweep should not assume those newer signals are already proven winners

## Things I Would Avoid During The PC Sweep

- do not update `docs/test_outputs/baselines/rulegen_quality_baseline.json`
- do not relax `docs/test_inputs/rulegen_quality_policy.json`
- do not overwrite canonical source-machine `*_latest` artifacts with exploratory PC outputs
- do not treat review-case preference changes as automatic quality wins without checking the triage details

## Return Path From The PC

After the broad sweep, the useful thing to bring back is not the whole output directory first.

Bring back:

- winning preset definition or preset diff
- winning benchmark JSON
- matching gate and triage artifacts
- a short summary of:
  - what changed
  - what metrics moved
  - which targets improved
  - which targets regressed

If the PC sweep finds a strong winner, refresh canonical source-machine artifacts only after that result is understood and intentional.
