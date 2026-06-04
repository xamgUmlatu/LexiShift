# Rulegen Test Pipeline

Status: active architecture guide
Role: Mixed
Purpose: Describe the end-to-end rulegen test pipeline as broad stages, canonical artifacts, and skip conditions, separate from the lower-level optimization details.
Last updated: 2026-03-28
Last verified: 2026-03-28
Source-of-truth: this doc defines the broad workflow contract; executable truth still lives in the benchmark, render, gate, and triage scripts plus `AGENTS.md`.

## Why This Exists

The rulegen workstream now has two different documentation needs:

- a detailed optimization/implementation plan
- a simple end-to-end view of what the pipeline does, what each stage emits, and when a stage can be skipped

This document is the second one.

It is intentionally black-boxed at the stage level.

## End Goal

The benchmark/test stack is being built to support two related outcomes:

1. find strong global maxima across the current sweep surface for a pair/resource methodology
2. later analyze which named settings or profiles work best for runtime-computable trait groups of targets, so rulegen can choose better settings for a specific word at runtime

The first goal is active now.
The second goal is planned later and must remain downstream of the same benchmark substrate, not a separate ad hoc workflow.

## Canonical Full Audit

The default full audit remains:

1. benchmark compute
2. render human-facing artifacts
3. quality gate
4. triage extraction

Canonical commands remain the ones listed in `AGENTS.md`.

## Black-Box Stages

### 1. Resolve Inputs

Inputs:

- pair list
- benchmark dataset
- preset or explicit sweep arguments
- resource overrides

Outputs:

- resolved run manifest
- resolved resource selection
- effective benchmark methodology

Skip conditions:

- never skip when the user intends to run a fresh benchmark

### 2. Load Resources

Inputs:

- resolved manifest

Outputs:

- normalized translation-pack resources
- resource checksums
- reusable preload metadata

Notes:

- database/storage specifics belong here, behind adapters/loaders
- later stages must consume normalized pair resources rather than assuming one database or one pack type

Skip conditions:

- can reuse cached metadata when the exact source packs are unchanged
- cannot skip when inputs or resources changed materially

### 3. Compile Benchmark IR

Inputs:

- normalized resources
- benchmark dataset
- pair-local snapshots such as `word_package`

Outputs:

- compiled pair context / benchmark IR
- candidate, case, and label tables or equivalent structures

Notes:

- this is the stage that turns rich loader/runtime structures into reusable sweep data
- this stage is the bridge to vectorized CPU and later optional GPU backends

Skip conditions:

- can be reused only when dataset, resources, compile version, and pair-local snapshots are unchanged

### 4. Sweep

Inputs:

- compiled benchmark IR
- config set or preset

Outputs:

- benchmark JSON
- best-run identity
- per-run summaries
- optional case-level details

Notes:

- this is the stage that searches for the current global maximum within the active preset surface
- current work is moving this stage toward dense numeric config/candidate evaluation

Skip conditions:

- can be skipped only when the exact benchmark JSON for the same inputs already exists and the user only wants downstream stages

### 5. Render

Inputs:

- benchmark JSON

Outputs:

- benchmark markdown
- benchmark HTML

Notes:

- render is human-facing, not a benchmark-semantic stage
- render is still useful by default because it is cheap and gives an immediately inspectable artifact

Skip conditions:

- okay to skip for tight perf or machine-only loops
- keep by default for normal quality review and handoff

### 6. Quality Gate

Inputs:

- benchmark JSON
- policy
- baseline
- POS artifacts

Outputs:

- gate JSON
- pass/fail findings

Notes:

- gate is the policy decision layer, not the search layer
- gate should consume the benchmark artifact and must not silently recompute benchmark behavior

Skip conditions:

- can be skipped for pure perf work or when only human rendering is needed
- should not be skipped for quality-significant rulegen changes

### 7. Triage

Inputs:

- benchmark JSON

Outputs:

- triage JSON
- triage markdown

Notes:

- triage converts benchmark failures/reviews into actionable case work
- triage is distinct from the policy gate

Skip conditions:

- can be skipped for pure perf work
- keep when any failure/review analysis is needed

### 8. Later Trait/Profile Analysis

Inputs:

- benchmark JSON
- per-case trait vectors
- named profile identity

Outputs:

- reports showing which profile families win for which runtime-computable trait regions

Notes:

- this stage is planned later
- it must reuse the same benchmark substrate rather than inventing a separate tuning workflow
- see `docs/rulegen/trait_conditioned_rulegen_profiles.md`

## Canonical Artifacts

Current default `en-es` latest artifacts:

- benchmark JSON: `docs/test_outputs/rulegen_benchmark_en_es_latest.json`
- benchmark markdown: `docs/test_outputs/rulegen_benchmark_en_es_latest.md`
- benchmark HTML: `docs/test_outputs/rulegen_benchmark_en_es_latest.html`
- gate JSON: `docs/test_outputs/rulegen_quality_gate_latest.json`
- triage JSON: `docs/test_outputs/rulegen_benchmark_triage_latest.json`
- triage markdown: `docs/test_outputs/rulegen_benchmark_triage_latest.md`

These artifacts are intended to be reusable across later stages.

## Default Usage Rules

### Use The Full Audit When

- rulegen scoring changes
- candidate filtering changes
- POS normalization changes
- pair tuning changes
- resource-selection methodology changes

### Use Compute-Only When

- measuring performance
- validating benchmark equivalence during optimization work
- rendering/gate/triage can reuse the same benchmark JSON later

### Reuse Existing Benchmark JSON When

- only human render is needed
- only gate/triage conclusions are needed
- no benchmark-semantic inputs changed

## Design Rules

1. Keep the benchmark methodology explicit.
2. Keep pack/database details below the normalized resource boundary.
3. Keep benchmark compute separate from downstream artifact materialization.
4. Keep the global benchmark baseline even when later trait-conditioned profile analysis exists.
5. Do not optimize one stage by secretly recomputing another.
6. Prefer one canonical workflow contract even if multiple wrapper scripts exist.

## Relationship To Other Docs

- optimization details: `docs/developer/rulegen_benchmark_optimization_plan.md`
- current state ledger: `docs/developer/feature_state_matrix.md`
- current rulegen work ordering: `docs/developer/rulegen_workstream_execution_order.md`
- later trait-conditioned routing plan: `docs/rulegen/trait_conditioned_rulegen_profiles.md`
