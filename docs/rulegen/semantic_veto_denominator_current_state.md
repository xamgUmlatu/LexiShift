# Semantic Veto Denominator Current State

Status: active reference
Role: Current-state explanation
Last updated: 2026-05-14
Last verified: 2026-05-14 against `docs/test_outputs/semantic_veto_denominator_audit_en_es_latest.md`
Purpose: keep the active-only semantic-veto denominator understandable before product cleanup or future corpus expansion
Source-of-truth: current counts come from `docs/test_outputs/semantic_veto_denominator_audit_en_es_latest.json`

## Current Answer

The current active-only semantic-veto lane is complete under the current
`en-es` denominator.

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

## Why The Queue Is Empty

The active-only generation queue is empty because the final post-tranche-011
plan has:

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

Future expansion is not primarily a prompt-generation task.

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

## Product Posture

For cleanup, the current product-facing posture should be:

- tranche-011 is the current operator-accepted active-only product checkpoint,
- tranche-003 remains the latest hands-on browser-extension smoke,
- active-only paid generation should not continue until the denominator or
  source-target review policy changes,
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
