# Productization Lane 6 Data Provenance And Pack Lifecycle Inventory

Status: active inventory
Role: Planning / WIP
Last updated: 2026-05-15
Last verified: 2026-05-15 read-only inspection of pack catalogs, source-manifest cache policy, installed-pack manifests, helper pack resolvers, semantic-pack installation/publication code, semantic data-lifecycle docs, en-es corpus-expansion audit plan, and focused pack-provenance validator tests
Purpose: record the current data-source, pack, manifest, installed-artifact, and generated-artifact lifecycle before corpus or semantic-veto expansion resumes
Source-of-truth: inventory only; current runtime truth lives in source code, installed manifests, generated SQLite artifacts, helper publication manifests, tests, and seam-specific canonical docs.
Related docs:
- `productization_closure_roadmap.md`
- `productization_lane4_validation_gate_inventory.md`
- `productization_lane5_runtime_seam_inventory.md`
- `data_source_normalization_execution_order.md`
- `../rulegen/semantic_routing_data_update_lifecycle.md`
- `../rulegen/semantic_veto_srs_corpus_expansion_plan.md`
- `../rulegen/semantic_veto_denominator_current_state.md`
- `../rulegen/lp_onboarding_operating_model.md`
- `../pack_source_manifest.json`
- `../../apps/gui/src/language_packs_catalog.py`
- `../../core/lexishift_core/helper/installed_packs.py`
- `../../core/lexishift_core/helper/pack_provenance.py`
- `../../core/lexishift_core/helper/rulegen_outputs.py`
- `../../core/lexishift_core/helper/use_cases/semantic_pack_install.py`
- `../../core/tests/helper/test_pack_provenance.py`

## Scope

Lane: Lane 6, data provenance and pack lifecycle.

Completed slices:

1. L6-A: current pack/source provenance inventory.
2. L6-B: pack provenance sidecar contract.

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
| Provenance sidecar | `core/lexishift_core/helper/pack_provenance.py`, future `<pack_root>/provenance.json` | Versioned contract for source identity, license status, source pointer, raw artifact checksums, build mode, generated artifact identity, and optional SQLite metrics. | No installer writes this file yet, and no lifecycle audit consumes it yet. |
| Pack refs/resolvers | `frequency_packs.py`, `translation_packs.py`, `embedding_packs.py`, `pair_resources.py`, `lp_capabilities.py` | Runtime-facing pack id, provider, source/POS profile, resolved path, and managed-vs-fallback resolution. | Full provenance for manual paths or legacy fallback files. |
| Semantic pack copy | `<data_root>/language_packs/<pair>/semantic_packs/<pack_id>/manifest.json` from `semantic_pack_install.py` | Semantic pack id/pair, generated timestamp, source path, raw/normalized inventory hashes, installed semantic inventory artifact hash/bytes. | Upstream source-batch lineage, source license/review state, release manifest identity, or why the compiled generation was selected. |
| Profile publication manifest | `<data_root>/srs/profiles/<profile_id>/srs_publication_manifest_<pair>.json` from `rulegen_outputs.py` | Ruleset/snapshot/semantic inventory family identity, `generation_id`, artifact hashes/bytes, and family-valid flag. | Source provenance for the data that produced the generation. It is a runtime publication manifest, not a source manifest. |
| Generated evidence | `docs/test_outputs/` audit, benchmark, and experiment artifacts | Evidence from the command that produced the artifact. | Architecture authority or current runtime truth without a source/code/test pointer. |

## Resource Family State

| Family | Current Managed Shape | Current Provenance | Main Lane 6 Gap |
| --- | --- | --- | --- |
| Translation dictionaries | App-managed FreeDict and Kaikki installs build to SQLite under a pack-id root and write `manifest.json`; helper resolution is pack-id-first with legacy filename fallbacks. | Catalog has source/provider URL fields; installed manifest has provider, build mode, artifact relpath, source filename, sqlite filename, and installed timestamp. | No complete source/license/raw-checksum/converter-version/schema/row-count record; manual and legacy fallback paths still depend on inference. |
| Frequency packs | App-managed frequency installs build to SQLite under a pack-id root and write `manifest.json`; runtime diagnostics expose frequency pack id/provider/POS profile. | Catalog plus installed manifest identify provider/build mode/source filename and the generated artifact path. | The installed manifest does not carry audit metrics, source/license clarity, raw checksum, or topic/domain coverage. Spanish expansion candidates need versioned pack ids and audit artifacts before promotion. |
| Embedding packs | App-managed embeddings use pack-id roots, manifest-backed artifacts, and embedding pack refs; manual/raw paths remain compatibility inputs. | Installed manifest records provider, build mode, source filename, sqlite filename, and artifact path. | License/source/version/checksum and conversion provenance are not first-class; manual/raw paths remain outside manifest-backed lifecycle. |
| Secondary lexical packs | WordNet, Moby, OpenThesaurus, OdeNet, JMDict, and CC-CEDICT remain mixed/raw or compatibility surfaces. | Catalog records source/provider URL fields; some managed downloads may write basic installed manifests. | Family-wide promotion decision is still pending; they should not be treated as core normalized runtime packs until evaluated. |
| Semantic source/evidence batches | Semantic lifecycle docs define source registry, raw batches, normalized evidence, compiled generation, publication family, and helper-local materialization layers. | Planning contracts require append-only raw evidence and explicit provenance. | The cross-pack Lane 6 gate still needs an implemented source/generation audit tying raw evidence, compiled inventory, semantic pack copy, and profile publication together. |
| Semantic compiled packs | Named en-es dev packs resolve from installed copy, catalog env, or current repo dev-pack paths; install writes a semantic pack copy and a profile publication family. | Pack copy manifest hashes raw/normalized inventory; publication manifest hashes runtime artifacts and assigns one generation id. | Dev-pack paths are hardcoded development fixtures; publication manifests do not yet carry upstream source-batch lineage or release-manifest identity. |
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

Loose ends to close before broad expansion:

1. The installed-pack manifest is an install record, not a complete provenance
   or license record.
2. The pack catalog and pack source manifest are not copied into installed-pack
   provenance in a way that can prove source URL, license, raw checksum, or
   converter inputs later.
3. Manual and legacy fallback paths can still enter runtime without a manifest
   lineage.
4. Generated SQLite schema, row counts, POS coverage, and topic/domain coverage
   are audit outputs, not pack-manifest fields.
5. Semantic publication manifests validate runtime artifact family integrity,
   but not upstream source-batch or review lineage.
6. Named semantic dev packs currently resolve through repo-local generated
   experiment paths, which is acceptable for operator work but not a release
   pack lifecycle.
7. There is no central pack-lifecycle audit command that reads catalog entries,
   installed manifests, semantic pack copies, publication manifests, and
   candidate SQLite metadata into one JSON/Markdown report.

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
2. No installer writes `provenance.json` yet.
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

## Planned Lane 6 Slices

| Slice | Goal | First Output |
| --- | --- | --- |
| L6-B Pack provenance contract | Initial sidecar validator completed; future work should wire installers/audits to it. | `pack_provenance.py` and focused validator tests. |
| L6-C Pack lifecycle audit command | Read catalog entries, installed manifests, source manifest overrides, candidate SQLite metadata, and semantic publication manifests into one report. | `scripts/testing/...` audit with JSON/Markdown output and focused tests. |
| L6-D Semantic generation lineage | Tie semantic source/evidence batches to compiled inventory, semantic pack copy, and profile publication manifest. | Generation/release manifest fields or sidecar plus installer validation. |
| L6-E En-es expansion candidate runbook | Convert the corpus-expansion plan into a candidate-pack checklist that another agent can run without re-deriving context. | Candidate pack readiness checklist and validation command bundle. |
| L6-F Manual path disposition | Decide which manual paths remain supported import/debug surfaces and which should be demoted before release. | Updated installed-vs-manual contract and targeted cleanup tasks. |

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
