# POS Normalization Workstream (SRS + Rulegen + LP Onboarding)

Status: Planned (design captured, implementation pending)  
Last updated: 2026-02-22

## Purpose

Create a language-pair-aware POS normalization layer that:

1. Preserves each source corpus/dictionary raw POS tags.
2. Maps raw POS into canonical tags that are stable across languages.
3. Feeds those canonical tags into SRS admission and rulegen scoring consistently.
4. Keeps behavior graceful when a language has partial POS or no POS.

This workstream is intentionally detailed so future contributors can add new languages without rediscovering design context.

## Why This Exists

Current behavior is uneven by language because POS interpretation happens with pair-specific and generic heuristics, not a single source-aware POS adapter layer.

The result:

- Some pairs get meaningful POS-aware admission bias.
- Some pairs collapse into `other` because raw tags are not currently interpreted.
- Rulegen has POS scoring hooks but they are mostly not wired for active pairs.

This causes quality drift across pairs and makes LP onboarding harder than it should be.

## Current Code Map (Verified Touchpoints)

### Active POS usage today

- SRS seed extraction and admission weighting:
  - `core/lexishift_core/srs/seed.py`
  - `core/lexishift_core/srs/admission_policy.py`
- Word metadata packaging:
  - `core/lexishift_core/lexicon/word_package.py`
- Rulegen scoring framework (POS hook available):
  - `core/lexishift_core/rulegen/generation.py` (`SimpleSignalProvider.pos_match_provider`)
- Rulegen pair modules:
  - `core/lexishift_core/rulegen/pairs/en_es.py`
  - `core/lexishift_core/rulegen/pairs/es_en.py`
  - `core/lexishift_core/rulegen/pairs/en_de.py`
  - `core/lexishift_core/rulegen/pairs/ja_en.py`

### Existing but underused hooks

- Candidate filtering supports POS allow-lists, but callers do not use it yet:
  - `core/lexishift_core/srs/selector.py` (`allowed_pos`)
- FreeDict conversion stores POS in SQLite, but default gloss loaders currently return only headword->translation mapping:
  - `scripts/data/convert_freedict_tei_to_sqlite.py`
  - `core/lexishift_core/resources/dict_loaders.py`

### UI/runtime metadata path

- Rule metadata and word_package are already carried to extension runtime:
  - `apps/chrome-extension/content/processing/replacements.js`

## Design Decisions (Locked For This Workstream)

1. Keep raw POS in source data.
   - We do not mutate raw corpus/dictionary values away.
   - Raw POS remains valuable for audits and converter-level debugging.

2. Add a middle normalization connector.
   - Canonical POS is computed at load/use time from raw POS plus source context.
   - Canonical POS is the value used for logic (admission bias, POS scoring, filters).

3. Store both raw and canonical in metadata where practical.
   - Suggested keys: `pos_raw`, `pos_canonical`.
   - Keep existing `pos` for backwards compatibility while migrating.

4. Missing POS must be non-fatal.
   - POS-aware logic is additive quality, not a hard dependency.
   - If POS is unknown, use neutral/other behavior.

5. Frequency columns and POS are separate concerns.
   - A language does not need both `pmw` and another frequency field.
   - POS normalization must work independently of the specific frequency numeric column.

## Canonical POS Contract

Adopt a stable canonical tag set for cross-language logic:

- `noun`
- `adjective`
- `verb`
- `adverb`
- `pronoun`
- `determiner`
- `adposition`
- `conjunction`
- `interjection`
- `numeral`
- `punctuation`
- `other`

Admission buckets remain intentionally coarse:

- `noun`, `adjective`, `verb`, `adverb`, `other`

Bucket mapping policy:

- `noun -> noun`
- `adjective -> adjective`
- `verb -> verb`
- `adverb -> adverb`
- everything else -> `other`

This preserves current admission math while allowing richer POS in metadata/scoring.

## Spanish POS Mapping (Initial Source-Aware Mapping)

For Spanish tags provided for `en-es` resources:

| Raw tag | Canonical POS |
| --- | --- |
| `n` | `noun` |
| `j` | `adjective` |
| `v` | `verb` |
| `r` | `adverb` |
| `c` | `conjunction` |
| `d` | `determiner` |
| `e` | `adposition` |
| `i` | `interjection` |
| `l` | `determiner` |
| `m` | `numeral` |
| `p` | `pronoun` |
| `-` | `punctuation` |

Notes:

- If a source uses multi-tag strings, split and keep the highest-priority lexical tag.
- Priority for bucket-affecting tags: noun > adjective > verb > adverb > other.
- Unknown tags fall back to `other` and should be logged in diagnostics counters.

## Workstream Plan

### Phase 0 - Baseline Audit (No Behavior Changes)

Goal:
- Freeze the pre-change baseline so behavior shifts are measurable.

Tasks:

1. Add/confirm a POS probe script that reports:
   - raw tag distribution per source pack
   - canonical tag distribution
   - admission bucket distribution by pair
2. Capture baseline reports for:
   - `en-ja`, `en-es`, `es-en`, `en-de`
3. Record representative words and POS-driven behavior checks in docs.
4. Add resource integrity audit checks for frequency DBs used by SRS/rulegen:
   - file exists
   - valid SQLite header
   - required `frequency` table exists
   - pack is linked in `settings.json` (`synonyms.frequency_packs`) when downloaded
5. Produce a cross-language data inventory table covering all active language resources (frequency, dictionaries, embeddings, stopwords) with:
   - language pair / target language
   - resource type
   - pack ID / logical name
   - source URL
   - local filename/path convention
   - license
   - schema/tables/required columns
   - POS fields and raw tag inventory status
   - current integration status (downloaded, linked, validated)
6. Document a short recovery playbook for invalid or unlinked packs (for example: zero-byte SQLite, header mismatch, missing `frequency` table, downloaded-but-not-linked).

Suggested code touchpoints:

- `scripts/testing/rulegen_probe_words.py` (extend or companion script)
- new script candidate: `scripts/testing/pos_normalization_probe.py`
- new inventory doc candidate: `docs/language_pairs/lp_data_inventory_matrix.md`
- frequency integrity script (implemented): `scripts/testing/resource_integrity_audit.py`

Phase 0 progress snapshot (2026-02-22):

- Completed:
  - Task 1 delivered via `scripts/testing/pos_normalization_probe.py`.
  - Task 2 baseline artifact captured at `docs/test_outputs/phase0_pos_baseline/phase0_pos_probe_2026-02-22.json`.
  - Task 3 representative behavior notes captured at `docs/rulegen/phase0_pos_baseline_findings.md`.
  - Task 4 delivered via `scripts/testing/resource_integrity_audit.py`.
  - Task 5 delivered via `docs/language_pairs/lp_data_inventory_matrix.md`.
  - Task 6 delivered via `docs/language_pairs/resource_recovery_playbook.md`.
- Remaining:
  - None for Phase 0 baseline scope.

Acceptance:

- Baseline report artifacts exist and are reproducible from CLI.
- Unknown/raw-unmapped POS tags are explicitly listed.
- Frequency DB integrity/linkage checks are reproducible and produce actionable failures.
- A single inventory table doc exists and covers all active language resources with ownership and validation status.

### Phase 1 - Introduce POS Normalization Module

Goal:
- Centralize raw->canonical POS mapping in one reusable module.

Tasks:

1. Add a new module (example):
   - `core/lexishift_core/pos/normalization.py`
2. Implement a source-aware API such as:
   - `normalize_pos(raw_pos, language_pair, source_provider, source_kind, target_language)`
3. Add registry-driven mapping by source profile:
   - `bccwj` (JA frequency)
   - `freq-es-cde` (Spanish frequency)
   - FreeDict-derived POS strings
   - DE frequency profile used by `freq-de-default`
4. Return a structured result:
   - `raw`
   - `canonical`
   - `bucket`
   - `matched_rule` (for diagnostics)

Acceptance:

- New module has focused unit tests for ES/JA/DE known tags and unknown-tag fallback.
- No behavioral change yet outside tests unless explicitly wired.

### Phase 2 - Wire Normalization Into SRS Seed + Admission

Goal:
- Make admission policy consume canonical POS reliably for all pairs.

Tasks:

1. In `core/lexishift_core/srs/seed.py`:
   - normalize POS as seeds are built
   - store both raw and canonical metadata
2. In `core/lexishift_core/srs/admission_policy.py`:
   - prefer canonical POS input for bucket resolution
   - keep legacy raw-text fallback behavior for compatibility
3. In `core/lexishift_core/lexicon/word_package.py`:
   - preserve `pos` for compatibility
   - add `pos_raw` and `pos_canonical` where available

Acceptance:

- S initialization works for all supported pairs without SQL/schema breakage.
- ES no longer collapses into `other` when valid ES tags are present.
- Existing JA behavior remains stable (no regression in bucket distribution quality).

### Phase 3 - Wire Normalization Into Rulegen Candidate Metadata

Goal:
- Make POS available as a first-class scoring signal in rule generation.

Tasks:

1. Extend loaders to expose POS where available:
   - `core/lexishift_core/resources/dict_loaders.py`
   - add an ordered loader variant that includes translation + POS metadata
2. In pair adapters (`en_es`, `es_en`, `en_de`, `ja_en`):
   - attach normalized source POS to `RuleCandidate.metadata`
   - attach target POS (from word_package/seed metadata) when present
3. In `core/lexishift_core/rulegen/generation.py`:
   - wire `pos_match_provider`
   - start with simple scoring:
     - exact canonical POS match -> bonus
     - lexical-compatible class (configurable) -> smaller bonus
     - unknown -> neutral (not penalty)

Acceptance:

- Rulegen outputs include POS metadata fields where source data supports it.
- POS scoring is deterministic and unit-tested.
- Top-3 definition cap still applies after scoring (no ordering regressions).

### Phase 4 - Optional POS Controls For Selection/Refresh

Goal:
- Make POS-aware selection controls usable without forcing strict filters.

Tasks:

1. Expose optional `allowed_pos` policy in refresh paths that call selector filtering.
2. Keep default permissive behavior.
3. Add diagnostics counters:
   - filtered_by_pos
   - admitted_by_pos_bucket
   - unknown_pos_seen

Touchpoints:

- `core/lexishift_core/srs/selector.py`
- `core/lexishift_core/helper/use_cases/refresh_set.py`
- `core/lexishift_core/srs/admission_refresh.py`

Acceptance:

- POS filter can be enabled by config without breaking current defaults.
- Diagnostics clearly show POS effects when enabled.

### Phase 5 - Converter + Resource Pipeline Hardening

Goal:
- Ensure new LP onboarding has a repeatable POS path.

Tasks:

1. For each converter/frequency builder, document:
   - raw POS source field
   - expected tag set
   - source provider ID used by normalization registry
2. Keep raw POS in SQLite as-is.
3. Avoid forcing canonical POS materialization into every source DB; canonical can stay runtime-derived.
4. Add "unknown tag inventory" output in converter logs for quick mapping updates.

Touchpoints:

- `scripts/data/convert_freedict_tei_to_sqlite.py`
- frequency build scripts under `core/lexishift_core/frequency/`
- `docs/language_pairs/language_pack_urls.txt`

Acceptance:

- New pack conversions ship with enough metadata to plug into normalization registry in one edit.

### Phase 6 - Tests, Diagnostics, and Docs Completion

Goal:
- Make maintenance practical and onboarding obvious.

Tasks:

1. Add targeted tests:
   - admission bucket mapping by pair/source
   - rulegen POS scoring behavior
   - unknown-tag fallback behavior
2. Add/extend probe scripts to print canonical POS outcomes for sample words.
3. Document all file touchpoints in docs and link from docs index.
4. Update language pair setup checklist to include POS normalization steps.

Acceptance:

- A new contributor can follow docs to add a language POS mapping without code archaeology.

## Required Data For New Languages (What To Gather)

For each new frequency/dictionary source, collect this minimal POS metadata:

1. Source provider ID
   - example: `freq-es-cde`, `freq-ja-bccwj`, `freedict_es_en`
2. Raw POS field name(s)
   - example: `pos`, `wtype`, or dictionary-specific field
3. Raw tag inventory
   - list all observed tags with brief meaning
4. Tag separators and multi-tag format
   - single code, pipe-delimited, semicolon-delimited, etc.
5. Known edge tags
   - punctuation markers, unknown placeholders, proper noun markers

With those five inputs, normalization mapping can be added with low risk.

## Risks And Mitigations

Risk: Over-aggressive mapping introduces wrong POS signals.  
Mitigation: keep unknown->neutral fallback; do not hard-filter by POS by default.

Risk: Different sources disagree on POS granularity.  
Mitigation: canonical layer decouples source tags from downstream logic.

Risk: Missing POS in some LPs causes inconsistent behavior.  
Mitigation: scoring/filters remain optional; admission defaults still function.

## Definition Of Done

1. SRS admission for all active LPs uses canonical POS when available.
2. Rulegen can consume canonical POS as an optional scoring signal.
3. Unknown POS tags are surfaced in diagnostics, not silently ignored.
4. New language onboarding docs explicitly include POS mapping steps and file references.
5. Existing LP behavior remains stable when POS is absent.

## Related Docs

- `docs/rulegen/rule_generation_technical.md`
- `docs/rulegen/rulegen_congruity_implementation_plan.md`
- `docs/srs/srs_roadmap.md`
- `docs/language_pairs/language_pair_setup_checklist.md`
- `docs/reference/glossary.md`
