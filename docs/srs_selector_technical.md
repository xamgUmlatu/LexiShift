# SRS Wi Selector — Weighted Scoring Technical Spec

## Purpose
Define a stable, modular weighting algorithm for selecting Wi (new and active learning words)
from a candidate pool. The algorithm must be:
- **Explainable** (we can tell the user why a word was chosen).
- **Composable** (each scoring signal can be added/removed without rewriting the system).
- **Calibratable** (weights can be tuned per user, profile, or experiment).
- **Future-proof** (support new signals without breaking existing behavior).

This document is a **living spec** and will evolve as we tune the model.

---

## High-level flow
1) **Candidate Pool** (frequency lists + optional expansions)
2) **Hard Filters** (remove invalid or excluded items)
3) **Feature Extraction** (signals per Wi)
4) **Weighted Scoring**
5) **Selection Policy** (top-N or weighted sampling)
6) **Post-processing** (balance, diversity, quotas)

---

## Data model (per candidate Wi)
Each candidate should support the following fields (not all required initially):
- `lemma` (canonical form)
- `language_pair` (e.g., `en-en`, `de-en`)
- `base_freq` (normalized 0–1)
- `topic_bias` (0–1)
- `user_pref` (0–1)
- `confidence` (0–1)
- `difficulty_target` (0–1)
- `recency` (0–1, lower = recent exposure)
- `source_type` (frequency_list, user_stream, curated, etc.)
- `pos` (optional)
- `metadata` (free-form)

Signals are **normalized to 0–1** before scoring.

**Important:** These values are **computed features**, not stored state.
The selector should derive them at runtime from underlying data sources
(frequency lists, user streams, dictionary consensus, embeddings, etc).
The fixed test dataset is only for offline validation.

---

## Hard filters (always applied)
These are boolean gates applied before scoring:
- **Already in S** (exclude)
- **Blocked / banned** (exclude)
- **Invalid form** (empty, non-lemma tokens)
- **Language-pair mismatch** (exclude)
- **POS exclusion** (optional)

---

## Weighting model (scoring)

### Base formula
```
score(Wi) = SUM( weight_k * signal_k ) * penalties
```

### Default signal weights (initial proposal)
These weights are **defaults**; they should be tunable.
- `base_freq`: **0.55**
- `topic_bias`: **0.15**
- `user_pref`: **0.10**
- `confidence`: **0.10**
- `difficulty_target`: **0.10**

### Penalties (multiplicative)
Apply after the sum to avoid extreme values:
- **recently seen**: `score *= 0.3` if recency below threshold
- **too easy / mastered**: `score *= 0.2`
- **oversubscribed source** (optional): `score *= 0.8`

---

## Signal definitions

### 1) base_freq
Normalized frequency from list or corpus.
- 1.0 = highest frequency
- 0.0 = lowest frequency

### 2) topic_bias
How relevant the word is to current user topics.
Derived from:
- word distribution in user stream
- explicit topic selection

### 3) user_pref
User personalization (manual preference sliders, known goals).

### 4) confidence
Confidence in the word's correctness / usefulness.
Derived from:
- dictionary consensus
- embedding similarity (optional)

### 5) difficulty_target
How well the word matches the user’s target difficulty band.
Derived from:
- user level
- SRS stability/difficulty metrics

---

## Selection policy
We can support multiple selection policies:
1) **Top-N** by score (deterministic)
2) **Weighted random** (probability proportional to score)
3) **Hybrid** (take top-K + sample rest)

Initial MVP: **Top-N** for clarity.

---

## Diversity & balance constraints (optional layer)
After selection, apply balancing rules:
- POS balance (e.g., max 40% nouns)
- Source balance (avoid all from one list)
- Topic diversity (avoid overfitting to one topic)

---

## Explainability
For each selected Wi, store a small explanation:
- dominant signal(s)
- final score
- top two contributing weights

Example:
```
Selected "gloaming" because base_freq=0.18, topic_bias=0.82, confidence=0.71
```

---

## Versioning
Include a `selector_version` in the output so we can:
- compare historical selections
- run A/B tests
- migrate rules if the scoring changes

---

## Testing with a fixed dataset (required for validation)
We should test the selector with a **fixed synthetic dataset** to ensure:
- changes in weights produce expected changes
- results are stable
- penalties behave as intended

**Dataset:** `docs/srs_selector_test_dataset.json` (simple list of ~20–50 items)

---

## Future extension points
The following signals may be added later without breaking the system:
- POS weighting
- Semantic distance to current user goals
- Session-based novelty
- User “avoid list” (negative preferences)

---

## MVP checklist (selector only)
- [ ] Define and store normalized `base_freq` list for each language.
- [ ] Implement filters (in-S, blocked, mismatched pair).
- [ ] Implement scoring with default weights.
- [ ] Use Top-N selection.
- [ ] Provide minimal explanation output.

---

## Notes
This selector is **independent of the ruleset engine**.
It only decides which Wi enter S and in what order.
All further scheduling is handled by the SRS scheduler.
