# Productization Lane 6 Data Provenance And Pack Lifecycle Inventory

Status: active inventory
Role: Planning / WIP
Last updated: 2026-05-15
Last verified: 2026-05-15 read-only inspection of pack catalogs, source-manifest cache policy, installed-pack manifests, helper pack resolvers, semantic-pack installation/publication code, semantic data-lifecycle docs, en-es corpus-expansion audit plan, en-es candidate readiness runbook, focused pack-provenance validator tests, focused pack-lifecycle audit tests, semantic-pack provenance install tests, app-managed non-semantic pack sidecar tests, manual resource settings audit tests, constrained manual embedding selection tests, safe manual-settings backfill tests, source-lineage publication tests, existing-install provenance backfill tests, external import plan tests, provenance review posture tests, strict lifecycle gate tests, and the SRS quality harness
Purpose: record the current data-source, pack, manifest, installed-artifact, and generated-artifact lifecycle before corpus or semantic-veto expansion resumes
Source-of-truth: inventory only; current runtime truth lives in source code, installed manifests, generated SQLite artifacts, helper publication manifests, tests, and seam-specific canonical docs.
Related docs:
- `productization_closure_roadmap.md`
- `productization_lane4_validation_gate_inventory.md`
- `productization_lane5_runtime_seam_inventory.md`
- `data_source_normalization_execution_order.md`
- `../rulegen/semantic_routing_data_update_lifecycle.md`
- `../rulegen/semantic_veto_srs_corpus_candidate_readiness_runbook.md`
- `../rulegen/semantic_veto_srs_corpus_expansion_plan.md`
- `../rulegen/semantic_veto_denominator_current_state.md`
- `../rulegen/lp_onboarding_operating_model.md`
- `../pack_source_manifest.json`
- `../../apps/gui/src/language_packs_catalog.py`
- `../../core/lexishift_core/helper/installed_packs.py`
- `../../core/lexishift_core/helper/pack_provenance.py`
- `../../core/lexishift_core/helper/rulegen_outputs.py`
- `../../core/lexishift_core/helper/semantic_pack_provenance.py`
- `../../core/lexishift_core/helper/use_cases/semantic_pack_install.py`
- `../../scripts/testing/pack_lifecycle_audit.py`
- `../../scripts/testing/pack_lifecycle_external_import_plan.py`
- `../../scripts/testing/pack_lifecycle_manual_backfill.py`
- `../../scripts/testing/pack_lifecycle_manual_resources.py`
- `../../scripts/testing/pack_lifecycle_provenance_backfill.py`
- `../../core/tests/helper/test_pack_provenance.py`
- `../../core/tests/dev/test_pack_lifecycle_audit.py`
- `../../core/tests/dev/test_pack_lifecycle_external_import_plan.py`
- `../../core/tests/dev/test_pack_lifecycle_manual_backfill.py`
- `../../core/tests/dev/test_pack_lifecycle_provenance_backfill.py`
- `../../apps/gui/tests/test_pack_provenance_sidecars.py`
- `../../apps/gui/tests/test_language_pack_table_mixin.py`

## Scope

Lane: Lane 6, data provenance and pack lifecycle.

Completed slices:

1. L6-A: current pack/source provenance inventory.
2. L6-B: pack provenance sidecar contract.
3. L6-C: pack lifecycle audit command.
4. L6-D: semantic pack provenance and lineage sidecar.
5. L6-E: en-es SRS corpus candidate readiness runbook.
6. L6-F: app-managed non-semantic installer provenance sidecars.
7. L6-G: manual resource settings disposition audit.
8. L6-H: constrained manual import/backfill contract.
9. L6-Ia: safe backfill for manual settings that already point at
   app-managed SQLite pack roots.
10. L6-Ja: semantic source-lineage propagation into publication manifests and
    lifecycle audit reporting.
11. L6-Ka: existing app-managed install provenance sidecar backfill.
12. L6-La: external/manual import preflight plan.
13. L6-Ma: lifecycle-audit provenance review posture.
14. L6-Na: strict pack lifecycle review gate.

This inventory does not promote a new corpus, change default pack selection,
launch paid semantic-veto generation, or mark expansion ready. It maps the
current lifecycle surfaces so the next implementation slices can close the
right gaps in order.

Explicitly out of scope:

1. overwriting the current `freq-es-cde` baseline,
2. changing SRS admission thresholds,
3. changing semantic-veto generation policy,
4. certifying remote update or release packaging,
5. treating generated `docs/test_outputs/` artifacts as source authority.

## L6-A Authority Map

| Layer | Current Surface | Answers | Does Not Answer Yet |
| --- | --- | --- | --- |
| Pack catalog | `apps/gui/src/language_packs_catalog.py` | Available app-managed packs, provider labels, URLs, Wayback URLs, filenames, build modes, required files, parse configs. | Whether a specific user has installed a pack, source license status, raw/download checksum, converter version, or row/schema audit results. |
| Pack source manifest | `docs/pack_source_manifest.json`, `apps/gui/src/pack_source_manifest.py` | Remote transport overrides, expected content type, TTL/cache policy. | Pack provenance, licensing, current installed state, generated artifact identity, or runtime default status. |
| Installed-pack manifest | `core/lexishift_core/helper/installed_packs.py`, `<data_root>/{language_packs,frequency_packs,embeddings}/<pack_id>/manifest.json` | Pack id/kind/provider, local kind, build mode, artifact relpath/kind, installed timestamp, source/sqlite filenames, required files, raw-retention flag. | Source URL, license/reuse status, raw source checksum, source dump/version, converter command/version, generated SQLite schema, row counts, POS/domain coverage, or current runtime adoption. |
| Provenance sidecar | `core/lexishift_core/helper/pack_provenance.py`, `<pack_root>/provenance.json` | Versioned contract for source identity, license status, source pointer, raw artifact checksums, build mode, generated artifact identity, and optional SQLite metrics; semantic installs and app-managed translation/frequency/embedding installs now write conservative sidecars. | Legacy installs, manual paths, raw checksums, converter versions, and approved license status still need follow-up lifecycle work. |
| Lifecycle audit | `scripts/testing/pack_lifecycle_audit.py` | Read-only JSON/Markdown audit of installed pack manifests, optional provenance sidecars, semantic pack copies, profile publication manifests, manual resource settings, catalog pack ids, and optional candidate SQLite metadata. | It does not backfill provenance sidecars, rewrite settings, prove licenses, replace the source-readiness audit, or promote packs. |
| Pack refs/resolvers | `frequency_packs.py`, `translation_packs.py`, `embedding_packs.py`, `pair_resources.py`, `lp_capabilities.py` | Runtime-facing pack id, provider, source/POS profile, resolved path, and managed-vs-fallback resolution. | Full provenance for manual paths or legacy fallback files. |
| Semantic pack copy | `<data_root>/language_packs/<pair>/semantic_packs/<pack_id>/manifest.json` and `provenance.json` from `semantic_pack_install.py` | Semantic pack id/pair, generated timestamp, source path, raw/normalized inventory hashes, source inventory generation fields when present, source batches when carried by the source inventory, installed semantic inventory artifact hash/bytes, and validated sidecar provenance. | Release manifest identity, approved review state, or why the compiled generation was selected. |
| Profile publication manifest | `<data_root>/srs/profiles/<profile_id>/srs_publication_manifest_<pair>.json` from `rulegen_outputs.py` | Ruleset/snapshot/semantic inventory family identity, `generation_id`, artifact hashes/bytes, family-valid flag, and optional semantic source lineage when the publisher provides it. | It is still a runtime publication manifest, not the source manifest or license approval record. |
| Generated evidence | `docs/test_outputs/` audit, benchmark, and experiment artifacts | Evidence from the command that produced the artifact. | Architecture authority or current runtime truth without a source/code/test pointer. |

## Resource Family State

| Family | Current Managed Shape | Current Provenance | Main Lane 6 Gap |
| --- | --- | --- | --- |
| Translation dictionaries | App-managed FreeDict and Kaikki installs build to SQLite under a pack-id root and write `manifest.json`; helper resolution is pack-id-first with legacy filename fallbacks. | Catalog has source/provider URL fields; installed manifest has provider, build mode, artifact relpath, source filename, sqlite filename, and installed timestamp. App-managed installs now also write `provenance.json` with source URL, Wayback URL when present, conservative `requires_review` license status, build mode, source filename, SQLite filename, generated artifact relpath/kind, and generated artifact SHA-1. | Existing installs need reinstall/backfill, source license approval is not encoded, raw source checksums are not retained, converter version/schema/row-count records are still audit outputs, and manual/legacy fallback paths still depend on inference. |
| Frequency packs | App-managed frequency installs build to SQLite under a pack-id root and write `manifest.json`; runtime diagnostics expose frequency pack id/provider/POS profile. | Catalog plus installed manifest identify provider/build mode/source filename and the generated artifact path. App-managed installs now also write `provenance.json` with source URL, Wayback URL when present, conservative license status, build mode, source filename, SQLite filename, artifact relpath/kind, and generated artifact SHA-1. | Audit metrics, approved source/license status, raw checksum, converter version, and topic/domain coverage are still outside installer-written provenance. Spanish expansion candidates need versioned pack ids and audit artifacts before promotion. |
| Embedding packs | App-managed embeddings use pack-id roots, manifest-backed artifacts, and embedding pack refs; manual/raw paths remain compatibility inputs. | Installed manifest records provider, build mode, source filename, sqlite filename, and artifact path. App-managed SQLite finalization now also writes `provenance.json` with source URL, Wayback URL when present, conservative license status, build mode, source filename, SQLite filename, artifact relpath/kind, and generated artifact SHA-1. | License approval, source version/checksum, raw vector retention, conversion parameters, and manual/raw-path provenance remain outside first-class lifecycle coverage. |
| Secondary lexical packs | WordNet, Moby, OpenThesaurus, OdeNet, JMDict, and CC-CEDICT remain mixed/raw or compatibility surfaces. | Catalog records source/provider URL fields; some managed downloads may write basic installed manifests. | Family-wide promotion decision is still pending; they should not be treated as core normalized runtime packs until evaluated. |
| Semantic source/evidence batches | Semantic lifecycle docs define source registry, raw batches, normalized evidence, compiled generation, publication family, and helper-local materialization layers. | Planning contracts require append-only raw evidence and explicit provenance. | The cross-pack Lane 6 gate still needs an implemented source/generation audit tying raw evidence, compiled inventory, semantic pack copy, and profile publication together. |
| Semantic compiled packs | Named en-es dev packs resolve from installed copy, catalog env, or current repo dev-pack paths; install writes a semantic pack copy and a profile publication family. | Pack copy manifest hashes raw/normalized inventory; publication manifest hashes runtime artifacts, assigns one generation id, and now carries semantic source lineage when available. | Dev-pack paths are hardcoded development fixtures; release-manifest identity and final review/approval lineage are still pending. |
| SRS profile runtime state | Profile-local store/status/signal/inventory files live under `<data_root>/srs/profiles/<profile_id>/`. | Runtime state can reference published rules and diagnostics. | These files are runtime/user state, not source packs; Lane 6 should keep this boundary explicit during expansion. |

## Expansion Readiness Rules

Before any larger Spanish corpus is promoted as a default or semi-default pack:

1. give the candidate a versioned pack id; do not overwrite `freq-es-cde`,
2. record source family, source URL or local source path, license/reuse status,
   source version or dump id, raw filename, and raw checksum,
3. record converter/build command, parse config, converter version if available,
   generated SQLite path, generated checksum, schema, row count, distinct lemma
   count, POS coverage, and topic/domain coverage,
4. run the source-readiness audit from
   `../rulegen/semantic_veto_srs_corpus_expansion_plan.md`,
5. run the SRS Zipf bridge and denominator audit only after the candidate
   passes source-readiness review,
6. keep the current 2k `freq-es-cde` audit as the comparison baseline,
7. do not launch paid semantic-veto generation until the expanded rulegen
   denominator separates covered, uncovered, weak, and no-visible families,
8. update this inventory, the corpus-expansion plan, and the denominator doc
   together when a candidate is promoted or rejected.

## Current Findings

What is already solid:

1. App-managed translation, frequency, and embedding families have pack-id roots
   and installed manifests.
2. Runtime-facing pack refs expose pack id, provider, and source/POS profile for
   the main managed families.
3. Semantic pack install writes both a helper-local semantic pack copy and a
   profile-local runtime publication family.
4. Runtime publication manifests carry `generation_id`, artifact hashes, byte
   counts, and family-valid state.
5. The en-es corpus-expansion plan already keeps the current 2k pack frozen and
   requires no-spend source-readiness audits before generation decisions.
6. `pack_provenance.py` now defines and validates a first `provenance.json`
   sidecar contract for the source/build/generated-artifact data that the
   installed manifest does not currently carry.
7. `pack_lifecycle_audit.py` now reports installed manifests, optional
   provenance sidecars, semantic pack copies, publication manifests, catalog
   ids, and optional candidate SQLite metadata into one JSON/Markdown surface.
8. Semantic pack install now writes a validated `provenance.json` sidecar for
   copied semantic packs and records a manifest `lineage` block without
   removing the older manifest fields.
9. `../rulegen/semantic_veto_srs_corpus_candidate_readiness_runbook.md` now
   gives a copy-pasteable candidate audit sequence before expanded Spanish
   corpus promotion or paid semantic-veto generation.
10. App-managed translation, frequency, and embedding installs now write
    conservative `provenance.json` sidecars at manifest/finalization time.
11. The lifecycle audit now reports manual/external resource settings and marks
    app-managed artifacts stored in manual-path fields as migration candidates.
12. Manual/external resource selection is now treated as a constrained
    license/import fallback for exact supported artifact shapes, not a broad
    file picker.
13. Semantic pack installation now passes semantic source lineage into the
    profile publication manifest, and the lifecycle audit reports whether
    publication manifests carry source lineage.
14. Missing provenance sidecars on catalog-backed app-managed installs now have
    a dry-run/apply backfill command that reuses the conservative installer
    sidecar contract.
15. A manually acquired external artifact can now be preflighted into an
    explicit manual-link/import plan before any settings rewrite, file copy, or
    runtime promotion.
16. The lifecycle audit now separates valid sidecars from release/promotion
    readiness by reporting license status, source pointer type, raw checksum
    coverage, generated artifact checksum presence, and review reasons.
17. The lifecycle audit now supports a strict `--fail-on-review` mode for
    promotion/release gates while preserving non-strict local audit behavior.

Loose ends to close before broad expansion:

1. The installed-pack manifest is an install record, not a complete provenance
   or license record.
2. The pack catalog and pack source manifest are not copied into installed-pack
   provenance in a way that can prove license approval, raw checksum, converter
   version, or source-version identity later.
3. Manual and legacy fallback paths can still enter runtime without a manifest
   lineage, but saved manual settings are now reportable through the lifecycle
   audit.
4. Generated SQLite schema, row counts, POS coverage, and topic/domain coverage
   are audit outputs, not pack-manifest fields.
5. Semantic publication manifests validate runtime artifact family integrity and
   can now carry source lineage when the publisher provides it, but release
   manifest identity and review/approval lineage remain pending.
6. Named semantic dev packs currently resolve through repo-local generated
   experiment paths, which is acceptable for operator work but not a release
   pack lifecycle.
7. The lifecycle audit is still read-only and gap-reporting. Sidecar mutation
   lives in explicit backfill commands instead of the audit command.
8. The manual-settings backfill command now covers only the safe case where a
   saved manual path already points at a manifest-backed app-managed SQLite
   pack root. It does not import external licensed artifacts.
9. Existing-install sidecar backfill does not prove license approval, raw source
   checksums, converter versions, or source-version identity; it records the
   conservative catalog/manifest information currently available.
10. External import preflight can say whether a manual link is format-safe and
    what review data is missing, but the actual copy/convert UX and managed
    pack writer are still future work.
11. Provenance review posture is now visible, but review approval remains a
    human/source-policy decision outside the audit command.
12. Strict lifecycle gating can fail on review findings, but it still does not
    replace the source-readiness, SRS Zipf bridge, or denominator audits needed
    before expanded corpus promotion.

## L6-B Pack Provenance Sidecar Contract

Product claim:

- Future app-managed corpus, dictionary, embedding, and semantic pack promotion
  needs an auditable source/build/generated-artifact record beyond the current
  install manifest.

Current implementation:

- `core/lexishift_core/helper/pack_provenance.py` defines
  `PACK_PROVENANCE_FILENAME = "provenance.json"` and
  `PACK_PROVENANCE_SCHEMA_VERSION = 1`.
- The validator requires top-level `pack_id`, `pack_kind`, `provider`,
  `source`, `build`, and `artifact` sections.
- `source` must include `source_name`, explicit `license_status`, and either
  `source_url` or `local_source_path`.
- `license_status` is intentionally explicit. Valid values are `confirmed`,
  `requires_review`, `unknown`, `not_redistributable`, and `internal_only`.
- Raw source artifacts can carry `filename`, `sha1`, and `sha256`.
- `build` must include `build_mode`; it can also carry command/parser/converter
  detail as optional data.
- `artifact` must include `artifact_relpath` and `artifact_kind`, can carry
  checksums, and can carry metrics such as `row_count`,
  `distinct_lemma_count`, `pos_rows`, and `topic_domain_rows`.
- The validator checks SHA-1/SHA-256 shape, non-negative metrics, and coverage
  metrics that do not exceed total row count.

Boundaries:

1. This is a sidecar contract, not a replacement for installed
   `manifest.json`.
2. Installer-written sidecars are currently conservative records, not source
   certification or license approval.
3. Manual paths and legacy fallback paths are still outside this contract until
   the lifecycle audit and manual-path disposition slices land.
4. The contract allows `license_status = "unknown"` or `requires_review`, but
   that only makes the uncertainty visible; it does not approve promotion.

Validation:

```bash
python3 -m pytest core/tests/helper/test_pack_provenance.py
python3 -m ruff check \
  core/lexishift_core/helper/pack_provenance.py \
  core/tests/helper/test_pack_provenance.py
python3 -m ruff format --check \
  core/lexishift_core/helper/pack_provenance.py \
  core/tests/helper/test_pack_provenance.py
```

## L6-C Pack Lifecycle Audit Command

Product claim:

- Developers should be able to inspect local pack lifecycle state without
  remembering which directories and manifests to inspect by hand.

Current implementation:

- `scripts/testing/pack_lifecycle_audit.py` emits JSON and Markdown reports.
- The audit inspects installed pack roots under:
  - `<data_root>/language_packs`,
  - `<data_root>/frequency_packs`,
  - `<data_root>/embedding_packs`.
- It checks each installed pack root for `manifest.json`, artifact existence,
  optional `provenance.json`, provenance validity, and unexpected pack-kind
  mismatches.
- It reads `<data_root>/settings.json` and reports manual/external language,
  frequency, embedding, embedding-pair, and legacy secondary-resource paths.
- It classifies app-managed artifacts still stored in manual path settings as
  `migrate_to_managed_pack_id` review items instead of treating them as source
  authority.
- It reports provenance review posture for installed and semantic pack
  sidecars: license status, source pointer kind, raw artifact checksum coverage,
  generated artifact checksum presence, artifact metric-key presence, and
  review reasons.
- It separately inspects semantic pack copies under
  `<data_root>/language_packs/<pair>/semantic_packs/<pack_id>/`.
- It inspects profile publication manifests under
  `<data_root>/srs/profiles/<profile_id>/`.
- It summarizes catalog pack ids from `language_packs_catalog.py`.
- It can inspect optional candidate SQLite files and report tables, primary
  table, row count, columns, and `meta` values.
- Summary status is:
  - `ok` when inspected state has no manifest/artifact/provenance issues,
  - `review` when only provenance sidecars are missing, manual paths need
    review, or schema-valid sidecars still need source/license/checksum review,
  - `error` when manifests, artifacts, provenance contents, publication
    manifests, or candidate SQLite inputs are invalid.
- `--fail-on-error` exits non-zero only for `status = error`.
- `--fail-on-review` exits non-zero unless `status = ok`; this is the strict
  gate for release/promotion checks.

Default command:

```bash
python3 scripts/testing/pack_lifecycle_audit.py \
  --data-root /path/to/LexiShift-data-root \
  --json-out docs/test_outputs/pack_lifecycle_audit_latest.json \
  --markdown-out docs/test_outputs/pack_lifecycle_audit_latest.md
```

Candidate SQLite inspection:

```bash
python3 scripts/testing/pack_lifecycle_audit.py \
  --data-root /path/to/LexiShift-data-root \
  --candidate-db /path/to/candidate.sqlite \
  --json-out docs/test_outputs/pack_lifecycle_audit_candidate.json \
  --markdown-out docs/test_outputs/pack_lifecycle_audit_candidate.md
```

Boundaries:

1. The audit does not create directories, write manifests, or mutate runtime
   state.
2. Missing `provenance.json` is currently `review`, not `error`, because
   existing installs and manual paths may predate sidecar-writing installers.
3. Manual path review findings are currently `review`, not `error`, because
   manual/external paths remain compatibility/import surfaces during migration.
4. Candidate SQLite inspection is intentionally shallow; source-readiness still
   belongs to `semantic_veto_srs_corpus_expansion_audit_en_es.py`.
5. Catalog presence is inventory context, not proof that a pack is installed or
   runtime-active.
6. Valid provenance sidecars can still require review. `requires_review`,
   `unknown`, `internal_only`, missing raw checksums, and missing generated
   artifact checksums are visible review reasons, not silent approval.
7. `--fail-on-review` does not make review decisions for the operator. It only
   turns unresolved review findings into a non-zero process exit.

Validation:

```bash
python3 -m pytest \
  core/tests/dev/test_pack_lifecycle_audit.py \
  core/tests/helper/test_pack_provenance.py
python3 -m ruff check \
  scripts/testing/pack_lifecycle_audit.py \
  scripts/testing/pack_lifecycle_manual_resources.py \
  core/tests/dev/test_pack_lifecycle_audit.py \
  core/lexishift_core/helper/pack_provenance.py \
  core/tests/helper/test_pack_provenance.py
python3 -m ruff format --check \
  scripts/testing/pack_lifecycle_audit.py \
  scripts/testing/pack_lifecycle_manual_resources.py \
  core/tests/dev/test_pack_lifecycle_audit.py \
  core/lexishift_core/helper/pack_provenance.py \
  core/tests/helper/test_pack_provenance.py
```

## L6-Ma Provenance Review Posture

Product claim:

- A valid `provenance.json` proves that the sidecar follows the contract; it
  does not prove that a pack is release-ready, license-approved, or complete
  enough for expansion.

Current implementation:

- `pack_lifecycle_audit.py` adds `provenance_review` to installed pack rows and
  semantic pack-copy rows.
- Family summaries now include `provenance_review_required_count` and
  `license_status_counts`.
- The top-level summary now includes `provenance_review_required_count`.
- The Markdown report has a `Provenance Review` section listing review-required
  packs with family, pack id, license status, source pointer kind, raw checksum
  coverage, generated artifact checksum presence, and review reasons.
- A sidecar with `license_status = "confirmed"`, a checksum for every raw
  artifact, and a generated artifact checksum can remain `ok`.
- A sidecar can be schema-valid but still produce `review` when the source
  license is not confirmed or checksum evidence is incomplete.

Boundaries:

1. This does not rewrite sidecars or installed manifests.
2. This does not approve source licenses.
3. This does not require artifact metrics yet; it reports metric-key presence so
   later candidate promotion gates can tighten family-specific requirements.
4. This does not replace the candidate source-readiness audit for expanded
   Spanish corpus work.

Validation:

```bash
python3 -m pytest core/tests/dev/test_pack_lifecycle_audit.py
python3 -m ruff check \
  scripts/testing/pack_lifecycle_audit.py \
  core/tests/dev/test_pack_lifecycle_audit.py
python3 -m ruff format --check \
  scripts/testing/pack_lifecycle_audit.py \
  core/tests/dev/test_pack_lifecycle_audit.py
```

## L6-Na Strict Lifecycle Review Gate

Product claim:

- The same lifecycle audit should support both ordinary local inspection and a
  strict release/promotion gate.

Current implementation:

- `pack_lifecycle_audit.py --fail-on-review` exits non-zero unless the summary
  status is `ok`.
- Existing `--fail-on-error` behavior remains narrower: it exits non-zero only
  when the summary status is `error`.
- `pack_lifecycle_audit_exit_code(...)` keeps the exit semantics testable
  without shelling out from unit tests.
- The en-es candidate readiness runbook now instructs operators to rerun the
  lifecycle audit with `--fail-on-review` before promotion or release
  packaging.

Boundaries:

1. Strict mode does not mutate data.
2. Strict mode does not approve licenses or sources.
3. Strict mode is not meant for all local development audits; non-strict audit
   output remains useful when a developer is intentionally collecting review
   findings.

Validation:

```bash
python3 -m pytest core/tests/dev/test_pack_lifecycle_audit.py
python3 -m ruff check \
  scripts/testing/pack_lifecycle_audit.py \
  core/tests/dev/test_pack_lifecycle_audit.py
python3 -m ruff format --check \
  scripts/testing/pack_lifecycle_audit.py \
  core/tests/dev/test_pack_lifecycle_audit.py
```

## L6-D Semantic Pack Provenance And Lineage

Product claim:

- A semantic pack copy should be able to explain which source inventory it came
  from and provide a sidecar provenance record that the lifecycle audit can
  validate.

Current implementation:

- `core/lexishift_core/helper/semantic_pack_provenance.py` builds semantic pack
  lineage and sidecar provenance payloads.
- `install_semantic_pack(..., copy_pack=True)` now writes
  `<data_root>/language_packs/<pair>/semantic_packs/<pack_id>/provenance.json`.
- The existing semantic pack `manifest.json` keeps `source_path`,
  `raw_inventory_sha1`, and `normalized_inventory_sha1`, and now also includes:
  - `lineage`,
  - `artifacts.provenance`.
- The install report now includes `source.source_pack_provenance_path`.
- The lineage block records:
  - source inventory path,
  - source inventory SHA-1,
  - source inventory `generated_at` and `generation_id` when present,
  - source inventory pair/profile when present,
  - normalized inventory SHA-1,
  - trigger, sense, competition-set, and phrase-set counts.
- The sidecar uses the L6-B `provenance.json` contract with
  `pack_kind = "semantic_inventory_pack"` and
  `artifact_kind = "semantic_inventory"`.

Boundaries:

1. Existing source inventories, including the current tranche dev inventory, do
   not always carry upstream source-batch ids or release-manifest ids. L6-D
   records absent fields as empty rather than inventing them.
2. L6-Ja now lets profile publication manifests carry semantic source lineage
   when the publisher provides it.
3. `copy_pack=False` does not rewrite an existing installed semantic pack copy.
4. This does not promote any semantic pack to a release channel.

Validation:

```bash
python3 -m pytest \
  core/tests/helper/test_semantic_pack_install.py \
  core/tests/helper/test_pack_provenance.py \
  core/tests/dev/test_pack_lifecycle_audit.py
python3 -m ruff check \
  core/lexishift_core/helper/semantic_pack_provenance.py \
  core/lexishift_core/helper/use_cases/semantic_pack_install.py \
  core/tests/helper/test_semantic_pack_install.py
python3 -m ruff format --check \
  core/lexishift_core/helper/semantic_pack_provenance.py \
  core/lexishift_core/helper/use_cases/semantic_pack_install.py \
  core/tests/helper/test_semantic_pack_install.py
```

## L6-E En-es Candidate Readiness Runbook

Product claim:

- A future Spanish corpus candidate should have a repeatable readiness sequence
  before it can affect defaults, denominator claims, or generation spend.

Current implementation:

- `../rulegen/semantic_veto_srs_corpus_candidate_readiness_runbook.md` now
  provides the operator runbook.
- The runbook sequences:
  1. pack lifecycle audit,
  2. source-readiness audit,
  3. SRS Zipf bridge with full rulegen,
  4. denominator audit,
  5. canonical doc updates before generation.
- It records stop conditions for missing license/source status, missing
  rank/frequency ordering, missing POS coverage, missing topic/domain metadata
  for personalization claims, candidate size shortfalls, and accidental
  `freq-es-cde` overwrite risk.
- It includes a next-agent handoff template so candidate work can resume without
  reconstructing the sequence from chat.

Boundaries:

1. The runbook does not choose a source.
2. It does not make a runtime default change.
3. It does not replace the source-readiness audit, SRS bridge, or denominator
   audit.
4. It does not permit paid generation before the expanded denominator is
   understood.

## L6-F App-Managed Non-Semantic Pack Provenance

Product claim:

- App-managed translation, frequency, and embedding pack installs should leave
  enough sidecar provenance for the lifecycle audit to distinguish managed
  artifacts from legacy/manual inference.

Current implementation:

- `write_app_managed_pack_provenance(...)` builds and atomically writes
  `<pack_root>/provenance.json` using the L6-B contract.
- `LanguagePackDownloadThread._write_manifest(...)` writes sidecars for
  app-managed translation dictionary installs, including FreeDict and Kaikki
  SQLite build outputs.
- `FrequencyPackDownloadThread._write_manifest(...)` writes sidecars for
  app-managed frequency pack installs.
- `LanguagePackPanelTransferMixin._finalize_embedding_pack(...)` writes
  sidecars when an app-managed embedding pack is finalized as an app-data
  SQLite artifact.
- The first implementation keeps `license_status = "requires_review"` by
  default. That is deliberate: it records uncertainty instead of silently
  treating catalog URLs as redistribution approval.
- The sidecar records source name, source URL, Wayback URL when present, source
  filename, build mode, SQLite filename when present, generated artifact
  relpath/kind, and generated artifact SHA-1 for file artifacts.

Boundaries:

1. Existing installed packs need reinstall or the L6-Ka backfill command to
   gain sidecars.
2. Manual paths, legacy fallback files, raw vector inputs, and compatibility
   lookup paths remain outside first-class provenance until an import/backfill
   implementation writes managed pack records for them.
3. Raw source checksums are not available after the current cleanup paths remove
   archives; the sidecar records filenames but does not invent raw checksums.
4. License review remains separate from installer writing. The sidecar makes
   review status explicit; it does not approve source usage.
5. Generated SQLite schema, row counts, POS coverage, and topic/domain coverage
   remain audit outputs, not installer-written manifest fields.

Validation:

```bash
python3 -m pytest \
  core/tests/helper/test_pack_provenance.py \
  apps/gui/tests/test_pack_provenance_sidecars.py
python3 -m ruff check \
  core/lexishift_core/helper/pack_provenance.py \
  apps/gui/src/language_packs.py \
  apps/gui/src/settings_language_packs_transfer_mixin.py \
  core/tests/helper/test_pack_provenance.py \
  apps/gui/tests/test_pack_provenance_sidecars.py
python3 -m ruff format --check \
  core/lexishift_core/helper/pack_provenance.py \
  apps/gui/src/language_packs.py \
  apps/gui/src/settings_language_packs_transfer_mixin.py \
  core/tests/helper/test_pack_provenance.py \
  apps/gui/tests/test_pack_provenance_sidecars.py
```

## L6-Ka Existing Install Provenance Backfill

Product claim:

- Existing app-managed installs that predate sidecar-writing installers should
  be able to gain conservative `provenance.json` sidecars without reinstalling
  packs or inferring license approval.

Current implementation:

- `scripts/testing/pack_lifecycle_provenance_backfill.py` is dry-run by default
  and emits JSON/Markdown reports.
- `--apply` writes missing `provenance.json` sidecars only for installed pack
  roots that have:
  - a valid installed `manifest.json`,
  - a catalog entry for the pack id,
  - an existing generated/downloaded artifact.
- The command scans:
  - `<data_root>/language_packs/<pack_id>/`,
  - `<data_root>/frequency_packs/<pack_id>/`,
  - `<data_root>/embedding_packs/<pack_id>/`.
- It reuses `write_app_managed_pack_provenance(...)`, so the sidecars match the
  installer-written contract and keep `license_status = "requires_review"`.
- Existing valid sidecars are left alone.
- Existing invalid sidecars are reported and not overwritten by this first
  backfill slice.

Default dry-run command:

```bash
python3 scripts/testing/pack_lifecycle_provenance_backfill.py \
  --data-root /path/to/LexiShift-data-root \
  --json-out docs/test_outputs/pack_lifecycle_provenance_backfill_latest.json \
  --markdown-out docs/test_outputs/pack_lifecycle_provenance_backfill_latest.md
```

Apply command:

```bash
python3 scripts/testing/pack_lifecycle_provenance_backfill.py \
  --data-root /path/to/LexiShift-data-root \
  --apply \
  --json-out docs/test_outputs/pack_lifecycle_provenance_backfill_latest.json \
  --markdown-out docs/test_outputs/pack_lifecycle_provenance_backfill_latest.md
```

Boundaries:

1. This does not rewrite installed manifests.
2. This does not approve source licenses or invent raw source checksums.
3. This does not backfill manual/external resources.
4. This does not overwrite invalid existing provenance sidecars; those remain
   review items.

Validation:

```bash
python3 -m pytest \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py \
  core/tests/dev/test_pack_lifecycle_audit.py \
  core/tests/helper/test_pack_provenance.py
python3 -m ruff check \
  scripts/testing/pack_lifecycle_provenance_backfill.py \
  scripts/testing/pack_lifecycle_audit.py \
  core/lexishift_core/helper/pack_provenance.py \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py
python3 -m ruff format --check \
  scripts/testing/pack_lifecycle_provenance_backfill.py \
  scripts/testing/pack_lifecycle_audit.py \
  core/lexishift_core/helper/pack_provenance.py \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py
```

## L6-G Manual Resource Settings Disposition Audit

Product claim:

- Manual/external resource settings should remain explicit compatibility inputs
  during migration, not hidden source-of-truth paths that look equivalent to
  app-managed pack ids.

Current implementation:

- `pack_lifecycle_audit.py` now includes `manual_resource_settings` in its JSON
  report and a `Manual Resource Settings` section in Markdown.
- The audit reads `<data_root>/settings.json` and reports:
  - `language_pack_paths`,
  - `frequency_pack_paths`,
  - `embedding_pack_paths`,
  - `embedding_pair_paths`,
  - legacy secondary aliases `wordnet_dir` and `moby_path`.
- It also reports managed id fields for context:
  - `managed_language_pack_ids`,
  - `managed_frequency_pack_ids`,
  - `embedding_pair_pack_ids`.
- Each manual row records the owning field, family, key, resolved path,
  existence, expected artifact format, format support, disposition, managed pack
  root when detected, and issues.
- Missing manual paths and app-managed artifacts stored in manual settings are
  `review` findings.
- Unsupported existing manual artifact shapes are also `review` findings.
- An app-managed artifact under a pack root with `manifest.json` receives
  disposition `migrate_to_managed_pack_id`.

Disposition policy:

1. Keep manual/external language, frequency, and embedding paths as
   compatibility/import surfaces for now.
2. Keep `wordnet_dir` and `moby_path` as legacy secondary-resource aliases
   while the shared `language_pack_paths` binding remains the effective source.
3. Treat app-managed artifact paths found in manual maps as migration
   candidates, not as the steady-state contract.
4. Treat missing manual paths as review findings. They indicate stale local
   state, but they are not pack-install errors.
5. Do not infer source/license provenance from a manual path. Manual source
   approval still requires an explicit future import/backfill contract.

Boundaries:

1. This slice does not rewrite settings or delete manual support.
2. It does not decide final phase-out for any manual path family.
3. It does not add provenance sidecars to manual/external resources.
4. It does not inspect every possible runtime fallback filename; it audits the
   saved settings surface that can carry user/manual paths across sessions.

Validation:

```bash
python3 -m pytest core/tests/dev/test_pack_lifecycle_audit.py
python3 -m ruff check \
  scripts/testing/pack_lifecycle_audit.py \
  scripts/testing/pack_lifecycle_manual_resources.py \
  core/tests/dev/test_pack_lifecycle_audit.py
python3 -m ruff format --check \
  scripts/testing/pack_lifecycle_audit.py \
  scripts/testing/pack_lifecycle_manual_resources.py \
  core/tests/dev/test_pack_lifecycle_audit.py
```

## L6-H Constrained Manual Import/Backfill Contract

Product claim:

- External pack selection exists because some licenses or distribution models
  require the user/operator to acquire a resource manually, not because
  LexiShift can safely consume arbitrary files.

Current implementation:

- The lifecycle audit now records an `expected_format` and `format_supported`
  value for saved manual resource paths.
- Existing manual paths with unsupported artifact shapes receive
  `unsupported_manual_artifact_format` review findings.
- Frequency manual paths are expected to be SQLite databases with a
  `frequency` table.
- Embedding manual paths are expected to be SQLite embedding databases or
  `.vec` / `.txt` / `.bin` vector files.
- Language manual paths remain limited to SQLite, TEI/XML, pack-specific text
  resources, or directories for pack-specific required-file workflows.
- The embedding picker no longer offers an all-files filter and now rejects
  unsupported manual file types even when the OS lets a path through.

UX policy:

1. Normal users should see installed/app-managed packs as the preferred path.
2. External selection should be labeled as manual compatibility/import, not as
   a general pack-install path.
3. External selection should be narrow and format-gated because runtime loaders
   expect exact schemas or vector formats.
4. License-restricted sources should use manual acquisition followed by a
   constrained link/import step.
5. A future first-class import flow should copy or convert an approved external
   artifact into an app-managed pack root, then write `manifest.json` and
   `provenance.json`.

Backfill policy:

1. If a saved manual path points inside an app-managed pack root with
   `manifest.json`, migrate it to managed pack-id state.
2. If a saved manual path points to an external file with a supported exact
   format, keep it manual until the user/operator chooses import.
3. If a saved manual path is missing, report review and leave cleanup to the
   user/operator; do not treat it as an installed-pack error.
4. If a saved manual path exists but has an unsupported format, reject it in UX
   paths where possible and report it in lifecycle audit.
5. Do not mark a manual path expansion-ready without an explicit source/license
   review and provenance/import record.

Boundaries:

1. This slice does not remove existing manual compatibility support.
2. It does not implement a full import wizard or external-artifact migration.
3. It does not prove license eligibility for manually acquired sources.
4. It does not convert valid external files into app-owned packs automatically.

Validation:

```bash
python3 -m pytest \
  core/tests/dev/test_pack_lifecycle_audit.py \
  apps/gui/tests/test_language_pack_table_mixin.py
python3 -m ruff check \
  scripts/testing/pack_lifecycle_audit.py \
  scripts/testing/pack_lifecycle_manual_resources.py \
  core/tests/dev/test_pack_lifecycle_audit.py \
  apps/gui/src/settings_language_packs.py \
  apps/gui/tests/test_language_pack_table_mixin.py
python3 -m ruff format --check \
  scripts/testing/pack_lifecycle_audit.py \
  scripts/testing/pack_lifecycle_manual_resources.py \
  core/tests/dev/test_pack_lifecycle_audit.py \
  apps/gui/src/settings_language_packs.py \
  apps/gui/tests/test_language_pack_table_mixin.py
```

## L6-La External Manual Import Plan

Product claim:

- When a source cannot be installed automatically, the operator should still get
  a precise, auditable preflight result before LexiShift links, copies, converts,
  or promotes the manually acquired artifact.

Current implementation:

- `scripts/testing/pack_lifecycle_external_import_plan.py` is read-only and
  emits JSON/Markdown reports.
- The command takes `--family`, `--pack-id`, `--path`, and optional source,
  license, and checksum fields.
- It reuses the same `manual_path_format_support(...)` classifier as the saved
  manual-settings audit, so external preflight and persisted settings review
  agree on the exact allowed artifact shapes.
- It reports:
  - path existence,
  - expected format,
  - whether a manual link is allowed,
  - whether an explicit operator import could proceed later,
  - missing source/license/checksum review fields,
  - a provenance sidecar preview,
  - and fixed boundaries showing that no mutation occurred.
- Manual linking can be format-safe even when `license_status` is
  `requires_review`, `unknown`, `internal_only`, or `not_redistributable`. That
  keeps license-restricted manual acquisition possible without pretending the
  artifact is expansion-ready.
- Promotion/import preflight is only `ok` when the path is supported, provenance
  preview validates, the license status is `confirmed`, and at least one raw
  artifact checksum is supplied.

Default command:

```bash
python3 scripts/testing/pack_lifecycle_external_import_plan.py \
  --family frequency \
  --pack-id freq-es-manual \
  --path /path/to/manual-frequency.sqlite \
  --source-name "Manual Spanish frequency source" \
  --license-status requires_review \
  --json-out docs/test_outputs/pack_lifecycle_external_import_plan_latest.json \
  --markdown-out docs/test_outputs/pack_lifecycle_external_import_plan_latest.md
```

Boundaries:

1. This does not copy or convert external artifacts.
2. This does not rewrite settings, manifests, or provenance sidecars.
3. This does not approve a source license.
4. This does not change runtime defaults or pack selection.
5. This is an executable contract for the future UX/import decision, not the
   import wizard itself.

Validation:

```bash
python3 -m pytest \
  core/tests/dev/test_pack_lifecycle_external_import_plan.py \
  core/tests/dev/test_pack_lifecycle_audit.py
python3 -m ruff check \
  scripts/testing/pack_lifecycle_external_import_plan.py \
  scripts/testing/pack_lifecycle_manual_resources.py \
  core/tests/dev/test_pack_lifecycle_external_import_plan.py
python3 -m ruff format --check \
  scripts/testing/pack_lifecycle_external_import_plan.py \
  scripts/testing/pack_lifecycle_manual_resources.py \
  core/tests/dev/test_pack_lifecycle_external_import_plan.py
```

## L6-Ia Safe Manual Settings Backfill

Product claim:

- Manual settings that already point at app-managed pack artifacts should be
  migrated to managed pack-id state without treating external files as trusted
  managed packs.

Current implementation:

- `scripts/testing/pack_lifecycle_manual_backfill.py` is dry-run by default and
  writes JSON/Markdown evidence for every proposed settings change.
- `--apply` rewrites `<data_root>/settings.json` and creates
  `settings.json.bak` unless `--no-backup` is supplied.
- The backfill migrates only manifest-backed app-managed SQLite artifacts under:
  - `<data_root>/language_packs/<pack_id>/`,
  - `<data_root>/frequency_packs/<pack_id>/`,
  - `<data_root>/embedding_packs/<pack_id>/`.
- Language and frequency manual maps are migrated to
  `managed_language_pack_ids` and `managed_frequency_pack_ids`.
- Embedding manual maps and pair paths are migrated to
  `embedding_pair_pack_ids` only when the catalog has an exact pair key for the
  managed embedding pack id.
- External supported files, missing paths, unsupported paths, and legacy
  secondary aliases such as `wordnet_dir` and `moby_path` remain manual/audit
  surfaces.

Default dry-run command:

```bash
python3 scripts/testing/pack_lifecycle_manual_backfill.py \
  --data-root /path/to/LexiShift-data-root \
  --json-out docs/test_outputs/pack_lifecycle_manual_backfill_latest.json \
  --markdown-out docs/test_outputs/pack_lifecycle_manual_backfill_latest.md
```

Apply command:

```bash
python3 scripts/testing/pack_lifecycle_manual_backfill.py \
  --data-root /path/to/LexiShift-data-root \
  --apply \
  --json-out docs/test_outputs/pack_lifecycle_manual_backfill_latest.json \
  --markdown-out docs/test_outputs/pack_lifecycle_manual_backfill_latest.md
```

Boundaries:

1. This is not a broad import wizard.
2. It does not copy, convert, or approve manually acquired external files.
3. It does not write provenance sidecars for existing installs.
4. It intentionally leaves secondary lexical compatibility aliases manual until
   those families have their own managed-pack decision.

Validation:

```bash
python3 -m pytest \
  core/tests/dev/test_pack_lifecycle_manual_backfill.py \
  core/tests/dev/test_pack_lifecycle_audit.py
python3 -m ruff check \
  scripts/testing/pack_lifecycle_manual_backfill.py \
  scripts/testing/pack_lifecycle_audit.py \
  scripts/testing/pack_lifecycle_manual_resources.py \
  core/tests/dev/test_pack_lifecycle_manual_backfill.py \
  core/tests/dev/test_pack_lifecycle_audit.py
python3 -m ruff format --check \
  scripts/testing/pack_lifecycle_manual_backfill.py \
  scripts/testing/pack_lifecycle_audit.py \
  scripts/testing/pack_lifecycle_manual_resources.py \
  core/tests/dev/test_pack_lifecycle_manual_backfill.py \
  core/tests/dev/test_pack_lifecycle_audit.py
```

## L6-Ja Semantic Source-Lineage Publication

Product claim:

- Runtime publication manifests should be able to point back to the semantic
  pack/source lineage that produced the published ruleset family, without
  changing runtime scoring policy or treating the publication manifest as a
  license approval record.

Current implementation:

- `write_rulegen_outputs(...)` accepts optional `source_lineage` metadata and
  copies it into `srs_publication_manifest_<pair>.json`.
- `install_semantic_pack(...)` builds semantic source lineage from the source
  inventory and passes it into the publication manifest.
- Installed semantic pack manifest lineage now preserves nested source inventory
  lineage and source batches when the source inventory carries them.
- `semantic_veto_active_only_full_pack_builder_en_es.py` writes a first
  builder-level lineage block into generated semantic inventories and records
  component/source batches in the combined normalized batch.
- `pack_lifecycle_audit.py` reports publication-manifest source-lineage
  presence, pack id, and source-batch count.

Boundaries:

1. This does not change rule generation, semantic admission, or runtime scoring.
2. This does not approve source licenses or replace source-readiness review.
3. Existing generated publication manifests need reinstall/regeneration before
   they carry the new optional lineage field.
4. Release manifest identity, converter versions, and final review/approval
   lineage remain queued for later L6-J work.

Validation:

```bash
python3 -m pytest \
  core/tests/helper/test_rulegen_outputs.py \
  core/tests/helper/test_semantic_pack_install.py \
  core/tests/dev/test_semantic_veto_active_only_full_pack_builder_en_es.py \
  core/tests/dev/test_pack_lifecycle_audit.py
python3 scripts/testing/srs_quality_harness.py \
  --json-out docs/test_outputs/srs_quality_latest.json
python3 -m ruff check \
  core/lexishift_core/helper/rulegen_outputs.py \
  core/lexishift_core/helper/semantic_pack_provenance.py \
  core/lexishift_core/helper/use_cases/semantic_pack_install.py \
  scripts/testing/semantic_veto_active_only_full_pack_builder_en_es.py \
  scripts/testing/pack_lifecycle_audit.py
python3 -m ruff format --check \
  core/lexishift_core/helper/rulegen_outputs.py \
  core/lexishift_core/helper/semantic_pack_provenance.py \
  core/lexishift_core/helper/use_cases/semantic_pack_install.py \
  scripts/testing/semantic_veto_active_only_full_pack_builder_en_es.py \
  scripts/testing/pack_lifecycle_audit.py
```

## Planned Lane 6 Slices

| Slice | Goal | First Output |
| --- | --- | --- |
| L6-B Pack provenance contract | Initial sidecar validator completed; future work should wire installers/audits to it. | `pack_provenance.py` and focused validator tests. |
| L6-C Pack lifecycle audit command | Initial read-only audit completed; future work should wire sidecar production and richer source-readiness checks. | `pack_lifecycle_audit.py` with JSON/Markdown output and focused tests. |
| L6-D Semantic generation lineage | Initial semantic pack sidecar and manifest lineage completed; upstream source batches are now preserved when source inventories carry them. | `semantic_pack_provenance.py`, installer wiring, and focused install tests. |
| L6-E En-es expansion candidate runbook | Completed as an operational runbook; future work should use it on the first real candidate. | `semantic_veto_srs_corpus_candidate_readiness_runbook.md`. |
| L6-F App-managed non-semantic installer provenance | Completed first installer-write slice for translation, frequency, and embedding managed installs. | `write_app_managed_pack_provenance(...)`, GUI installer/finalization wiring, and focused sidecar tests. |
| L6-K Existing install provenance backfill | Completed first safe sidecar backfill for catalog-backed app-managed installs that have manifests and artifacts but lack `provenance.json`. | `pack_lifecycle_provenance_backfill.py`, focused dry-run/apply tests. |
| L6-G Manual path disposition audit | Completed first audit/report slice for saved manual resource settings; future work should choose final phase-out/backfill policy per family. | `manual_resource_settings` in `pack_lifecycle_audit.py`, Markdown report section, and focused tests. |
| L6-H Constrained manual import/backfill contract | Completed first policy and enforcement slice: external selection is a narrow license/import fallback for exact supported artifact shapes. | Audit format checks, embedding picker validation/filter tightening, contract docs, and focused tests. |
| L6-I Import/backfill implementation | Safe managed-artifact settings backfill is now implemented; future work should add a first-class external import flow only after source/license decisions are explicit. | `pack_lifecycle_manual_backfill.py`, focused tests, and future provenance sidecar writing for imported resources. |
| L6-J Source-batch and release lineage | Initial semantic source-lineage propagation is implemented; future work should add release-manifest, converter-version, and approval/review lineage once upstream inventories and pack candidates carry those ids. | Publication `source_lineage`, updated semantic/source manifests, lifecycle audit fields, and candidate audit evidence. |
| L6-L External/manual import preflight | Completed first read-only executable import plan so manually acquired sources can be format-gated and review-gated before any UX/import mutation. | `pack_lifecycle_external_import_plan.py`, focused tests, and documented command contract. |
| L6-M Provenance review posture | Completed first lifecycle-audit reporting slice that distinguishes schema-valid sidecars from release/promotion readiness. | `provenance_review` audit fields, summary counts, Markdown review table, and focused tests. |
| L6-N Strict lifecycle review gate | Completed first strict audit gate for promotion/release checks without changing default local-audit behavior. | `--fail-on-review`, exit-code helper, candidate runbook update, and focused tests. |

## Validation Bundle For L6-A

This slice is docs-only inventory work. Minimum validation:

```bash
python3 scripts/dev/check_doc_references.py
git diff --check
npm --prefix scripts run check:changed:staged
```

Run `npm --prefix scripts run check:state` only when a later Lane 6 slice
changes `feature_state_matrix.md`, default behavior, evidence paths, or status
claims.
