# Semantic Veto SRS Corpus Candidate Readiness Runbook

Status: active runbook
Role: Runbook / operational
Last updated: 2026-05-16
Last verified: 2026-05-16 Lane 6 pack lifecycle audit command with strict review gate, source-readiness audit command, SRS Zipf bridge candidate frequency override, denominator audit command review, and promotion evidence bundle command
Purpose: give future agents a copy-pasteable sequence for evaluating an en-es Spanish SRS corpus or frequency-pack candidate before promotion or paid semantic-veto generation
Source-of-truth: runbook only; current runtime truth lives in source code, generated artifacts, pack manifests, and the owning Lane 6 inventory.
Related docs:
- `semantic_veto_srs_corpus_expansion_plan.md`
- `semantic_veto_srs_spanish_expansion_source_probe_2026-05-16.md`
- `semantic_veto_denominator_current_state.md`
- `../developer/productization_lane6_data_provenance_inventory.md`
- `../developer/productization_closure_roadmap.md`

## Scope

Use this runbook when a concrete Spanish candidate SQLite pack exists and the
question is whether it is ready to feed SRS admission, rulegen denominator
refresh, and later semantic-veto generation decisions.

This runbook does not choose the source for you. It prevents accidental
promotion of a source whose provenance, size, schema, POS coverage, topic/domain
coverage, or downstream denominator effect is still unknown.

Do not use this runbook to:

1. overwrite the current `freq-es-cde` baseline,
2. update rulegen quality baselines,
3. launch paid generation,
4. make a default-on runtime change,
5. claim topic-personalized SRS coverage from a source with no topic/domain
   metadata.

## Inputs

Fill these in before running commands:

| Field | Value |
| --- | --- |
| Candidate pack id | `freq-es-expanded-v1` or another versioned id |
| Candidate SQLite path | `/absolute/path/to/candidate.sqlite` |
| Source name | source/provider name |
| Source URL or local source path | URL/path |
| Source version or dump id | version/date/dump id |
| License status | `confirmed`, `requires_review`, `unknown`, `not_redistributable`, or `internal_only` |
| Raw source checksum | SHA-1 or SHA-256 if available |
| Build command/config | command and parser profile used to create the SQLite |
| Intended target size | `5000`, `10000`, or smaller staged target |
| Data root for local install/audit | `/absolute/path/to/LexiShift-data-root` |

If `license_status` is `unknown` or `requires_review`, the candidate may be
audited, but it is not promotion-ready.

## Step 1: Pack Lifecycle Audit

Run the local pack lifecycle audit first. It checks installed manifests,
optional `provenance.json` sidecars, semantic pack copies, publication
manifests, catalog ids, and optional candidate SQLite metadata.

```bash
python3 scripts/testing/pack_lifecycle_audit.py \
  --data-root /absolute/path/to/LexiShift-data-root \
  --candidate-db /absolute/path/to/candidate.sqlite \
  --json-out docs/test_outputs/pack_lifecycle_audit_en_es_candidate.json \
  --markdown-out docs/test_outputs/pack_lifecycle_audit_en_es_candidate.md
```

For a promotion/release gate, rerun the same audit with strict review handling:

```bash
python3 scripts/testing/pack_lifecycle_audit.py \
  --data-root /absolute/path/to/LexiShift-data-root \
  --candidate-db /absolute/path/to/candidate.sqlite \
  --json-out docs/test_outputs/pack_lifecycle_audit_en_es_candidate.json \
  --markdown-out docs/test_outputs/pack_lifecycle_audit_en_es_candidate.md \
  --fail-on-review
```

Interpretation:

- `status = ok`: no manifest/artifact/provenance errors in inspected state.
- `status = review`: provenance, manual-path, source/license, or checksum
  review remains. This is acceptable for research, but not for promotion.
- `status = error`: stop and fix missing manifests, missing artifacts, invalid
  provenance, invalid publication manifests, or missing candidate SQLite input.

Promotion requirement:

- a promoted app-managed candidate should have a valid `provenance.json`
  sidecar; missing sidecars should not be waved through as release evidence,
- the strict `--fail-on-review` lifecycle audit should exit successfully before
  promotion or release packaging.

## Step 2: Source-Readiness Audit

Run the dedicated no-spend corpus audit against the candidate:

```bash
python3 scripts/testing/semantic_veto_srs_corpus_expansion_audit_en_es.py \
  --candidate-db /absolute/path/to/candidate.sqlite \
  --json-out docs/test_outputs/semantic_veto_srs_corpus_expansion_audit_en_es_candidate.json \
  --markdown-out docs/test_outputs/semantic_veto_srs_corpus_expansion_audit_en_es_candidate.md
```

Minimum checks to read from the Markdown/JSON:

1. candidate exists and opens as SQLite,
2. row count,
3. distinct non-empty lemma count,
4. duplicate or empty lemma rate,
5. resolved rank/order column,
6. resolved frequency column,
7. POS column coverage,
8. topic/domain column coverage,
9. readiness for the intended target size,
10. source metadata from the SQLite `meta` table when present.

Stop conditions:

- candidate does not reach the intended distinct-lemma target,
- no usable rank/order and no usable frequency column,
- POS coverage is missing and no explicit backfill plan exists,
- topic/domain metadata is missing but the product claim depends on
  personalization,
- source or license status is missing,
- candidate is just a renamed copy of the current 2k baseline.

## Step 3: SRS Zipf Bridge

Only after the source-readiness audit passes for the intended target size, run
the bridge with full rulegen:

```bash
python3 scripts/testing/semantic_veto_srs_zipf_bridge_en_es.py \
  --frequency-db /absolute/path/to/candidate.sqlite \
  --include-full-rulegen \
  --json-out docs/test_outputs/semantic_veto_srs_zipf_bridge_en_es_expanded_candidate.json \
  --markdown-out docs/test_outputs/semantic_veto_srs_zipf_bridge_en_es_expanded_candidate.md
```

`--frequency-db` should be the same candidate SQLite audited in Step 2. This
keeps research candidates out of the installed default pack path until the
source-readiness, rulegen, denominator, and promotion evidence checks agree.

Read these outputs before moving on:

- expanded SRS target lemma count,
- generated rulegen source-target family count,
- visible replacement-family yield,
- weak or no-visible family count,
- current semantic-veto coverage overlap.

## Step 4: Denominator Audit

Refresh denominator accounting against the current semantic-veto pack:

```bash
python3 scripts/testing/semantic_veto_denominator_audit_en_es.py \
  --srs-zipf-bridge-json docs/test_outputs/semantic_veto_srs_zipf_bridge_en_es_expanded_candidate.json \
  --json-out docs/test_outputs/semantic_veto_denominator_audit_en_es_expanded_candidate.json \
  --markdown-out docs/test_outputs/semantic_veto_denominator_audit_en_es_expanded_candidate.md
```

Interpret the candidate by bucket:

| Bucket | Decision |
| --- | --- |
| Good SRS target and visible browser replacement family | Eligible for future semantic-veto evidence selection. |
| Good SRS target but weak browser replacement family | Consider SRS-only admission or lower replacement priority. |
| Domain/preference target with low general frequency | Keep as user-preference overlay, not general baseline. |
| Poor learner target or bad source mapping | Exclude or keep out of default admission. |

## Step 5: Promotion Evidence Bundle

After the lifecycle, source-readiness, SRS Zipf bridge, and denominator
artifacts have candidate-specific filenames, run the bundle gate:

```bash
python3 scripts/testing/pack_lifecycle_promotion_evidence.py \
  --pack-id freq-es-expanded-v1 \
  --pack-kind frequency \
  --pair en-es \
  --pack-lifecycle-json docs/test_outputs/pack_lifecycle_audit_en_es_candidate.json \
  --source-readiness-json docs/test_outputs/semantic_veto_srs_corpus_expansion_audit_en_es_candidate.json \
  --srs-zipf-bridge-json docs/test_outputs/semantic_veto_srs_zipf_bridge_en_es_expanded_candidate.json \
  --denominator-json docs/test_outputs/semantic_veto_denominator_audit_en_es_expanded_candidate.json \
  --json-out docs/test_outputs/pack_lifecycle_promotion_evidence_en_es_candidate.json \
  --markdown-out docs/test_outputs/pack_lifecycle_promotion_evidence_en_es_candidate.md \
  --fail-on-review
```

Interpretation:

- `status = ok`: the required promotion evidence exists and is promotion-grade.
- `status = review`: at least one supplied proof artifact is review-level.
- `status = error`: at least one required proof artifact is missing, unreadable,
  pointed at the wrong pack, or otherwise not usable as promotion evidence.

This command does not approve the source, install the pack, promote defaults, or
launch generation. It only checks that the required proof artifacts form a
complete candidate bundle.

## Step 6: Update Canonical Docs Before Generation

Before any paid generation or default promotion:

1. update `semantic_veto_srs_corpus_expansion_plan.md` with the candidate
   result,
2. update `semantic_veto_denominator_current_state.md` if the denominator
   changes,
3. update `../developer/productization_lane6_data_provenance_inventory.md` if
   provenance, manifests, or audit status changed,
4. keep the current 2k `freq-es-cde` audit as a frozen comparison baseline,
5. preserve all generated candidate artifacts with candidate-specific filenames.

Do not refresh `*_latest` artifacts only for timestamp freshness. Refresh them
only when the producing command is part of the honest validation bundle.

## Promotion Checklist

A candidate is ready for product testing only when all of these are true:

- versioned pack id is chosen and does not overwrite `freq-es-cde`,
- source URL/path, version/dump id, and license status are explicit,
- raw source checksum is recorded when available,
- build command/config is recorded,
- generated SQLite checksum is recorded,
- normal pack lifecycle audit is not `error`,
- strict pack lifecycle audit with `--fail-on-review` passes before promotion,
- valid `provenance.json` sidecar exists for app-managed promotion,
- source-readiness audit reaches the intended target size,
- rank/frequency ordering is present,
- POS coverage is present or explicitly backfilled,
- topic/domain coverage is present or explicitly deferred,
- SRS Zipf bridge with full rulegen was rerun,
- denominator audit separates covered, uncovered, weak, and no-visible families,
- promotion evidence bundle with `--fail-on-review` passes,
- no paid generation is launched before the new denominator is understood.

## Handoff Summary Template

Use this at the top of any next-agent handoff:

```text
Active task: en-es SRS corpus candidate readiness
Candidate pack id:
Candidate SQLite:
Data root:
Source/license status:
Pack lifecycle audit JSON/MD:
Source-readiness audit JSON/MD:
SRS Zipf bridge JSON/MD:
Denominator audit JSON/MD:
Promotion evidence JSON/MD:
Current decision:
Next required action:
Do not overwrite freq-es-cde:
Do not launch paid generation yet:
```
