# Semantic Veto SRS Corpus Expansion Plan

Status: active planning reference
Role: Planning / WIP
Last updated: 2026-06-08
Last verified: 2026-06-08 with SPALEX Figshare metadata/API check, SPALEX-only pack build, source-stack audit refresh, corpus expansion audit, SRS Zipf bridge full-rulegen run, active-only generation plan, and SRS quality harness
Related docs:
- `semantic_veto_srs_corpus_candidate_readiness_runbook.md`
- `semantic_veto_srs_spanish_expansion_source_probe_2026-05-16.md`
- `semantic_veto_denominator_current_state.md`
- `../srs/srs_interest_tailored_admission_algorithm.md`
- `../srs/srs_interest_tailored_data_acquisition_plan.md`
- `../test_outputs/semantic_veto_srs_source_stack_audit_en_es_latest.md`
- `../test_outputs/semantic_veto_srs_corpus_expansion_audit_en_es_spalex_latest.md`
- `../test_outputs/pack_lifecycle_audit_spalex_latest.md`
- `../test_outputs/semantic_veto_srs_zipf_bridge_en_es_spalex_latest.md`
- `../test_outputs/srs_admission_expansion_audit_en_es_spalex_10k_latest.md`
- `../test_outputs/srs_topic_signal_inventory_en_es_current_latest.md`
- `../test_outputs/semantic_veto_srs_zipf_bridge_en_es_spalex_10k_full_rulegen_latest.md`
- `../test_outputs/semantic_veto_active_only_full_generation_plan_en_es_spalex_10k_latest.md`
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
- native topic/domain metadata coverage: `0 / 2,000` rows.

That is enough for the current general-frequency baseline, but not enough for a
5k-10k corpus or topic-personalized SRS admission.

A follow-up installed-source topic signal inventory clarifies that "no native
topic columns" does not mean "no enrichment signal exists." Current CDE joined
to installed Kaikki/Wiktionary has trusted explicit `sense_topics` for `234 /
1,984` distinct lemmas (`11.8%`) and review-only tag/category signals for
`1,890 / 1,984` lemmas (`95.3%`). The trusted slice already includes product
topic examples such as `medicine` (`42`), `sports` (`33`), `finance` (`24`),
`business` (`23`), `music` (`15`), and `law` (`15`). The tag/category surface is
large but noisy, so it is useful for allowlist and overlay work, not automatic
profile-topic promotion.

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
policy before promotion. A follow-up filter scenario probe shows basic
numeric/surface cleanup is not the main lever: `9,981 / 10,000` rows remain
surface-clean, while mapped non-ambiguous surface-clean rows fall to `3,936 /
10,000` and confident weighted-bucket rows remain `4,122 / 10,000`.

The local `wordfreq` package license posture is also research-only for now. The
installed package reports Apache-2.0, but its metadata states that bundled data
may be redistributed under Creative Commons Attribution-ShareAlike 4.0 and
includes source-specific attribution requirements. Any `wordfreq`-derived pack
promotion therefore needs explicit attribution/sharealike handling before it can
be product evidence.

The 2026-05-17 SPALEX + Kaikki source-stack audit is a stronger practical path
for the next expansion slice. SPALEX `word_info.csv` has `44,853` clean distinct
spellings with complete frequency, Zipf, prevalence, and percentage-known
coverage. The Figshare metadata reports `CC BY 4.0`, which makes it more
promotion-friendly than the proprietary CDE/WordFrequency Spanish 40k option,
subject to attribution and source-manifest handling. However, SPALEX is not an
exact standalone replacement for the current baseline: `278` current CDE lemmas
are absent from SPALEX, including short/function-heavy or otherwise
baseline-useful rows. That is a continuity/comparison concern, not a reason to
make CDE part of the publishable pack. The production-safe frequency frontier
should be `freq-es-spalex-v1` in SPALEX-only mode, while the CDE-seed union
remains an internal/manual-supply benchmark.

Against that combined 10k target, installed Kaikki/Wiktionary coverage is strong
enough for a research pack: `9,469 / 10,000` candidates have Spanish-headword
coverage, and CDE plus Kaikki POS maps `9,435 / 10,000`. Explicit Kaikki topic
coverage is only `1,353 / 10,000`, with an initial medicine/health signal for
`248 / 10,000`, so domain overlays and embedding-assisted topic tagging remain
necessary before interest-tailored SRS admission can be claimed as complete.
Kaikki enrichment also remains promotion-review data until attribution,
share-alike/GFDL posture, and dated dump identity are encoded.

The follow-up 2026-05-17 provisional pack build moved this from source-stack
audit to a concrete research artifact. The original
`freq-es-spalex-expanded-v1` artifact is a CDE-seed plus SPALEX union and should
now be treated as an internal benchmark only, because it inherits the
manual-supply CDE dependency. `scripts/data/build_spalex_frequency_pack_en_es.py`
now defaults to `freq-es-spalex-v1` in `spalex_only` mode: SPALEX-ranked rows are
the primary frequency frontier, runtime `pmw` is a unified rank-descending
commonness score, and original SPALEX frequency fields are preserved in separate
columns. Optional Kaikki enrichment may add POS/topics, but that component stays
review-gated until attribution, share-alike/GFDL posture, and dated dump identity
are encoded.

The 2026-06-08 clean-source bridge run is also clean: the `freq-es-spalex-v1`
candidate override produced `10,000` SRS target lemmas, `17,328` source-target
families, `10,547` distinct English source triggers, and no bridge issues. This
denominator is larger than the earlier CDE-seed/older-source run because the
current installed rulegen source resolves through the managed Wiktionary ES->EN
pack.

The existing LLM-generated tranche-011 evidence should be retained. It contains
`922` normalized evidence rows and `455` active source-target family keys. Under
the old/frozen denominator, that represented `455 / 570` active-only families
covered, with the remaining `115` excluded by source-target review. Against the
new SPALEX-only 10k denominator, a direct full-artifact overlap check finds about
`270` tranche-011 source-target families still inside the expanded denominator.
The `23 / 17,328` figure from
`semantic_veto_active_only_full_generation_plan_en_es_spalex_only_10k_latest`
comes from a smaller product-scope evidence input, not from the full
tranche-011 normalized evidence file. Do not read it as a discard or failure of
the previous paid LLM run.

This leaves a clear product posture:

- keep `en-es-active-only-combined-full-v1-tranche-011` as the current
  operator-accepted semantic reference checkpoint,
- run a provenance audit before hosted/bundled redistribution so the semantic
  pack does not carry protected CDE/WordFrequency rank, frequency, or source
  table data,
- make future paid generation SPALEX-only by default, using
  `freq-es-spalex-v1`, managed Wiktionary, and reviewed POS/topic overlays,
- use the expanded active-only generation plan as a queueing and spend-planning
  artifact, not as an automatic quality failure.

The active-only generation planner reads the expanded bridge as a real
denominator and reports `17,305` uncovered families, with a review posture of
`247` approved, `6` excluded, and `17,052` unreviewed source-target rows. This is
useful expansion evidence, but not a spend decision: the unreviewed majority
needs tranche review before paid generation, and SRS-only admission remains
separable from semantic-veto evidence generation.

The SRS admission check is now the first UX-pipeline gate before veto work. The
SPALEX 10k admission audit passes with `10,000` selected unique lemmas, rank
resolved through `id`, commonness resolved through `pmw`, `94.3%` POS mapping,
and an expected POS-weighting shift from `19` non-lexical/function-heavy rows in
the rank-order top 100 to `0` in the admission-order top 100. Profile-interest
diagnostics show usable tagged support for `medicine`, `finance`, `sports`, and
`music`, while preserving the limitation that topic coverage is sparse at
`13.5%` of the 10k frontier.

SAT and TOEFL are product-aligned preference families if legal source review
allows them, but they are not current data facts. Treat them like other
interest-tailored overlays: useful once sourced and attributed, unavailable as
automatic admissions signals until then.

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
7. Treat license/provenance review as a promotion gate, not as a post-release
   cleanup.
8. Do not start another paid semantic-veto generation wave until the expanded
   source creates a measured replacement-family denominator.

## Candidate Source Families

| Source Family | Why It Might Help | Main Risk | First Validation |
| --- | --- | --- | --- |
| SPALEX-only | Leading publishable frequency path: SPALEX supplies 44,853 frequency/prevalence rows under CC BY 4.0 source posture and avoids inheriting CDE. | SPALEX spellings are not guaranteed to behave exactly like lemmas, and it omits 278 current CDE rows. | Build `freq-es-spalex-v1`, audit overlap/POS/topic/rulegen yield, and compare against the current CDE baseline. |
| SPALEX plus current CDE seed | Internal continuity benchmark: keeps the old CDE rows first, then adds SPALEX-ranked rows. | Not publishable by default because it inherits the manual-supply CDE source. | Use only for comparison against current behavior, not as the release candidate. |
| Kaikki/Wiktionary enrichment | Supplies POS, glosses, dictionary compatibility, reverse-check support, and partial topic/category metadata. | Share-alike/GFDL posture and dated dump identity are promotion gates; explicit topic coverage is partial. | Join against SPALEX/CDE combined candidates and record field-level provenance. |
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

When the candidate source is SPALEX plus installed Kaikki, run the stack audit
without downloading large Kaikki raw dumps:

```bash
python3 scripts/testing/semantic_veto_srs_source_stack_audit_en_es.py \
  --spalex-csv /path/to/word_info.csv \
  --json-out docs/test_outputs/semantic_veto_srs_source_stack_audit_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_srs_source_stack_audit_en_es_latest.md
```

This audit checks whether SPALEX can provide the expanded ranked frontier, whether
the current CDE seed must be retained, and how much installed Kaikki coverage is
available for POS, glosses, explicit topics, medicine/health signals, and reverse
Spanish translation targets.

### Phase 2: Pack Naming And Installation

Do not overwrite `freq-es-cde.sqlite` during research.

Preferred naming:

- `freq-es-cde.sqlite`: frozen current baseline,
- `freq-es-spalex-v1`: publishable SPALEX-only default frequency pack,
- `freq-es-spalex-expanded-v1`: internal CDE-seed plus SPALEX-ranked comparison pack,
- `freq-es-expanded-topic-v1.sqlite`: first topic/domain-aware candidate,
- `freq-es-hybrid-v1.sqlite`: first merged baseline plus overlays candidate.

The app-managed/default frequency source can be promoted independently from
semantic-veto coverage. `freq-es-spalex-v1` is the preferred clean source
default; semantic-veto denominator coverage remains a separate tranche-review
and generation problem.

Build the SPALEX pack into a normal data-root-shaped temp directory:

```bash
python3 scripts/data/build_spalex_frequency_pack_en_es.py \
  --spalex-csv /path/to/word_info.csv \
  --pack-root /tmp/lexishift-spalex-audit/data-root/frequency_packs/freq-es-spalex-v1 \
  --overwrite \
  --write-sidecars
```

This writes `main.sqlite`, `manifest.json`, and `provenance.json`; it does not
download SPALEX or Kaikki and it does not mutate the installed product data root.
Add `--no-kaikki-enrichment` when a pure CC BY frequency-only pack is needed for
license isolation. Add `--source-mode spalex_cde_union --pack-id
freq-es-spalex-expanded-v1 --provider freq-es-spalex-expanded-v1` only when
building the legacy internal comparison pack.

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

For expanded candidates, also run the active-only planner against the same
bridge artifact:

```bash
python3 scripts/testing/semantic_veto_active_only_full_generation_plan_en_es.py \
  --srs-zipf-bridge-json docs/test_outputs/semantic_veto_srs_zipf_bridge_en_es_expanded_candidate.json \
  --json-out docs/test_outputs/semantic_veto_active_only_full_generation_plan_en_es_expanded_candidate.json \
  --markdown-out docs/test_outputs/semantic_veto_active_only_full_generation_plan_en_es_expanded_candidate.md
```

The current-state denominator audit remains useful, but it is anchored to the
active-only plan artifact supplied to it. If the bridge source-target count and
active-only denominator differ, read it as a scope-mismatch/accounting warning,
not as expanded-candidate coverage.

The important outputs are:

- expanded SRS target lemmas,
- expanded rulegen source-target families,
- families already covered by current semantic-veto evidence,
- new uncovered families,
- approved, excluded, and unreviewed source-target rows,
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
