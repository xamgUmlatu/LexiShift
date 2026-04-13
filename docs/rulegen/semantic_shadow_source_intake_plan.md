# Semantic Shadow Source Intake Plan

Status: active plan
Role: Planning / operational
Purpose: prepare broad data-source experimentation for semantic-shadow mining without turning runtime veto into a source-specific heuristic pile
Last updated: 2026-04-11
Last verified: 2026-04-11 repo-doc review against the current semantic-shadow miner, support scorer, experiment harness, and runtime-readiness plan
Source-of-truth: planning doc only; executable truth still lives in the current semantic-shadow modules and experiment artifacts
Related inputs:
- `docs/test_inputs/semantic_shadow_source_registry.json`
- `docs/rulegen/semantic_routing_data_update_lifecycle.md`
- `docs/rulegen/semantic_shadow_testing_architecture.md`
- `docs/rulegen/semantic_routing_runtime_readiness.md`

## Why this exists

The current veto frontier is no longer blocked by basic plumbing.

The remaining hard problems are:

- coverage: can the miner surface the right competing senses at all,
- discrimination: can it keep real blockers while dropping harmless near-neighbors,
- and provenance: can we later boil a broad research stack down to a small runtime-safe contract.

That means the next phase should be source-heavy, but only in the offline research layer.

The intended operating model is:

- ingest broadly,
- normalize aggressively,
- ablate ruthlessly,
- publish narrowly.

## Core design rules

### 1. Broad ingest, narrow runtime

Research can use many noisy or partial sources.
Runtime should eventually consume only a distilled blocker set plus compact provenance.

Do not let the runtime policy become a direct union of every source-specific rule.

### 2. Separate coverage from discrimination

Not all sources solve the same problem.

- Coverage sources help surface missing candidates or missing seed triggers.
- Discrimination sources help separate true competing senses from synonyms, paraphrases, and phrase leakage.
- Cue sources help build better downstream runtime evidence once a blocker is already known.
- Silver sources may accelerate discovery, but they must remain explicitly tagged and non-authoritative.

### 3. Keep provenance explicit

Every new source family must stay visible in artifacts and in ablations.

If a source helps, we should be able to answer:

- which cases it fixed,
- whether it helped coverage or discrimination,
- what new noise it introduced,
- and whether the gain survives once the source is removed but the derived feature remains.

### 4. Normalize into one evidence model

New sources should not introduce bespoke downstream logic by default.

Each source should map into a common offline evidence shape with fields such as:

- `source_id`
- `source_family`
- `role`
- `relation_type`
- `pair`
- `trigger`
- `active_target`
- `candidate_target`
- `sense_locator`
- `candidate_pos`
- `is_multiword`
- `evidence_text`
- `example_count`
- `confidence`
- `path_length`
- `runtime_publishable`
- `provenance`

The exact final implementation can evolve, but the discipline should not.

### 5. Branch the churn, not the stable harness

The current veto branch should stay focused on:

- schemas
- evaluation harnesses
- diagnostics
- stable miner improvements that survive measurement

Broad source-ingestion work should move to a dedicated experiment branch once external source families begin landing.

## Source classes

Use these classes deliberately.

### A. Structured coverage sources

Goal:
- surface blocker candidates that current lexical mining misses

Examples:
- Wiktionary sense and translation inventories
- WordNet or Open Multilingual WordNet style sense graphs
- bilingual dictionary exports with explicit per-sense structure
- aligned phrase or translation tables

Primary success signal:
- fewer `seed_missing` and `candidate_missing` harmful-allow rows

### B. Discrimination sources

Goal:
- separate true competing senses from harmless near-neighbors

Examples:
- definitions and gloss text
- example sentence banks
- argument-structure or selectional-preference signals
- contextual or sentence-embedding comparisons over example usage

Primary success signal:
- fewer `promotion_miss` rows without a parallel rise in `false_abstain`

### C. Cue-generation sources

Goal:
- build better runtime-facing evidence for an already known blocker

Examples:
- source-derived anchor extraction
- source-derived example bundles
- later, reviewed or generated cue bundles

Primary success signal:
- better future runtime separation once the blocker set is fixed

### D. Silver or synthetic sources

Goal:
- cheaply propose candidates or cues that can later be filtered by stronger evidence

Examples:
- LLM-generated shadow proposals
- LLM-generated anchor/cue drafts
- heuristic paraphrase generation

Primary success signal:
- improved recall after downstream filtering

Guardrail:
- silver data must remain tagged as silver and must not silently become a gold assumption

## Repo operating model

### Source registry

The approval and planning queue lives in:

- `docs/test_inputs/semantic_shadow_source_registry.json`

That file is intentionally machine-readable so future scripts can:

- build approval queues
- render source readouts
- or validate that experiment rows only depend on approved source families

### Code placement

When new source families are implemented, prefer this split:

- source-specific normalization and loading under `core/lexishift_core/rulegen/`
- experiment orchestration under `scripts/testing/`
- documentation and approval state under `docs/rulegen/` and `docs/test_inputs/`

Do not bury new source-family assumptions inside the runtime publication layer.

### Experiment discipline

Every source family should be tested in four stages:

1. intake-only
2. intake plus normalization
3. intake plus one simple gating policy
4. ablation against the current best lexical baseline

The key question is not "does this source seem smart".
The key question is "which failure bucket moved, and at what precision cost".

## Immediate approval queue

The next likely source families worth considering are:

1. `wiktionary_sense_inventory_dump`
   - likely value: structured coverage and sense-link expansion
   - main risk: noisy sense alignment and normalization burden

2. `open_multilingual_wordnet`
   - likely value: coarse sense-graph coverage and cross-lemma competition hints
   - main risk: sense granularity mismatch with learner-facing dictionary senses

3. `aligned_phrase_table`
   - likely value: coverage for phrase-sensitive competitors and MWE spillover
   - main risk: high noise without strong filtering

4. `example_sentence_bank`
   - likely value: stronger discrimination and future runtime cue quality
   - main risk: uneven coverage and heavier preprocessing cost

5. `llm_shadow_proposals`
   - likely value: cheap candidate recall for hard lexical misses
   - main risk: silent hallucination or benchmark-shaped overfitting unless strictly quarantined

6. `llm_anchor_cues`
   - likely value: richer runtime evidence once blockers are known
   - main risk: good prose that is semantically weak or unstable

These should not all be added at once.
The first step is to approve a small batch with one coverage-heavy source and one discrimination-heavy source.

## Recommended next move after approval

Once a source family is approved:

1. create a dedicated experiment branch for source-heavy ingestion
2. add one adapter and one normalized evidence lane
3. expose that lane in the semantic-shadow experiment harness
4. run gold-proxy, veto-proxy, and row-compare ablations against the lexical control
5. keep only the derived evidence fields or source families that survive measurement

That sequence is intentionally conservative.
It keeps the current veto workstream understandable while still moving quickly on data discovery.
