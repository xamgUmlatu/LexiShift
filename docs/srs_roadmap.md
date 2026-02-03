# SRS Roadmap (S‑growth + Practice Layer)

## Goal
Build a non‑destructive SRS Practice Layer that grows a set **S** of learning items per language pair, schedules exposure, and adapts to user feedback. S is driven by:
- High‑frequency base lexicon
- User text stream (what they read/write)
- Optional dictionary/embedding confidence
- Due‑based sampling + capacity throttling

## What’s already completed
1) **Practice Layer design**
- `docs/srs_practice_layer_design.md` (architecture + MVP outline)

2) **SRS schema**
- `docs/srs_schema.md` (settings, items, store, bundle format)

3) **Core SRS data model + persistence**
- `core/lexishift_core/srs.py` (settings, items, store, bundle, load/save)

4) **Scheduler logic (MVP)**
- `core/lexishift_core/srs_scheduler.py`
  - due‑based selection
  - rating feedback (Again/Hard/Good/Easy)

5) **Practice gate (runtime filter)**
- `core/lexishift_core/srs_gate.py` (non‑destructive rule filtering)

6) **SRS store persistence (GUI state layer)**
- `apps/gui/src/state.py` now loads/saves `srs_store.json`

7) **Embeddings per language‑pair**
- Embeddings are now pair‑aware and rules store `language_pair` metadata.

8) **Practice gate integration (GUI preview)**
- GUI preview uses active SRS items to filter rules at runtime.
- Falls back to normal behavior when SRS is disabled or empty.

---

## Remaining steps (by phase)

### Phase 1 — Minimal SRS practice gate (no UI yet)
- **Practice gate (runtime filter)** ✅
  - Filter rules by active SRS items without mutating rulesets.
  - Keep “SRS off” behavior identical to today.
- **SRS store integration** ✅
  - SRS store is loaded/saved in the GUI state layer (`srs_store.json`).
  - Export/import bundle paths still pending.

### Phase 2 — Initial UX hooks
- **Feedback capture**
  - Minimal rating UI (Again/Hard/Good/Easy) for replacements.
  - Log feedback to SRS store history.
- **Practice mode toggle**
  - A global “SRS mode” switch that activates the practice gate.

### Phase 3 — Growing S (core sources)
- **High‑frequency lexicon base**
  - Per language pair, seed S with top‑N frequency list.
- **Coverage scalar**
  - Use a single slider value to control expansion beyond the base lexicon.

### Phase 4 — User‑context growth
- **Text stream collector**
  - Collect words the user reads/writes (on‑device only).
  - Add recurring words into candidate pool for S.
- **Eligibility rules**
  - Define thresholds for “recurring” vs “one‑off”.

### Phase 5 — Quality & confidence metrics
- **Consensus filter (optional)**
- **Embedding ranking (optional)**
- **Confidence score**
  - Use dictionary/embedding agreement to score candidates.
  - Optionally weight SRS frequency by confidence.

### Phase 6 — Synchronization & persistence
- **Export/import settings**
  - SRS settings + store bundle should sync across app/extension/plugin.
- **Progress history**
  - Persist historical progress so learning history is never lost.

---

## Metrics we intend to use
- **Due‑based scheduling** (core SRS mechanic)
- **Capacity** (max active items, max new items/day)
- **Frequency base** (high‑frequency lexicon)
- **User stream recurrence** (what they actually read/write)
- **Consensus filter** (multi‑dictionary agreement)
- **Embedding similarity** (ranking/threshold)
- **Confidence score** (optional weight for SRS frequency)

---

## MVP recommendation
- Practice gate + scheduler + feedback capture
- High‑frequency base seed
- Coverage scalar
- Export/import of SRS settings + store

Everything else (consensus, embeddings, user streams) can be layered on later via plug‑ins.
See also: `docs/rule_generation_technical.md` for precomputed rule + confidence plans.

---

## Implementation workstream tracking

### Workstream A — Practice gate + scheduling ✅
- Core SRS models, scheduler, gate, and GUI preview integration are in place.
- Chrome Extension: SRS mode can gate rules using the fixed selector dataset (test only).
- Extension feedback UI + logging are implemented (Ctrl+1/2/3/4 popup).
- Exposure logging is available (Advanced → Logging).
- Extension logs now update a local `srsStore` snapshot for future sync.

### Workstream B — S growth (seed + expansion) ⏳
- **Seed with frequency lists** ✅ (`core/lexishift_core/srs_seed.py`).
- **JA seed logic:** `core_rank` selection + `pmw` weighting + JMDict filter (implemented).
- **Coverage scalar** to expand beyond seed ✅ (`core/lexishift_core/srs_growth.py`).
- **Growth planning + store updates** ✅ (`core/lexishift_core/srs_growth.py`, `core/lexishift_core/srs_store_ops.py`).
- **GUI wiring (seed refresh)** ✅ Settings save triggers JA seed growth when packs are available.
- **Candidate ingestion** (not implemented).
- **Selector test dataset** ✅ (`docs/srs_selector_test_dataset.json`)
- **Selector harness** ✅ (`scripts/srs_selector_demo.py`, `core/lexishift_core/srs_selector.py`)

### Workstream C — User stream intake ⏳
- Text stream capture + recurrence thresholds not implemented.
- Requires language detection/segmentation for JP.

### Workstream D — Quality & confidence scoring ⏳
- Consensus + embedding ranking are planned but not wired into SRS growth yet.
 - Rule generation confidence scaffolding exists; see `docs/rule_generation_technical.md`.

### Workstream E — Sync/export ⏳
- Bundle format exists; export/import UI + wiring pending.

---

## Data requirements & current status (S growth)

### Required (for MVP S growth)
1) **Monolingual frequency lists** (EN, DE, JP)
   - Used to seed S with top‑N lemmas.
   - **Status:** EN + JP downloaded and converted to SQLite via GUI frequency packs. DE still pending.
   - **Decision (JA seed):** use `core_rank` from BCCWJ for selection; use `pmw` for weighting.

2) **Language‑aware tokenization/segmentation**
   - EN/DE: word tokenization is already available in the engine.
   - JP: requires a segmentation strategy for user‑stream intake (not implemented yet).

### Optional (quality boosts)
3) **Lemma/POS metadata**
   - Improves filtering (e.g., only nouns/verbs).
   - **Status:** depends on source list.
   - **Decision:** JMDict‑filtered seed ensures every S item has a dictionary entry.

4) **Embedding files per language pair**
   - Used for confidence and ranking (optional).
   - **Status:** optional, not required for MVP S growth.

5) **Dictionary confidence signals**
   - Consensus across dictionaries (planned).
   - **Status:** dictionaries exist; consensus logic not wired to SRS.

### User‑stream data (generated by app)
6) **User text stream**
   - Captured from app/extension/plugin during normal use.
   - **Status:** ingestion pipeline not built yet.
