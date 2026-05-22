# Browsing Data-Based SRS Admission Plan

Status: active planning workstream
Role: Planning / WIP
Last updated: 2026-05-23
Last verified: 2026-05-23 by SRS hybrid model, interest-tailored admission algorithm, helper exposure path, signal queue, and profile-context code reads
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

## P0 Scope

P0 is word-level browsing relevance only.

In scope:

- exact normalized source-word hits from visible browsing text;
- exact normalized target-word hits when the user browses target-language text;
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
browsing_signal_cap = 8.0
replacement_exposure_weight = 0.35
browsing_alpha = 0.50
max_browsing_boost = 1.50
```

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
- global max browsing boost;
- per-source mapping confidence multiplier;
- minimum source-quality threshold;
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
- Keep actual admission unchanged.

Exit criteria:

- preview proves smooth movement without all-or-nothing behavior;
- disabled/off state exactly matches neutral admission.

### Phase 3: Gated Admission Boost

- Allow browsing boost in actual admission refresh only when the user opted in.
- Keep boost capped and readiness-gated.
- Add diagnostics and rollback/clear behavior.

Exit criteria:

- SRS harness remains clean;
- no scheduling mutation from browsing-only events;
- opt-out disables further boost without deleting SRS review history.

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
- opt-out stops applying browsing boosts.

Harness checks:

- SRS quality harness for scheduling/admission boundaries;
- changed-file workflow check;
- browser smoke for opt-in/off state and clear-data control when UI lands.

## Open Decisions

1. Exact storage path for browsing admission aggregates.
2. Whether replacement exposure should share the same aggregate or remain a
   separate input that gets fused at scoring time.
3. Initial per-page and per-day caps.
4. Whether source-side mappings need minimum confidence thresholds by LP.
5. How much diagnostic detail should be user-facing versus developer-only.

## Non-Goals

- building a browsing history system;
- inferring sensitive interests;
- storing raw text;
- syncing browsing signals remotely;
- replacing explicit topic preferences;
- replacing FSRS scheduling;
- treating passive exposure as recall.
