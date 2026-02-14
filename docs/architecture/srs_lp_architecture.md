# SRS LP Architecture Contract

Purpose:
- Define how LP (Language Pair) support is structured across core, helper, GUI, and extension.
- Make future LP additions predictable and backward-compatible.

## 1) Source Of Truth

Primary registry:
- `core/lexishift_core/helper/lp_capabilities.py`

`PairCapability` is the canonical LP contract. Surfaces should read capabilities, not hardcode pair assumptions.

Current capability responsibilities:
- Rulegen support (`rulegen_mode`)
- Default frequency DB name (`default_frequency_db`)
- Seed/rulegen dictionary requirements (`requires_jmdict_*`, `requires_freedict_de_en_for_rulegen`)
- UI SRS pair exposure (`srs_selectable`)

Compatibility rule:
- Add new capability fields with safe defaults.
- Do not remove or silently repurpose existing fields consumed by diagnostics/UI.

## 2) Layer Responsibilities

Core (`lexishift_core`):
- Owns LP requirements, seed/admission policy, rulegen adapters, and diagnostics contracts.
- Must accept LP-specific requirements through capabilities, not pair string special-cases outside policy modules.
- Owns pair-scoped SRS defaults in `srs/pair_policy.py` (bootstrap/refresh sizing defaults + feedback window defaults).

Helper (`helper_engine`, helper CLI/native host):
- Resolves resources per LP via capability defaults.
- Enforces only the resources required by that LP and action (`initialize`, `refresh`, `rulegen`).
- Emits LP-aware diagnostics (`requirements`, resolved paths, missing inputs).

GUI / Extension:
- Select LP and pass LP through helper requests.
- Use helper diagnostics for readiness/preflight UI.
- Avoid duplicating LP requirement logic; only format/present state.

## 3) SRS Pipeline By LP

1. LP selection:
- SRS selectable pairs are capability-driven (`selectable_srs_pairs()`).

2. Resource resolution:
- Frequency DB, dictionary paths resolved from capability defaults (with explicit overrides allowed).

3. Seed candidate selection:
- Frequency DB is required.
- Dictionary gate is LP-specific (`require_jmdict` true only for LPs that need it).
- Source metadata must be generic (derived from selected frequency source), not hardcoded to a single corpus.

4. Admission weighting:
- POS bucket classification is pair-aware (at minimum JA and DE specific classifiers plus generic fallback).

5. Rule generation:
- Dispatches via adapter keyed by `rulegen_mode`.
- Unsupported LPs return no rules until adapter exists; they must not break existing LPs.

6. Pair policy defaults:
- `set_top_n`, `feedback_window_size`, and `initial_active_count` fall back to pair policy defaults when omitted.
- Policy defaults are surfaced by helper diagnostics (`pair_policy`) so UI and operators can verify effective behavior.

## 4) LP-Specific UX vs Core SRS

Allowed LP-specific UX:
- Example: Japanese replacement display mode (`romaji` vs `kana/kanji`).
- These are presentation options and can vary by LP.

Non-negotiable core invariants:
- Scheduler math, admission refresh policy contracts, and store schema stay LP-agnostic.
- LP-specific UX must not fork core SRS state transitions.
- LP-specific display metadata should be additive and scoped to UI/runtime rendering.
  - Example: `metadata.morphology.target_surface` can change rendered text (for inflected forms), while canonical SRS identity stays on `rule.replacement`.

## 5) Adding A New LP Safely

1. Add/update capability in `core/lexishift_core/helper/lp_capabilities.py`.
2. Add/verify frequency source default and dictionary requirements.
3. Add rulegen adapter if cross-lingual/monolingual rulegen is expected.
4. Ensure helper diagnostics show resolved paths and missing inputs for that LP.
5. Add LP E2E tests (`initialize -> refresh -> publish -> diagnostics`).
6. Update docs:
   - `docs/language_pairs/lp_resource_requirements.md`
   - `docs/srs/srs_roadmap.md`
   - LP setup checklist docs

## 6) Regression Guardrails

- Keep `en-ja` behavior as reference baseline.
- Every new LP test should include:
  - initialize success with required resources only,
  - refresh publish behavior,
  - non-empty runtime artifacts when data is valid.
- Changes to LP capability fields should include tests for:
  - `supported_rulegen_pairs()`
  - `selectable_srs_pairs()`
  - resource requirement diagnostics output.
