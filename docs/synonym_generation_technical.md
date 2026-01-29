# Synonym Generation Technical Notes

## Scope
This document describes how LexiShift generates synonym-based rules today, how language pairs are assigned, and how optional embeddings affect ranking and fallback. It also calls out current assumptions and limitations.

## Conceptual Flow
1) User selects language packs (dictionaries) in the bulk synonym generation dialog.
2) Packs are grouped into language pairs (e.g., `en-en`, `de-en`, `ja-ja`).
3) For each language pair, the app loads its selected sources, generates synonyms, and emits rules tagged with that language pair.
4) Optional embeddings are applied per language pair when enabled.

The system intentionally keeps packs and embeddings separate:
- Packs = source material for candidates (dictionaries, WordNet, etc.).
- Embeddings = optional scoring/ranking and fallback for candidates, scoped to a language pair.

## Language Pairs
A language pair is a normalized identifier for the direction (monolingual or cross-lingual) the synonyms belong to.

Current pair normalization:
- Monolingual: `en-en`, `de-de`, `ja-ja`
- Cross-lingual: `de-en`, `en-ja`, `en-zh`

Pairs are derived from dictionary pack IDs. Example mapping:
- WordNet / Moby -> `en-en`
- OpenThesaurus / OdeNet -> `de-de`
- JP WordNet -> `ja-ja`
- FreeDict DE↔EN -> `de-en`
- JMDict JA↔EN -> `en-ja`
- CC-CEDICT ZH↔EN -> `en-zh`

## Rules and Pair Attribution
Synonym rules are created as `VocabRule` entries. Each rule produced by synonym generation gets:
- `tags = ("synonym",)`
- `metadata.language_pair = <pair>`

This metadata is the authoritative link for downstream behavior (embedding selection, rule filtering, etc.).

## Dictionary Processing
Sources are loaded into a unified in-memory synonym map per language pair.

Current dictionary sources:
- English monolingual: WordNet, Moby Thesaurus
- German monolingual: OpenThesaurus, OdeNet
- Japanese monolingual: JP WordNet (tab or SQLite)
- DE↔EN: FreeDict
- JA↔EN: JMDict
- ZH↔EN: CC‑CEDICT

Important: dictionaries are combined per pair. If multiple sources exist for the same pair, their synonyms are merged unless the consensus filter is enabled.

## Consensus Filter (Optional)
If `require_consensus` is enabled and multiple sources are present for the same pair:
- Only synonym candidates appearing in *all* selected sources are kept.
- This is applied per pair, not across all packs globally.

## Embeddings (Optional)
Embeddings are now per language pair.

Configuration fields:
- `embedding_pair_paths[pair] = [list of embedding paths]`
- `embedding_pair_enabled[pair] = true/false`

Behavior:
- If embeddings are disabled for a pair, no ranking or fallback occurs for that pair.
- If enabled, the embedding index is built from all paths in the pair (merging vectors).

Supported use cases:
- Monolingual ranking: use monolingual vectors (e.g., `cc.en.300.vec` for `en-en`).
- Cross‑lingual ranking: use aligned vectors for both languages in the pair (e.g., `wiki.en.align.vec` + `wiki.de.align.vec` for `de-en`).

## Ranking and Filtering
When embeddings are enabled for a pair:
- Candidates are scored by cosine similarity between the target word and candidate.
- Candidates below the threshold are excluded.
- If the threshold is 0.0, unknown candidates may be appended (legacy behavior).

## Embedding Fallback (Optional)
If no dictionary synonyms are found:
- And embeddings are enabled with neighbor support:
  - Nearest neighbors are used as a fallback list.
- If embeddings do not support neighbor lookup, fallback is skipped.

Fallback is applied per pair, using that pair’s embedding index.

## Replacement‑Side Filtering UI
The replacement panel can apply a similarity threshold per replacement word.
- The pair is inferred from the rules that target that replacement.
- The appropriate embedding index is loaded for that pair (if enabled).
- Only rules with matching pair metadata are affected.

## User Responsibility (Important)
LexiShift currently expects users to practice due diligence:
- Only select language pairs that make sense for the input words.
- Example: Do not run DE↔EN packs on Japanese input.

The system does **not** automatically detect the language of input words or block incompatible pairs.

## Current Limitations
- No automatic language detection for input lists.
- If a replacement word has mixed pair tags, the app currently picks the dominant pair for that replacement (by count).
- Cross‑lingual embeddings are experimental; quality varies by language and vector set.

## Planned Improvements
- Language detection to guide pair selection.
- Clearer UI indicators for active pair and embedding state.
- Pair‑specific thresholds and pair‑scoped UI feedback.

