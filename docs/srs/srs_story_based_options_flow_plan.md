# SRS Story-Based Options Flow Plan

Status: active target UX plan
Role: Planning
Last updated: 2026-05-27
Last verified: 2026-05-27 selected-story shell, curtains, and guided new-story modal through focused extension/options tests
Purpose: define the target Options-page SRS UX before beta-facing cleanup so implementation can follow the same flow deliberately
Source-of-truth: product UX plan only; implemented/default-on status remains in `docs/developer/feature_state_matrix.md` and code/tests.

## Current Implementation State

As of 2026-05-27, the Options page has the beta-facing structural flow:

- selected profile/pair SRS controls are grouped under a selected-story block;
- the admitted-words dashboard is behind an `Open dashboard` curtain;
- admission sampling is behind a `Sample possible words` curtain;
- maintenance tools remain collapsed under `Manage SRS data`;
- the start-new-story block opens a guided modal for language/profile choice,
  proficiency, topics, starting size, sampling, and initialization;
- modal sampling and initialization copy the visible modal values into the
  existing Options controls, persist profile/language/SRS settings, and then
  call the existing preview or initialize workflow.

Not implemented yet:

- full story enumeration across all profile/pair SRS stores;
- persisted story summary counts outside the dashboard payload;
- final user-facing naming for the technical size/initialization labels.

## Decision

The Options page should present SRS as a set of learner-facing "stories" rather
than a flat control panel.

An SRS story is the learner's active journey for one profile and language pair:

- selected profile
- source language
- target language
- admission preferences
- active/admitted SRS inventory
- dashboard state
- lifecycle and maintenance state

The exact user-facing name may change later. This document uses "SRS story" as
the implementation/product-planning term.

## Target Page Shape

When a user scrolls through Options, the SRS area should have two main surfaces.

### Existing SRS Stories

If the selected profile already has SRS data for one or more language pairs, each
story appears as a compact block.

Each story block should show:

- language pair, such as `English -> Spanish`
- profile identity
- enabled/paused state
- compact SRS inventory counts:
  - active words
  - due words
  - queued words
  - removed/discarded words when relevant
- current learner preferences:
  - proficiency estimate
  - selected topics
  - active-size setting
  - automatic refresh state
- last refresh or last rules publication time when available

Each story block should provide user-facing actions:

- `Open dashboard`
- `Sample possible words`
- `Edit preferences`

Each story block may provide advanced actions behind an additional collapsed
management area:

- rebalance to current preferences
- manual refresh and rule publication
- reset SRS data
- future restore/mastery/release controls

Dashboard and sampling must not be permanently expanded on the main page. They
are large inspection tools and should open only when requested.

### Start New SRS Story

Below the existing story blocks, the page should show one simple block for
starting a new story.

The block should be intentionally small:

- short title
- short description
- one primary button, such as `Start a new SRS story`

Clicking this button opens a guided popup/modal/drawer flow.

## New Story Linear Flow

Starting SRS for a language pair is a high-impact action because it creates the
initial admitted set. It should feel deliberate and linear.

The flow order must be:

1. Choose source language.
2. Choose target language.
3. Choose or confirm profile.
4. Set proficiency estimate.
5. Choose topic interests.
6. Set starting/active size controls.
7. Optionally sample likely target-language words.
8. Initialize only after the user accepts the settings.

The initialize action should use the exact settings visible in the flow. The
user should not need to know that saving preferences first is safer.

Implementation requirement:

- either initialization saves the visible preferences first and then calls
  helper initialization,
- or the flow prevents initialization until preferences are persisted.

The first beta implementation can use the current helper APIs and controller
methods, but the user experience should no longer require discovering the
correct order from a long page.

## Sampling Behavior

Sampling remains important and should be reused.

Sampling in the new-story flow should:

- use the current visible source/target/profile/preference values;
- be probabilistic where the backend supports probabilistic preview;
- change when the user presses the sample button again;
- show target-language words the user might see if they initializes with those
  settings;
- make it clear that a sample is preview evidence, not a guarantee of exact
  admission.

Sampling in an existing story block should:

- use the story's current persisted preferences;
- be hidden until the user expands the sampling curtain;
- support repeated sampling without requiring a full page reload.

## Curtain Pattern

Large SRS surfaces should be collapsed by default and opened in-place when the
user asks for them.

Use the curtain pattern for:

- dashboard
- sampling
- preference editing if it becomes too large for the compact story block
- maintenance tools

Expected behavior:

- clicking the story action opens the section below the story block;
- the section visually belongs to that story;
- opening one section must not make the full Options page feel like a debug
  console;
- the user can close the section or leave it collapsed while browsing other
  settings.

Implementation note:

- native `<details>` can be acceptable for the first version if styled clearly;
- a custom disclosure component is acceptable later if the interaction needs
  smoother animation or stricter state control.

## Control Disposition

Move or regroup current controls as follows.

Keep in normal story/new-story UX:

- source language
- target language
- SRS enabled/paused state
- proficiency estimate
- topic picker
- max active words or equivalent active-size control
- starting learning words or equivalent initial-size control
- sample possible words
- initialize/start learning
- dashboard access

Keep visible only after expansion:

- dashboard table/list
- dashboard filters, sorting, pagination
- sample preview output
- preference edit form for existing stories if it is large

Keep advanced/collapsed:

- advanced topic tags
- challenge target
- automatic refresh thresholds
- manual refresh and publish
- rebalance preview/apply
- reset SRS data
- debug/runtime diagnostics
- sampled rulegen
- semantic pack installation/debug inputs
- helper data-folder tools

Do not make these prominent in the ordinary beta learner path:

- internal `S` terminology
- rule publication details
- helper diagnostics
- semantic pack inventory paths
- raw bootstrap/top-N implementation language

## Naming Boundary

Final user-facing labels for the current size controls are intentionally not
decided here.

The naming problem needs a focused pass because the current labels are
technically accurate but not product-level:

- `Bootstrap S size (top N)`
- `Initial active subset`
- `Initialize S for this pair`
- `Refresh S + publish rules`

Until that pass is complete:

- do not rename these casually;
- do not introduce a second competing vocabulary;
- keep internal docs explicit that these are implementation labels, not final UX
  copy.

## Implementation Plan

Implement in small, reversible slices.

### Slice 1: Story Shell

Add a story-list section to the SRS card.

Requirements:

- show existing SRS story blocks for selected profile/pairs that have data;
- show compact counts and preferences;
- keep existing controls available while the new shell is validated;
- no backend schema migration.

### Slice 2: Dashboard Curtain

Move the admitted-words dashboard under the active story block as an expandable
curtain.

Requirements:

- keep the existing dashboard workflow and helper calls;
- scope refresh/list actions to the story's profile/pair;
- keep advanced details opt-in inside the dashboard.

### Slice 3: Sampling Curtain

Move sampling under the active story block and into the new-story flow.

Requirements:

- sampling uses current story preferences for existing stories;
- sampling uses unsaved visible form values inside the new-story flow;
- repeated sampling remains fast and non-mutating.

### Slice 4: New Story Flow

Add the `Start a new SRS story` entry and a linear modal/drawer.

Requirements:

- user chooses source/target before admission settings;
- proficiency and topic interests are front and center;
- sample preview is available before initialization;
- initialization cannot accidentally use stale/default preferences.

### Slice 5: Preferences In Story Blocks

Expose persisted preferences inside existing story blocks.

Requirements:

- compact summary is always visible;
- full edit form can be collapsed;
- saving preferences updates future sampling, refresh, rebalance, and
  automatic growth behavior.

### Slice 6: Remove Old Flat Control Path

Once the story flow is validated, remove or permanently hide the old flat SRS
control path.

Requirements:

- no duplicate initialize buttons competing for attention;
- no dashboard floating outside a story context;
- no maintenance actions in the main learner path.

## Acceptance Criteria

Before this UX is considered beta-ready:

- a fresh user can start en-es SRS without knowing implementation order;
- the user must see preference controls before initialization;
- initialization uses the visible preferences;
- existing SRS data appears as one or more story blocks;
- dashboard and sampling are available but collapsed by default;
- maintenance actions are reachable but clearly secondary;
- reset remains clearly dangerous and profile/pair scoped;
- no ordinary beta path requires reading `S`, `bootstrap`, `rulegen`,
  `publish`, or helper-diagnostic terminology.

## Non-Goals

This plan does not require:

- changing the admission algorithm;
- changing SRS scheduling math;
- adding browsing-based admission to the product path;
- improving topic coverage;
- solving final marketing/product naming;
- migrating existing helper store files;
- adding multi-profile collaboration.

## Open Questions

- Final public name for "SRS story".
- Final labels for active size, initial size, candidate pool, and start action.
- Whether the story flow should be modal, drawer, or inline stepper.
- Whether a user can have multiple stories for the same language pair under the
  same profile, or exactly one story per profile/pair.
- Whether old inactive stories should appear by default or under archived
  stories.
- Whether reset should offer a sub-choice to preserve discarded-word metadata.

## Verification Targets

Add or update tests when implementation starts:

- Options markup test: lifecycle controls are inside story or advanced
  containers, not loose at the root of SRS Practice.
- Controller test: new-story initialize persists visible preferences before or
  during initialization.
- Helper/extension smoke: initialized story appears in story list with dashboard
  counts.
- Preflight update: family-beta manual signoff starts from the story flow rather
  than from the old flat SRS controls.
