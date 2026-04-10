# Semantic Routing Runtime Readiness

Status: planning slice
Role: Planning / WIP
Last updated: 2026-04-10
Last verified: 2026-04-10 repo-doc/runtime-contract review plus rule-payload provenance inspection, first `en-es` shadow inventory artifact, first triage pass over promotion quality, named promotion-policy comparison, and active-trigger matching refinement for bundled forward glosses
Purpose: define the implementation boundary for a future semantic-routing admission layer so work stays focused on the missing end-to-end pieces rather than early optimization
Source-of-truth: planning doc only; runtime truth still lives in code, `docs/developer/feature_state_matrix.md`, and future implementation evidence
Verification:
- `README.md`
- `docs/getting-started/index.md`
- `docs/architecture/extension_system_map.md`
- `docs/srs/srs_roadmap.md`
- `docs/rulegen/rule_generation_technical.md`
- `docs/rulegen/semantic_routing_data_contract.md`
- `docs/rulegen/semantic_routing_publication_contract.md`
- `core/lexishift_core/rulegen/generation.py`
- `core/lexishift_core/persistence/storage.py`
- `core/tests/rulegen/test_rulegen_generation.py`
- `core/tests/rulegen/test_rulegen_en_es_kaikki_provenance.py`

## Purpose

This document exists to answer one narrow product question:

- what must be true before LexiShift can safely use semantic routing to decide whether a browser replacement should apply in real reading?

The intended end-to-end experience is:

1. the user reads a normal English page,
2. runtime notices an opportunity to use a target lemma already active in SRS,
3. a semantic gate decides whether the local sentence clearly supports that learner target,
4. LexiShift either:
   - applies the replacement,
   - surfaces a softer non-destructive affordance,
   - or abstains entirely.

The governing product preference is:

- false abstain is usually acceptable,
- harmful replacement is not.

This asymmetry should shape both the research program and the eventual runtime policy.

## What Current Strong Prototype Results Actually Mean

Current prototype readouts often use phrases like:

- `source-derived + cosine`
- `automatic sense text`

Those labels are directionally correct, but incomplete.

The current semantic-routing research prototype is not yet fully automatic end to end.
It already shows that source-backed sense representations can score very well once the ambiguity family is known.
It does not yet prove that LexiShift can discover, select, and serve the right semantic competition set automatically during browser runtime.

That distinction matters enough to be explicit.

## Boundary: Manual Vs Automatic Today

| Layer | Current status | What is manual | What is automatic |
|---|---|---|---|
| Ambiguity family framing | manual | which source family is being evaluated; which sense is active; which benchmark cases belong to the family | none |
| Shadow-family framing | mixed | final promoted shadow set is still handpicked | sibling-sense candidate mining can already be programmatic |
| Context transformation | automatic | none | masking, context windows, raw vs masked sentence views |
| Sense representation | mostly automatic | optional handwritten cue bundles | reverse sense text, gloss bundles, qualifiers, anchor construction, source-derived merged text views |
| Cue augmentation | mixed | handwritten hints and future authored cue bundles | Kaikki-derived cues and raw-example-derived cues |
| Serving policy | missing | no production policy yet | benchmark-side policy experiments only |

### Manual today

The current research loop still relies on people to specify:

- which ambiguity family to test,
- which sense is the active learner sense,
- which sibling senses are the first important blockers,
- which sentences count as clear allow, abstain, phrase control, or weak-context control,
- and any handwritten cue bundles.

That means current prototype success should be interpreted as:

- given a manually framed ambiguity family and a known active sense,
- source-derived evidence plus cosine scoring can work very well.

It should not be interpreted as:

- LexiShift can already discover the full sense-competition structure automatically from runtime text.

### Source-derived today

Once the active sense and candidate shadows are known, the prototype already builds many useful pieces automatically:

- masked and unmasked runtime context views,
- reverse-sense text,
- reverse gloss bundles,
- forward translation/gloss text,
- qualifier text from tags/topics/categories,
- compact anchors,
- Kaikki-text cue bundles,
- raw-example cue bundles when examples exist.

This is the part of the system that has been most encouraging.
It suggests that good runtime semantic gating may be achievable without heavy dependence on manually authored cue text.

## Current Emitted-Rule Provenance Reality

This is the most important current boundary for runtime planning.

Today, the repo has two different provenance layers:

- `candidate metadata` during rulegen/benchmarking
- `emitted rule metadata` in persisted rulesets consumed by helper/runtime

Those are not the same thing.

The verified current behavior is:

| LP / pair | Candidate-level sense evidence | Emitted rule-level sense pointer |
|---|---|---|
| `en-es` | rich candidate metadata can include `dictionary_record`, `dictionary_record_views`, `gloss_provenance`, `sense_provenance`, `target_provenance`, and shadow-risk metadata | shared `metadata.semantic_admission` is emitted by default adapter/helper paths; it carries stable `trigger_id`, `sense_id`, and `competition_set_id` using `sense_provenance` first and `freedict_gloss` fallback, and it now has a narrow `status=ready` PoC when real sibling senses are present in the same emitted batch (`competition_mode=emitted_rule_siblings`) |
| `en-de` | same general shape as `en-es` for Kaikki/provenance-aware candidate generation | shared `metadata.semantic_admission` is emitted by default adapter/helper paths; it can now carry stable `trigger_id`, `sense_id`, and `competition_set_id` using `sense_provenance` first and `freedict_gloss` fallback, but currently stays `status=unavailable` because shadow promotion is not solved yet |
| `en-ja` | no analogous rich sense-provenance layer today; candidate metadata is mostly gloss order, POS, script forms, and word-package information | shared `metadata.semantic_admission` is emitted by default adapter/helper paths and can now carry a stable `jmdict_entry`-backed active pointer derived from target forms, but it still stays `status=unavailable` because shadow promotion is not solved and the pointer is coarser than source-sense provenance |
| `de-en` | candidate metadata is mostly gloss order and POS | shared `metadata.semantic_admission` is emitted by default adapter/helper paths and can now carry a stable `freedict_gloss`-backed active pointer derived from deterministic gloss order, but it still stays `status=unavailable` because shadow promotion is not solved |
| `es-en` | candidate metadata is mostly gloss order, reverse-check info, and POS | shared `metadata.semantic_admission` is emitted by default adapter/helper paths and can now carry a stable `freedict_gloss`-backed active pointer derived from deterministic gloss order, but it still stays `status=unavailable` because shadow promotion is not solved |

So the current answer to:

- "for any emitted LP rule, do we already know exactly which source sense it points to?"

is:

- not fully.

What is true today is weaker:

- the repo now has a shared emitted-rule semantic-routing pointer contract,
- all current rulegen LPs can now preserve a stable active pointer into that contract,
- pointer strength differs by pair:
  - `en-es` / `en-de`: richest, source-sense provenance first
  - `de-en` / `es-en`: deterministic FreeDict gloss-slot locator
  - `en-ja`: deterministic JMDict entry locator
- `en-es` now also has a first narrow competition-set publication PoC that can emit `status=ready` from real emitted sibling senses,
- helper publication can now emit a minimal semantic inventory sidecar,
- but no LP yet emits a fully ready competition/shadow set by default.

This means active-sense provenance is not checked off yet.
It is still one of the main missing seams before semantic routing can become a real admission layer.

## What Is Still Missing For True End-To-End Automatic Semantic Routing

These are the pieces that matter before serious optimization.

### 1. Active-sense provenance seam

LexiShift needs a reliable runtime/build-time way to know:

- which source sense a candidate replacement came from,
- not just which target lemma was emitted.

This has to come from rulegen provenance and survive into the runtime-facing rule payload.

Without it:

- semantic routing is only a benchmark thought experiment,
- not a runtime admission layer.

The current verified gap is concrete:

- adapter/helper publication paths can now preserve a shared `metadata.semantic_admission` pointer,
- all current rulegen LPs can now populate stable active-pointer ids there,
- only `en-es` and `en-de` currently reach source-sense-provenance quality by default,
- `en-es` can now publish a limited emitted-sibling competition set, but that is still narrower than true mined shadow promotion,
- but helper publication still does not emit ready competition/shadow sets by default,
- and weaker LPs still rely on coarser entry/gloss locators rather than full source-sense provenance.

### 2. Automatic shadow-candidate mining

The system needs to enumerate sibling senses of the same source trigger from installed pack data and collapse them into stable sense clusters.

Desired output:

- a small ranked inventory of real semantic competitors,
- not a raw bag of translations or every gloss row.

This is partly understood as a mining problem already, but it is not yet integrated into the main runtime product path.

First implemented research seam:

- `scripts/testing/semantic_shadow_inventory_en_es.py` can now mine a research-only `en-es` shadow inventory from reviewed benchmark trigger phrases plus installed forward/reverse translation packs.
- The latest artifact at `docs/test_outputs/semantic_shadow_inventory_en_es_latest.md` shows broad sibling coverage, which is encouraging.
- The follow-on triage at `docs/test_outputs/semantic_shadow_inventory_triage_en_es_latest.md` shows why publication is still blocked:
  - zero-signal promotions can be removed,
  - but the remaining top-1 preview is still dominated by `same_pos_as_active` rather than benchmark-aligned competition evidence.
- The follow-on policy comparison at `docs/test_outputs/semantic_shadow_policy_compare_en_es_latest.md` now makes the algorithm tradeoff explicit:
  - `same_pos_lenient_v1`: broader still after active-trigger matching (`111` promoted triggers) and therefore even noisier as a runtime candidate
  - `benchmark_backed_v1`: cleaner (`19` promoted triggers) but narrow
  - `cross_checked_v1`: narrower still (`11` promoted triggers), and now the practical runtime-shaped starting point
  - `cross_checked_backoff_missing_active_v1`: now converges to the same `11` promoted triggers after active-side trigger matching was improved for bundled forward glosses and benchmark-only shadow rescue was disabled when the active side is completely empty
- The gap queue at `docs/test_outputs/semantic_shadow_policy_gap_queue_en_es_latest.md` now isolates what the stricter policy still drops:
  - `5` rows due to missing active POS or missing active-side support
  - `3` rows due to explicit cross-POS mismatch without reviewed trigger support
- The most useful concrete fix so far is local and interpretable:
  - active-side trigger matching now uses the existing `en_es_support` gloss-fragment normalization, so bundled forward glosses like `to take, catch, hold, to get, to seize` can supply real active evidence for bare triggers such as `take` and `catch`
  - this was enough to move `coger / catch -> vista` out of the provisional review queue and into the stricter gap queue, which is the right safety direction
- There is now a single review packet at `docs/test_outputs/semantic_shadow_review_packet_en_es_latest.md`:
  - it combines the current policy snapshot, provisional keep rows, provisional drop rows, and the active-side evidence summary for each row
  - it makes the current practical recommendation explicit: treat `cross_checked_v1` as the provisional `en-es` runtime-shaped policy, keep the six surviving blocker rows, and keep the eight dropped rows out of the blocker set for now
- There is now a first lower-bound grading surface at `docs/test_outputs/semantic_shadow_gold_proxy_en_es_latest.md`:
  - it derives a reviewed-trigger-overlap gold proxy directly from `docs/test_inputs/rulegen_benchmark_cases/en_es.json`
  - it scores the current shadow-promotion policies against that proxy without inventing a second benchmark surface
  - this is not a sentence-level semantic veto benchmark, but it gives immediate candidate precision/recall, trigger-hit, underblocking, and overblocking metrics for automatic shadow promotion
  - on the latest `en-es` artifact, the strict policies (`cross_checked_v1` and `cross_checked_backoff_missing_active_v1`) tie as the best current lower-bound:
    - candidate precision `54.5%`
    - candidate recall `60.0%`
    - gold-trigger hit rate `60.0%`
    - overblocking rate `3.6%`
  - the same artifact also clarifies the current limiting factor:
    - the mined candidate pool reaches only `60.0%` trigger-level recall against the overlap proxy
    - so the next bottleneck is not just promotion strictness; it is also shadow-candidate coverage

So this seam is no longer hypothetical.
What remains open is the conservative promotion policy, not whether sibling mining can run at all.

### 3. Shadow-promotion policy

Mining candidates is not enough.
LexiShift also needs a conservative promotion rule for which candidates actually become blockers in runtime.

The first production shadow set should stay:

- small,
- interpretable,
- and obviously tied to harmful confusion classes.

### 4. Phrase/idiom preemption as a separate lane

Some bad replacements are not really “wrong sense” problems.
They are phrase problems.

Examples:

- idioms,
- frozen collocations,
- multiword sports/baseball patterns,
- lexicalized expressions that should be blocked before semantic scoring even starts.

If phrase preemption is not separated from semantic veto, the runtime gate will stay muddy and harder to calibrate.

### 5. Abstain-first serving policy

The production system needs an explicit decision ladder that prefers abstain over risky allow.

The likely runtime outcomes are:

1. hard replace,
2. soft candidate / reveal / annotation,
3. abstain.

This should be an intentional product policy, not an accidental side effect of a benchmark threshold.

### 6. Runtime observability

Before rollout, LexiShift needs diagnostics that can answer:

- why a replacement applied,
- why it abstained,
- which shadow won,
- whether phrase preemption fired,
- which provenance row and cue view were used.

Without that, runtime trust and debugging will be poor even if benchmark numbers look promising.

### 7. Broader benchmark confidence

The current benchmark direction is useful, but not sufficient by itself.

Before a default runtime launch, confidence should come from:

- more source families,
- more holdout cases,
- mirrored-family hazards,
- and eventually more than one pair or direction.

## Implementation Ladder

The recommended order is:

1. define the runtime admission contract,
2. land active-sense provenance in rule outputs,
3. land shadow-candidate mining and clustering,
4. land a conservative shadow-promotion policy,
5. separate phrase preemption from semantic veto,
6. add runtime observability,
7. only then optimize cue forms, score composition, and model choice.

The key principle is:

- do not optimize a benchmark-only slice before the runtime admission seam itself is real.

## Minimum Runtime Contract

The future runtime semantic gate should be able to answer:

1. what source token/phrase candidate was considered,
2. which active sense it came from,
3. which shadows were considered,
4. which context view was scored,
5. which policy decided the outcome,
6. whether the final result was:
   - replace,
   - soft affordance,
   - abstain.

That contract should be explicit in rule metadata and runtime diagnostics before any broad default-on rollout.

## First Research Steps

These are the first work items worth doing now.

### Step 1. Inventory current rulegen/runtime provenance

Goal:

- determine what sense-level provenance already survives from rulegen to emitted rules and into the browser runtime.

Questions to answer:

- do emitted rules already carry enough metadata to identify the originating sense row?
- if not, what is the smallest additional provenance payload needed?
- where does that payload need to be preserved:
  - helper output,
  - stored ruleset,
  - extension runtime?

Output:

- a short provenance gap note plus proposed metadata contract.

### Step 2. Define the semantic-admission payload schema

Goal:

- define the minimal runtime-side structure needed for semantic gating.

Minimum fields likely include:

- source trigger,
- active target lemma,
- active sense id / normalized sense text,
- source pair,
- candidate provenance id,
- ranked shadow candidates,
- phrase-preemption hints,
- optional cue/source view ids.

Output:

- a schema note or example payload attached to the provenance review.

### Step 3. Productize shadow-candidate mining

Goal:

- turn sibling-sense inventory mining into a repeatable repo-supported tool and policy, not just an exploratory artifact.

Questions to answer:

- how should sibling clusters be defined?
- which same-POS and cross-POS senses are worth considering?
- what ranking hints are stable enough to use?

Output:

- a documented candidate miner plus a small launch policy for primary/secondary shadows.

### Step 4. Separate phrase-preemption requirements

Goal:

- define which hazards should be blocked before semantic scoring.

Questions to answer:

- which known bad applies are really phrase problems?
- what metadata or lexical patterns can signal those cheaply?
- how should phrase-preemption interact with semantic veto in runtime?

Output:

- a phrase-preemption checklist and a first candidate test set.

### Step 5. Define the abstain-first runtime policy

Goal:

- make the serving asymmetry explicit before implementation drift sets in.

Questions to answer:

- what confidence bar is needed for hard replacement?
- when should runtime prefer soft annotation to hard replacement?
- what families deserve stricter admission thresholds?

Output:

- a runtime decision-policy note that can later be wired into extension behavior.

## Out Of Scope For This Slice

These are useful later, but not the first bottlenecks:

- squeezing a few extra benchmark points from better cue wording,
- large prompt-authored cue libraries,
- heavier model experimentation,
- runtime UI polish for already-approved semantic replacements.

Those can matter later.
They are not the first blockers for safe end-to-end semantic routing.

## Current Recommendation

Treat semantic routing as a future runtime admission layer, not as a current shipped feature.

The immediate program should focus on:

- provenance,
- shadow selection,
- phrase preemption,
- and abstain-first serving policy.

Only after those seams are explicit should the project invest heavily in optimization.
