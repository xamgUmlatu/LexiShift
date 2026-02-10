# LexiShift Rule Generation: Precomputed Rules + Confidence Scoring

Purpose
- Define a generalized, language‑pair aware pipeline for precomputing replacement rules from a target set S.
- Attach a confidence score to each rule so downstream UI can filter by a user‑controlled threshold.
- Keep the pipeline modular so pair‑specific logic can be plugged in without rewriting the core flow.
- Set planning architecture details live in `docs/srs_set_planning_technical.md`.

Scope
- Covers rule generation for monolingual and cross‑lingual language pairs.
- Focuses on precomputed rules (no runtime dictionary queries in the extension/plugin).
- Integrates optional embeddings‑based scoring (when available) without making it mandatory.

Key concepts
- **Target set S**: the words/lemmas the user is learning (the words we want to surface).
- **Set planning**: pre-rulegen strategy selection step for initializing/updating S.
- **Source candidates**: words/phrases likely to appear in user text that can map to a target.
- **Rule**: `source_phrase` → `replacement` with metadata and confidence.

Rule schema (canonical)
- `source_phrase` (string)
- `replacement` (string) — target word from S
- `language_pair` (string; e.g., `en-en`, `en-jp`, `de-en`)
- `confidence` (float, 0.00–1.00)
- `source_dict` (string; dictionary id)
- `source_type` (enum: synonym | translation | expansion | slang | phrase | inferred)
- `metadata` (object; optional: POS, sense_id, frequency, notes)

Pipeline overview
0) **Set Planning (new scaffold)**
   - Input: pair, objective, profile context, signal summary.
   - Output: plan metadata (effective strategy + execution mode).

1) **Initial Set Expansion**
   - Input: S, language_pair, enabled dictionaries.
   - Output: raw source candidates (glosses, synonyms, translations).

2) **Normalization**
   - Normalize casing, punctuation, spacing.
   - De‑duplicate candidates.
   - Drop noise (very rare, invalid tokens, empty).

3) **Variant Expansion (pluggable)**
   - Morphological variants (plural, tense, inflection).
   - Common abbreviations / slang expansions.
   - Phrase expansions (optional).

4) **Scoring**
   - Assign confidence per rule (0–1).
   - Deterministic scoring for V1; embeddings scoring is optional.

5) **Rule Emission**
   - Emit rules with full metadata + confidence.
   - Store per language_pair ruleset.

Pair‑agnostic core
- The core pipeline should operate on:
  - `source_candidates` (normalized strings)
  - `target_word` (from S)
  - `dictionary_metadata` (source type + priority)
  - `language_pair` configuration (tokenizer, lemmatizer, variant rules)

Language‑pair specific modules (pluggable)
- **Tokenizer / segmentation**
  - Needed for languages without spaces (JP/CH/KR).
- **Inflection engine**
  - EN/DE benefit from inflection expansion for high recall.
- **POS alignment**
  - Optional, but improves confidence when dictionary provides POS.
- **Phrase expansion**
  - Optional; should have a confidence penalty due to risk.

Confidence scoring (V1 proposal)
Score is computed as a weighted sum, capped to [0, 1].

Inputs (typical)
- Dictionary priority (trusted sources score higher)
- Source frequency (common terms score higher)
- POS match (bonus if POS is known and aligned)
- Variant penalty (slang / aggressive expansions reduce score)
- Phrase penalty (multi‑word heuristics are lower confidence)

Example weighting (illustrative)
- `dict_priority`: +0.30 to +0.60
- `frequency_weight`: +0.00 to +0.20
- `pos_match`: +0.10
- `variant_penalty`: −0.05 to −0.20
- `phrase_penalty`: −0.05 to −0.25

Embeddings‑based scoring (optional)
- Use embeddings when available to improve ranking:
  - Monolingual similarity: source ↔ target.
  - Cross‑lingual similarity (requires multilingual embeddings).
- Embeddings adjust confidence, not replace base score.
- Recommended: apply as a multiplicative or additive adjustment with a clamp.
- If embeddings are missing/disabled for a pair, skip this step entirely.

Filtering at runtime
- Extension/app reads the precomputed ruleset and filters:
  - `confidence >= user_threshold`.
- Threshold slider should be pair‑aware (same slider can apply to a selected pair).

Data requirements (by pair)
- **Monolingual (EN/DE/JP)**
  - Monolingual synonym source (WordNet/OdeNet/OpenThesaurus/JP WordNet).
  - Frequency list (to prioritize sources that appear in text).
  - Optional: embeddings.
- **Cross‑lingual (EN↔DE, EN↔JP)**
  - Bilingual dictionary (FreeDict/JMDict).
  - Optional: multilingual embeddings.
  - Optional: tokenizer for JP.

Storage & versioning
- Store rules per language_pair with version metadata.
- Record the input dictionary set + scoring config used to generate.
- Allow regeneration when dictionaries or scoring parameters change.

Planned UX implications
- Users select dictionaries per language pair.
- Users adjust confidence threshold (slider).
- Embeddings are an optional download; if enabled, they improve scoring.

Open questions
- How to prioritize source candidates when multiple dictionaries overlap?
- How to handle POS ambiguity when POS is missing?
- How to detect and demote overly generic sources (e.g., “thing”, “do”)?
- How to treat multi‑word phrases across languages with different tokenization rules?

Current known quality gap (important)
- In current JA-target rulegen, some emitted English source phrases are too broad (gloss-like definitions rather than context-appropriate triggers).
- Result: runtime replacement can be technically correct but pedagogically weak or noisy.
- This is a quality issue in source-candidate selection/scoring, not an SRS storage or scheduling failure.

Quality hardening track (next)
1) Generic gloss suppression
   - Maintain pair-specific denylist/demotion lists for broad function-like terms and over-generic glosses.
   - Apply strong penalties before final candidate ranking.
2) POS/sense-aware filtering
   - Require POS compatibility where available.
   - Prefer primary sense; aggressively down-rank secondary/ambiguous senses unless evidence is strong.
3) Confidence gating refinement
   - Add explicit penalties for candidates that are high-frequency but semantically broad.
   - Raise minimum confidence thresholds for broad source types.
4) Emission diagnostics
   - Persist reason codes for why a candidate survived filtering (for auditability and tuning).
   - Add review reports showing top noisy candidates by pair.

Next steps (current workstream focus)
1) **Frequency provider for EN glosses (JA→EN)**
   - Why: use high‑frequency English glosses to generate rules that actually appear in text.
   - Status: COCA lemmas list downloaded and converted to SQLite via the GUI frequency pack flow.
   - Output: a `frequency_provider(candidate)` function that returns 0–1 weight.
   - Pack size (SQLite): ~2 MB.

2) **JA frequency list (for JP target weighting)**
   - Why: lets SRS and rulegen favor common JP targets or allow rare ones intentionally.
   - Status: BCCWJ SUW downloaded and converted to SQLite via the GUI frequency pack flow.
   - Pack size (SQLite): ~50 MB.

### Current plan (JA target, EN source)
We are locking in a **JMDict‑filtered core set** for initial S bootstrap:

1) **Selection (initial S):** use `core_rank` from BCCWJ SUW.  
2) **Filter:** intersect top‑N by `core_rank` with **JMDict lemmas** (to avoid junk).  
3) **Weighting:** use `pmw` (per‑million‑words) as the primary frequency signal.  
4) **Rulegen:** for each JA lemma in S, use JMDict glosses, **single‑word English only**.  
5) **Confidence decay:** the first gloss gets 100% of base weight; secondary glosses decay (e.g. 70%/50%).  

> **Note:** confidence scoring is WIP and will evolve. This is a baseline model.

### Diagram (planned algorithm)
See `docs/weight_selection_diagram.mmd` for the S bootstrap + rulegen flow.

### Testing harness (parameter sweeps)
- Seed report: `scripts/testing/ja_en_seed_report.py`
- Rulegen sweeps: `scripts/testing/ja_en_rulegen_sweep.py`
  - Supports `--top-n`, `--thresholds`, `--decays`, and optional `--coca` weighting.
- All-in-one runner (writes output files): `scripts/testing/run_ja_en_tests.py`
- Human review sampler: `scripts/testing/ja_en_sample_review.py`
2) **Rulegen harness for JA→EN**
   - Why: generate a concrete ruleset JSON from a target set S and JMDict.
   - Needed from you: preferred output path + any S test list you want to use.
   - Output: CLI/script that writes rules with `confidence`, `source_type`, `language_pair`.
3) **Pair config registry**
   - Why: keep pair‑specific modules (tokenizer/inflector/embeddings) isolated and reusable.
   - Needed from you: confirm which pairs are V1 and which dictionary sources should be wired.
   - Output: `pair_registry.py` (or similar) + mapping to available sources.

Implementation status
- Core pipeline skeleton lives in `core/lexishift_core/rulegen/generation.py`.
- `RuleMetadata` now supports `source_type` + `confidence` fields and is serialized in datasets.
- JA→EN generator scaffold (JMDict) lives in `core/lexishift_core/rulegen/pairs/ja_en.py`.
- Frequency lexicon loader lives in `core/lexishift_core/frequency/core.py` (generic).
- SQLite frequency access + normalization lives in `core/lexishift_core/frequency/sqlite_store.py` and `core/lexishift_core/frequency/providers.py`.
- Seed builder for JA targets lives in `core/lexishift_core/srs/seed.py` (core_rank selection + pmw weighting).
- Set planning scaffold lives in:
  - `core/lexishift_core/srs/set_strategy.py`
  - `core/lexishift_core/srs/set_planner.py`
  - `core/lexishift_core/helper/engine.py` (`srs_plan_set`, extended `srs_initialize`)
- Normalization utilities live in `core/lexishift_core/scoring/weighting.py`.
- End-to-end test script: `scripts/build_ja_en_srs_rules.py` (BCCWJ + JMDict + optional COCA).
