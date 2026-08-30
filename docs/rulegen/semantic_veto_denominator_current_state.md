# Semantic Veto Denominator Current State

Status: active reference
Role: Canonical current
Last updated: 2026-06-08
Last verified: 2026-06-08 against the tranche-011 artifact set plus the SPALEX-only 10k SRS Zipf bridge and active-only generation plan
Purpose: keep the active-only semantic-veto denominator understandable before product cleanup or future corpus expansion
Source-of-truth: frozen tranche-011 counts come from `docs/test_outputs/semantic_veto_denominator_audit_en_es_latest.json`; clean-source expansion counts come from `docs/test_outputs/semantic_veto_srs_zipf_bridge_en_es_spalex_only_10k_full_rulegen_latest.json` and `docs/test_outputs/semantic_veto_active_only_full_generation_plan_en_es_spalex_only_10k_latest.json`

## Current Answer

The current active-only semantic-veto lane is complete under the frozen
tranche-011 `en-es` denominator. That does not mean the newer SPALEX-only
10k denominator is fully covered.

The important denominator distinction is:

- `1,984` Spanish target lemmas are currently SRS-admissible under the installed
  frequency/source resources.
- `570` English-source / Spanish-target replacement families are currently
  produced by rulegen from that SRS target universe.
- `455 / 570` replacement families now have active-only semantic evidence.
- the remaining `115 / 570` replacement families are not waiting for paid LLM
  generation; they are excluded by source-target review.

The current accounting identity is:

```text
570 = 49 pre-full-generation covered + 406 reviewed/generated + 115 excluded
```

The current semantic pack was not thrown away. The full tranche-011 artifact set
contains:

- `922` normalized evidence rows,
- `455` active source-target family keys,
- `455` triggers / competition sets in the semantic inventory.

The 2026-06-08 SPALEX-only expansion work changes the denominator rather than
invalidating that LLM evidence. The clean-source bridge expands the planning
universe to `10,000` SRS-admissible Spanish targets, `17,328` source-target
families, and `10,547` distinct English source triggers. A direct overlap check
of the full tranche-011 normalized evidence against that expanded denominator
finds about `270` covered source-target families. The smaller `23 / 17,328`
figure in the SPALEX-only generation plan is a product-scope planning figure
based on the smaller `en-es-active-only-combined-product-scope-v1` evidence file;
it should not be read as "only 23 full tranche-011 families remain useful."

Interpretation:

- keep `en-es-active-only-combined-full-v1-tranche-011` as the current
  operator-accepted semantic reference checkpoint,
- do not discard the existing LLM evidence,
- before public hosted/bundled redistribution, run a provenance audit so the
  semantic pack does not carry protected CDE/WordFrequency rank, frequency, or
  source-table data,
- make future paid generation and coverage expansion use the clean
  `freq-es-spalex-v1` / Wiktionary / POS-overlay source stack.

## What The Numbers Mean

`1,984` is the learner-target universe currently exposed by the installed SRS
frequency/source data. It answers "how many Spanish target lemmas can this
current local SRS setup plausibly admit?"

`570` is the semantic-veto replacement-family universe. It answers "for the
current SRS target lemmas, how many English browser triggers does rulegen
currently publish as replacement rules?"

These are not interchangeable. A Spanish target can be learnable in SRS without
having a useful English browser replacement trigger. Conversely, a single target
can appear in more than one source-target family.

## Why The Frozen Queue Is Empty

The frozen active-only generation queue is empty because the final
post-tranche-011 plan has:

- generation queue families: `0`,
- selected requests: `0`,
- evidence outside the denominator: `0`,
- uncovered families: `115`,
- source-target review exclusions: `115`.

Those `115` exclusions split into:

- `27` no-visible-replacement rows, usually identical forms, compounds, or
  source shapes that would not create a meaningful visible browser replacement,
- `88` weak source-target mappings where generating active cue data would
  strengthen a questionable replacement pair.

## Expansion Levers

Future expansion is not primarily a prompt-generation task under the frozen
denominator. Under the clean SPALEX-only denominator, new prompt generation is
again useful, but only after tranche review chooses high-value source-target
families from the expanded queue.

The main levers are:

1. Expand or replace the Spanish frequency/source pack so the SRS learner-target
   universe grows beyond the current `1,984` unique lemmas.
2. Improve rulegen dictionary/filter coverage so more visible source-target
   replacement families are produced from the existing or expanded SRS target
   universe.
3. Change source-target review policy if we intentionally want to admit some
   currently excluded weak or no-visible mappings.
4. Generate shadow or phrase/no-winner data only for already covered families
   where active-only evidence leaves clear harmful-replacement classes.

The corpus-expansion decision path is tracked in
`docs/rulegen/semantic_veto_srs_corpus_expansion_plan.md`. Use that plan and
`scripts/testing/semantic_veto_srs_corpus_expansion_audit_en_es.py` before
choosing a new 5k-10k Spanish source or running more paid generation.

## Product Posture

For cleanup, the current product-facing posture should be:

- tranche-011 is the current operator-accepted active-only product checkpoint,
- tranche-003 remains the latest hands-on browser-extension smoke,
- active-only paid generation should not continue from the old post-tranche-011
  queue,
- any new paid generation should be based on the SPALEX-only expansion plan and
  tranche-reviewed source-target rows,
- product docs should label SRS learner-target counts and semantic-veto
  replacement-family counts separately.

## Validation

Refresh the audit with:

```bash
python3 scripts/testing/semantic_veto_denominator_audit_en_es.py --fail-on-review
```

Then run:

```bash
PYTHONPATH=apps/gui/src:core python3 -m pytest \
  core/tests/dev/test_semantic_veto_denominator_audit_en_es.py

python3 scripts/dev/check_doc_references.py
```
