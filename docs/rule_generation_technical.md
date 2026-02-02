# LexiShift Rule Generation: Precomputed Rules + Confidence Scoring

Purpose
- Define a generalized, language‑pair aware pipeline for precomputing replacement rules from a target set S.
- Attach a confidence score to each rule so downstream UI can filter by a user‑controlled threshold.
- Keep the pipeline modular so pair‑specific logic can be plugged in without rewriting the core flow.

Scope
- Covers rule generation for monolingual and cross‑lingual language pairs.
- Focuses on precomputed rules (no runtime dictionary queries in the extension/plugin).
- Integrates optional embeddings‑based scoring (when available) without making it mandatory.

Key concepts
- **Target set S**: the words/lemmas the user is learning (the words we want to surface).
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
1) **Seed Expansion**
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

Next steps (current workstream focus)
1) **Frequency provider for EN glosses (JA→EN)**
   - Why: use high‑frequency English glosses to generate rules that actually appear in text.
   - Needed from you: a frequency dataset for English words (single‑word, no phrases).
   - Output: a `frequency_provider(candidate)` function that returns 0–1 weight.
   - Conversion: use `scripts/convert_frequency_to_sqlite.py` for long‑term local use.

2) **JA frequency list (for JP target weighting)**
   - Why: lets SRS and rulegen favor common JP targets or allow rare ones intentionally.
   - Needed from you: BCCWJ SUW TSV (or equivalent).
   - Conversion: use `scripts/convert_bccwj_frequency_to_sqlite.py`.
2) **Rulegen harness for JA→EN**
   - Why: generate a concrete ruleset JSON from a target set S and JMDict.
   - Needed from you: preferred output path + any S test list you want to use.
   - Output: CLI/script that writes rules with `confidence`, `source_type`, `language_pair`.
3) **Pair config registry**
   - Why: keep pair‑specific modules (tokenizer/inflector/embeddings) isolated and reusable.
   - Needed from you: confirm which pairs are V1 and which dictionary sources should be wired.
   - Output: `pair_registry.py` (or similar) + mapping to available sources.

Implementation status
- Core pipeline skeleton lives in `core/lexishift_core/rule_generation.py`.
- `RuleMetadata` now supports `source_type` + `confidence` fields and is serialized in datasets.
- JA→EN generator scaffold (JMDict) lives in `core/lexishift_core/rule_generation_ja_en.py`.
- Frequency lexicon loader lives in `core/lexishift_core/frequency.py` (generic).
