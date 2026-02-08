# SRS Hybrid Model Technical Spec (Feedback-Driven)

## Purpose
Define a concrete architecture for set `S` as "the user's current study inventory," while keeping room for future profile-driven growth.

This spec resolves ambiguity between:
- "set of active words"
- "probability distribution over all words"

The adopted model is a hybrid.

---

## 1) Core decisions

1. `S` is the persisted study inventory (sparse, explicit items).
2. The full corpus is not stored as dense probabilities; non-members are implicit weight `0`.
3. Scheduling is event-driven by user feedback only.
4. Showing a replacement in UI is **not** a scheduling event.
5. Feedback uses the existing 4-choice UI:
   - `1` -> `again`
   - `2` -> `hard`
   - `3` -> `good`
   - `4` -> `easy`

---

## 2) Hybrid model

### 2.1 Candidate universe `U` (logical, not fully persisted)
- Derived from frequency packs, dictionaries, curated sources, and later profile signals.
- Provides candidates for introducing new items into `S`.

### 2.2 Study inventory `S` (persisted)
- Stored in helper-owned `srs/profiles/<profile_id>/srs_store.json`.
- Each item tracks learning state + scheduling fields.
- Sparse representation keeps storage bounded and avoids writing entire corpus.

### 2.3 Due set `D` (runtime view)
- `D = { item in S | item.next_due <= now or item.next_due missing }`
- Scheduler serves due items first.

### 2.4 Introduction frontier `N` (runtime view)
- Candidates from `U` not currently in `S`.
- Ranked by bootstrap/profile policy when new capacity is available.

### 2.5 Two-weight model (explicit)
- **Weight 1 (admission weight)**: used only to decide which candidates enter `S`.
- **Weight 2 (serving priority)**: used only to decide which items already in `S` are shown next.
- Weight 1 can depend on frequency rank, POS filters/biases, and profile signals.
- Weight 2 should stay dominated by SRS state (`next_due`, `stability`, `difficulty`) and policy caps.
- Current bootstrap default POS ordering is explicit and centralized in code (`srs_admission_policy.py`):
  - noun > adjective > verb > adverb > other
  - coefficients are named constants, not inlined magic numbers.

---

## 3) Item lifecycle states

Recommended state machine (target architecture):
- `new`: item admitted to `S`, no feedback yet.
- `learning`: early repetitions after first failures/successes.
- `review`: stable periodic review state.
- `mature`: long-interval items (still in `S`, low frequency).
- `relearn`: item lapsed after being stable.
- `suspended`: temporarily excluded from serving.

State transitions are driven by feedback ratings and scheduling thresholds.

---

## 4) Scheduling policy

### 4.1 Serving priority
1. Serve due items (`D`) sorted by oldest `next_due`.
2. If daily/session budget remains, admit new items from `N`.
3. Never exceed caps:
   - `max_active_items`
   - `max_new_items_per_day`

### 4.2 Feedback update semantics (MVP-compatible)
Current helper logic already supports these effects:
- `again`:
  - decreases stability
  - increases difficulty
  - short next interval
- `hard`:
  - slight stability growth
  - slight difficulty increase
  - medium next interval
- `good`:
  - stronger stability growth
  - slight difficulty decrease
  - longer next interval
- `easy`:
  - strongest stability growth
  - larger difficulty decrease
  - longest next interval

This naturally gives:
- mastered words -> lower appearance frequency (long intervals)
- forgotten words -> higher appearance frequency (short intervals)

### 4.3 Probability usage (where it still fits)
Probability/weighted scoring is useful for:
- selecting which new candidates enter `S`
- tie-breaking when multiple due/new items compete
- profile-aware personalization

Probability should not replace due-based scheduling as the primary review driver.

---

## 5) Data model guidance

Per-item fields that make the model extensible:
- identity:
  - `item_id`, `lemma`, `language_pair`
- provenance:
  - `source_type` (`initial_set`, `frequency_list`, `user_stream`, `curated`, `extension`, ...)
- scheduler:
  - `next_due`, `last_seen`, `stability`, `difficulty`
- state:
  - `status` (target state machine above)
  - `lapses`, `review_count` (planned)
- history:
  - timestamped feedback entries (`again|hard|good|easy`)
- optional ranking metadata:
  - `base_weight`, `profile_weight`, `priority_bias`

---

## 6) Signals and ingestion policy

Scheduling signals (authoritative):
- feedback events only (`again|hard|good|easy`)

Non-authoritative telemetry:
- exposure/display logs may still be stored for analytics/debugging
- these do not change scheduling directly in this model

This separation prevents accidental schedule drift from passive displays.

---

## 7) Integration with current surfaces

Chrome extension and Discord plugin should both:
1. emit feedback events with pair + lemma + rating
2. rely on helper as source of truth for `S`
3. consume helper outputs for active/due behavior

The options debug button should be interpreted as:
- "show rulegen output for current helper-managed `S`"
- not "regenerate all rules from the global corpus"

---

## 8) Initial `S` bootstrap (starter policy)

Recommended practical starter policy:
1. initialize `S` from a high-frequency, dictionary-valid subset for pair
2. cap by explicit sizing policy:
   - `bootstrap_top_n` default `800` (clamped)
   - `initial_active_count` default `40` (clamped, never above bootstrap size)
3. start with neutral scheduler parameters
4. move quickly to feedback-driven adaptation

Practical JP note:
- Because high-frequency Japanese corpora contain many function words, bootstrap admission should apply stopword/POS filters before finalizing the first active subset.

This keeps startup quality high while avoiding premature complexity.

---

## 9) Future profile-driven growth

Profile data should guide:
- admission into `S` (what gets added)
- priority bias (what gets added first)

Profile data should not directly override per-item SRS review math after admission; feedback remains primary.

Planned profile-driven strategies:
- `profile_bootstrap`
- `profile_growth`
- `adaptive_refresh` (feedback aggregation based)

---

## 10) Practical implication for current WIP

Today:
- helper scheduler + feedback updates already exist
- set planner/profile weighting is scaffolded
- feedback popup (1..4) already maps cleanly to scheduler inputs

Next architecture step:
- route all new-item admissions through planner policy
- keep review scheduling strictly feedback-driven
- treat exposure as analytics only unless policy later opts in explicitly
