# Project Integrity Secondary Pass Plan

Status: active planning
Role: Planning / WIP
Last updated: 2026-04-17
Last verified: 2026-04-17 planning draft strengthened with risk scoring, traceability, and manual scenario guidance
Purpose: define the invariant-driven follow-on review that comes after the first structural stabilization pass so correctness risks are checked deliberately, one seam at a time
Source-of-truth: planning doc only; executable truth still lives in code, tests, `feature_state_matrix.md`, and the evidence artifacts generated during each slice
Related docs:
- `project_integrity_stabilization_runbook.md`
- `project_integrity_stabilization_backlog.md`
- `project_integrity_secondary_pass_notes.md`
- `documentation_governance.md`
- `feature_state_matrix.md`
- `project_health_gate_structure.md`
- `../rulegen/semantic_routing_publication_contract.md`
- `../rulegen/semantic_routing_runtime_readiness.md`
- `../srs/srs_profile_schema.md`

## Purpose

The first stabilization pass reduced structural pressure, tightened routing, and made several contradictions explicit.
That work lowered risk, but it did not by itself prove that the highest-risk seams are semantically correct across state transitions, helper/runtime boundaries, or recovery paths.

This secondary pass exists to answer a different question:

"Given the system that now exists, which small, deliberate reviews will most improve trust that it behaves correctly?"

The answer is not a broad rewrite.
It is a queue of narrow, evidence-backed passes that each start with surrounding-area research, write down the invariants, and then verify or fix one seam at a time.

## What This Pass Adds Beyond The First Pass

The first pass was strong on:

- structural pressure reduction,
- routing cleanup,
- explicit contradiction logging,
- and bounded health remediation.

This pass adds perspectives that are easy to miss during structural cleanup:

1. Invariant integrity: what must always remain true, not just what currently happens on the happy path.
2. Round-trip integrity: whether settings, manifests, or inventories can be saved, reloaded, and reused without drift.
3. Boundary integrity: whether helper, runtime, GUI, controller, and artifact contracts still agree after recent changes.
4. Temporal integrity: whether initialize, refresh, reset, pause, resume, import, delete, and re-run flows preserve the right state over time.
5. Failure and recovery behavior: what happens on missing packs, partial artifacts, stale manifests, invalid settings, and interrupted flows.
6. Evidence integrity: whether our tests and harnesses are actually exercising the claim we think they are exercising.
7. Authority integrity: whether docs, state ledgers, and generated artifacts are being treated with the right level of authority.

## Definition Of Done

A secondary-pass slice is done only when all of the following are true:

1. The seam is explicitly bounded.
2. The surrounding-area packet is written down before editing.
3. The slice risk score and claim-to-evidence map are explicit.
4. The invariants and scenario matrix are explicit.
5. Findings are classified as:
   - fixed now,
   - verified-as-expected,
   - logged in `project_integrity_secondary_pass_notes.md`,
   - or promoted to `feature_state_matrix.md` / backlog / seam docs.
6. The smallest honest validation bundle has been run.
7. The resulting checkpoint is narrow enough to explain in one short handoff.
8. No interesting side finding is left only in chat history.

## Lightweight Review Controls

These controls are intentionally small.
They add rigor without turning every slice into heavy process.

### Risk scoring

Before starting a slice, score it on three dimensions:

- likelihood: how likely the seam is to hide a real defect
- blast radius: how broadly the defect would affect behavior if present
- observability: how hard the defect would be to notice without a deliberate review

Use `low`, `medium`, or `high` for each.

Interpretation:

- `very high` priority: high blast radius plus hard observability, or three clearly elevated dimensions
- `high` priority: any two dimensions elevated
- `medium` priority: one elevated dimension or narrower/localized impact
- `low` priority: bounded, well-exercised seam with easy detection

The score is for sequencing and review depth, not for hiding low-risk work forever.

### Claim-to-evidence traceability

For every slice, write a compact map before editing:

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| What we think is true | Which module or test is supposed to prove it | Harness/test/artifact/doc | verified / uncertain / contradicted |

This helps prevent "verified" from meaning only "someone once wrote it in a doc."

### Finding taxonomy

Every finding should carry a category as well as a disposition.
Use the categories from `project_integrity_secondary_pass_notes.md` so repeated patterns are visible across slices.

## Per-Move Playbook

Every move in the secondary pass should follow this loop.

### 1. Surrounding-area packet

Before changing anything, read the local area around the seam:

- the touched module,
- its immediate callers and callees,
- the closest tests,
- the docs and state-ledger entries making present-tense claims,
- the harnesses or scripts that generate evidence for that area,
- and any recent artifacts or notes already attached to the seam.

Write down:

- the exact seam,
- the main executable contract,
- what is explicitly out of scope,
- the slice risk score,
- and the validation floor for this slice.

If the research reveals multiple seams, split the work before editing.

### 2. Contract sketch

Summarize the seam in plain language:

- who owns the source of truth,
- what inputs are accepted,
- what outputs or persisted state are produced,
- and which layers must agree.

If code and docs disagree, assume code/tests are the stronger signal until evidence says otherwise.

### 2b. Claim-to-evidence map

List the main present-tense claims that matter for this slice and attach each one to:

- the owning module or API,
- the nearest tests or harness,
- the evidence artifact if one exists,
- and the current confidence level.

If a claim has no credible evidence surface, that gap is itself part of the review result.

### 3. Invariant list

Write down the properties that must remain true.
Prefer statements of the form:

- "saving and reloading does not change X"
- "reset removes Y and preserves Z"
- "helper/runtime diagnostics report the same state using compatible fields"
- "generated artifacts reference the same identity across manifest, cache, and consuming layer"

### 4. Scenario matrix

Build a small scenario table before editing:

- happy path,
- degraded path,
- stale or partially-migrated path,
- repeated action / idempotency path,
- and undo/reset/recovery path.

When the seam is persistence-heavy, also ask whether a round-trip or property-style test should exist, for example:

- serialize -> deserialize -> serialize remains stable
- save -> reload -> consume preserves the same identity
- reset -> rerun does not retain stale derived state

The goal is to catch subtle correctness bugs that file-size cleanup would never reveal.

### 5. Verification or fix

Then do one of two things:

- verification-only, if the seam appears correct but under-documented, or
- a bounded fix, if the invariants are actually being violated.

Do not broaden into adjacent cleanups unless the seam cannot be made coherent otherwise.

### 6. Evidence run

Run the smallest honest bundle:

- `V0` for doc and diff hygiene,
- `V1` for changed-scope repo safety,
- `V2` for semantic helper/runtime seams,
- `V3` for SRS seams,
- `V4` for rulegen scoring/filtering/POS seams,
- plus targeted tests for the touched modules.

### 7. Finding classification

Classify every interesting finding:

- fix now,
- doc/state clarification now,
- carry forward in `project_integrity_secondary_pass_notes.md`,
- or promote immediately to `feature_state_matrix.md` if it changes a current truth claim.

Also assign one taxonomy tag:

- `contract mismatch`
- `persistence drift`
- `lifecycle bug`
- `negative-path gap`
- `docs/state drift`
- `false-green evidence`
- `tooling noise`

### 8. Checkpoint

Leave a narrow checkpoint when the slice is coherent.
Before committing, re-read the contract sketch and answer explicitly:

- did this slice change behavior,
- clarify existing behavior,
- or only improve evidence and structure?

If the slice uncovered another seam, start a new backlog item or notes-ledger entry instead of silently carrying extra scope forward.

## No-Go Rules

1. Do not use the secondary pass as cover for a broad refactor.
2. Do not relax baselines, thresholds, or policy files to make evidence look cleaner.
3. Do not promote planning text into current truth without code/tests/evidence.
4. Do not fix out-of-scope observations in the same slice unless they block the seam under review.
5. Do not close a slice while a meaningful side finding exists only in conversation history.

## Periodic Synthesis Checkpoints

After every two or three completed slices, stop and do a short synthesis pass:

1. re-read the notes ledger
2. look for repeated taxonomy patterns
3. re-rank the remaining queue using the risk scores
4. decide whether any recurring manual scenario should become an automated test
5. update the plan order only if the new evidence justifies it

This keeps the plan responsive without turning it into a moving target every hour.

## Current Synthesis Checkpoint (2026-04-18)

Context:

- completed slices since the previous synthesis stop: `D7` runtime diagnostics join point and `D8` extension/UI admission wiring

Observed repeated patterns:

1. `false-green evidence` is now a confirmed recurring pattern.
   - D7 needed explicit LP E2E assertions so publication-manifest existence and generation-family coherence stopped being only implied.
   - D8 found a Phase 5 validation note already citing a Node-backed workflow test that had not yet been committed into the tree.
2. cross-layer seams remain most trustworthy when the evidence sits exactly at the join point rather than only in broad harnesses.
   - examples: runtime diagnostics payload assertions and Node-backed controller/workflow propagation tests.
3. previously logged negative-path concerns remain real but did not justify reordering the next slice.
   - partial-save behavior (`N-005`)
   - forgiving active-inventory drift model (`N-006`)

Queue decision:

1. keep `E1` through `E4` next in order.
   - D8 closed the immediate extension-side admission wiring audit.
   - the next highest-value correctness seam is still data-source normalization holdouts across tooling, runtime resolution, and docs.
2. keep `F14` after the `E` wave unless E1-E4 uncovers a concrete behavior bug that makes the preventive split urgent.
   - D8 confirmed that the current workflow structure is near-limit and worth splitting later, but not currently incorrect.
3. keep `N-002` as tooling follow-through rather than promoting it into the execution queue ahead of product seams.

Automation candidates:

1. already promoted during these slices:
   - explicit LP E2E manifest-family assertions in `D7`
   - committed Node-backed workflow propagation coverage in `D8`
2. next likely automation target:
   - after `E1` maps the translation-pack holdouts, add a small regression bundle that proves benchmark/tooling/runtime surfaces all resolve the same managed-vs-legacy translation-pack contract before docs cite it as current truth.

Net effect:

- no major queue reorder
- stronger bias toward seam-local executable evidence before present-tense checkpoint docs make validation claims
- proceed next with `E1` translation-pack holdout audit

## E1 Checkpoint (2026-04-18)

Context:

- completed slice since the last synthesis stop: `E1.1` translation-pack tooling holdout audit

Observed outcome:

1. the benchmark/runtime translation-pack seam is behaving better than the remaining developer-facing copy suggested.
   - benchmark default resolution, helper/runtime pack refs, and benchmark resource payload identity now have direct shared regression coverage for both manifest-backed installs and legacy flat SQLite defaults.
2. covered synthetic SRS harness defaults are already aligned with the SQLite-first direction.
   - `en-es` journey fixtures and `en-de` quality-harness translation fixtures remain SQLite-backed rather than TEI-backed.
3. the main remaining translation-pack holdout is now narrower than the original `E1` risk shape.
   - benchmark CLI copy was cleaned up in this slice.
   - probe-side path-shaped copy/output remains a carry-forward item because that file is already mid-split and did not justify mixing a larger refactor into this checkpoint.

Queue decision:

1. proceed next with `E2` frequency-pack holdout audit.
   - translation-pack runtime correctness did not uncover a deeper bug that would justify reordering the queue.
2. keep `E4` in place for the remaining installed-vs-manual wording cleanup.
   - `N-008` now captures the probe-side holdout so it does not get lost.

Net effect:

- `E1` raised the evidence level around translation-pack normalization without broad behavior churn
- benchmark/help surfaces are closer to the managed-pack contract
- the next highest-value normalization seam is still frequency-pack follow-through

## E2 Checkpoint (2026-04-18)

Context:

- completed slice since the previous checkpoint: `E2.1` frequency-pack tooling and diagnostics holdout audit

Observed outcome:

1. the frequency-pack runtime seam is already consistent across the helper entrypoints, native host, and runtime diagnostics.
   - managed manifest-backed installs resolve to the same `main.sqlite` artifacts through helper CLI defaults, native-host defaults, and diagnostics.
   - legacy flat `freq-*.sqlite` files still act as compatibility fallback when no managed install is present.
2. the main practical gap in this seam was wording, not resolution behavior.
   - helper subcommands that accepted `--set-source-db` described it as a raw SQLite path without saying installed frequency packs were the default.
3. one broader holdout remains outside this bounded slice.
   - execution-layer helper/native-host APIs still use the path-first `set_source_db` field name, which is acceptable for now but should remain explicit as a compatibility/debug override rather than being mistaken for the managed-pack contract.

Queue decision:

1. proceed next with `E3` embedding-pack settings/runtime split audit.
   - `E2` did not uncover a deeper frequency correctness defect that justifies reordering the queue.
2. keep `E4` for the remaining installed-vs-manual contract cleanup across helper/tooling/UI wording.
   - `N-008` and `N-009` now capture the remaining translation/frequency path-shaped surfaces.

Net effect:

- `E2` raised the evidence level around frequency-pack defaults and diagnostics without broad behavior churn
- helper/help surfaces are closer to the installed-pack-first contract
- the next highest-value normalization seam remains embedding follow-through

## Secondary-Pass Perspectives

Use these perspectives deliberately.
They are the viewpoints the first pass only partially exercised.

### A. Persistence and round-trip integrity

Questions:

- Does save -> reload -> consume preserve identity and intent?
- Are managed ids and manual compatibility paths staying in their intended lanes?
- Do imports, exports, and share payloads round-trip without silent drift?

### B. Cross-layer contract integrity

Questions:

- Do helper, runtime, GUI, controller, and docs use the same names, shapes, and semantics?
- Are diagnostics fields aligned enough for operators to reason about failures?
- Has lazy loading changed import behavior without changing contract behavior?

### C. Temporal and lifecycle integrity

Questions:

- What happens across initialize, refresh, reset, delete, pause, resume, install, unlink, and retry flows?
- Are caches, manifests, inventories, or derived artifacts invalidated at the correct times?

### D. Failure and degraded-mode integrity

Questions:

- What happens with missing packs, stale manifests, partial outputs, incompatible settings, or absent helper capabilities?
- Do we fail loudly enough to be diagnosable without corrupting state?

### E. Evidence and false-green integrity

Questions:

- Are tests/harnesses covering the actual risky behavior or only a nearby proxy?
- Are warnings being normalized into background noise?
- Are generated artifacts fresh enough to justify any claim they are supporting?

### F. Authority and documentation integrity

Questions:

- Is a generated report being treated as if it were architecture truth?
- Are `implemented`, `default-on`, and `verified` still separated?
- Are contradictions being made explicit rather than hand-waved away?

## Secondary-Pass Track Queue

The queue below is the recommended order after the structural-health pass.
Each track should still be split into narrow checkpoint slices during execution.

| Track | Focus | Risk | Why it is next | Validation floor | Related backlog ids |
|---|---|---|---|---|---|
| `SP1` | Resource settings and round-trip correctness | `very high` | Recent work touched settings/resource seams, and round-trip drift here can poison later passes. | `V0`, `V1`, targeted GUI/settings tests | `E1`, `E2`, `E3`, `E4`, `F15`, `F16` |
| `SP2` | SRS profile, admission, publication, and runtime correctness | `very high` | This seam is stateful, cross-layer, and already has a known due-aware warning that needs a deliberate answer. | `V0`, `V1`, `V3`, targeted SRS tests | `C1`, `C3`, `C4`, `D2`-`D8` |
| `SP3` | Semantic publication and runtime contract correctness | `high` | Semantic publication/runtime claims span docs, helper outputs, diagnostics, and runtime fallback behavior. | `V0`, `V2`, targeted semantic/helper tests | `B1`-`B5` |
| `SP4` | Rulegen artifact and source-selection correctness | `high` | Structural splits reduced pressure, but source resolution and artifact identity still need correctness review. | `V0`, `V4`, targeted rulegen tests | `E1`, `B3`, `F12`, `F13` |
| `SP5` | Extension/controller workflow correctness | `high` | Controller ordering, module loading, share/import, and runtime scan behavior need explicit post-refactor verification. | `V0`, `V1`, targeted extension/controller tests | `C2`, `D8`, `F14` |
| `SP6` | Documentation, state-ledger, and backlog reconciliation | `medium` | After seam reviews, current-truth docs and backlog snapshots need to reflect what was actually learned. | `V0`, `V1`, `check:state` when needed | `A2`, `A3`, `A4`, `B6` |
| `SP7` | Evidence and tooling reliability | `medium-high` | We should tighten the signal quality of the harnesses and repo-safety output before calling the broader cleanup "trustworthy". | `V0`, `V1`, targeted tooling checks | `G1`-`G4` |

## Track Detail

### `SP1`: Resource Settings And Round-Trip Correctness

Primary question:
Can managed and manual resource configuration survive save/load/use/delete flows without identity drift?

Seed slices:

1. settings serialization authority (`AppSettings`, resource config models, manifest-backed ids)
2. managed-id vs manual-path separation
3. install/unlink/delete conversion lifecycle
4. panel-state/UI snapshot coherence after reload

Core invariants:

- managed resources persist by id, not by accidental path backfill
- manual compatibility paths do not overwrite managed identity
- mixed managed/manual state remains distinguishable after reload
- remove/unlink actions do not leave orphaned UI or stale config state

Manual scenario checklist:

1. save managed translation/frequency/embedding pack selections, restart the settings surface, and confirm ids survive without path drift
2. save a mixed managed/manual configuration, reload it, and confirm the two modes remain distinguishable
3. unlink or delete an installed pack, reload, and confirm stale UI state and stale config fields are gone
4. run a serialize -> deserialize -> serialize comparison for the touched settings objects where practical
5. verify the consuming helper/runtime path resolves the same resource identity that the UI persisted

### `SP2`: SRS Profile, Admission, Publication, And Runtime Correctness

Primary question:
Do profile settings, admission planning, publication, and runtime serving still describe the same executable system?

Seed slices:

1. profile schema and sizing authority
2. preview/rebalance contract and non-mutating guarantees
3. initialize/refresh/reset inventory correctness
4. due-aware publication and runtime-serving semantics
5. diagnostics coherence across helper/runtime/UI

Core invariants:

- profile inputs are validated against the actual supported schema
- preview paths do not mutate live state unless explicitly meant to
- refresh/reset mutate only the artifacts they own
- published, admitted, due, and served sets have explainable relationships

Manual scenario checklist:

1. edit profile settings, save, reload, and confirm the persisted schema matches the supported allowlist and sizing authority
2. run preview/rebalance paths and confirm they do not mutate live state before an explicit apply step
3. execute initialize -> refresh -> reset on the same pair/profile and inspect diagnostics after each stage
4. compare admitted, published, due, and served counts in a scenario that exercises the known due-aware warning
5. repeat a pause/resume or rerun flow and confirm state transitions stay explainable rather than accumulating stale inventory

### `SP3`: Semantic Publication And Runtime Contract Correctness

Primary question:
Are semantic artifacts, helper outputs, diagnostics, and runtime gating still coherent after the recent cleanup work?

Seed slices:

1. manifest, `generation_id`, and reset semantics
2. helper/runtime fallback and eligible-match gating
3. diagnostics field consistency across cache/helper/runtime layers
4. PoC boundary clarity for emitted-sibling `ready` pointers and LP-specific behavior

Core invariants:

- publication artifacts identify one coherent generation
- reset actually removes the semantic state the runtime expects to be gone
- runtime fallback behavior matches the docs and diagnostics
- PoC behavior is not silently described as full readiness

### `SP4`: Rulegen Artifact And Source-Selection Correctness

Primary question:
After structural splits and lazy loading, are rulegen inputs, source resolution, and emitted artifacts still equivalent in meaning?

Seed slices:

1. translation/frequency/embedding pack source resolution
2. artifact referential integrity across manifests, word packages, and helper consumers
3. lazy-load equivalence for helper/rulegen entrypoints
4. FAIL/REVIEW triage follow-through for benchmark cases

Core invariants:

- resource selection uses the intended authority path
- generated artifacts point to the same identity across producer and consumer surfaces
- lazy-load changes do not silently change contract behavior
- unresolved benchmark failures are either promoted to cases or explicitly explained

### `SP5`: Extension And Controller Workflow Correctness

Primary question:
Did the options/controller/runtime splits preserve behavior across boot order, workflow transitions, and share/import flows?

Seed slices:

1. options bootstrap and module-load contract
2. profile share/import/export payload fidelity
3. SRS workflow action transitions
4. DOM scan ordering and scan-budget behavior

Core invariants:

- module registration order still satisfies the pages that consume it
- share/import round-trips preserve the fields the receiving side expects
- controller actions leave state transitions explainable and idempotent where intended
- scan ordering changes do not silently widen runtime work or miss caps

### `SP6`: Documentation, State-Ledger, And Backlog Reconciliation

Primary question:
After the seam reviews, do our current docs and ledgers say exactly what the system now supports and what remains unresolved?

Seed slices:

1. feature-state contradiction refresh
2. stale present-tense claims in seam docs
3. backlog snapshot refresh after structural-health completion
4. generated-evidence references that need narrower wording

Core invariants:

- current docs route to the right authority surface
- `implemented`, `default-on`, and `verified` remain separate
- stale planning snapshots are not left looking current

### `SP7`: Evidence And Tooling Reliability

Primary question:
Can we trust the signals produced by our local safety loop, or are important warnings being normalized away?

Seed slices:

1. repo-safety advisory noise, including local style-tool availability
2. harness coverage gaps and warning semantics
3. artifact freshness and stable handoff paths
4. missing checks that would catch likely cross-layer regressions earlier

Core invariants:

- local safety commands produce actionable signal
- warnings that matter are visible and interpretable
- evidence paths are stable enough for later review

## Recommended Starting Order

Recommended near-term order:

1. `SP1`: resource settings and round-trip correctness
2. `SP2`: SRS profile/admission/publication/runtime correctness
3. `SP3`: semantic publication/runtime correctness
4. `SP5`: extension/controller workflow correctness
5. `SP4`: rulegen artifact correctness
6. `SP6`: docs/state/backlog reconciliation
7. `SP7`: evidence/tooling reliability

Reasoning:

- `SP1` and `SP2` sit on the most stateful user-facing seams touched by recent cleanup.
- `SP3` is the next highest contract-risk area because it crosses helper/runtime/docs boundaries.
- `SP5` verifies the UI and runtime seams whose structure changed most recently.
- `SP4` should happen after the higher-level contract seams are freshly understood, because rulegen evidence is expensive and easier to interpret once those boundaries are clearer.
- `SP6` and `SP7` close the loop by reconciling current-truth docs and improving trust in the evidence itself.

## Recording Side Findings

Any interesting observation that is not part of the current slice should go into `project_integrity_secondary_pass_notes.md` before the slice is closed.

Use that ledger for:

- out-of-scope correctness observations,
- tooling noise that should be cleaned up later,
- stale docs/backlog snapshots discovered mid-pass,
- and questions that need a future seam-specific review.

Do not silently hold those items in memory.
