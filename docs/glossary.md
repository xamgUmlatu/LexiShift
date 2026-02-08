# LexiShift Glossary

This glossary defines the major concepts, data objects, and workflows used across the LexiShift ecosystem (GUI app, Chrome extension, BetterDiscord plugin, and core engine).

## Core Entities

- **Rule**: A replacement mapping that transforms `source_phrase -> replacement`. Stored in rulesets as `VocabRule`.
- **Source phrase**: The literal text or token to match in input text.
- **Replacement**: The target text inserted in place of the source phrase.
- **Rule metadata**: Additional fields such as `source`, `source_type`, `language_pair`, and `confidence`.
- **Ruleset**: A collection of rules stored as JSON (the “Source of Truth” for replacements).
- **Profile**: A higher‑level container representing a user’s working context (active ruleset, settings, metadata).
- **Profile source mode**: How a client chooses a profile for SRS settings.
  - local selection: use client-local selected profile id (global in extension runtime).
- **Resolved profile ID**: The effective profile ID after applying source mode rules (helper-follow or manual override).
- **Dataset**: The JSON structure that contains rules + settings (aka a ruleset file).

## Pipelines and Processing

- **Tokenizer**: Splits input text into tokens (words, punctuation, spaces).
- **Replacement engine**: Applies rules to text using a longest‑match strategy (trie).
- **Helper bridge**: Extension service-worker boundary that owns native-messaging calls to LexiShift Helper.
- **Inflection expansion**: Optional step that generates inflected variants of a source phrase.
- **Pipeline**: A chained sequence of transformations (e.g., synonym lookup → inflection expansion → ruleset).
- **Consensus filter**: Optional filter that keeps candidate synonyms only if multiple dictionaries agree.
- **Embedding ranking**: Optional similarity scoring using word embeddings.

## Language‑Learning Concepts

- **SRS (Spaced Repetition System)**: Algorithmic scheduling to show items at optimal intervals for learning.
- **S (study inventory)**: The persisted set of words currently being learned by the user for a language pair.
- **Candidate universe (U)**: The larger candidate pool used for possible admission into `S` (frequency packs, dictionaries, profile signals, etc.).
- **Initial S bootstrap**: The initial S built from frequency lists (legacy term: “seed”).
- **Bootstrap top N**: Size of initial inventory admission for S (default `800`, clamped by policy).
- **Initial active count**: Declared initial active subset within bootstrap S (default `40`).
- **Selector**: The scoring algorithm that chooses which words from S should be active right now.
- **Active items**: Words currently eligible for replacement (the “practice gate”).
- **Feedback**: User rating (again/hard/good/easy) that updates SRS weights.
- **Set planner**: Strategy decision layer that decides how S should be initialized/updated.
- **Set strategy**: Named policy such as `frequency_bootstrap`, `profile_bootstrap`, `profile_growth`, `adaptive_refresh`.
- **Signal queue**: Append-only stream of SRS events; feedback is authoritative for scheduling, exposure is optional telemetry.
- **Profile-first SRS storage**: Profile is the top-level container; pair-scoped SRS settings/signals are nested under that profile.

## Frequency and Weighting

- **Frequency list**: A corpus‑derived list of words with ranks or counts.
- **Frequency pack**: A downloaded dataset converted to SQLite for efficient lookups.
- **core_rank**: BCCWJ column used for *selection* (lower = more universal).
- **pmw**: “Per Million Words” column used for *weighting* (higher = more common).
- **Admission weight (weight 1)**: Score used to decide whether a candidate from `U` should enter `S` (or re-enter during growth).
- **Admission bias**: Additional multiplier/additive factor applied to admission weight (for POS, profile interests, proficiency, etc.).
- **POS bucket**: Coarse part-of-speech class (`noun`, `adjective`, `verb`, `adverb`, `other`) used by admission bias policy.
- **Serving priority (weight 2)**: Runtime serving score inside `S`, primarily derived from due-time and SRS state (`next_due`, `stability`, `difficulty`).
- **Effective serving probability**: The normalized chance a word is shown from currently eligible items; this is derived from serving priority and policy caps, not used for admission.
- **Gloss decay**: A penalty applied to secondary dictionary glosses (e.g., 100% / 70% / 50%).
- **Confidence**: A 0..1 value attached to rules to support filtering and threshold sliders.

## Language Pairs

- **Language pair**: The direction of replacement (e.g., `en-ja` or `de-en`).
- **Monolingual**: Source and target are the same language (e.g., `en-en`).
- **Cross‑lingual**: Source and target differ (e.g., `en-ja`).

## Dictionaries / Data Sources

- **WordNet**: English lexical database (synonyms, senses).
- **Moby Thesaurus**: Large English synonym list.
- **OpenThesaurus**: German synonym dataset.
- **OdeNet**: German lexical network (XML).
- **JMDict**: Japanese dictionary with English glosses.
- **Japanese WordNet**: JP WordNet (SQLite or tab format).
- **FreeDict**: Bilingual dictionaries (e.g., DE↔EN).
- **CC‑CEDICT**: Chinese→English dictionary.
- **COCA**: English frequency list (lemmas).
- **BCCWJ**: Japanese frequency list (SUW).

## Embeddings

- **Embedding**: Numeric vector representation of a word used for similarity scoring.
- **Monolingual embeddings**: Same‑language vectors (e.g., en‑en).
- **Cross‑lingual embeddings**: Aligned vectors for translation similarity (e.g., de‑en).
- **Embedding pack**: Downloaded embedding file optionally enabled for similarity ranking.

## Rule Generation (SRS / Automation)

- **Rule generation**: Automated creation of replacement rules from dictionary data.
- **Set initialization**: Explicit mutation action that initializes S for a pair (`srs_initialize`).
- **Candidate**: A potential rule before filtering and scoring.
- **Signals**: Inputs to scoring (dictionary priority, frequency, penalties, embeddings).
- **Score weights**: Tunable coefficients for combining signals into a confidence.
- **Broad gloss**: A source candidate that is semantically too generic (definition-like) and often low pedagogical value for replacement.
- **Quality hardening**: Rulegen filtering/scoring pass focused on demoting broad glosses and ambiguous sources before runtime serving.

## UX / Interface

- **Replacement highlight**: Visual cue for replaced words (coloring or style).
- **Feedback popup**: Right‑click UI to rate word difficulty (SRS feedback).
- **Confidence slider**: UI to enable/disable rules based on confidence threshold.
- **Language pack manager**: GUI table for downloading or linking dictionaries.
- **Embedding manager**: GUI table for downloading or linking embeddings.

## Files and Formats

- **Ruleset JSON**: Canonical rule storage format (used by app, extension, plugin).
- **Share code**: Compact string representation for importing/exporting rules.
- **SQLite pack**: Local database storing frequency or other large resources.
- **Wayback URL**: Archive fallback if a primary download URL fails.

## Platforms

- **GUI app**: PySide6 desktop application (rule management + settings).
- **Chrome extension**: Replaces text in web pages using rulesets + SRS gate.
- **BetterDiscord plugin**: Replaces text inside Discord messages using rulesets + SRS gate.

## Status / Tags

- **Enabled**: Rule or pack is active.
- **Downloaded**: Pack is stored in app data directory.
- **Linked**: Pack path is manually set by user.
- **Invalid**: Pack path fails validation (missing required file).
