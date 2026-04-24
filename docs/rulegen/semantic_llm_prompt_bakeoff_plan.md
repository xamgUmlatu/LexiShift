# Semantic LLM Prompt Bakeoff Plan

Status: active plan
Role: Planning / operational
Purpose: define a cheap, rigorous prompt-selection workflow for semantic LLM cue and shadow generation before LexiShift spends a larger semantic-generation budget
Last updated: 2026-04-24
Last verified: 2026-04-24 repo-doc review against the runtime-readiness, LLM queueing, source-intake, and semantic-evidence normalization seams
Source-of-truth: planning doc only; current implemented truth still lives in the runtime-readiness artifacts, the LLM intake/evidence schemas, and the offline normalization code
Related docs:
- `docs/rulegen/semantic_llm_generation_queueing_plan.md`
- `docs/rulegen/semantic_shadow_source_intake_plan.md`
- `docs/rulegen/semantic_routing_runtime_readiness.md`
- `docs/rulegen/semantic_routing_generalization_evaluation_plan.md`
- `docs/rulegen/semantic_routing_data_update_lifecycle.md`
- `docs/test_inputs/semantic_routing/semantic_llm_intake_batch.schema.json`
- `docs/test_inputs/semantic_routing/semantic_evidence_batch.schema.json`
- `docs/test_inputs/semantic_routing/semantic_family_inventory.schema.json`

Routing note:

- use this document when the question is how to choose, compare, and confirm prompt wording cheaply
- do not use it to decide which families deserve LLM spend at all; that still belongs to `semantic_llm_generation_queueing_plan.md`
- do not use it to redefine the current runtime or publication contracts

## Why This Exists

LexiShift now has enough semantic-routing evidence to route future LLM work by failure class, but not enough prompt evidence to justify spending a full budget tranche blindly.

The current runtime story is:

- the active fixed-shadow runtime residue is still mostly weak-active-support, not a broad missing-shadow crisis
- the live harmful-replace seam is still phrase-leak-sensitive (`play:005`)
- the highest-value first data spend is therefore still cue-heavy rather than broad shadow generation

That is enough to choose a prompt matrix shape.
It is not enough to say one exact prompt is already known to be best.

This workstream exists to bridge that gap cheaply.

## Goal

Demonstrate that one prompt family per generation job is good enough to justify a larger batch spend, without paying full-tranche cost just to compare wording.

The desired output is not:

- one universal prompt for all semantic generation
- or a bespoke handcrafted prompt per lemma

The desired output is:

- a small set of stable prompt slots
- each tied to one job and one failure bucket
- with cheap screening, target-model confirmation, and downstream acceptance gates

## Non-Goals

This workstream should not try to solve:

- family queueing from scratch
- phrase/parsing failures with better prompt prose
- runtime rollout policy
- final budget allocation for all future waves
- general model selection for the whole semantic-routing stack

If a family still looks like `needs_phrase_parsing_fix` or `needs_algorithm_fix`, it should usually be excluded from prompt spend rather than absorbed into it.

## Current Starting Point

The repo already has the right scaffolding for a measured bakeoff:

- current LLM row types are:
  - `shadow_candidate`
  - `bridge_candidate`
  - `anchor_cue`
- current queue buckets already separate:
  - `needs_shadow_data`
  - `needs_cue_data`
  - `needs_algorithm_fix`
  - `needs_phrase_parsing_fix`
- LLM intake and normalized evidence already preserve:
  - `model_id`
  - `prompt_version`
  - `prompt_slot`
  - `temperature`
  - `cost_metadata`

That means prompt work can be versioned and compared cleanly instead of becoming ad hoc batch prose.

Current output-contract posture:

- the model should emit only the fields it is actually deciding:
  - required `evidence_text`
  - optional `confidence`
- the runner should synthesize the richer stored intake row from the frozen request context:
  - row ids
  - targets
  - trigger
  - prompt slot
  - sense metadata
- this keeps the model output smaller, cheaper, and less fragile without weakening stored provenance

Current frozen pre-prompt artifacts:

- `docs/test_inputs/semantic_routing/semantic_family_inventory_en_es_v10.json`
- `docs/test_inputs/semantic_routing/semantic_prompt_bakeoff_queue_en_es.json`
- `docs/test_inputs/semantic_routing/semantic_prompt_slot_manifest.json`
- `docs/test_inputs/semantic_routing/semantic_prompt_spec_en_es_v10.json`
- `docs/test_outputs/semantic_llm_queue_review_en_es_latest.md`
- `docs/test_outputs/semantic_llm_prompt_smoke_latest.md`

Current `v10` read:

- first-tranche prompt work should still be cue-heavy rather than shadow-heavy
- the accepted active-sense overlay is the clean bounded runtime comparator
- `play` remains the phrase-risk negative control
- `report` widened the held-out cue-like residue
- the zero-noise soft ladder no longer adds real lift on the frozen slice

## Core Design Rules

### 1. Prompt by job, not by word

Prompt families should align to:

- row type
- likely failure bucket
- and family archetype

They should not be keyed to one isolated lemma unless a tiny rescue list later justifies that.

### 2. Keep the number of prompt slots small

The first tranche should use a small matrix:

- enough to compare meaningful prompt strategies
- not enough to create an unmanageable interaction grid

Default posture:

- `3` cue slots
- `1` shadow slot
- optional bridge slot only if the queue later proves it is needed

### 3. Keep prompt wording fixed within a measured batch

Within one comparison stage, keep fixed:

- prompt text
- model
- temperature
- output schema
- family slice

Do not vary multiple prompt ideas and model choices inside the same batch and then pretend the result is attributable.

### 4. Cheap models may screen, but target models must confirm

Prompt bakeoff should happen in stages:

- cheap proxy model for format, clarity, and obvious loser elimination
- intended target model for finalist confirmation
- larger target-model tranche only after a winner is accepted

Proxy models may eliminate bad prompts.
They should not alone decide the final winner.

### 5. Judge prompts by downstream movement, not prose aesthetics

A prompt wins only if it improves the right failure bucket at acceptable cost.

The key question is not:

- does the output sound smart?

The key question is:

- does it reduce the target error class without widening the wrong one?

### 6. Keep phrase-risk families as negative controls

The bakeoff must include phrase-sensitive or lexicalized-expression controls so cue prompts are not accidentally rewarded for leaking into phrase/parsing territory.

Current default negative control family:

- `play`

### 7. Preserve batch provenance and reuse

Every batch should remain traceable by:

- `batch_id`
- `model_id`
- `prompt_version`
- `prompt_slot`
- family slice
- and cost metadata

That is how later budget waves stay additive rather than repetitive.

## First Prompt Matrix

The current `v10` runtime evidence supports a cue-heavy first matrix.

### Slot 1. `cue_contrastive_general_v1`

Use for:

- ordinary weak-active-support families with a plausible current competition set

Expected row type:

- `anchor_cue`

Prompt intent:

- ask for short, contrastive evidence text that separates one active target from one named shadow target
- prefer concrete discriminators over dictionary-style paraphrase

Primary target archetypes:

- same-POS or ordinary competition families such as `plant` and `drink`

Kill signals:

- generic gloss restatements
- long prose with weak contrast
- cues that would apply equally well to active and shadow

### Slot 2. `cue_cross_pos_frame_v1`

Use for:

- cross-POS weak-active-support families where syntactic frame or nearby lexical context matters

Expected row type:

- `anchor_cue`

Prompt intent:

- ask for cues tied to grammatical environment, local collocates, and frame-sensitive meaning signals

Primary target archetypes:

- `check`
- `order`
- `trip`
- `report`

Kill signals:

- cues that describe world knowledge but ignore frame
- cues that collapse noun and verb readings back together

### Slot 3. `cue_minimal_rescue_v1`

Use for:

- families where the goal is a small high-precision rescue cue, not broad semantic prose

Expected row type:

- `anchor_cue`

Prompt intent:

- ask for minimal, high-signal cue text intended to help a bounded rescue path instead of replacing the main evidence surface

Primary target archetypes:

- hard false-abstain rows that already look nearly recoverable

Kill signals:

- verbose cue bundles
- broad semantic summaries that look likely to widen harmful replace

### Slot 4. `shadow_expand_core_v1`

Use for:

- families the queue classifies as `needs_shadow_data`

Expected row type:

- `shadow_candidate`

Prompt intent:

- ask for one or two plausible learner-relevant competing targets with compact evidence and strong sense hints

Primary target archetypes:

- coverage-thin families only

Kill signals:

- synonym churn
- vague bridge-like speculation
- candidate floods that are unlikely to survive normalization or promotion

### Deferred Slot. `bridge_expand_core_v1`

Default posture:

- defer

Reason:

- current runtime residue is more cue-heavy than bridge-heavy
- this slot should not enter the first cheap bakeoff unless the queue produces a clear bridge-specific family slice

## Model Policy

### Stage A. Proxy screening

Allowed model:

- a cheaper model than the intended full-generation model

Purpose:

- eliminate prompts that fail schema discipline or obviously generate low-value rows

Questions to answer:

- does the model understand the task
- does the output normalize cleanly
- does the prompt produce concise, contrastive rows rather than generic prose

This stage is allowed to reject prompts.
It is not allowed to crown the final winner.

### Stage B. Target-model finalist confirmation

Required model:

- the same model intended for the first real generation tranche

Purpose:

- confirm that the surviving prompt slots still perform on the actual model that will be used for paid generation

Questions to answer:

- does prompt ranking survive model transfer
- does the target model still obey the output contract
- do downstream acceptance signals remain favorable

### Stage C. Full tranche

Required model:

- same as Stage B, unless a deliberate new model experiment is being run and tracked as a new tranche

Purpose:

- real budget spend for accepted slots only

## Evaluation Slice

The first bakeoff should use a small stratified family slice.

### Tune-side weak-active-support

- `plant`
- `drink`

### Held-out cross-POS weak-active-support

- `check`
- `order`
- `trip`
- `report`

### Negative controls

- `play`
- `watch`

### Reserve-only calibration slice

- `park`

Principles:

- do not choose only easy families
- do not choose only phrase families
- include at least one held-out family from the active frontier

## Acceptance Gates

### Gate 1. Format and schema

Accept only if:

- rows parse as valid LLM intake batches
- required fields are present
- `prompt_version` and `prompt_slot` are populated
- normalization does not collapse a large share of rows as malformed

Reject if:

- format drift is common
- prompt ambiguity creates unstable row shapes

### Gate 2. Quick human review

Accept only if sampled rows are mostly keepable.

Review questions:

- is the row actually discriminative
- is it too generic
- does it look phrase/parsing-confused
- would a reviewer keep it for offline evidence at all

This review should be sampled, not exhaustive.

### Gate 3. Downstream cue evaluation

For cue slots, compare against the current fixed-shadow runtime slice.

Success means:

- weak-active-support residue shrinks on the target families
- harmful replace does not widen beyond the slot budget
- phrase-risk negative controls do not regress

The intended acceptance shape is:

- clear movement on the intended family archetype
- no obvious contamination of the `play` phrase-risk seam

### Gate 4. Downstream shadow evaluation

For shadow slots, compare against the current shadow-mining evaluation surfaces.

Success means:

- new candidates survive normalization and promotion
- at least one real coverage-related failure class improves
- harmful allow does not simply become false-abstain junk everywhere

### Gate 5. Target-model confirmation

A prompt slot is only accepted for real budget spend if:

- it passes the earlier gates on the target model
- and still looks better than the competing slot when evaluated downstream

## Budget Posture

The first budget wave should reserve most money for the accepted final tranche, not for prompt comparison.

Default planning split:

- `10-15%` proxy screening
- `15-25%` target-model finalist confirmation
- `60-75%` accepted tranche execution

The exact numbers may move with model pricing.
The important rule is:

- do not spend most of the budget just proving prompt wording

## Planned Deliverables

The first implementation pass for this workstream should add:

### Planning and input artifacts

- `docs/test_inputs/semantic_routing/semantic_prompt_bakeoff_queue_en_es.json`
- `docs/test_inputs/semantic_routing/semantic_prompt_slot_manifest.json`
- `docs/test_inputs/semantic_routing/semantic_family_inventory_en_es_v10.json`
- `docs/test_inputs/semantic_routing/semantic_prompt_replay_fixture_en_es_v10.json`
- optional prompt text templates or prompt-spec file keyed by `prompt_version` and `prompt_slot`

### Scripts

- `scripts/testing/semantic_llm_prompt_preflight_en_es.py`
- `scripts/testing/semantic_llm_prompt_cost_estimate_en_es.py`
- `scripts/testing/semantic_llm_prompt_smoke.py`
- `scripts/testing/semantic_llm_prompt_bakeoff_en_es.py`
- `scripts/testing/semantic_llm_prompt_reporting.py`

### Output artifacts

- `docs/test_outputs/semantic_llm_prompt_preflight_latest.json`
- `docs/test_outputs/semantic_llm_prompt_preflight_latest.md`
- `docs/test_outputs/semantic_llm_prompt_cost_estimate_latest.json`
- `docs/test_outputs/semantic_llm_prompt_cost_estimate_latest.md`
- `docs/test_outputs/semantic_llm_prompt_replay_latest.json`
- `docs/test_outputs/semantic_llm_prompt_replay_latest.md`
- `docs/test_outputs/semantic_llm_prompt_bakeoff_latest.json`
- `docs/test_outputs/semantic_llm_prompt_bakeoff_latest.md`
- `docs/test_outputs/semantic_llm_prompt_confirmation_latest.json`
- `docs/test_outputs/semantic_llm_prompt_confirmation_latest.md`
- `docs/test_outputs/semantic_llm_queue_review_en_es_latest.md`
- immutable batch-specific raw response, intake, and normalized evidence artifacts under:
  - `docs/test_outputs/experiments/semantic_llm_prompt_batches/`

## Phase Plan

### Phase 1. Freeze the queue slice

Objective:

- define the tiny family slice and prompt slots before any paid comparison run

Deliverables:

- bakeoff queue artifact
- slot manifest
- family inventory artifact
- target-model choice for Stage B and C

Acceptance:

- each chosen family has a declared archetype
- each prompt slot has one job

Current status:

- landed on `v10`
- chosen default model pair:
  - Stage A proxy: `gpt-5.4-mini`
  - Stage B/C target: `gpt-5.4`
- active slots:
  - `cue_contrastive_general_v1`
  - `cue_cross_pos_frame_v1`
- reserve slot:
  - `cue_minimal_rescue_v1`
- deferred slot:
  - `shadow_expand_core_v1`
- current next prerequisite before prompt spend:
  - completed: tiny `example_sentence_bank` feasibility pilot over the frozen queue
  - current read:
    - the installed packs expose `0 / 6` target families with example-bearing queued rows
    - all `6 / 6` target families do expose reverse-side auxiliary sense text
- current next choice before prompt spend:
    - completed: one last reverse-aux-text control on that same frozen queue slice
  - current read from that control:
    - `reverse_aux_plus_all_evidence` improves the queue-slice point read from `77.5%` accuracy / `50.0%` replace recall / `1` harmful / `8` false abstains
    - to `82.5%` / `62.5%` / `1` / `6`
    - recovered rows: `plant:002`, `drink:002`, `order:002`
    - persistent residue: `play:005`, `play:002`, `check:002`, `trip:002`, `report:001`, `report:002`

### Phase 2. Proxy smoke pass

Objective:

- cheaply remove obviously weak prompt variants

Deliverables:

- raw cheap-model batches
- schema/normalization summary
- sampled review notes

Acceptance:

- surviving prompts are structurally reliable
- obviously generic or malformed prompts are dropped

Current status:

- prompt wording and stage defaults are now frozen in:
  - `docs/test_inputs/semantic_routing/semantic_prompt_spec_en_es_v10.json`
- the frozen prompt contract is now the simplified `semantic_prompt_bakeoff_v2` shape:
  - the model emits only `evidence_text`
  - optional `confidence` may still be emitted
  - the runner synthesizes all fixed ids and metadata into the intake batch
- the local prompt preview bundle is now rendered in:
  - `docs/test_outputs/semantic_llm_prompt_smoke_latest.md`
- the new no-spend preflight surface is now rendered in:
  - `docs/test_outputs/semantic_llm_prompt_preflight_latest.md`
- the new no-spend cost-estimate surface is now rendered in:
  - `docs/test_outputs/semantic_llm_prompt_cost_estimate_latest.md`
- the live execution runner is now implemented in:
  - `scripts/testing/semantic_llm_prompt_bakeoff_en_es.py`
- the live runner now refuses API spend unless `--execute-live` is passed explicitly
- live execution is now also fail-closed on three explicit guards:
  - exact `--require-selected-request-count`
  - explicit `--input-rate-per-1m` and `--output-rate-per-1m`
  - explicit `--max-estimated-cost-ceiling-usd`
- the live runner now preserves:
  - an append-only per-request journal keyed by operator-supplied `--run-id`
  - immutable raw response bundles
  - immutable raw LLM intake batches
  - immutable normalized evidence batches
  - plus the stable `latest` summary artifact
- live interruption handling is now explicit:
  - re-running the same live slice without `--resume` is rejected if the journal already exists
  - `--resume` reuses already completed request outcomes from the journal instead of re-spending them
  - if a request was started but no outcome was recorded, resume refuses and asks for manual inspection rather than risking duplicate spend
- the same runner now also supports a strict no-spend replay mode backed by:
  - `docs/test_inputs/semantic_routing/semantic_prompt_replay_fixture_en_es_v10.json`
  - `docs/test_outputs/semantic_llm_prompt_replay_latest.md`
- current replay read:
  - `3` selected requests
  - `1` accepted row
  - `1` forced API error
  - `1` strict malformed-row rejection
  - accepted replay data survives into immutable raw, intake, and normalized artifacts with replay provenance attached
- first live proxy read on the older verbose contract showed:
  - all `6 / 6` requests accepted and normalized
  - but the cross-POS slot still drifted toward gloss-like noun summaries, especially on `order`
  - and the model was being asked to echo ids and metadata that the runner already knew
- second live proxy read on the simplified `semantic_prompt_bakeoff_v2` contract now shows:
  - all `6 / 6` requests accepted and normalized again
  - proxy token usage dropped materially:
    - input tokens `3414 -> 2545`
    - output tokens `1137 -> 222`
  - the cross-POS slot moved in the intended direction:
    - `check`, `order`, `trip`, and `report` now emphasize determiner/preposition/document framing instead of broad noun-gloss summaries
  - the simplified contract therefore looks strictly better as the proxy default:
    - cheaper
    - less fragile
    - and more aligned with the intended cue job
- current next step is therefore:
  - target confirmation on the same simplified contract
- current preview read:
  - `2` active slots
  - `6` rendered target-family prompt requests
  - `play` and `watch` remain held out as negative controls, not prompt targets
- current local limitation:
  - the new preflight now resolves the environment split more precisely:
  - current Codex command shell is still not ready for direct spend
  - sourced shell + repo venv are ready enough for execution
  - the preflight command template is now spend-capped by default rather than showing an uncapped live command
  - the same preflight surface now points at a `--run-id`-based live path so paid runs are resumable rather than timestamp-bound
  - the new cost-estimate artifact now keeps the token-volume review explicit before any live run:
    - current proxy slice estimate is `2814` input tokens and `540` expected output tokens across the `6` frozen requests
    - pricing stays intentionally external to the repo unless current rates are supplied explicitly at runtime
  - the sourced-shell + repo-venv live path is now proven on real proxy execution, not just preflight

### Phase 3. Target-model finalist pass

Objective:

- confirm that prompt ranking survives on the real model

Deliverables:

- finalist target-model batches
- normalized evidence rows with stable provenance

Acceptance:

- at least one slot per active job survives target-model confirmation

Current status:

- `semantic_prompt_bakeoff_v2` has now also passed a real live `gpt-5.4` target run:
  - all `6 / 6` requests accepted and normalized
  - target token usage stayed close to proxy:
    - input tokens `2545`
    - output tokens `231`
  - the target cues preserved the same qualitative improvement seen in proxy:
    - cross-POS rows remained frame-sensitive rather than reverting to broad noun-gloss summaries
    - `order`, `trip`, `check`, and `report` all stayed on determiner/quantity/document framing
- current read:
  - the simplified `v2` contract now looks validated on both:
    - proxy `gpt-5.4-mini`
    - target `gpt-5.4`
  - the remaining missing gate is no longer prompt-quality confirmation
  - it is downstream effect on the fixed-shadow runtime slice

### Phase 4. Downstream bakeoff

Objective:

- judge finalists by actual failure-bucket movement

Deliverables:

- cue-slot downstream comparison
- shadow-slot downstream comparison if a shadow slot is active

Acceptance:

- winner slots have measurable value on the intended bucket
- phrase-risk and harmful-replace controls stay acceptable

### Phase 5. Tranche decision

Objective:

- approve, defer, or reject each slot for larger budget spend

Deliverables:

- accepted slot list
- rejected slot list
- cost and evidence summary

Acceptance:

- the tranche decision is based on downstream results, not prompt aesthetics alone

## Stop Rules

Stop and re-route if:

- a family still looks primarily `needs_phrase_parsing_fix`
- a prompt only wins on the proxy model but not the target model
- a prompt improves cue recall only by reopening the phrase-leak seam
- a shadow prompt floods the candidate pool without surviving promotion
- the bakeoff starts drifting toward bespoke prompts per lemma

## Practical Current Takeaway

LexiShift is ready to choose the first prompt matrix rigorously enough.

LexiShift is not yet ready to claim that one exact prompt wording is already known to be best.

The correct next move is:

1. keep the `v10` queue slice fixed
2. treat the `example_sentence_bank` pilot as a feasibility result, not as a live cue source on current packs
3. keep `reverse_aux_plus_all_evidence` as the last cheap non-LLM control on that same slice
4. keep `semantic_prompt_bakeoff_v1` and the rendered smoke bundle fixed as the current wording baseline
5. run the actual cheap proxy batch on a configured API surface
6. confirm finalists on the target model
7. spend the real batch budget only on accepted slots
