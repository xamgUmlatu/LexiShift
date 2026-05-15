# Productization Lane 6 Data Provenance And Pack Lifecycle Inventory

Status: active inventory
Role: Planning / WIP
Last updated: 2026-05-16
Last verified: 2026-05-16 read-only inspection of pack catalogs, source-manifest cache policy, installed-pack manifests, helper pack resolvers, semantic-pack installation/publication code, semantic data-lifecycle docs, en-es corpus-expansion audit plan, en-es candidate readiness runbook, focused pack-provenance validator tests, focused pack-lifecycle audit tests, semantic-pack provenance install tests, app-managed non-semantic pack sidecar tests, manual resource settings audit tests, constrained manual embedding selection tests, safe manual-settings backfill tests, source-lineage publication tests, existing-install provenance backfill tests, external import plan tests, provenance review posture tests, strict lifecycle gate tests, promotion evidence bundle tests, app-managed build/parser lineage tests, app-managed raw artifact checksum tests, app-managed converter source digest tests, source-identity classification tests, safe source-identity writer/backfill tests, dated Kaikki source-dump policy tests, source-bundle lineage tests, embedding/manual checksum lineage tests, frequency SQLite metric sidecar tests, source-bundle checksum coverage tests, generated DE component checksum capture tests, executable provenance policy tests, source-bundle pinning policy tests, source-policy decision queue tests, source-identity policy category tests, explicit dated Wiktextract source-dump seam tests, and the SRS quality harness
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
- `../../core/lexishift_core/helper/pack_artifact_metrics.py`
- `../../core/lexishift_core/helper/pack_provenance.py`
- `../../core/lexishift_core/helper/pack_source_identity.py`
- `../../core/lexishift_core/helper/rulegen_outputs.py`
- `../../core/lexishift_core/helper/semantic_pack_provenance.py`
- `../../core/lexishift_core/helper/use_cases/semantic_pack_install.py`
- `../../scripts/testing/pack_lifecycle_audit.py`
- `../../scripts/testing/pack_lifecycle_external_import_plan.py`
- `../../scripts/testing/pack_lifecycle_manual_backfill.py`
- `../../scripts/testing/pack_lifecycle_manual_resources.py`
- `../../scripts/testing/pack_lifecycle_policy.py`
- `../../scripts/testing/pack_lifecycle_provenance_lineage.py`
- `../../scripts/testing/pack_lifecycle_provenance_backfill.py`
- `../../scripts/testing/pack_lifecycle_promotion_evidence.py`
- `../../scripts/testing/pack_lifecycle_source_identity_plan.py`
- `../../scripts/testing/pack_lifecycle_source_policy_decisions.py`
- `../../core/tests/helper/test_pack_artifact_metrics.py`
- `../../core/tests/helper/test_pack_source_identity.py`
- `../../core/tests/helper/test_pack_provenance.py`
- `../../core/tests/dev/test_pack_lifecycle_audit.py`
- `../../core/tests/dev/test_pack_lifecycle_external_import_plan.py`
- `../../core/tests/dev/test_pack_lifecycle_manual_backfill.py`
- `../../core/tests/dev/test_pack_lifecycle_policy.py`
- `../../core/tests/dev/test_pack_lifecycle_provenance_backfill.py`
- `../../core/tests/dev/test_pack_lifecycle_promotion_evidence.py`
- `../../core/tests/dev/test_pack_lifecycle_source_identity_plan.py`
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
15. L6-Oa: promotion evidence bundle contract.
16. L6-Pa: app-managed build/parser lineage.
17. L6-Qa: app-managed raw artifact checksums for source files available during
    install/conversion.
18. L6-Ra: app-managed converter source digests.
19. L6-Sa: catalog source-identity classification surface.
20. L6-Ta: safe source-version writer/backfill for classified catalog rows.
21. L6-Ua: dated Kaikki source-dump write gate.
22. L6-Va: source-bundle lineage for generated DE frequency output.
23. L6-Wa: embedding/manual checksum lineage.
24. L6-Xa: frequency SQLite artifact metrics.
25. L6-Ya: source-bundle component checksum coverage reporting.
26. L6-Za: generated DE pipeline source-bundle component checksum capture.
27. L6-Zb: executable provenance promotion policy.
28. L6-Zc: source-bundle promotion pinning policy.
29. L6-Zd: source-policy decision queue.
30. L6-Ze: source-identity policy category taxonomy.
31. L6-Zf: explicit dated Wiktextract source-dump seam.

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
| Provenance sidecar | `core/lexishift_core/helper/pack_provenance.py`, `<pack_root>/provenance.json` | Versioned contract for source identity, license status, source pointer, raw artifact checksums, build mode, generated artifact identity, optional build/parser lineage, optional source-bundle component checksums, and optional SQLite metrics; semantic installs and app-managed translation/frequency/embedding installs now write conservative sidecars. | Legacy installs, manual paths, embedding raw-source checksums, source-version identity, release/package-version identity, and approved license status still need follow-up lifecycle work. |
| Lifecycle audit | `scripts/testing/pack_lifecycle_audit.py` | Read-only JSON/Markdown audit of installed pack manifests, optional provenance sidecars, semantic pack copies, profile publication manifests, manual resource settings, catalog pack ids, and optional candidate SQLite metadata. | It does not backfill provenance sidecars, rewrite settings, prove licenses, replace the source-readiness audit, or promote packs. |
| Pack refs/resolvers | `frequency_packs.py`, `translation_packs.py`, `embedding_packs.py`, `pair_resources.py`, `lp_capabilities.py` | Runtime-facing pack id, provider, source/POS profile, resolved path, and managed-vs-fallback resolution. | Full provenance for manual paths or legacy fallback files. |
| Semantic pack copy | `<data_root>/language_packs/<pair>/semantic_packs/<pack_id>/manifest.json` and `provenance.json` from `semantic_pack_install.py` | Semantic pack id/pair, generated timestamp, source path, raw/normalized inventory hashes, source inventory generation fields when present, source batches when carried by the source inventory, installed semantic inventory artifact hash/bytes, and validated sidecar provenance. | Release manifest identity, approved review state, or why the compiled generation was selected. |
| Profile publication manifest | `<data_root>/srs/profiles/<profile_id>/srs_publication_manifest_<pair>.json` from `rulegen_outputs.py` | Ruleset/snapshot/semantic inventory family identity, `generation_id`, artifact hashes/bytes, family-valid flag, and optional semantic source lineage when the publisher provides it. | It is still a runtime publication manifest, not the source manifest or license approval record. |
| Generated evidence | `docs/test_outputs/` audit, benchmark, and experiment artifacts | Evidence from the command that produced the artifact. | Architecture authority or current runtime truth without a source/code/test pointer. |

## Resource Family State

| Family | Current Managed Shape | Current Provenance | Main Lane 6 Gap |
| --- | --- | --- | --- |
| Translation dictionaries | App-managed FreeDict and Kaikki installs build to SQLite under a pack-id root and write `manifest.json`; helper resolution is pack-id-first with legacy filename fallbacks. | Catalog has source/provider URL fields; installed manifest has provider, build mode, artifact relpath, source filename, sqlite filename, and installed timestamp. App-managed installs now also write `provenance.json` with source URL, Wayback URL when present, conservative `requires_review` license status, build mode, build command, parser config when applicable, converter source SHA-256 digest, source filename, SQLite filename, generated artifact relpath/kind, generated artifact SHA-1, and downloaded raw artifact SHA-1/SHA-256 for new installs. | Existing installs need reinstall/backfill, source license approval is not encoded, schema/row-count records are still audit outputs, and manual/legacy fallback paths still depend on inference. |
| Frequency packs | App-managed frequency installs build to SQLite under a pack-id root and write `manifest.json`; runtime diagnostics expose frequency pack id/provider/POS profile. | Catalog plus installed manifest identify provider/build mode/source filename and the generated artifact path. App-managed installs now also write `provenance.json` with source URL, Wayback URL when present, conservative license status, build mode, build command, parser config/POS-inventory config when applicable, converter source SHA-256 digest, source filename, SQLite filename, artifact relpath/kind, generated artifact SHA-1, parsed raw-source SHA-1/SHA-256 for new downloaded-source conversions, available source-bundle component SHA-1/SHA-256 for generated DE pipeline inputs present during install, and frequency SQLite metrics (`row_count`, `distinct_lemma_count`, `pos_rows`, `topic_domain_rows`) when the artifact is readable during install or sidecar backfill. | Approved source/license status, source version, complete generated-pipeline component coverage for reused/missing inputs, full schema detail, and promotion-ready audit artifacts are still outside installer-written provenance. Spanish expansion candidates need versioned pack ids and audit artifacts before promotion. |
| Embedding packs | App-managed embeddings use pack-id roots, manifest-backed artifacts, and embedding pack refs; manual/raw paths remain compatibility inputs. | Installed manifest records provider, build mode, source filename, sqlite filename, and artifact path. App-managed SQLite finalization now also writes `provenance.json` with source URL, Wayback URL when present, conservative license status, build mode, embedding converter command, converter source SHA-256 digest when the script is available, source filename, SQLite filename, artifact relpath/kind, generated artifact SHA-1, and raw vector SHA-1/SHA-256 when the app-managed conversion source is still available during finalization. External import preflight also computes file checksums for supported manual paths before any mutation. | License approval, source version/release identity, raw vector retention, conversion parameters, directory checksums, existing-install backfill checksums, and manual/raw-path sidecar writing remain outside first-class lifecycle coverage. |
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
7. run the promotion evidence bundle before product testing, release packaging,
   default promotion, or paid generation,
8. do not launch paid semantic-veto generation until the expanded rulegen
   denominator separates covered, uncovered, weak, and no-visible families,
9. update this inventory, the corpus-expansion plan, and the denominator doc
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
18. `pack_lifecycle_promotion_evidence.py` now makes the promotion evidence
    bundle executable by checking lifecycle, source-readiness, SRS Zipf bridge,
    and denominator artifacts together before promotion.
19. App-managed sidecar writing and existing-install sidecar backfill now record
    build command and parser config when the catalog/installer already knows
    those values, and the lifecycle audit reports source/build lineage presence.
20. New app-managed translation downloads and frequency conversions now hash the
    available raw/downloaded or parsed source before cleanup and write raw
    artifact SHA-1/SHA-256 into `provenance.json`.
21. New app-managed sidecars and safe existing-install backfill now record a
    `build.converter_version` source digest for known converter modules/scripts
    when no package-level version exists.
22. `pack_lifecycle_source_identity_plan.py` now provides a read-only
    classification surface for catalog source-version/source-dump candidates:
    currently `8` safe-to-write candidates, `2` label-only cases, `16`
    policy-needed cases, and `1` source-bundle case.
23. App-managed sidecar writing and existing-install sidecar backfill now use
    the shared source-identity classifier to write durable
    `source.source_version` only for `safe_to_write` catalog rows. `label_only`,
    `needs_policy`, and `source_bundle_needed` rows are withheld from sidecar
    source identity; generated pipeline rows are handled through
    `source.source_bundle` instead of pretending a single source-version field
    exists.
24. The shared source-identity classifier now distinguishes a Kaikki dump family
    label from a durable dated dump identity: `enwiktionary` alone stays
    `needs_policy`, while a dated identity such as `enwiktionary:YYYY-MM-DD` is
    eligible for the same safe sidecar writer.
25. App-managed sidecar writing and existing-install sidecar backfill now record
    `source.source_bundle` for the German generated frequency pipeline,
    capturing component URL lineage for the Leipzig corpus,
    FreeDict/OdeNet/OpenThesaurus whitelist inputs, german-pos-dict POS inputs,
    and Morfologik tooling inputs.
26. App-managed frequency sidecar writing and safe existing-install sidecar
    backfill now write frequency SQLite metrics under `artifact.metrics` when
    the generated artifact is readable: row count, distinct non-empty lemmas,
    rows with POS, and rows with topic/domain metadata.
27. Source-bundle component checksums are now schema-validated when present, and
    lifecycle lineage reports component checksum coverage separately from source
    URL/component-count lineage.
28. New app-managed generated DE frequency installs now compute source-bundle
    component checksums for pipeline input files that are present before the
    temporary build workspace is cleaned up.
29. Provenance promotion policy is now executable: `pack_lifecycle_policy.py`
    returns a versioned policy verdict, `pack_lifecycle_audit.py` includes it in
    pack rows, and promotion evidence checks require the policy verdict to be
    ready.
30. Source-bundle promotion policy now treats URL-recorded but unpinned bundles
    as review findings. `component_urls_recorded` lineage remains valid
    provenance, but promotion needs an explicit pinned lineage status such as
    `pinned_snapshot` or `pinned_component_artifacts`.
31. The lifecycle audit now emits a read-only source-policy decision queue that
    groups non-ready provenance checks into concrete follow-up categories and
    recommended actions, such as license review, source identity, raw/generated
    checksums, source-bundle checksum coverage, source-bundle pinning, and
    frequency metrics.
32. The source-identity plan now groups catalog rows by source-policy category,
    so the remaining `19` non-safe rows are no longer a flat queue: `3`
    dated-Wiktextract dump-pinning rows, `8` fastText release/snapshot policy
    rows, `2` branch-source pinning rows, `3` release/snapshot policy rows, `2`
    source-label policy rows, and `1` source-bundle lineage policy row.
33. Catalog-like language packs can now carry an explicit `source_dump` value.
    The shared source-identity classifier writes it into provenance only when it
    normalizes to a dated Wiktextract identity such as
    `enwiktionary:YYYY-MM-DD`; undated `enwiktionary` remains policy-needed.
    Kaikki parser config and conversion calls use the explicit dated dump when
    present, otherwise preserving the current `enwiktionary` family label.

Loose ends to close before broad expansion:

1. The installed-pack manifest is an install record, not a complete provenance
   or license record.
2. The pack catalog and pack source manifest are not copied into installed-pack
   provenance in a way that can prove license approval, package/release version,
   or source-version identity later; raw checksums are currently captured only
   for new app-managed translation/frequency installs where the source is
   available during install/conversion.
3. Manual and legacy fallback paths can still enter runtime without a manifest
   lineage, but saved manual settings are now reportable through the lifecycle
   audit.
4. Full generated SQLite schema remains an audit output rather than a
   pack-manifest field. Frequency sidecars now carry narrow row/POS/topic-domain
   metric counts when the artifact is readable, but translation/embedding
   metrics still need family-specific definitions.
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
   checksums, package/release versions, or source-version identity; it records
   the conservative catalog/manifest information currently available.
10. External import preflight can say whether a manual link is format-safe and
    what review data is missing, but the actual copy/convert UX and managed
    pack writer are still future work.
11. Provenance review posture is now visible through an executable policy
    verdict and source-policy decision queue, including source-bundle pinning
    review, but license/review approval remains a human/source-policy decision
    outside the audit command.
12. Strict lifecycle gating can fail on review findings, but it still does not
    replace the source-readiness, SRS Zipf bridge, or denominator audits needed
    before expanded corpus promotion.
13. The promotion evidence bundle checks that required proof artifacts exist
    and pass; it does not create missing policy-gated source-dump,
    license-approval, non-installer checksum, complete source-bundle component
    checksum coverage, or source-bundle pinning evidence.
14. Build command, parser config, and converter source-digest lineage are now
    captured for app-managed install/backfill paths where known, but existing
    sidecars need reinstall or explicit backfill to gain that data.
15. Raw checksum capture is still incomplete for app-managed embedding
    finalization when the raw vector is no longer available, existing-install
    backfill, external directories, managed-import sidecar writing, and generated
    DE frequency pipeline component inputs that were reused or not present during
    the installer-time capture callback.
16. Safe source-version mutation is implemented only for `safe_to_write` rows,
    but existing sidecars need reinstall or explicit backfill to gain it, and
    current Kaikki catalog rows still lack dated dump identity. Label-only
    samples, policy-gated sources, and embedding release identity remain
    unresolved.
17. Source-bundle lineage is now recorded for the generated DE frequency
    pipeline, and installer-time checksum capture can write component hashes for
    files present during the build. It still does not prove complete component
    checksum coverage, license approval, or pinned snapshots for rolling upstream
    sources.
18. Frequency SQLite metrics are now part of the executable provenance promotion
    policy, but they are still sidecar evidence rather than source-readiness
    proof. They do not replace the source-readiness audit, schema audit, SRS
    Zipf bridge, denominator audit, or promotion evidence bundle.

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

## L6-Oa Promotion Evidence Bundle

Product claim:

- A candidate pack should not be promoted from scattered green-looking
  artifacts; the exact evidence bundle should be executable and fail when a
  required proof file is missing, stale, review-level, or pointed at the wrong
  pack/pair.

Current implementation:

- `scripts/testing/pack_lifecycle_promotion_evidence.py` reads existing JSON
  artifacts and emits a JSON/Markdown bundle report.
- For `pack-kind = frequency`, the required bundle is:
  - strict-ready pack lifecycle audit,
  - source-readiness/corpus-expansion audit,
  - SRS Zipf bridge,
  - denominator audit.
- The lifecycle evidence must have `summary.status = ok`, zero
  `provenance_review_required_count`, and a matching pack row with manifest,
  artifact, valid provenance, and no per-pack provenance review requirement.
- The downstream evidence must have `status = ok`, the expected decision id,
  and the requested pair.
- `--fail-on-review` exits non-zero unless the whole bundle status is `ok`.

Default command:

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

Boundaries:

1. This does not approve licenses, choose sources, install packs, rewrite
   settings, promote defaults, or launch generation.
2. This does not replace the underlying audits; it only verifies that their
   outputs form a complete promotion gate.
3. Non-frequency packs currently require lifecycle evidence first; family-specific
   downstream bundles should be added only when their promotion path
   has an equivalent downstream proof sequence.

Validation:

```bash
python3 -m pytest core/tests/dev/test_pack_lifecycle_promotion_evidence.py
python3 -m ruff check \
  scripts/testing/pack_lifecycle_promotion_evidence.py \
  core/tests/dev/test_pack_lifecycle_promotion_evidence.py
python3 -m ruff format --check \
  scripts/testing/pack_lifecycle_promotion_evidence.py \
  core/tests/dev/test_pack_lifecycle_promotion_evidence.py
```

## L6-Pa App-Managed Build/Parser Lineage

Product claim:

- A managed pack sidecar should say how the generated artifact was built when
  the app already knows the converter command or parser configuration.

Current implementation:

- `pack_provenance.py` now validates optional source/build lineage fields:
  `source.source_version`, `source.source_dump`, `build.command`,
  `build.converter_version`, `build.parser_profile`, and
  `build.parser_config`.
- App-managed translation installs write `build.command` and parser config for
  FreeDict and Kaikki converters.
- App-managed frequency installs write `build.command` and parser config,
  including parse config and POS-inventory config where available.
- App-managed embedding finalization writes the embedding converter command.
- Existing-install provenance backfill writes the same build command/parser
  config fields when catalog metadata is available.
- The lifecycle audit now reports `provenance_lineage` for sidecars and renders
  a `Source/Build Lineage` section without turning missing build/parser fields
  into strict review failures.

Boundaries:

1. This does not infer source versions, dump ids, converter package versions,
   license approval, or raw source checksums.
2. This does not rewrite existing sidecars unless the explicit provenance
   backfill command is run with `--apply`.
3. This does not make build/parser lineage a promotion blocker yet; it makes
   the lineage visible and available for later candidate gates.

Validation:

```bash
python3 -m pytest \
  core/tests/helper/test_pack_provenance.py \
  apps/gui/tests/test_pack_provenance_sidecars.py \
  core/tests/dev/test_pack_lifecycle_audit.py \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py
python3 -m ruff check \
  core/lexishift_core/helper/pack_provenance.py \
  apps/gui/src/language_packs.py \
  apps/gui/src/settings_language_packs_transfer_mixin.py \
  scripts/testing/pack_lifecycle_audit.py \
  scripts/testing/pack_lifecycle_provenance_lineage.py \
  scripts/testing/pack_lifecycle_provenance_backfill.py \
  core/tests/helper/test_pack_provenance.py \
  apps/gui/tests/test_pack_provenance_sidecars.py \
  core/tests/dev/test_pack_lifecycle_audit.py \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py
python3 -m ruff format --check \
  core/lexishift_core/helper/pack_provenance.py \
  apps/gui/src/language_packs.py \
  apps/gui/src/settings_language_packs_transfer_mixin.py \
  scripts/testing/pack_lifecycle_audit.py \
  scripts/testing/pack_lifecycle_provenance_lineage.py \
  scripts/testing/pack_lifecycle_provenance_backfill.py \
  core/tests/helper/test_pack_provenance.py \
  apps/gui/tests/test_pack_provenance_sidecars.py \
  core/tests/dev/test_pack_lifecycle_audit.py \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py
```

## L6-Qa App-Managed Raw Artifact Checksums

Product claim:

- A managed pack sidecar should include checksum evidence for the source artifact
  when the app has that artifact in hand during install or conversion.

Current implementation:

- `apps/gui/src/language_packs.py` now computes SHA-1 and SHA-256 for the
  downloaded language-pack artifact after a completed download and before
  post-processing or cleanup.
- `FrequencyPackDownloadThread._convert_to_sqlite(...)` now computes SHA-1 and
  SHA-256 for the resolved parsed source file after archive extraction and
  before conversion cleanup.
- `LanguagePackDownloadThread._write_manifest(...)` and
  `FrequencyPackDownloadThread._write_manifest(...)` pass those checksums into
  `write_app_managed_pack_provenance(...)`, which writes them under
  `source.raw_artifacts[0]`.
- Focused GUI sidecar tests cover checksum calculation, language sidecar
  pass-through, and frequency conversion checksum capture.

Boundaries:

1. This does not approve source licenses or source versions.
2. This does not rewrite existing sidecars or backfilled sidecars; those source
   files are usually gone by the time a backfill runs.
3. L6-Wa now captures app-managed embedding raw-vector checksums when the
   conversion source is still available during finalization.
4. This does not add generated SQLite schema to installer sidecars. L6-Xa now
   adds narrow frequency row/POS/topic-domain metric counts.
5. The DE frequency pipeline uses the L6-Va source-bundle lineage path because
   it builds from dependency/source components rather than one downloaded
   source file in this thread.

Validation:

```bash
python3 -m pytest apps/gui/tests/test_pack_provenance_sidecars.py
python3 -m ruff check \
  apps/gui/src/language_packs.py \
  apps/gui/tests/test_pack_provenance_sidecars.py
python3 -m ruff format --check \
  apps/gui/src/language_packs.py \
  apps/gui/tests/test_pack_provenance_sidecars.py
```

## L6-Ra App-Managed Converter Source Digests

Product claim:

- A managed pack sidecar should identify the converter implementation that built
  the artifact, even when the repo does not expose a package-level converter
  version.

Current implementation:

- `pyproject.toml` does not define a project package version, so this slice does
  not invent a semantic release version.
- `apps/gui/src/language_packs.py` maps known build modes to converter modules
  or scripts and writes `build.converter_version` as
  `source_sha256:<module-or-script>:<digest>`.
- The covered build modes are FreeDict conversion, Kaikki gloss/translation
  conversion, generic frequency conversion, the German frequency pipeline, and
  the embedding converter script when that script is available.
- App-managed translation/frequency installs, app-managed embedding
  finalization, and safe catalog-backed sidecar backfill all use the same digest
  format.
- The lifecycle audit already reports `converter_version` through the L6-Pa
  `provenance_lineage` surface.

Boundaries:

1. This is a converter source-code digest, not a reviewed release number.
2. This does not record Python, dependency, OS, or build-environment versions.
3. This does not rewrite existing sidecars unless the explicit provenance
   backfill command is run with `--apply`.
4. This does not add source-version/dump identity for remote corpora.
5. Manual/external imports and legacy fallback paths still need a first-class
   import/provenance writer before they gain the same lineage.

Validation:

```bash
python3 -m pytest \
  apps/gui/tests/test_pack_provenance_sidecars.py \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py
python3 -m ruff check \
  apps/gui/src/language_packs.py \
  apps/gui/src/settings_language_packs_transfer_mixin.py \
  scripts/testing/pack_lifecycle_provenance_backfill.py \
  apps/gui/tests/test_pack_provenance_sidecars.py \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py
python3 -m ruff format --check \
  apps/gui/src/language_packs.py \
  apps/gui/src/settings_language_packs_transfer_mixin.py \
  scripts/testing/pack_lifecycle_provenance_backfill.py \
  apps/gui/tests/test_pack_provenance_sidecars.py \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py
```

## L6-Sa Catalog Source-Identity Classification

Product claim:

- Before writing `source.source_version` or `source.source_dump`, the catalog
  should expose which candidate identities are obvious evidence and which ones
  need source-policy decisions.

Current implementation:

- `core/lexishift_core/helper/pack_source_identity.py` owns the shared
  classification policy used by both reporting and safe sidecar writing.
- `scripts/testing/pack_lifecycle_source_identity_plan.py` is a read-only
  command that emits JSON and Markdown reports.
- The report classifies catalog rows into:
  - `safe_to_write`,
  - `label_only`,
  - `needs_policy`,
  - `source_bundle_needed`,
  - `unknown`.
- It records the candidate field, candidate value, rationale, and recommended
  action for each catalog row.
- It also records `policy_category` for each row and
  `summary.policy_category_counts`, so source-policy follow-up can target a
  category instead of a flat `needs_policy` bucket.
- Current catalog summary from the focused test/CLI run:
  - `27` catalog rows,
  - `8` `safe_to_write`,
  - `2` `label_only`,
  - `16` `needs_policy`,
  - `1` `source_bundle_needed`,
  - `0` `unknown`.
- Current policy-category summary from the same focused run:
  - `8` `ready_source_identity`,
  - `3` `dated_wiktextract_dump_pinning`,
  - `8` `fasttext_release_snapshot_policy`,
  - `2` `branch_source_pinning`,
  - `3` `release_snapshot_policy`,
  - `2` `source_label_policy`,
  - `1` `source_bundle_lineage_policy`.
- Safe candidates include explicit release/version-like catalog evidence such as
  FreeDict release archives, Japanese WordNet `v1.1`, English WordNet 2025, and
  BCCWJ `ver1_0`.
- `label_only` rows keep useful sample labels such as `lemmas_60k` and
  `spanish_lemmas20k` out of durable `source_version` until policy defines what
  those labels mean.
- Kaikki, fastText, rolling/head URLs, and ambiguous secondary lexical exports
  remain `needs_policy`.
- For Kaikki, `source_dump=enwiktionary` is treated as a dump-family label only;
  durable sidecar `source.source_dump` requires a dated identity like
  `enwiktionary:YYYY-MM-DD`.
- Catalog-like Kaikki packs can now provide that dated identity through
  `source_dump`; the classifier keeps undated values as `needs_policy` and
  exports only dated values through `safe_pack_source_identity_fields(...)`.
- The German generated frequency pipeline is `source_bundle_needed` because the
  source-identity writer must not collapse it to one source-version string. The
  sidecar writer records this separately through L6-Va `source.source_bundle`
  lineage.

Default command:

```bash
python3 scripts/testing/pack_lifecycle_source_identity_plan.py \
  --json-out docs/test_outputs/pack_lifecycle_source_identity_plan_latest.json \
  --markdown-out docs/test_outputs/pack_lifecycle_source_identity_plan_latest.md
```

Boundaries:

1. This does not write provenance sidecars.
2. This does not approve licenses.
3. This does not pin rolling sources or change catalog URLs.
4. This does not make label-only candidates safe to promote.
5. This does not make undated Kaikki dump-family labels safe to write.
6. This does not replace source-readiness audits for expanded corpus candidates.

Validation:

```bash
python3 -m pytest core/tests/dev/test_pack_lifecycle_source_identity_plan.py
python3 -m ruff check \
  core/lexishift_core/helper/pack_source_identity.py \
  scripts/testing/pack_lifecycle_source_identity_plan.py \
  core/tests/helper/test_pack_source_identity.py \
  core/tests/dev/test_pack_lifecycle_source_identity_plan.py
python3 -m ruff format --check \
  core/lexishift_core/helper/pack_source_identity.py \
  scripts/testing/pack_lifecycle_source_identity_plan.py \
  core/tests/helper/test_pack_source_identity.py \
  core/tests/dev/test_pack_lifecycle_source_identity_plan.py
```

## L6-Ta Safe Source-Version Writer/Backfill

Product claim:

- Durable sidecar source identity should be written only when the catalog
  evidence was already classified as safe to write.

Current implementation:

- `safe_pack_source_identity_fields(...)` exports only `safe_to_write`
  decisions whose candidate field is `source_version` or `source_dump`.
- App-managed language, frequency, and embedding sidecar writers call that
  helper before writing `provenance.json`.
- Existing-install provenance backfill calls the same helper before writing
  missing sidecars.
- Current catalog safe writes are source-version-only: FreeDict release
  archives, Japanese WordNet `wnja-v1.1`, English WordNet 2025, and BCCWJ
  `ver1_0`.
- Dated Kaikki dump identities can be exported as `source.source_dump`, but the
  current catalog rows do not yet carry one.
- `freq-es-cde`, `freq-en-coca`, Kaikki, fastText, rolling/head URLs, and the
  German generated frequency pipeline remain withheld from durable source
  identity fields.

Boundaries:

1. This does not mark license status as confirmed.
2. This does not write `source_dump` for Kaikki until a dated dump policy exists.
3. This does not convert label-only filenames into source versions.
4. This does not mutate existing sidecars unless the explicit backfill command
   is run with `--apply`.
5. This does not write source-version or source-dump fields for generated
   pipeline outputs. L6-Va handles the German generated frequency pipeline
   through `source.source_bundle` instead.

Validation:

```bash
python3 -m pytest \
  core/tests/helper/test_pack_source_identity.py \
  core/tests/dev/test_pack_lifecycle_source_identity_plan.py \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py \
  apps/gui/tests/test_pack_provenance_sidecars.py
python3 -m ruff check \
  core/lexishift_core/helper/pack_source_identity.py \
  scripts/testing/pack_lifecycle_source_identity_plan.py \
  apps/gui/src/language_packs.py \
  apps/gui/src/settings_language_packs_transfer_mixin.py \
  scripts/testing/pack_lifecycle_provenance_backfill.py \
  core/tests/helper/test_pack_source_identity.py \
  apps/gui/tests/test_pack_provenance_sidecars.py \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py
python3 -m ruff format --check \
  core/lexishift_core/helper/pack_source_identity.py \
  scripts/testing/pack_lifecycle_source_identity_plan.py \
  apps/gui/src/language_packs.py \
  apps/gui/src/settings_language_packs_transfer_mixin.py \
  scripts/testing/pack_lifecycle_provenance_backfill.py \
  core/tests/helper/test_pack_source_identity.py \
  apps/gui/tests/test_pack_provenance_sidecars.py \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py
```

## L6-Ua Dated Kaikki Source-Dump Write Gate

Product claim:

- `source.source_dump` must identify a dated dump, not only the broad
  Wiktionary/Wiktextract family.

Current implementation:

- `pack_source_identity.py` now treats `enwiktionary` as a Kaikki dump-family
  label, not a durable sidecar dump identity.
- The classifier recognizes dated dump markers in Kaikki source URLs or
  filenames and normalizes them to `enwiktionary:YYYY-MM-DD`.
- The safe writer can export that dated `source_dump` value, but current
  catalog Kaikki rows remain `needs_policy` because their source URL is rolling
  and their filenames do not contain a dated dump marker.
- Current classification remains unchanged: `8` safe-to-write rows, `16`
  policy-needed rows, and all three Kaikki rows still report
  `record_dated_wiktextract_dump_before_writing_source_dump`.

Boundaries:

1. This does not change current Kaikki catalog URLs.
2. This does not write `source_dump=enwiktionary` to sidecars.
3. This does not approve Kaikki license or promotion readiness.
4. This does not choose the future dump acquisition/pinning mechanism.

Validation:

```bash
python3 -m pytest \
  core/tests/helper/test_pack_source_identity.py \
  core/tests/dev/test_pack_lifecycle_source_identity_plan.py
python3 scripts/testing/pack_lifecycle_source_identity_plan.py \
  --json-out /tmp/lexishift_source_identity_plan_kaikki_policy.json \
  --markdown-out /tmp/lexishift_source_identity_plan_kaikki_policy.md
```

## L6-Va Source-Bundle Lineage For Generated Frequency Pipeline

Product claim:

- A generated multi-input pack should expose its source component set instead
  of pretending one `source_version` or `source_dump` field explains the
  artifact.

Current implementation:

- `pack_provenance.py` now validates optional `source.source_bundle` objects.
- A source bundle requires `bundle_id`, `bundle_kind`, and at least one
  component with `role`, `source_name`, and a source pointer:
  `source_url`, `local_source_path`, or `build_ref`.
- Source-bundle components may include `sha1` and/or `sha256`, and the validator
  rejects malformed checksum fields when they are present.
- `pack_source_identity.py` keeps the German generated frequency pipeline out
  of safe single-field source identity, and now exports a DE frequency source
  bundle for `build_mode = "de_frequency_pipeline"`.
- The DE bundle records component URL lineage for the Leipzig corpus,
  FreeDict DE-EN, OdeNet, OpenThesaurus, german-pos-dict resources, and
  Morfologik tooling inputs.
- App-managed frequency sidecar writing and existing-install provenance
  backfill pass the source bundle into `provenance.json`.
- `pack_lifecycle_provenance_lineage.py` reports source-bundle presence,
  bundle id, component count, and component checksum coverage in JSON and
  Markdown lineage output.

Boundaries:

1. `source.source_bundle` is not license approval.
2. The installer-written DE bundle still records component URLs and filenames by
   default; component checksums are validated and reported when present, but
   full component checksum capture is not complete yet.
3. This does not write `source_version` or `source_dump` for generated
   pipeline output.
4. Rolling/head upstream URLs still need a future pinning or snapshot policy
   before they become promotion-grade evidence.
5. Existing installed sidecars need reinstall or explicit provenance backfill
   before they gain this lineage.

Validation:

```bash
python3 -m pytest \
  core/tests/helper/test_pack_provenance.py \
  core/tests/helper/test_pack_source_identity.py \
  apps/gui/tests/test_pack_provenance_sidecars.py \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py \
  core/tests/dev/test_pack_lifecycle_audit.py
python3 -m ruff check \
  core/lexishift_core/helper/pack_provenance.py \
  core/lexishift_core/helper/pack_source_identity.py \
  apps/gui/src/language_packs.py \
  scripts/testing/pack_lifecycle_provenance_backfill.py \
  scripts/testing/pack_lifecycle_provenance_lineage.py \
  core/tests/helper/test_pack_provenance.py \
  core/tests/helper/test_pack_source_identity.py \
  apps/gui/tests/test_pack_provenance_sidecars.py \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py \
  core/tests/dev/test_pack_lifecycle_audit.py
python3 -m ruff format --check \
  core/lexishift_core/helper/pack_provenance.py \
  core/lexishift_core/helper/pack_source_identity.py \
  apps/gui/src/language_packs.py \
  scripts/testing/pack_lifecycle_provenance_backfill.py \
  scripts/testing/pack_lifecycle_provenance_lineage.py \
  core/tests/helper/test_pack_provenance.py \
  core/tests/helper/test_pack_source_identity.py \
  apps/gui/tests/test_pack_provenance_sidecars.py \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py \
  core/tests/dev/test_pack_lifecycle_audit.py
```

## L6-Wa Embedding/Manual Checksum Lineage

Product claim:

- When a raw embedding or manual external artifact is already present locally,
  the provenance path should capture checksum evidence without asking the
  operator to reconstruct it by hand.

Current implementation:

- `LanguagePackPanelTransferMixin._finalize_embedding_pack(...)` now computes
  SHA-1/SHA-256 for the prior app-managed raw vector file when finalizing a
  converted embedding SQLite artifact.
- The resulting app-managed embedding `provenance.json` writes those hashes
  under `source.raw_artifacts[0]` before the temporary raw vector file is
  cleaned up.
- `pack_lifecycle_external_import_plan.py` now computes SHA-1/SHA-256 for
  supported file paths when `--raw-sha1`/`--raw-sha256` are not supplied.
- The external import plan reports the checksum source as either `provided`,
  `computed_from_external_path`, or `unavailable`, and feeds the computed
  checksum into the provenance preview and promotion blockers.
- The external import plan remains read-only: it still does not copy, convert,
  write settings, write sidecars, or change runtime defaults.

Boundaries:

1. This does not approve source licenses.
2. This does not create a managed import UX.
3. This does not checksum directories or deleted/missing raw sources.
4. Existing-install sidecar backfill still cannot invent raw checksums after
   source files are gone.
5. Generated DE frequency pipeline component checksum capture remains a
   source-bundle follow-up.

Validation:

```bash
python3 -m pytest \
  apps/gui/tests/test_pack_provenance_sidecars.py \
  core/tests/dev/test_pack_lifecycle_external_import_plan.py
python3 -m ruff check \
  apps/gui/src/settings_language_packs_transfer_mixin.py \
  apps/gui/tests/test_pack_provenance_sidecars.py \
  scripts/testing/pack_lifecycle_external_import_plan.py \
  core/tests/dev/test_pack_lifecycle_external_import_plan.py
python3 -m ruff format --check \
  apps/gui/src/settings_language_packs_transfer_mixin.py \
  apps/gui/tests/test_pack_provenance_sidecars.py \
  scripts/testing/pack_lifecycle_external_import_plan.py \
  core/tests/dev/test_pack_lifecycle_external_import_plan.py
```

## L6-Xa Frequency SQLite Artifact Metrics

Product claim:

- A frequency pack sidecar should carry the basic generated-artifact counts that
  are repeatedly needed for corpus expansion review, while still leaving full
  schema/source-readiness evaluation to the dedicated audits.

Current implementation:

- `pack_artifact_metrics.py` provides a conservative SQLite probe for
  `pack_kind = "frequency"` only.
- The probe reads the `frequency` table when available and returns:
  `row_count`, `distinct_lemma_count`, `pos_rows`, and
  `topic_domain_rows`.
- Invalid, missing, non-frequency, or unsupported SQLite artifacts return no
  metrics instead of inventing evidence.
- App-managed frequency sidecar writing passes these metrics into
  `provenance.json` as `artifact.metrics`.
- Existing-install provenance sidecar backfill uses the same metrics helper
  when a catalog-backed frequency artifact is readable.

Boundaries:

1. This does not approve source licenses or source versions.
2. This does not record full SQLite schema details.
3. This does not define translation or embedding metric semantics.
4. This does not make missing metrics a strict review failure yet.
5. This does not replace source-readiness, SRS Zipf bridge, denominator, or
   promotion evidence audits.

Validation:

```bash
python3 -m pytest \
  core/tests/helper/test_pack_artifact_metrics.py \
  core/tests/helper/test_pack_provenance.py \
  apps/gui/tests/test_pack_provenance_sidecars.py \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py
python3 -m ruff check \
  core/lexishift_core/helper/pack_artifact_metrics.py \
  core/lexishift_core/helper/pack_provenance.py \
  apps/gui/src/language_packs.py \
  scripts/testing/pack_lifecycle_provenance_backfill.py \
  core/tests/helper/test_pack_artifact_metrics.py \
  core/tests/helper/test_pack_provenance.py \
  apps/gui/tests/test_pack_provenance_sidecars.py \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py
python3 -m ruff format --check \
  core/lexishift_core/helper/pack_artifact_metrics.py \
  core/lexishift_core/helper/pack_provenance.py \
  apps/gui/src/language_packs.py \
  scripts/testing/pack_lifecycle_provenance_backfill.py \
  core/tests/helper/test_pack_artifact_metrics.py \
  core/tests/helper/test_pack_provenance.py \
  apps/gui/tests/test_pack_provenance_sidecars.py \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py
```

## L6-Ya Source-Bundle Checksum Coverage Surface

Product claim:

- Multi-input source bundles should be able to show whether component checksums
  are present, without treating checksum presence as license approval or URL
  pinning.

Current implementation:

- `pack_provenance.py` validates optional `sha1` and `sha256` fields on
  `source.source_bundle.components[]` using the same checksum shape checks as
  raw/generated artifacts.
- `pack_lifecycle_provenance_lineage.py` reports
  `source_bundle_component_checksum_count` and
  `source_bundle_component_missing_checksum_count`.
- Lifecycle Markdown renders source-bundle checksum coverage as `checked/total`
  beside the bundle id.

Boundaries:

1. This is the schema/reporting layer. L6-Za is the installer-time capture layer
   for generated DE frequency pipeline inputs.
2. This does not pin rolling/head upstream URLs.
3. This does not approve source licenses.
4. This does not make missing source-bundle component checksums a strict review
   failure yet.

Validation:

```bash
python3 -m pytest \
  core/tests/helper/test_pack_provenance.py \
  core/tests/dev/test_pack_lifecycle_audit.py
python3 -m ruff check \
  core/lexishift_core/helper/pack_provenance.py \
  scripts/testing/pack_lifecycle_provenance_lineage.py \
  core/tests/helper/test_pack_provenance.py \
  core/tests/dev/test_pack_lifecycle_audit.py
python3 -m ruff format --check \
  core/lexishift_core/helper/pack_provenance.py \
  scripts/testing/pack_lifecycle_provenance_lineage.py \
  core/tests/helper/test_pack_provenance.py \
  core/tests/dev/test_pack_lifecycle_audit.py
```

## L6-Za Generated DE Component Checksum Capture

Product claim:

- A generated multi-input frequency artifact should record checksums for the
  source-bundle component files that were actually available during its managed
  build.

Current implementation:

- `run_de_frequency_pipeline(...)` accepts an optional
  `source_bundle_component_paths_cb` callback and calls it before the temporary
  build workspace is removed.
- `_source_bundle_component_paths(...)` exposes the pipeline's expected local
  component paths for the Leipzig corpus archive, FreeDict source archive when
  downloaded during this run, OdeNet, OpenThesaurus, german-pos-dict inputs, and
  Morfologik tool jars.
- `source_bundle_fields_for_pack(...)` can now accept component paths and add
  SHA-1/SHA-256 fields to matching source-bundle components when the files are
  present.
- `FrequencyPackDownloadThread._build_de_pipeline(...)` captures the checked
  source bundle from the callback, and `_write_manifest(...)` writes the captured
  bundle into `provenance.json`.

Boundaries:

1. This captures available installer-time files only. It does not invent
   checksums for reused FreeDict installs, branch paths not exercised by the run,
   or files already gone before backfill.
2. This does not pin rolling/head upstream URLs.
3. This does not approve source licenses.
4. This does not make incomplete component checksum coverage a strict review
   failure yet.

Validation:

```bash
python3 -m pytest \
  core/tests/helper/test_pack_source_identity.py \
  core/tests/frequency/test_de_pipeline_pos_sources.py \
  apps/gui/tests/test_pack_provenance_sidecars.py
python3 -m ruff check \
  core/lexishift_core/helper/pack_source_identity.py \
  core/lexishift_core/frequency/de/pipeline.py \
  apps/gui/src/language_packs.py \
  core/tests/helper/test_pack_source_identity.py \
  core/tests/frequency/test_de_pipeline_pos_sources.py \
  apps/gui/tests/test_pack_provenance_sidecars.py
python3 -m ruff format --check \
  core/lexishift_core/helper/pack_source_identity.py \
  core/lexishift_core/frequency/de/pipeline.py \
  apps/gui/src/language_packs.py \
  core/tests/helper/test_pack_source_identity.py \
  core/tests/frequency/test_de_pipeline_pos_sources.py \
  apps/gui/tests/test_pack_provenance_sidecars.py
```

## L6-Zb Executable Provenance Promotion Policy

Product claim:

- The pack lifecycle rules should be a reusable policy verdict, not only prose in
  docs or one-off checks embedded in a single audit command.

Current implementation:

- `pack_lifecycle_policy.py` defines `pack_provenance_promotion_policy` version
  `2`.
- The policy checks provenance existence/validity, confirmed license status,
  source pointer, durable source identity, raw artifact checksum coverage,
  generated artifact checksum coverage, source-bundle component checksum
  coverage, source-bundle pinning status, and frequency metric completeness.
- `pack_lifecycle_audit.py` writes `provenance_policy` into each installed-pack
  and semantic-pack row, while preserving the older `provenance_review` shape as
  a compatibility view.
- `pack_lifecycle_promotion_evidence.py` now requires the pack row's
  `provenance_policy` to be present, `status = "ok"`, and `promotion_ready =
  true`.

Boundaries:

1. This policy is promotion-oriented. Local app-managed installs can still write
   valid sidecars with `requires_review`; the policy reports that as review, not
   schema failure.
2. This does not create license approval records.
3. This does not replace source-readiness, SRS Zipf, denominator, or schema
   audits; it makes the provenance portion executable.
4. Translation and embedding metric semantics remain future family-specific
   policy work.

Validation:

```bash
python3 -m pytest \
  core/tests/dev/test_pack_lifecycle_policy.py \
  core/tests/dev/test_pack_lifecycle_audit.py \
  core/tests/dev/test_pack_lifecycle_promotion_evidence.py
python3 -m ruff check \
  scripts/testing/pack_lifecycle_policy.py \
  scripts/testing/pack_lifecycle_audit.py \
  scripts/testing/pack_lifecycle_promotion_evidence.py \
  core/tests/dev/test_pack_lifecycle_policy.py \
  core/tests/dev/test_pack_lifecycle_audit.py \
  core/tests/dev/test_pack_lifecycle_promotion_evidence.py
python3 -m ruff format --check \
  scripts/testing/pack_lifecycle_policy.py \
  scripts/testing/pack_lifecycle_audit.py \
  scripts/testing/pack_lifecycle_promotion_evidence.py \
  core/tests/dev/test_pack_lifecycle_policy.py \
  core/tests/dev/test_pack_lifecycle_audit.py \
  core/tests/dev/test_pack_lifecycle_promotion_evidence.py
```

## L6-Zc Source-Bundle Promotion Pinning Policy

Product claim:

- A multi-input generated pack should not become promotion-ready merely because
  it records component URLs and checksums; it also needs an explicit pinning
  decision for the source-bundle lineage.

Current implementation:

- `pack_lifecycle_policy.py` now reports source-bundle component pointer
  coverage through `source_bundle_component_pointer_count`.
- When a provenance sidecar has `source.source_bundle.components[]`, the policy
  requires every component to have a source pointer and requires the bundle's
  `lineage_status` to be promotion-grade.
- Promotion-grade source-bundle lineage statuses are currently:
  - `pinned_snapshot`
  - `pinned_component_artifacts`
- Existing DE generated-frequency sidecars that only say
  `component_urls_recorded` remain valid provenance, but the promotion policy
  now returns review reason `source_bundle_pinning_missing` until an explicit
  pinning/source-policy decision is recorded.

Boundaries:

1. This does not download or pin any source data.
2. This does not approve licenses.
3. This does not change local install behavior; it only makes promotion gating
   stricter.
4. The actual per-source pinning decision still belongs to future source policy
   work.

Validation:

```bash
python3 -m pytest \
  core/tests/dev/test_pack_lifecycle_policy.py \
  core/tests/dev/test_pack_lifecycle_audit.py \
  core/tests/dev/test_pack_lifecycle_promotion_evidence.py
python3 -m ruff check \
  scripts/testing/pack_lifecycle_policy.py \
  core/tests/dev/test_pack_lifecycle_policy.py \
  core/tests/dev/test_pack_lifecycle_audit.py \
  core/tests/dev/test_pack_lifecycle_promotion_evidence.py
python3 -m ruff format --check \
  scripts/testing/pack_lifecycle_policy.py \
  core/tests/dev/test_pack_lifecycle_policy.py \
  core/tests/dev/test_pack_lifecycle_audit.py \
  core/tests/dev/test_pack_lifecycle_promotion_evidence.py
```

## L6-Zd Source-Policy Decision Queue

Product claim:

- A lifecycle audit should show the exact source-policy work still blocking
  promotion, not only a generic `review` status or a flat list of policy
  reasons.

Current implementation:

- `pack_lifecycle_source_policy_decisions.py` builds the source-policy decision
  report.
- `pack_lifecycle_audit.py` now adds top-level `source_policy_decisions` to the
  JSON report.
- The report is read-only and derives its rows from non-`ok`
  `provenance_policy.checks` on installed and semantic packs.
- Each row records family, pack id, pack kind, provenance path, policy status,
  check id/status, review reason, category, observed value, and a recommended
  action.
- Current categories include:
  - `license_review`
  - `provenance_sidecar`
  - `source_pointer`
  - `source_identity`
  - `raw_artifact_checksum`
  - `generated_artifact_checksum`
  - `source_bundle_pointer`
  - `source_bundle_checksum`
  - `source_bundle_pinning`
  - `frequency_metrics`
- The Markdown audit now includes a `Source Policy Decision Queue` table so the
  next source-policy pass can pick one concrete review category instead of
  reopening the whole pack lifecycle surface.

Boundaries:

1. This does not approve a source license.
2. This does not pin source data, download artifacts, or mutate sidecars.
3. Recommended actions are review routing labels, not automatic fixes.
4. The queue is only as complete as the installed/semantic packs visible to the
   lifecycle audit.

Validation:

```bash
python3 -m pytest \
  core/tests/dev/test_pack_lifecycle_audit.py \
  core/tests/dev/test_pack_lifecycle_policy.py \
  core/tests/dev/test_pack_lifecycle_promotion_evidence.py
python3 -m ruff check \
  scripts/testing/pack_lifecycle_audit.py \
  scripts/testing/pack_lifecycle_policy.py \
  scripts/testing/pack_lifecycle_source_policy_decisions.py \
  core/tests/dev/test_pack_lifecycle_audit.py \
  core/tests/dev/test_pack_lifecycle_policy.py \
  core/tests/dev/test_pack_lifecycle_promotion_evidence.py
python3 -m ruff format --check \
  scripts/testing/pack_lifecycle_audit.py \
  scripts/testing/pack_lifecycle_policy.py \
  scripts/testing/pack_lifecycle_source_policy_decisions.py \
  core/tests/dev/test_pack_lifecycle_audit.py \
  core/tests/dev/test_pack_lifecycle_policy.py \
  core/tests/dev/test_pack_lifecycle_promotion_evidence.py
```

## L6-Zf Explicit Dated Wiktextract Source-Dump Seam

Product claim:

- A Kaikki/Wiktextract pack should have an explicit, safe path for recording a
  dated dump identity once a source-policy decision approves one, without
  pretending the current rolling URL is already pinned.

Current implementation:

- `LanguagePackInfo` now has optional `source_dump`.
- `pack_source_identity.py` treats explicit Kaikki `source_dump` values as
  safe only when they normalize to a dated Wiktextract identity such as
  `enwiktionary:YYYY-MM-DD`.
- App-managed language-pack sidecar writing already calls
  `safe_pack_source_identity_fields(...)`, so a dated source dump is written to
  `provenance.json` only when the shared classifier marks it safe.
- Kaikki parser config, conversion calls, and existing-install sidecar backfill
  now use the explicit `source_dump` when present; otherwise they preserve the
  current `enwiktionary` dump-family label.

Boundaries:

1. This does not download, choose, or verify a Wiktextract dump.
2. This does not set the current Kaikki catalog rows to a dated dump.
3. This does not approve source licenses.
4. Undated `source_dump = enwiktionary` remains policy-needed and is not written
   as durable sidecar source identity.

Validation:

```bash
python3 -m pytest \
  core/tests/helper/test_pack_source_identity.py \
  core/tests/dev/test_pack_lifecycle_source_identity_plan.py \
  apps/gui/tests/test_pack_provenance_sidecars.py \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py
python3 -m ruff check \
  core/lexishift_core/helper/pack_source_identity.py \
  apps/gui/src/language_packs_catalog.py \
  apps/gui/src/language_packs.py \
  scripts/testing/pack_lifecycle_provenance_backfill.py \
  scripts/testing/pack_lifecycle_source_identity_plan.py \
  core/tests/helper/test_pack_source_identity.py \
  core/tests/dev/test_pack_lifecycle_source_identity_plan.py \
  apps/gui/tests/test_pack_provenance_sidecars.py \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py
python3 -m ruff format --check \
  core/lexishift_core/helper/pack_source_identity.py \
  apps/gui/src/language_packs_catalog.py \
  apps/gui/src/language_packs.py \
  scripts/testing/pack_lifecycle_provenance_backfill.py \
  scripts/testing/pack_lifecycle_source_identity_plan.py \
  core/tests/helper/test_pack_source_identity.py \
  core/tests/dev/test_pack_lifecycle_source_identity_plan.py \
  apps/gui/tests/test_pack_provenance_sidecars.py \
  core/tests/dev/test_pack_lifecycle_provenance_backfill.py
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
3. L6-Qa and L6-Wa now capture raw checksums for new app-managed
   translation/frequency installs and available embedding conversion sources;
   this first L6-F slice did not rewrite older sidecars.
4. License review remains separate from installer writing. The sidecar makes
   review status explicit; it does not approve source usage.
5. Full generated SQLite schema remains an audit output. L6-Xa writes narrow
   frequency metrics to sidecars, but translation/embedding metric semantics
   remain future work.

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
| L6-O Promotion evidence bundle | Completed first executable bundle gate for frequency-pack promotion evidence. | `pack_lifecycle_promotion_evidence.py`, focused tests, and candidate runbook update. |
| L6-P App-managed build/parser lineage | Completed first sidecar-write/backfill/reporting slice for build command and parser config where already known. | Optional provenance schema fields, installer/backfill wiring, lifecycle lineage report, and focused tests. |
| L6-Q App-managed raw artifact checksums | Completed first installer/converter checksum slice for source files available during managed translation/frequency installs. | Installer checksum capture, provenance sidecar wiring, and focused GUI sidecar tests. |
| L6-R App-managed converter source digests | Completed first converter lineage slice using source SHA-256 digests where no package-level converter version exists. | Installer/backfill `build.converter_version` wiring and focused sidecar/backfill tests. |
| L6-S Catalog source-identity classification | Completed first read-only decision surface for source-version/source-dump candidates. | `pack_lifecycle_source_identity_plan.py`, Markdown/JSON report, and focused tests. |
| L6-T Safe source-version writer/backfill | Completed first mutation slice for classified safe source-version candidates only. | `pack_source_identity.py`, installer/backfill wiring, and focused safe/withheld identity tests. |
| L6-U Dated Kaikki source-dump gate | Completed first policy gate that keeps undated Kaikki family labels out of sidecar `source_dump`. | Dated dump normalization in `pack_source_identity.py` plus focused safe/withheld tests. |
| L6-V Source-bundle lineage | Completed first multi-input lineage slice for generated DE frequency output. | Optional `source.source_bundle` schema, DE bundle writer/backfill, lifecycle lineage reporting, and focused tests. |
| L6-W Embedding/manual checksum lineage | Completed first checksum slice for app-managed embedding conversion sources and read-only manual external import preflight files. | Embedding finalization raw-vector checksums, external import preflight auto-checksums, and focused tests. |
| L6-X Frequency SQLite artifact metrics | Completed first generated-artifact metric slice for frequency sidecars only. | Frequency SQLite metric helper, installer/backfill `artifact.metrics` wiring, and focused tests. |
| L6-Y Source-bundle checksum coverage | Completed first schema/reporting surface for component checksum coverage without treating missing hashes as approval. | Component checksum validation, lifecycle lineage checksum counts, and focused tests. |
| L6-Za Generated DE component checksum capture | Completed first installer-time capture for source-bundle component files available during generated DE frequency builds. | DE pipeline component-path callback, checked source-bundle writer path, and focused tests. |
| L6-Zb Provenance promotion policy | Completed first reusable executable policy verdict for promotion-oriented provenance checks. | `pack_lifecycle_policy.py`, audit `provenance_policy` rows, promotion evidence policy checks, and focused tests. |
| L6-Zc Source-bundle promotion pinning policy | Completed first promotion-policy blocker for URL-recorded but unpinned source bundles. | Source-bundle pointer/pinning policy checks and focused policy/audit tests. |
| L6-Zd Source-policy decision queue | Completed first read-only queue of concrete source-policy blockers and recommended review actions. | `pack_lifecycle_source_policy_decisions.py`, `source_policy_decisions` JSON, Markdown decision table, and focused audit tests. |
| L6-Ze Source-identity policy category taxonomy | Completed first category breakdown for catalog source-identity decisions. | `policy_category` rows, category summary counts, Markdown category table, and focused source-identity plan tests. |
| L6-Zf Explicit dated Wiktextract source-dump seam | Completed safe catalog/provenance seam for future approved dated Kaikki dump identities. | Optional `LanguagePackInfo.source_dump`, classifier safe-write guard, parser/backfill propagation, and focused provenance tests. |

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
