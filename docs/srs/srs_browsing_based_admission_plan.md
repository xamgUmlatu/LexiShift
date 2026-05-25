# Browsing Data-Based SRS Admission Plan

Status: active planning workstream
Role: Planning / WIP
Last updated: 2026-05-26
Last verified: 2026-05-26 by SRS hybrid model, interest-tailored admission algorithm, helper exposure path, signal queue, profile-context code reads, browsing-admission research harness, read-only backend simulation prototype, fractional browsing-budget tests, and SRS quality harness seeded browsing preview
Purpose: define the planned opt-in browsing word-signal layer for SRS admission without treating passive browsing as review feedback
Source-of-truth: planning reference only; current executable truth lives in SRS/helper code, extension signal code, tests, generated SRS artifacts, and `docs/developer/feature_state_matrix.md`.

## Product Goal

Use the learner's actual reading life to shape future SRS admission.

The intended product behavior is:

> Words the user repeatedly encounters while browsing become more likely to
> enter SRS, if they fit the learner's level and are supported by LexiShift's
> source data.

The intended product behavior is not:

> Automatically study every word the user browses, infer private interests from
> pages, or treat passive page views as successful SRS reviews.

This feature must be opt-in. It should feel like "make SRS more relevant to
what I read," not like hidden surveillance or automatic curriculum takeover.

## Current Architecture Fit

LexiShift's SRS model already has the required separation:

- feedback events are authoritative for scheduling;
- exposure/display logs are non-authoritative;
- admission into `S` is separate from review scheduling after admission;
- profile context can influence admission previews and future admission
  strategies;
- the helper owns persisted SRS state and the signal queue.

This feature should extend the admission signal layer. It should not change the
FSRS scheduler directly.

Hard boundary:

- browsing signals may affect **Weight 1**: admission probability into `S`;
- browsing signals must not directly affect **Weight 2**: due scheduling or
  FSRS state for already-admitted items;
- only explicit SRS feedback (`again`, `hard`, `good`, `easy`) changes
  scheduler state.

SRS-specific constraint:

- admission is sticky. Once a word enters `S`, it normally stays in review until
  the learner masters it, suspends/discards it, or a later lifecycle policy
  removes it. Therefore browsing relevance must be treated as review-budget
  pressure, not as a disposable ranking hint.
- browsing should influence *which eligible new words* compete for limited
  admission slots. It must not make accidental one-page exposure create durable
  review debt.

## Current Executable Admission Audit

Current code has three different SRS admission-related surfaces. They should
not be treated as interchangeable.

1. **Admission preview**
   - Options uses the admission preview button to call the helper
     `srs_preview_admission` path.
   - This path is non-mutating and already supports weighted-without-replacement
     preview sampling.
   - This is the best first integration point for browsing-based scoring
     because it can show neutral vs browsing-influenced results without creating
     durable review obligations.

2. **Initial set creation**
   - Options uses the initialize button to call `srs_initialize`.
   - The helper builds seed candidates, applies profile topic overlays when
     present, selects the initial active set, persists selected `SrsItem` rows,
     updates active inventory, and publishes rulegen outputs.
   - Browsing should not silently affect this path until the user has opted in
     and preview diagnostics are available.

3. **Refresh / growth admission**
   - Options uses the refresh button to call `srs_refresh`.
   - The helper computes a hard admission budget from `max_active_items`,
     `max_new_items_per_day`, current due pressure, and feedback-window
     retention.
   - If budget remains, growth admission filters out existing lemmas and selects
     new candidates by ranked score.
   - This is the right eventual runtime mutation point for browsing influence,
     because it already has review-pressure and feedback-safety gates.

There is also a **rebalance** surface. Rebalance can park swappable active
items and activate better candidates, but it is not the same as full deletion
or permanent release. Mature or well-established items are protected by
history, stability, or future review due date.

Lifecycle caveat:

- `SrsItem` currently stores scheduler fields, exposures, history, and
  word-package metadata, but it does not expose a canonical persisted
  `discarded`, `suspended`, `released`, or `mastered` lifecycle flag.
- Selector code has a `mastered` penalty concept, and rebalance has
  protected/swappable/parked states, but those are not yet a full user-facing
  lifecycle contract.
- Actual browsing-influenced admission should therefore wait for either a
  lifecycle blocklist/cooldown surface or an explicit decision that
  re-suggestion after discard/suspend is out of scope.

Existing exposure paths are also not the right browsing-admission substrate:

- extension exposure logging may retain URL and writes to extension-local
  storage;
- extension-local exposure recording can create local store rows;
- the native helper exposure endpoint can create helper SRS items when called
  with missing lemmas.

Browsing admission should use a stricter separate aggregate signal store:
bounded counts in, no raw text, no URL by default, no direct SRS item creation.

## P0 Scope

P0 is word-level browsing relevance only.

In scope:

- exact normalized source-word hits from visible browsing text;
- exact normalized target-word hits when the user browses target-language text;
- explicit or conservatively inferred page language side, so source-language
  pages do not accidentally count same-spelling target lemmas as direct target
  hits;
- LexiShift replacement exposure counts as a low-to-medium relevance signal;
- decayed, capped local counters;
- admission preview diagnostics comparing neutral and browsing-influenced
  admission;
- later gated admission boost after preview and tests prove smooth behavior.

Out of scope for P0:

- topic inference from browsing;
- page classification;
- embeddings;
- LLM analysis;
- raw page-text retention;
- long-term per-site profiles;
- automatic scheduling updates from passive exposure.

Topic inference is intentionally deferred because users already have explicit
topic controls. Word-level signal inference is more direct, more explainable,
and easier to bound mathematically.

Both reading directions matter:

- beginners may mostly browse source-language pages, so source-side tokens need
  to map through the source-target bridge;
- advanced users may browse target-language pages, so target-side direct lemma
  hits should be supported when page language side is known or inferred
  confidently;
- mixed pages can emit both sides, but direct target hits should stay disabled
  for source-side packets to avoid same-spelling false positives.

## Privacy Policy

Default posture:

- off by default;
- local-only;
- profile-scoped;
- no raw page text stored;
- no URL storage for the browsing-admission signal by default;
- no remote sync or telemetry;
- disabled in private/incognito contexts;
- ignore password fields, text inputs, editable fields, hidden DOM, and local
  files unless a later policy explicitly permits them;
- per-site pause and denylist controls;
- clear-data action for browsing admission signals.

The current developer reference notes that existing exposure telemetry may
retain URL. Browsing admission should use a stricter separate signal surface
instead of relying on URL-retaining exposure logs.

Suggested user-facing copy:

> Use words from pages I read to make future SRS suggestions more relevant.

Suggested diagnostics:

- recent boosted words;
- signal age;
- whether a word came from source-side reading, target-side reading, or
  LexiShift replacement exposure;
- no raw text preview unless a developer-only debug mode is explicitly enabled.

## Signal Model

The browser should not score the whole corpus on every page. It should emit a
small local signal packet.

P0 packet shape:

```json
{
  "version": 1,
  "pair": "en-es",
  "profile_id": "default",
  "source": "browsing_visible_text",
  "captured_at": "2026-05-23T00:00:00+00:00",
  "signals": [
    {
      "surface": "mortgage",
      "side": "source",
      "normalized": "mortgage",
      "count": 2
    },
    {
      "surface": "hipoteca",
      "side": "target",
      "normalized": "hipoteca",
      "count": 1
    }
  ]
}
```

The helper should aggregate to a profile/pair browsing-signal store, not write
raw page text.

Candidate aggregate shape:

```json
{
  "version": 1,
  "pair": "en-es",
  "profile_id": "default",
  "updated_at": "2026-05-23T00:00:00+00:00",
  "items": {
    "hipoteca": {
      "target_lemma": "hipoteca",
      "source_hit_count": 4.2,
      "target_hit_count": 1.0,
      "replacement_exposure_count": 0.0,
      "last_seen_at": "2026-05-23T00:00:00+00:00",
      "source_mapping_confidence": 0.85
    }
  }
}
```

Counts in the aggregate should be decayed values, not unbounded lifetime totals.

## Computational Model

The efficient path is simple:

1. Browser extracts visible tokens locally.
2. Browser normalizes and caps token counts.
3. Helper maps source-side hits to candidate target lemmas using installed
   source-target data.
4. Helper updates bounded decayed counters.
5. Admission preview or refresh later reads candidate browsing values by lemma.

Expected complexity:

```text
page capture: O(visible_tokens)
helper aggregation: O(unique_capped_tokens + mapped_targets)
admission scoring: O(candidate_count)
```

For a `10,000` candidate frontier, admission-time dictionary lookups are cheap.

Avoid for P0:

- browser-side full-corpus scans;
- embeddings at page time;
- page-wide semantic classifiers;
- running a model or LLM over page content;
- source-target mapping loops that scale with the full dictionary for every
  page.

Implementation hint:

- build a compact lookup index for normalized source terms to target candidates;
- build a compact target lemma set for direct target-side hits;
- cap each page to a small unique-token budget before helper submission.
- disable direct target lookup unless the packet says `side=target` or
  `side=mixed`; source-side same-spelling words should only flow through the
  source-target bridge.

## Resource, Timing, And Latency Budget

The feature should be shaped as a low-priority signal path. It must not make
normal browsing, replacement, or review feel slower.

Recommended E2E timing:

1. **Page-time capture**
   - collect visible tokens from already-scanned text where possible;
   - debounce capture until the page is idle or after a short delay;
   - cap unique normalized tokens per page before any helper call;
   - cap per-token contribution from one page;
   - drop the packet rather than blocking the page when the extension is busy.

2. **Local packet buffer**
   - keep only compact normalized counts in memory or extension storage;
   - flush in small batches, for example on idle, on tab hidden, and on a
     periodic timer;
   - coalesce repeated page packets before helper submission;
   - tolerate packet loss because browsing signals are relevance hints, not
     authoritative progress records.

3. **Helper ingest**
   - update a bounded aggregate store with decayed counts;
   - use source/target lookup indexes keyed by pair and source-pack version;
   - avoid scanning the full dictionary or full candidate corpus for every
     page packet;
   - prune low-signal and stale rows during ingest or read.

4. **Admission-time scoring**
   - read browsing aggregates only during preview, simulation, initialize, or
     refresh workflows;
   - never rescore admission probabilities during ordinary review display;
   - recompute user-specific probabilities on demand instead of caching stale
     final probabilities;
   - persist selected decisions and explanations, not every transient score.

Initial budgets to validate in tests and local profiling:

| Budget | Suggested starting point | Rationale |
| --- | ---: | --- |
| Per-page unique normalized tokens | `100-200` | Enough to capture topic-relevant repetition without storing a page-sized vocabulary dump. |
| Per-token page contribution cap | `3-5` | Prevents one repetitive page from dominating. |
| Packet flush interval | `30-60s` | Keeps writes batched without making the signal feel stale. |
| Helper aggregate rows per profile/pair | `2,000-5,000` | Bounded storage while leaving room for varied reading. |
| Aggregate prune threshold | near-zero decayed signal | Lets stale interests disappear naturally. |
| Admission-time candidate frontier | current LP frontier, e.g. `10k` | Cheap dictionary lookup per candidate; no page-time corpus scan. |

Latency posture:

- page capture and helper submission should be async and best-effort;
- the user should never wait for browsing-signal ingest before replacements,
  reviews, or page interaction continue;
- if the helper is offline, packets can be dropped or retained within a small
  bounded queue;
- if the queue is full, oldest or weakest browsing packets should be discarded
  before raw text or unbounded history is ever stored;
- diagnostics should report signal freshness and dropped-packet counts only at
  a high level.

Storage posture:

- store target-lemma aggregates, not raw page text;
- do not store URL by default;
- avoid storing long-lived unmapped source tokens. If unmapped-token diagnostics
  are needed, keep them developer-only, count-only, and aggressively bounded;
- decay can be applied lazily at ingest/read time, so no background cron is
  required just to age out signals;
- clearing browsing admission signals must not delete normal SRS review
  history.

Current prototype evidence:

- `core/lexishift_core/srs/browsing_admission.py` defines the decayed,
  bounded aggregate store, ingest result diagnostics, strength presets, and
  read-only admission-share/probability simulation.
- `core/lexishift_core/helper/use_cases/browsing_admission.py` persists
  opt-in browsing signal packets into the profile-scoped helper aggregate store
  while ignoring private packet fields such as URLs and raw page text.
- `scripts/helper/lexishift_native_host.py`,
  `scripts/helper/lexishift_helper.py`, and
  `apps/chrome-extension/shared/helper/helper_client.js` expose the dev ingest
  route as `srs_browsing_signal_ingest` /
  `ingest_browsing_admission_signals`; it requires explicit opt-in and does
  not create SRS items.
- `apps/chrome-extension/shared/srs/srs_browsing_admission_signals.js` can
  build and flush dev-only helper packets from replacement exposure batches
  when hidden setting `srsBrowsingAdmissionSignalsEnabled` is true. The packet
  builder immediately reduces browser observations to target lemmas, counts,
  pair, and profile; it does not forward URL, raw text, source phrase, or
  context text.
- `core/lexishift_core/srs/admission_suppression.py` defines a generic
  suppression/cooldown store for discarded, suspended, user-blocked, and manual
  cooldown lemmas.
- `core/lexishift_core/helper/use_cases/refresh_set.py` now loads active
  suppression entries and passes blocked lemmas into refresh admission, so real
  refresh growth cannot admit suppressed lemmas.
- `core/lexishift_core/srs/admission_refresh.py` now exposes a preview-only
  browsing refresh simulation that reuses the actual refresh decision, filters,
  candidate scoring, and budget before reporting `Off`, `Balanced`, and
  `Strong` outcomes.
- `core/lexishift_core/helper/use_cases/refresh_set.py` returns this diagnostic
  under `browsing_admission_preview`; it does not alter actual refresh
  selection.
- `docs/srs/srs_admission_lifecycle_current_state.md` records the current
  code-backed audit for initial admission, refresh growth, rebalance,
  feedback/exposure caveats, and release/discard/suspend gaps.
- `scripts/testing/srs_browsing_admission_backend_simulation.py` renders a
  synthetic helper-persisted report without runtime SRS mutation.
- `docs/test_outputs/srs_browsing_admission_backend_simulation_latest.md`
  records the current fixture: helper ingest succeeds only with opt-in, packet
  caps apply, stale/low-signal rows prune, suppressed lemmas receive zero
  admission probability, and `Off < Balanced < Strong` browsing-lane share is
  monotonic.

## Probability Model

Browsing should create a smooth, saturating, bounded boost.

For candidate `i`:

```text
raw_browsing_i =
  source_hit_count_i * source_mapping_confidence_i
  + target_hit_count_i
  + replacement_exposure_count_i * replacement_exposure_weight
```

Normalize with a saturating function:

```text
browsing_signal_i =
  log(1 + raw_browsing_i) / log(1 + browsing_signal_cap)
```

Then clamp:

```text
browsing_signal_i = clamp(browsing_signal_i, 0, 1)
```

Recommended initial constants:

```text
browsing_signal_cap = 16.0
replacement_exposure_weight = 0.35
browsing_alpha = 0.25
max_browsing_boost = 1.35
```

These are intentionally conservative for ranked top-N admission. Early
research should treat large one-page rank jumps as a sign that
`browsing_alpha` or the saturation curve is too aggressive.

The curve is intentionally logarithmic in raw browsing count and linear only in
the normalized browsing signal. A true exponential boost is deferred because it
can become all-or-nothing quickly in a sticky SRS setting.

Optional fit-aware extension:

```text
browsing_boost_i =
  1
  + min(
      max_browsing_boost - 1,
      browsing_alpha
      * browsing_signal_i
      * proficiency_fit_i
      * explicit_preference_fit_i
      * source_mapping_confidence_i
    )
```

The current research harness models the conservative base boost. Before runtime
admission uses browsing, preview/simulation should compare the base formula
against the fit-aware extension. The product goal is that browsing helps most
when the word is repeatedly encountered, level-appropriate, source-supported,
and aligned with explicit preferences.

Suggested strength presets:

| UX preset | `browsing_alpha` | `max_browsing_boost` | Product meaning |
| --- | ---: | ---: | --- |
| Off | `0.00` | `1.00` | Browsing signals are ignored for admission. |
| Balanced | `0.15-0.25` | `1.25-1.35` | Browsing is a quiet relevance nudge. |
| Strong | `0.35-0.50` | `1.50-1.75` | Browsing can materially shape new admissions, still bounded. |

Boost:

```text
browsing_boost_i =
  1 + min(max_browsing_boost - 1, browsing_alpha * browsing_signal_i)
```

Candidate score integration:

```text
final_score_i =
  base_score_i
  * source_quality_i
  * pos_quality_i
  * readiness_gate_i
  * explicit_preference_boost_i
  * browsing_boost_i
```

The readiness gate remains mandatory. Browsing relevance can move a candidate
up; it cannot make unsupported, too-easy, or too-hard candidates dominate.

## Mathematical Design Space

Let:

```text
E = eligible candidate set after hard filters
B = new-admission budget from the SRS refresh policy
x_i = neutral admission score for candidate i
r_i = readiness multiplier for candidate i
p_i = explicit preference affinity for candidate i
q_i = source/mapping confidence for candidate i
b_i = normalized browsing signal for candidate i
```

Hard filters and budget are outside the browsing model:

```text
E = candidates
    - malformed rows
    - wrong pair
    - blocked lemmas
    - already admitted lemmas
    - disallowed POS/source/license rows
    - rulegen-unsupported rows when rulegen is required

B = min(max_new_items_per_day, max_active_items - due_count)
```

Then the refresh policy may reduce `B` to zero under high due pressure or low
retention. Browsing only acts after this point.

### Option A: Score-Only Boost

The simplest model is a bounded multiplier:

```text
fit_i = r_i * q_i * (1 + preference_alignment_weight * p_i)

browsing_boost_i =
  1 + min(max_browsing_boost - 1, browsing_alpha * b_i * fit_i)

s_i = x_i * browsing_boost_i

selected = top_B(sort_by(s_i, descending))
```

Benefits:

- easy to implement on top of existing ranked growth admission;
- deterministic and explainable;
- browsing cannot exceed the multiplier cap.

Weakness:

- deterministic top-N can feel all-or-nothing near score thresholds. A small
  boost may do nothing, while a slightly larger boost may abruptly admit many
  browsed words.

This is acceptable for preview diagnostics, but probably not ideal as the final
product feel by itself.

### Option B: Weighted Sampling

The existing selector already supports weighted-without-replacement sampling in
preview/lab contexts. Browsing can contribute to sampling mass:

```text
score_mass_i = s_i
base_mass_i = x_i * r_i
mass_i = lambda * base_mass_i + (1 - lambda) * score_mass_i
```

For the first selected word:

```text
P(i first) = mass_i / sum(mass_j for j in E)
```

For a preferred or browsed group `A`:

```text
P(first word in A) =
  sum(mass_i for i in A) / sum(mass_j for j in E)
```

For `B > 1`, selection is sequential without replacement:

```text
P_t(i selected at draw t) =
  mass_i / sum(mass_j for j in remaining_candidates_t)
```

Expected group share is best computed by simulation or by running the exact
selector repeatedly with fixed fixtures. There is no honest one-line formula
that maps a user-facing strength value to final share because the remaining
pool changes after every draw.

Current diagnostic convention:

- `deterministic_selection_probability` is exact for the current two-lane
  prototype: selected rows are `1.0`, unselected rows are `0.0`.
- `browsing_lane_probability`, `general_lane_probability`, and
  `approximate_selection_probability` estimate how likely each word would be
  under the planned smoother weighted lane model.
- The approximation uses:

```text
P(included in lane) ~= 1 - exp(-lane_budget * word_mass / total_lane_mass)
P(combined) = P(browsing) + (1 - P(browsing)) * P(general)
```

This is a calibration diagnostic, not a user-facing promise. It is useful
because it lets us inspect all candidate words at a given profile/signal state
before actual admission mutation is enabled.

Benefits:

- smoother than top-N;
- stronger browsing signals gradually increase probability mass;
- easy to report realized share in diagnostics.

Weakness:

- share is probabilistic and can vary per run unless seeded;
- product copy must avoid exact percentage promises.

### Option C: Mixture Budget

The strongest product-control model is a two-lane budget:

```text
V = sum(b_i for i in E)
volume_factor = 1 - exp(-V / tau)

B_browsing = floor(B * rho_strength * volume_factor)
B_general = B - B_browsing
```

Small admission budgets need one extra rule. A pure floor can make `Balanced`
look identical to `Off` even when the learner has strong browsing evidence.
The current preview therefore computes the fractional browsing budget first:

```text
raw_browsing_budget = B * rho_strength * volume_factor
B_browsing = floor(raw_browsing_budget)

if B_browsing == 0
   and raw_browsing_budget >= min_fractional_browsing_budget_strength
   and browsing_pool is not empty:
  B_browsing = 1
```

Current preview thresholds:

```text
Off      min_fractional_browsing_budget = 1.00
Balanced min_fractional_browsing_budget = 0.50
Strong   min_fractional_browsing_budget = 0.35
```

This makes `Balanced` noticeable when there is real signal, without increasing
the score boost or allowing browsing to bypass the overall admission budget.

Where `rho_strength` is a preset:

```text
Off      rho = 0.00
Balanced rho = 0.20-0.30
Strong   rho = 0.40-0.55
```

Then:

```text
browsing_pool = { i in E where b_i >= browsing_min_signal }
general_pool = E - selected_browsing

selected_browsing = weighted_sample(browsing_pool, B_browsing)
selected_general = weighted_sample_or_topN(general_pool, B_general)
selected = selected_browsing + selected_general
```

This does not mean the user sees a percentage control. The UX can remain
`Off / Balanced / Strong`. The percentage is a backend guardrail that prevents
browsing from creating too much durable SRS debt.

Benefits:

- browsing influence becomes smooth and bounded;
- Strong can be meaningfully stronger than Balanced without taking over all
  admissions;
- diagnostics can report the realized browsing share after each preview or
  refresh.

Weakness:

- slightly more implementation work;
- needs careful fallback behavior when there are too few browsed eligible
  candidates.

Recommended MVP direction: use **Option C** for actual mutation, with the
bounded score boost from **Option A** inside each lane and weighted sampling
from **Option B** for preview/simulation. This gives us mathematical smoothness,
product control, and explainable diagnostics.

### Option D: Adaptive Bandit Later

A later system could tune browsing strength from user outcomes:

```text
alpha_next =
  clamp(alpha_current + learning_rate * (observed_success - target_success))
```

Where observed success could include keep/discard behavior, review retention,
or explicit "not relevant" feedback for admitted browsing-driven words.

This is not MVP. It needs more lifecycle data and could be hard to explain. It
is best treated as a future calibration layer after the fixed policy is proven.

## Admission Budget And Sticky State

Browsing admission needs a budget layer in addition to a score layer.

The score layer answers:

```text
How much more eligible is this candidate because the learner has encountered it?
```

The budget layer answers:

```text
How many durable new SRS obligations should browsing be allowed to create?
```

Recommended MVP behavior:

- browsing never bypasses `max_new_per_day`, `initial_active_count`,
  `max_active`, pair readiness, blocked terms, or rulegen/source-quality gates;
- browsing-influenced admissions are sampled from the normal eligible frontier
  after score computation and distribution normalization;
- one page can create diagnostics and a small boost, but should not create a
  durable admission unless the candidate survives budget, readiness, and
  sampling-share policy;
- if the learner discards/suspends a word, browsing should not immediately
  re-admit it. Add a cooldown or explicit re-suggest policy before actual
  browsing admission is enabled;
- already admitted or mastered words should not be duplicated through browsing.
  Browsing may be diagnostic later, but should not create a second admission
  path for the same target lemma.

Suggested realized-share targets for simulation, not user-facing promises:

| UX preset | Target behavior when strong browsing signals exist |
| --- | --- |
| Off | `0%` browsing-driven admissions. |
| Balanced | Browsing-relevant candidates should appear noticeably, but normally stay below a minority share of new admissions. |
| Strong | Browsing-relevant candidates may become a large minority or narrow majority, but still respect readiness and daily/session caps. |

These are calibration targets, not product copy. User-facing UX should avoid
exact percentage guarantees because realized share depends on the eligible
frontier, proficiency, explicit preferences, source coverage, and review budget.

## Admission, Review, And Page Replacement

Browsing admission must stay separate from page replacement.

Admission answers:

```text
Which target lemmas should become durable SRS obligations?
```

Review scheduling answers:

```text
Which admitted items are due according to the scheduler?
```

Runtime page replacement answers:

```text
Which eligible words should be replaced on this page right now?
```

These decisions share state, but they should not collapse into one algorithm.
A word being admitted or learned does not mean it should be replaced everywhere
forever.

Product rules:

- explicit topic preferences bend admission probabilities, but do not collapse
  the learner into only that topic;
- browsing signals bend admission probabilities, but do not bypass budget,
  readiness, suppression, or source-quality gates;
- page replacement must have its own visual/cognitive load budget;
- long-used profiles should see dropoff for old, stable, or mastered words so
  pages do not become saturated with every word learned since onboarding;
- due, recently learned, and target-relevant items should usually outrank
  mature or mastered items for runtime replacement;
- mastered/released items may remain eligible for rare reinforcement later, but
  they should not compete equally with active learning items.

Recommended runtime replacement priority:

```text
new / learning       high eligibility
young review         medium-high eligibility
mature review        medium-low eligibility
mastered / released  rare reinforcement only
discarded/suspended  not eligible while suppressed
```

Recommended page-level safeguards:

- hard max replacements per page;
- density limit per paragraph or viewport;
- cap repeated replacements of the same lemma;
- probabilistic or state-based dropoff for mature items;
- hard suppression for discarded, blocked, or unsafe items.

## Decay And Caps

Browsing signals should fade unless reinforced.

Recommended first design:

```text
short_half_life_days = 7
medium_half_life_days = 30
browsing_signal = 0.70 * short_window + 0.30 * medium_window
```

Caps:

- per-page max unique tokens;
- per-page max count per normalized token;
- per-day max contribution per lemma;
- per-day or per-session browsing-influenced admission share;
- global max browsing boost;
- per-source mapping confidence multiplier;
- minimum source-quality threshold;
- discard/suspend cooldown before re-suggestion;
- readiness gate always applied after browsing boost.

These caps prevent one repetitive page, one spammy site, or one unusual session
from dominating admission.

## Smoothness Requirements

The product should feel gradual:

- one encounter gives a small nudge;
- repeated encounters noticeably move candidates;
- frequent encounters saturate instead of overwhelming everything;
- signals decay when the user's reading changes;
- explicit user preferences remain clearer and stronger than inferred browsing
  signals;
- a neutral profile stays stable when browsing signals are off.

Validation should measure monotonicity:

- increasing browsing count should not lower a candidate's admission score when
  all other inputs are constant;
- increasing browsing count should have diminishing returns;
- candidates outside the readiness band should remain suppressed;
- realized admission share should move, but not become all-or-nothing.

## UX Recommendations

Settings:

- main toggle: "Use browsing activity for SRS suggestions";
- strength preset: `Off`, `Balanced`, `Strong`;
- per-site pause/denylist;
- clear browsing learning signals;
- optional diagnostics toggle.

Diagnostics:

- "Browsing is currently boosting these words";
- "Last updated";
- "Signals decay automatically";
- "Only future SRS suggestions are affected";
- "Review scheduling still depends on your SRS feedback."

Avoid:

- percentages as UX promises;
- page category claims;
- showing raw captured text;
- saying the app "knows" the user's interests.

## Implementation Plan

### Phase 0: Planning And Fixtures

- Define browsing signal store schema.
- Define source/target lookup contract.
- Add privacy policy notes and controls spec.
- Add synthetic signal fixtures for tests.

Exit criteria:

- schema and constants documented;
- no runtime behavior change.

### Phase 1: Read-Only Capture And Audit

- Add opt-in dev capture of visible tokens.
- Normalize and cap token counts.
- Send local aggregate packets to helper.
- Write profile/pair browsing signal aggregate.
- Add audit command that reports what would be boosted.

Exit criteria:

- raw page text is not persisted;
- signals decay and cap correctly;
- no admission scoring change.

### Phase 2: Admission Preview Integration

- Add browsing signal lookup to admission preview only.
- Show neutral vs browsing-influenced previews.
- Include per-candidate `browsing_signal`, `browsing_boost`, and explanation.
- Add realized-share simulation for `Off`, `Balanced`, and `Strong` across a
  fixed new-word budget.
- Keep offline page/text fixture research connected to the same helper ingest,
  bounded aggregate store, and strength simulation used by the production-shaped
  backend path.
- Keep actual admission unchanged.

Exit criteria:

- preview proves smooth movement without all-or-nothing behavior;
- simulation reports browsing-relevant share, preferred+browsed share,
  repeated-signal impact, and any effectively guaranteed candidates;
- disabled/off state exactly matches neutral admission.

### Phase 3: Gated Admission Boost

- Allow browsing boost in actual admission refresh only when the user opted in.
- Keep boost capped, readiness-gated, and budget/share-capped.
- Add diagnostics and rollback/clear behavior.
- Enforce discard/suspend cooldowns before browsing can re-suggest a target.

Exit criteria:

- SRS harness remains clean;
- no scheduling mutation from browsing-only events;
- opt-out disables further boost without deleting SRS review history;
- already admitted/mastered targets are not duplicated by browsing admission.

### Phase 4: Post-MVP Enhancements

- consider topic inference only after word-level signals are proven;
- consider embeddings only in offline/local indexed form;
- consider per-domain controls only if privacy and UX justify them;
- add realized-share calibration reports.

## Test Plan

Focused tests:

- token cap and normalization;
- no raw text persisted;
- source-side hit maps to target candidates;
- target-side hit boosts exact target lemma;
- decay math;
- saturation math;
- disabled toggle produces no signal writes;
- browsing-only signal does not update FSRS scheduling fields;
- admission preview shows monotonic but capped score movement;
- realized-share simulation shows `Off < Balanced < Strong` browsing influence
  without all-or-nothing admission;
- browsing boost cannot exceed new-word budget, active-set budget, or configured
  share caps;
- discarded/suspended/already-admitted words are not immediately re-admitted by
  browsing;
- opt-out stops applying browsing boosts.

Harness checks:

- SRS quality harness for scheduling/admission boundaries;
- changed-file workflow check;
- offline page/text fixture probe via
  `scripts/testing/srs_browsing_admission_research_en_es.py`, including its
  canonical helper/core probe section;
- browser smoke for opt-in/off state and clear-data control when UI lands.

## Lifecycle Audit Result

The lifecycle audit is now captured in
`docs/srs/srs_admission_lifecycle_current_state.md`.

Key result:

- Runtime browsing admission should enter only through `srs_refresh`.
- `srs_initialize` remains bootstrap-only.
- `srs_rebalance_apply` remains active-set rebalance, not browsing-driven
  displacement.
- `srs_refresh` now includes a preview-only browsing admission diagnostic, but
  actual refresh selection remains neutral.
- `record_feedback` and `record_exposure` must not be reused for browsing
  admission because they can create SRS store rows directly.
- Refresh admission now respects active suppression entries, so discarded,
  suspended, user-blocked, or manual-cooldown lemmas cannot be admitted through
  refresh while suppression is active.
- A user-facing discard/suspend/block writer remains unimplemented.

## Open Decisions

1. Exact storage path for browsing admission aggregates.
2. Whether replacement exposure should share the same aggregate or remain a
   separate input that gets fused at scoring time.
3. Initial per-page and per-day caps.
4. Whether source-side mappings need minimum confidence thresholds by LP.
5. Whether page language side should be user-selected, inferred locally, or
   derived from language-pair context for P0.
6. Exact `Off` / `Balanced` / `Strong` constants after realized-share
   simulation.
7. Whether browsing share caps should be strict hard caps or soft weighted
   pressure.
8. Discard/suspend cooldown duration and whether users can explicitly allow
   re-suggestions.
9. How much diagnostic detail should be user-facing versus developer-only.

## Non-Goals

- building a browsing history system;
- inferring sensitive interests;
- storing raw text;
- syncing browsing signals remotely;
- replacing explicit topic preferences;
- replacing FSRS scheduling;
- treating passive exposure as recall.
