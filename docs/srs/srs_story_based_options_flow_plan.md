# SRS Story-Based Options Flow Plan

Status: active target UX plan
Role: Planning
Last updated: 2026-05-31
Last verified: 2026-05-31 selected-story shell, curtains, hidden active-story pool backing control, guided new-story modal, missing-language-data setup panel, and resource-settings existing-GUI activation through focused extension/options/native-host tests
Purpose: define the target Options-page SRS UX before beta-facing cleanup so implementation can follow the same flow deliberately
Source-of-truth: product UX plan only; implemented/default-on status remains in `docs/developer/feature_state_matrix.md` and code/tests.

## Current Implementation State

As of 2026-05-28, the Options page has the beta-facing structural flow:

- selected profile/pair SRS controls are grouped under a selected-story block;
- admission sampling is behind a `Sample next words` curtain placed directly
  after the active story's admission-preference controls;
- the admitted-words dashboard is behind an `Open dashboard` curtain placed
  directly after sampling;
- display/feedback controls sit in the normal expanded story surface after the
  dashboard curtain;
- the collapsed `Advanced` section contains same-level new-word timing
  thresholds and a story-scoped delete action only;
- SRS story cards, topic panels, curtains, and dashboard surfaces follow the
  same card-theme CSS-variable path as the rest of the Options page;
- active-story new-word preference edits are draft changes until the learner
  presses `Save preferences`;
- the main SRS shell does not show generic installed-data copy; language-data
  readiness belongs in setup, diagnostics, or actionable error/status states;
- there is no visible SRS enable switch in the ordinary story surface; starting
  a story through initialization is the learner-facing enable action, while the
  legacy `srs-enabled` input remains hidden as a controller backing field;
- the active-story proficiency slider shows its previous saved setting and has a
  restore action;
- the start-new-story block opens a guided modal for source/target language
  choice, proficiency, topics, starting size, sampling, and initialization; the
  profile is inherited from the active profile through a hidden backing value
  and is not presented as a learner-facing setup choice;
- the new-story proficiency slider starts at an explicit beginner value (`0%`)
  when there is no existing proficiency value to copy into the flow;
- each fresh new-story modal opening starts with no topic chips selected, even
  if the previous cancelled setup sample persisted draft topic settings for
  preview;
- modal sampling copies the visible modal values into the existing Options
  controls, may persist draft language/SRS preference inputs for the active
  profile, and then calls the existing read-only preview workflow without
  activating the story;
- modal and active-story sampling render the same fetched preview payload as a
  learner-facing word/topic list by default, with the technical preview payload
  retained behind a local Advanced details disclosure that toggles without
  re-running the sample; local source paths are not printed in this learner
  surface;
- modal initialization copies and persists the visible modal values with the
  hidden story-enabled backing field set, then calls the existing initialize
  workflow;
- the advanced setup-only vocabulary search range controls how broad a ranked
  candidate pool sampling and new-word selection may inspect. It remains hidden
  behind advanced setup controls because ordinary learners should not need it;
- if helper preflight reports missing language data during modal sampling or
  initialization, the setup modal shows an inline data-readiness panel with
  learner-facing resource labels, an action to open LexiShift's GUI Resource
  settings tab with the pair added/focused in the persistent Learning Languages
  resource view, and a retry action. The Learning Languages resource view
  promotes exact app-managed downloads and per-resource file-location reveal
  actions; broad manual file selection remains in the detailed resource tabs
  rather than the learner-facing pair card. Repeated opens reuse the
  already-running GUI through the single-instance activation channel when
  possible; if the GUI is closed, the helper launches it. The extension still
  does not download language data directly.

Not implemented yet:

- full story enumeration across all profile/pair SRS stores;
- persisted story summary counts outside the dashboard payload;
- final user-facing policy for whether candidate-pool depth belongs in learner
  settings, setup-only advanced controls, or a future data-source/download model;
- user-facing browsing-data opt-in controls for browsing-based admission.

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

- new-word timing thresholds
- delete SRS story for the current profile/language pair
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

- use the story's current visible preferences for preview;
- require an explicit save action before changed preferences become the saved
  story defaults for future refresh/growth;
- be hidden until the user expands the sampling curtain;
- support repeated sampling without requiring a full page reload.

## Curtain Pattern

Large SRS surfaces should be collapsed by default and opened in-place when the
user asks for them.

Use the curtain pattern for:

- dashboard
- sampling
- preference editing if it becomes too large for the compact story block
- Advanced timing/reset controls

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
- display/feedback settings
- proficiency estimate
- topic picker
- max active words or equivalent active-size control
- explicit preference save action
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
- new-word timing thresholds
- delete SRS story
- debug/runtime diagnostics
- sampled rulegen
- semantic pack installation/debug inputs
- helper data-folder tools

Do not make these prominent in the ordinary beta learner path:

- internal `S` terminology
- rule publication details
- manual active-word update and learning-word refresh controls
- helper diagnostics
- helper and sentence-fit technical status inside the active story
- semantic pack inventory paths
- raw bootstrap/top-N implementation language
- candidate-pool depth controls until the data-source/download/storage policy is
  decided

## Naming Boundary

Final user-facing labels for some technical controls are intentionally not
decided here.

The naming problem needs a focused pass because the current labels are
technically accurate but not product-level:

- `Bootstrap S size (top N)`
- `Initial active subset`
- `Initialize S for this pair`
- `Refresh S + publish rules`

The active-practice size control has a beta-facing label: `Words in active
practice`. It means how many learning words LexiShift keeps in active rotation
at once.

Until that pass is complete:

- do not rename these casually;
- do not introduce a second competing vocabulary;
- keep internal docs explicit that these are implementation labels, not final UX
  copy.

Candidate-pool depth is no longer visible in existing story blocks. It remains a
hidden backing value for current controllers and a setup-only advanced control
until the broader source-pack/cloud/local-storage question is resolved.

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
- saving preferences updates future sampling, refresh, and automatic growth
  behavior.

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
- sampling and dashboard are adjacent and collapsed by default;
- changed new-word preferences have an explicit save point;
- proficiency edits show the previous saved setting and can be restored before
  saving;
- display/feedback controls are reachable without being buried in Advanced;
- Advanced contains timing thresholds and reset, not routine/manual
  active-word operation buttons;
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
- Final labels for initial size, candidate pool, and start action.
- Whether candidate-pool depth should stay setup-only, move to a future advanced
  data-source control, or disappear from user settings entirely.
- Where the eventual browsing-data opt-in belongs once browsing aggregates are
  consumed by production admission, likely near admission preferences rather than
  under generic logging.
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
