# LexiShift Rule Generation: Precomputed Rules + Confidence Scoring

Purpose
- Define a generalized, language‑pair aware pipeline for precomputing replacement rules from a target set S.
- Attach a confidence score to each rule so downstream UI can filter by a user‑controlled threshold.
- Keep the pipeline modular so pair‑specific logic can be plugged in without rewriting the core flow.
- Set planning architecture details live in `docs/srs/srs_set_planning_technical.md`.

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
- `metadata` (object; optional: POS, sense_id, frequency, notes, morphology)

Pipeline overview
0) **Set Planning (new scaffold)**
   - Input: pair, objective, profile context, signal summary.
   - Output: plan metadata (effective strategy + execution mode).

1) **Initial Set Expansion**
   - Input: S, language_pair, enabled dictionaries.
   - Output: raw source candidates (glosses, synonyms, translations).

2) **Normalization**
   - Normalize casing, punctuation, spacing.
   - For English source-gloss pipelines, strip a leading infinitive marker (`to `) from dictionary glosses at candidate-normalization time so `to do` can become `do` without altering raw dictionary metadata.
   - De‑duplicate candidates.
   - Drop noise (very rare, invalid tokens, empty).

3) **Variant Expansion (pluggable)**
   - Morphological variants (plural, tense, inflection).
   - Common abbreviations / slang expansions.
   - Phrase expansions (optional).
   - LP-aware paired morphology can attach `metadata.morphology` (`source_form`, `source_phrase_base`, `target_surface`, `target_lemma`).

4) **Scoring**
   - Assign confidence per rule (0–1).
   - Deterministic scoring for V1; embeddings scoring is optional.
   - Definition ranking for per-target top-K selection is handled by a dedicated mechanism module:
     - `core/lexishift_core/rulegen/ranking.py`
     - Current strategy: dictionary entry order (`gloss_index`, earlier is higher rank).
   - Pair modules can attach ranking metadata (for example `semantic_demotion`) to down-rank known generic/noisy gloss terms before top-K definition selection.

4.5) **Definition Cap (Current Policy)**
   - Keep top 3 definitions per target (`max_definitions_per_target=3` by default).
   - Cap is applied after filtering/scoring using definition buckets keyed by dictionary order metadata.
   - Morphology variants for selected definitions are retained.

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
  - EN/DE/ES benefit from inflection expansion for high recall.
  - Current context-free policy is conservative: noun-number style morphology only (plural-focused), with no context-free tense/aspect generation.
  - Current paired morphology implementation: `en-es` noun plural source forms with Spanish display-surface mapping.
  - Context-dependent morphology (for tense/aspect/disambiguation) is a future/stretch goal and is not part of the current default rulegen path.
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
- **Monolingual (EN/DE/ES/JP)**
  - Monolingual synonym source (WordNet/OdeNet/OpenThesaurus/JP WordNet).
  - Frequency list (to prioritize sources that appear in text).
  - Optional: embeddings.
- **Cross‑lingual (EN↔DE, EN↔JP, EN↔ES)**
  - Bilingual dictionary (FreeDict/JMDict).
  - Optional: multilingual embeddings.
  - Optional: tokenizer for JP.

Current morphology handling (`en-es`)
- Rulegen emits both canonical and plural source forms only when target canonical POS is `noun` (for example `hour` and `hours` for `hora`).
- Emitted rules keep canonical `replacement` lemma (for example `hora`) for SRS identity.
- Plural display form is carried in `metadata.morphology.target_surface` (for example `horas`) and consumed by extension runtime.

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
Reference plan:
- `docs/rulegen/rulegen_congruity_implementation_plan.md` documents the temporary top-3 source limitation decision and the scoring-framework direction, plus the architecture-investigation checklist used before implementation changes.

Current operational policy update:
- Rulegen now applies pair-specific generic-gloss demotion lists (for example `appearing`, `looking`, `like` for English-source LPs) via metadata-driven ranking penalties.
- The defaults are centralized in `core/lexishift_core/rulegen/semantic_demotion.py` and consumed by pair adapters.
- Penalty sensitivity is controlled by `semantic_demotion_scale` (threaded through pair tuning / benchmarks; `0` disables, `1` uses base priors).
- This is a conservative heuristic layer and remains tunable; it does not replace future context-dependent disambiguation work.

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

Polysemy disambiguation candidates (research backlog)
1) Reverse-check scoring (forward + reverse dictionary consistency)
   - Add a score bonus/penalty when `source -> target` is or is not supported by reverse lookup.
   - Example: for `en-es`, validate candidate English source against reverse dictionary evidence from ES back to EN.
   - Expected impact: better rejection of one-way or sense-misaligned translations.
2) Sense-risk penalties from dictionary metadata
   - Use available sense/domain/register/qualifier cues to demote ambiguous or specialized senses.
   - Candidate sources: FreeDict TEI sense notes/labels, JMDict sense metadata, and optional Wiktionary/Kaikki exports.
   - Expected impact: fewer incorrect replacements for high-polysemy glosses.
3) Translation-probability + entropy features (parallel corpus)
   - Build lexical probability tables (`P(target|source)`, `P(source|target)`) from aligned corpora (for example OPUS + `fast_align`).
   - Persist to a compact SQLite feature store and use as rulegen ranking signals.
   - Expected impact: stronger statistical filtering of weak/rare sense mappings.
4) Multi-source agreement bonus
   - Reward candidates corroborated by multiple independent resources (for example FreeDict + aligned probabilities + optional WordNet links).
   - Track provenance count/support in rule metadata.
   - Expected impact: higher precision on accepted mappings.
5) Runtime abstain for high-risk ambiguity
   - At apply time, skip replacement when confidence margin is weak and polysemy risk is high.
   - Emit diagnostics reason codes for abstained replacements.
   - Expected impact: immediate user-trust improvement before full offline disambiguation is complete.
6) Embeddings usage policy
   - Treat static/contextless embedding similarity as a secondary signal only.
   - Use it for weak bonus/penalty and uncertainty margin; do not rely on it as primary polysemy disambiguation.

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
See `docs/rulegen/weight_selection_diagram.mmd` for the S bootstrap + rulegen flow.

### Testing harness (parameter sweeps)
- Seed report: `scripts/testing/ja_en_seed_report.py`
- Rulegen sweeps: `scripts/testing/ja_en_rulegen_sweep.py`
  - Supports `--top-n`, `--thresholds`, `--decays`, and optional `--coca` weighting.
- All-in-one runner (writes output files): `scripts/testing/run_ja_en_tests.py`
- Human review sampler: `scripts/testing/ja_en_sample_review.py`
- Pair-level benchmark sweep + leaderboard: `scripts/testing/rulegen_benchmark.py`
  - Dataset: `docs/test_inputs/rulegen_benchmark_cases.json`
  - Outputs ranked JSON/Markdown reports for iterative tuning across pairs.
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
- `RuleMetadata` now supports `source_type`, `confidence`, and `morphology` fields and is serialized in datasets.
- JA→EN generator scaffold (JMDict) lives in `core/lexishift_core/rulegen/pairs/ja_en.py`.
- EN→DE, EN→ES, and ES→EN generators live in `core/lexishift_core/rulegen/pairs/en_de.py`, `core/lexishift_core/rulegen/pairs/en_es.py`, and `core/lexishift_core/rulegen/pairs/es_en.py`.
- Paired inflection expansion utilities live in `core/lexishift_core/rulegen/utils.py` (`PairedInflectionVariantExpander`).
- Frequency lexicon loader lives in `core/lexishift_core/frequency/core.py` (generic).
- SQLite frequency access + normalization lives in `core/lexishift_core/frequency/sqlite_store.py` and `core/lexishift_core/frequency/providers.py`.
- Seed builder for LP targets lives in `core/lexishift_core/srs/seed.py` (rank selection + frequency-column weighting with `pmw` preference and fallback columns).
- Set planning scaffold lives in:
  - `core/lexishift_core/srs/set_strategy.py`
  - `core/lexishift_core/srs/set_planner.py`
  - `core/lexishift_core/helper/engine.py` (`srs_plan_set`, extended `srs_initialize`)
- Normalization utilities live in `core/lexishift_core/scoring/weighting.py`.
- End-to-end test script: `scripts/build/ja_en_srs_rules.py` (BCCWJ + JMDict + optional COCA).
