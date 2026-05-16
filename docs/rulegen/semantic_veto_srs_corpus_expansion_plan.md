# Semantic Veto SRS Corpus Expansion Plan

Status: active planning reference
Role: Planning / WIP
Last updated: 2026-05-16
Last verified: 2026-05-16 with source-readiness audit review, local no-download wordfreq candidate probe, candidate POS backfill audit, and SRS Zipf bridge candidate frequency override tests
Related docs:
- `semantic_veto_srs_corpus_candidate_readiness_runbook.md`
- `semantic_veto_srs_spanish_expansion_source_probe_2026-05-16.md`
- `semantic_veto_denominator_current_state.md`
- `../developer/productization_lane6_data_provenance_inventory.md`

## Purpose

The current en-es active-only semantic-veto lane is complete for the current
installed SRS source universe, but that universe is small:

- `2,000` installed Spanish frequency rows,
- `1,984` distinct SRS-admissible Spanish target lemmas,
- `570` rulegen replacement families,
- `455` semantic-veto-covered replacement families.

The next product question is not "generate more LLM data immediately." The next
question is "what larger Spanish learner corpus should feed SRS admission,
rulegen, and eventual semantic-veto coverage?"

This document keeps that decision open. We should not assume the current
frequency pack is the only valid foundation, and we should not assume every
expanded word needs semantic-veto evidence.

## Current Finding

The expansion ceiling is currently a source-data ceiling.

`scripts/testing/semantic_veto_srs_zipf_bridge_en_es.py` already requests up to
`50,000` SRS seed candidates, but the installed `freq-es-cde.sqlite` source has
only `2,000` rows and `1,984` distinct non-empty lemmas. Its metadata references
`spanish_lemmas20k.txt`, but that source file is not installed in the current
frequency-pack directory.

The current pack has:

- usable rank/order column: `id`,
- usable frequency column: `freq`,
- POS coverage: `2,000 / 2,000` rows,
- topic/domain metadata coverage: `0 / 2,000` rows.

That is enough for the current general-frequency baseline, but not enough for a
5k-10k corpus or topic-personalized SRS admission.

The 2026-05-16 no-download `wordfreq` probe shows the opposite side of the
decision: a temporary 10k Spanish candidate can clear the raw size/rank/frequency
ceiling and can be fed into the SRS Zipf bridge via `--frequency-db`, but it has
`0%` POS coverage, `0%` topic/domain coverage, and only `25.7%` overlap with the
current 1,984-lemma CDE sample. That makes it useful as a candidate strategy,
not a drop-in promoted replacement.

A follow-up POS backfill audit against installed Spanish-headword lexical
resources found that Wiktionary ES-EN supplies exact-headword POS for `5,497 /
10,000` candidate lemmas and mapped POS for `5,036 / 10,000`; however, only
`4,122 / 10,000` have a confident weighted lexical bucket after ambiguous POS is
treated conservatively. This makes a 5k POS-aware shortlist plausible, but it
does not make the temporary candidate a 10k POS-complete source. Rank-band
coverage also shows the top rows are not automatically cleaner: only `18%` of
the top 100 and `35%` of the top 500 have confident weighted lexical buckets,
so common function words, forms, and numerals need explicit filtering/defaulting
policy before promotion.

## Decision Principles

1. Freeze the current 2k pack as the comparison baseline.
2. Version any expanded pack separately until it has passed audit and rulegen
   denominator checks.
3. Treat corpus source selection as a product/data decision, not a semantic-veto
   prompt decision.
4. Keep general-frequency expansion and topic/domain overlay expansion separable.
5. Preserve provenance per source; merged packs should not erase whether a row
   came from frequency, learner-level, dictionary, or domain data.
6. Do not claim profile-personalized SRS coverage from a source that has no
   topic/domain metadata.
7. Do not start another paid semantic-veto generation wave until the expanded
   source creates a measured replacement-family denominator.

## Candidate Source Families

| Source Family | Why It Might Help | Main Risk | First Validation |
| --- | --- | --- | --- |
| Recovered or rebuilt Spanish 20k frequency list | Fastest continuity path if it preserves current rank/POS semantics. | Provenance or license may be unclear; likely no topic metadata. | Confirm source, row count, schema, POS coverage, duplicate rate. |
| General frequency corpus | Best broad 5k-10k browsing/SRS coverage. | Frequency alone may include low-learning-value rows. | Compare overlap with current 2k and rulegen family yield. |
| Learner-level or CEFR-style list | Better staged learner progression. | May be smaller or missing usable frequency values. | Verify level coverage and merge with frequency ranking. |
| Dictionary-derived lemma expansion | Large source pool without needing a frequency list first. | Poor ranking can admit obscure or awkward lemmas. | Require rank backfill, POS validation, and exclusions. |
| Domain/topic overlays | Enables medical, legal, travel, and other preference-driven SRS expansion. | Domain rows may not be comparable to general-frequency rows. | Store domain tags and treat as overlay, not replacement. |
| Hybrid base-frequency plus overlays | Most product-aligned path for general plus personalized learning. | Merge policy can hide provenance and duplicate lemmas. | Audit per-source contribution after merge. |

## Expansion Methodology

### Phase 1: Candidate Source Audit

Run the no-spend source-readiness audit on the current pack and each candidate
SQLite pack:

Use `semantic_veto_srs_corpus_candidate_readiness_runbook.md` when a concrete
candidate SQLite exists and another agent needs the full pack lifecycle,
source-readiness, SRS bridge, denominator, and documentation-update sequence.

```bash
python3 scripts/testing/semantic_veto_srs_corpus_expansion_audit_en_es.py \
  --candidate-db /path/to/candidate.sqlite \
  --json-out docs/test_outputs/semantic_veto_srs_corpus_expansion_audit_en_es_candidate.json \
  --markdown-out docs/test_outputs/semantic_veto_srs_corpus_expansion_audit_en_es_candidate.md
```

The audit checks:

- row count,
- distinct non-empty lemma count,
- duplicate or empty lemma rows,
- rank/frequency column resolution,
- POS column coverage,
- topic/domain column coverage,
- readiness for 2k, 5k, and 10k target sizes,
- source metadata from the SQLite `meta` table when present.

If POS coverage is missing, run the backfill audit before treating the candidate
as SRS-ready:

```bash
python3 scripts/testing/semantic_veto_srs_candidate_pos_backfill_audit_en_es.py \
  --candidate-db /path/to/candidate.sqlite \
  --json-out docs/test_outputs/semantic_veto_srs_candidate_pos_backfill_audit_en_es_candidate.json \
  --markdown-out docs/test_outputs/semantic_veto_srs_candidate_pos_backfill_audit_en_es_candidate.md
```

This audit is intentionally conservative: it joins candidate lemmas only to
Spanish resource `headword_lc` values, excludes English-side translation POS,
and does not mutate the candidate or installed language packs.

### Phase 2: Pack Naming And Installation

Do not overwrite `freq-es-cde.sqlite` during research.

Preferred provisional naming:

- `freq-es-cde.sqlite`: frozen current baseline,
- `freq-es-expanded-v1.sqlite`: first expanded general-frequency candidate,
- `freq-es-expanded-topic-v1.sqlite`: first topic/domain-aware candidate,
- `freq-es-hybrid-v1.sqlite`: first merged baseline plus overlays candidate.

The first install should be local and reversible. Only promote a pack as the
default after SRS, rulegen, and semantic-veto denominator artifacts are refreshed.

### Phase 3: SRS And Rulegen Denominator Refresh

After choosing a candidate source, rerun the existing bridge with full rulegen:

```bash
python3 scripts/testing/semantic_veto_srs_zipf_bridge_en_es.py \
  --frequency-db /absolute/path/to/candidate.sqlite \
  --include-full-rulegen \
  --json-out docs/test_outputs/semantic_veto_srs_zipf_bridge_en_es_expanded_candidate.json \
  --markdown-out docs/test_outputs/semantic_veto_srs_zipf_bridge_en_es_expanded_candidate.md
```

Use `--frequency-db` for candidate evaluation so the bridge reads the same
SQLite file that passed the source-readiness audit. This avoids installing a
research candidate or overwriting the frozen `freq-es-cde` baseline before the
candidate has denominator evidence.

Then refresh denominator accounting against the current semantic-veto pack:

```bash
python3 scripts/testing/semantic_veto_denominator_audit_en_es.py \
  --srs-zipf-bridge-json docs/test_outputs/semantic_veto_srs_zipf_bridge_en_es_expanded_candidate.json \
  --json-out docs/test_outputs/semantic_veto_denominator_audit_en_es_expanded_candidate.json \
  --markdown-out docs/test_outputs/semantic_veto_denominator_audit_en_es_expanded_candidate.md
```

The important outputs are:

- expanded SRS target lemmas,
- expanded rulegen source-target families,
- families already covered by current semantic-veto evidence,
- new uncovered families,
- weak/no-visible families that should not receive paid evidence.

### Phase 4: Generation Decision

Only after Phase 3 should we decide what to generate.

Possible outcomes:

- If the expanded corpus produces many useful visible replacement families,
  generate evidence for a high-value subset.
- If it mostly produces weak or no-visible mappings, improve source/rulegen
  filtering before generation.
- If topic overlays create valuable SRS targets but little browser replacement
  value, admit them into SRS without semantic-veto data.
- If domain-specific rows are useful but sparse, keep them as user-preference
  overlays rather than part of the general 5k/10k baseline.

## Product Interpretation

Expanding the SRS corpus and expanding semantic-veto coverage are related but
not identical.

An expanded word may fall into one of four buckets:

1. Good SRS target and good browser replacement family: eligible for future
   semantic-veto evidence.
2. Good SRS target but weak browser replacement family: admit to SRS, avoid or
   downgrade replacement.
3. Good domain/preference target but low general frequency: admit only when the
   user profile asks for that topic.
4. Poor learner target or bad source mapping: exclude or keep out of default
   admission.

The product should not require semantic-veto evidence for every SRS word. The
semantic-veto pack should focus on replacement families where browser
replacement is actually visible and useful.

## Current Audit Command

Refresh the current source-readiness artifact with:

```bash
python3 scripts/testing/semantic_veto_srs_corpus_expansion_audit_en_es.py \
  --json-out docs/test_outputs/semantic_veto_srs_corpus_expansion_audit_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_srs_corpus_expansion_audit_en_es_latest.md
```

Focused tests:

```bash
PYTHONPATH=apps/gui/src:core python3 -m pytest \
  core/tests/dev/test_semantic_veto_srs_corpus_expansion_audit_en_es.py
```

## Definition Of Done For First Expansion

The first expansion is ready to product-test when:

- a versioned candidate frequency pack is installed locally,
- the corpus audit shows at least the chosen target size of distinct lemmas,
- rank/frequency ordering is present,
- POS coverage is present or explicitly backfilled,
- topic/domain coverage is either present or explicitly deferred,
- the SRS Zipf bridge has been rerun with full rulegen,
- the denominator audit separates covered, uncovered, weak, and no-visible
  families,
- no paid LLM generation is launched until the new denominator is understood.
