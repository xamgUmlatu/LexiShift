# Vocabulary Practice Options Flow Plan

Status: active target UX plan; current beta LP setup flow accepted
Role: Planning
Last updated: 2026-07-15
Last verified: 2026-07-15 manual en-ja creation-flow smoke passed after hard frontier-Gaussian hybrid admission promotion, fast indexed preview, localized setup copy, topic picker filtering, persisted browsing-admission toggle state, and early Options theme/backdrop loading; earlier 2026-06-02 learner-facing Vocabulary Practice naming pass plus selected-story shell, direct Vocabulary Library entry, sampling curtain, hidden active-story pool backing control, guided new-story modal, page-level setup progress popup, missing-language-data setup panel, and resource-settings existing-GUI activation through focused extension/options/native-host tests
Purpose: define the target Options-page Vocabulary Practice UX before beta-facing cleanup so implementation can follow the same flow deliberately
Source-of-truth: product UX plan only; implemented/default-on status remains in `docs/developer/feature_state_matrix.md` and code/tests.

## Current Implementation State

As of 2026-07-15, the Options page has the beta-facing structural flow and the
current LP setup flow is accepted for the tested beta scope:

- selected profile/pair practice controls are grouped under a selected-practice block;
- admission sampling is behind a `Sample next words` curtain placed directly
  after the active practice's admission-preference controls;
- the dedicated `Vocabulary Library` entry is placed directly after sampling;
- display controls sit as an inline word-highlight color control plus feedback
  sound toggle in the normal expanded practice surface after the Vocabulary
  Library entry;
- the collapsed `Advanced` section contains same-level new-word timing
  thresholds and a practice-scoped delete action only;
- practice cards, topic panels, curtains, and the Vocabulary Library entry
  follow the same card-theme CSS-variable path as the rest of the Options page,
  and the dedicated Vocabulary Library applies the selected profile's Options
  background and card-theme preferences;
- Options applies the selected profile's saved card theme and page backdrop as
  soon as synced settings load, before the full background preview/status sync
  finishes later in normal page initialization;
- active-practice new-word preference edits are draft changes until the learner
  presses `Save preferences`;
- the main Vocabulary Practice shell does not show generic installed-data copy; language-data
  readiness belongs in setup, diagnostics, or actionable error/status states;
- there is no visible SRS enable switch in the ordinary practice surface; starting
  practice through initialization is the learner-facing enable action, while the
  legacy `srs-enabled` input remains hidden as a controller backing field;
- the active-practice proficiency slider shows its previous saved setting and has a
  restore action;
- the start-practice block opens a guided modal for source/target language
  choice, proficiency, topics, starting size, sampling, and initialization; the
  profile is inherited from the active profile through a hidden backing value
  and is not presented as a learner-facing setup choice;
- current beta LP setup smoke has passed for the en-ja creation flow after the
  hard hybrid admission selector, setup preview performance path, topic picker,
  localized setup copy, and early theme/backdrop loading changes;
- the new-practice proficiency slider always starts at an explicit beginner
  value (`0%`) on fresh setup-modal open, even if the active practice already
  has a saved proficiency value;
- each fresh new-practice modal opening starts with no topic chips selected, even
  if the previous cancelled setup sample persisted draft topic settings for
  preview;
- modal sampling copies the visible modal values into the existing Options
  controls, may persist draft language/practice preference inputs for the active
  profile, and then calls the existing read-only preview workflow without
  activating practice;
- modal and active-practice sampling render the same fetched preview payload as a
  learner-facing word/topic list by default, with the technical preview payload
  retained behind a local Advanced details disclosure that toggles without
  re-running the sample; each Options-page sample request sends a fresh preview
  seed, and the helper returns a sampled subset of the planned active pool
  instead of the deterministic prefix; local source paths are not printed in
  this learner surface;
- modal initialization copies and persists the visible modal values with the
  hidden story-enabled backing field set, shows a page-level blocking progress
  popup while the helper starts practice, then refreshes Options on success so
  the newly created practice card is visible immediately;
- the advanced setup-only vocabulary search range controls how broad a ranked
  candidate pool sampling and new-word selection may inspect. It remains hidden
  behind advanced setup controls because ordinary learners should not need it;
- if helper preflight reports missing language data during modal sampling or
  initialization, the setup modal shows an inline data-readiness panel with
  learner-facing resource labels, an action to open LexiShift's GUI Resource
  settings tab with the pair added/focused in the persistent Learning Languages
  resource view, and a retry action. The Learning Languages resource view
  promotes exact app-managed downloads and per-resource file-location reveal
  actions, shows each package's catalog size, renders per-resource download
  progress, includes the required Kaikki/Wiktionary `wiktionary-es-en`
  dictionary resource for en-es, and routes license-restricted frequency data
  such as `freq-es-cde` through Learning Languages manual setup with provider
  access, local-use rights confirmation, and local conversion from a
  user-supplied licensed `spanish_lemmas20k.txt` source rather than pretending
  it is safe to auto-download. Broad manual file selection remains available in
  the detailed resource tabs as a compatibility path. Repeated opens reuse the
  already-running GUI through the single-instance activation channel when
  possible; if the GUI is closed, the helper launches it. The extension still
  does not download language data directly.

Not implemented yet:

- full practice enumeration across all profile/pair SRS stores;
- persisted practice summary counts outside the dashboard payload;
- final user-facing policy for whether candidate-pool depth belongs in learner
  settings, setup-only advanced controls, or a future data-source/download model;
- user-facing browsing-data opt-in controls for browsing-based admission.

## Decision

The Options page should present the SRS-backed learning feature as learner-facing
Vocabulary Practice rather than exposing the SRS acronym or the temporary
"story" metaphor in ordinary UI.

A Vocabulary Practice instance is the learner's active journey for one profile
and language pair:

- selected profile
- source language
- target language
- admission preferences
- active/admitted practice inventory
- dashboard state
- lifecycle and maintenance state

Internal code and storage names may continue to use `srs` and `story` where they
describe existing implementation boundaries. User-facing copy should say
`Vocabulary Practice`, `practice`, `learning words`, or `practice settings`
unless the surface is explicitly technical diagnostics/import-export.

## Target Page Shape

When a user scrolls through Options, the Vocabulary Practice area should have two
main surfaces.

### Existing Vocabulary Practice

If the selected profile already has practice data for one or more language pairs,
each practice instance appears as a compact block.

Each practice block should show:

- language pair, such as `English -> Spanish`
- profile identity
- enabled/paused state
- compact practice inventory counts:
  - active words
  - due words
  - queued words
  - removed/discarded words when relevant
- current learner preferences:
  - proficiency estimate
  - selected topics
  - active-size setting
  - automatic refresh thresholds
- last refresh or last rules publication time when available

Each practice block should provide user-facing actions:

- `Open Vocabulary Library`
- `Sample possible words`
- `Edit preferences`

Each practice block may provide advanced actions behind an additional collapsed
management area:

- new-word timing thresholds
- delete Vocabulary Practice for the current profile/language pair
- future restore/mastery/release controls

The Vocabulary Library must not be permanently expanded on the main page. It is
a large inspection tool and should open as a dedicated page. Sampling remains a
collapsed in-place curtain.

### Start Vocabulary Practice

Below the existing practice blocks, the page should show one simple block for
starting Vocabulary Practice.

The block should be intentionally small:

- short title
- short description
- one primary button, such as `Start Vocabulary Practice`

Clicking this button opens a guided popup/modal/drawer flow.

## New Practice Linear Flow

Starting Vocabulary Practice for a language pair is a high-impact action because it creates the
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

Sampling in the new-practice flow should:

- use the current visible source/target/profile/preference values;
- be probabilistic where the backend supports probabilistic preview;
- change when the user presses the sample button again;
- show target-language words the user might see if they initializes with those
  settings;
- make it clear that a sample is preview evidence, not a guarantee of exact
  admission.

Sampling in an existing practice block should:

- use the practice's current visible preferences for preview;
- require an explicit save action before changed preferences become the saved
  practice defaults for future refresh/growth;
- be hidden until the user expands the sampling curtain;
- support repeated sampling without requiring a full page reload.

## Curtain Pattern

Large Vocabulary Practice surfaces should be collapsed by default and opened
in-place when the user asks for them.

Use the curtain pattern for:

- sampling
- preference editing if it becomes too large for the compact practice block
- Advanced timing/reset controls

Expected behavior:

- clicking the practice action opens the section below the practice block;
- the section visually belongs to that practice;
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

Keep in normal practice/new-practice UX:

- source language
- target language
- enabled/paused state
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
- delete Vocabulary Practice
- debug/runtime diagnostics
- sampled rulegen
- semantic pack installation/debug inputs
- helper data-folder tools

Do not make these prominent in the ordinary beta learner path:

- internal `S` terminology
- rule publication details
- manual active-word update and learning-word refresh controls
- helper diagnostics
- helper and sentence-fit technical status inside the active practice
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

Candidate-pool depth is no longer visible in existing practice blocks. It remains a
hidden backing value for current controllers and a setup-only advanced control
until the broader source-pack/cloud/local-storage question is resolved.

## Implementation Plan

Implement in small, reversible slices.

### Slice 1: Practice Shell

Add a practice-list section to the Vocabulary Practice card.

Requirements:

- show existing practice blocks for selected profile/pairs that have data;
- show compact counts and preferences;
- keep existing controls available while the new shell is validated;
- no backend schema migration.

### Slice 2: Vocabulary Library Entry

Move admitted-word inspection out of the active practice block and into a
dedicated Vocabulary Library page opened from a compact story-card entry.

Requirements:

- keep the existing dashboard read model/helper routes where possible;
- scope refresh/list actions to the selected profile and selected active
  language pair;
- let the dedicated page switch among active language pairs for the selected
  profile;
- keep advanced details opt-in inside the dedicated page.

### Slice 3: Sampling Curtain

Move sampling under the active practice block and into the new-practice flow.

Requirements:

- sampling uses current practice preferences for existing practice instances;
- sampling uses unsaved visible form values inside the new-practice flow;
- repeated sampling remains fast and non-mutating.

### Slice 4: New Practice Flow

Add the `Start Vocabulary Practice` entry and a linear modal/drawer.

Requirements:

- user chooses source/target before admission settings;
- proficiency and topic interests are front and center;
- sample preview is available before initialization;
- initialization cannot accidentally use stale/default preferences.

### Slice 5: Preferences In Practice Blocks

Expose persisted preferences inside existing practice blocks.

Requirements:

- compact summary is always visible;
- full edit form can be collapsed;
- saving preferences updates future sampling, refresh, and automatic growth
  behavior.

### Slice 6: Remove Old Flat Control Path

Once the practice flow is validated, remove or permanently hide the old flat SRS
control path.

Requirements:

- no duplicate initialize buttons competing for attention;
- no dashboard floating outside a practice context;
- no maintenance actions in the main learner path.

## Acceptance Criteria

Before this UX is considered beta-ready:

- a fresh user can start en-es Vocabulary Practice without knowing implementation order;
- the user must see preference controls before initialization;
- initialization uses the visible preferences;
- existing practice data appears as one or more practice blocks;
- sampling and dashboard are adjacent and collapsed by default;
- changed new-word preferences have an explicit save point;
- proficiency edits show the previous saved setting and can be restored before
  saving;
- display/feedback controls are reachable without being buried in Advanced;
- Advanced contains timing thresholds and reset, not routine/manual
  active-word operation buttons;
- reset remains clearly dangerous and profile/pair scoped;
- no ordinary beta path requires reading `SRS`, `story`, `S`, `bootstrap`, `rulegen`,
  `publish`, or helper-diagnostic terminology.

## Non-Goals

This plan does not require:

- changing the admission algorithm;
- changing SRS scheduling math;
- adding browsing-based admission to the product path;
- improving topic coverage;
- renaming internal `srs_*` implementation identifiers;
- migrating existing helper store files;
- adding multi-profile collaboration.

## Open Questions

- Final labels for initial size and candidate pool.
- Whether candidate-pool depth should stay setup-only, move to a future advanced
  data-source control, or disappear from user settings entirely.
- Where the eventual browsing-data opt-in belongs once browsing aggregates are
  consumed by production admission, likely near admission preferences rather than
  under generic logging.
- Whether the practice flow should be modal, drawer, or inline stepper.
- Whether a user can have multiple practice instances for the same language pair
  under the same profile, or exactly one practice instance per profile/pair.
- Whether old inactive practice instances should appear by default or under
  archived practice.
- Whether reset should offer a sub-choice to preserve discarded-word metadata.

## Verification Targets

Add or update tests when implementation starts:

- Options markup test: lifecycle controls are inside practice or advanced
  containers, not loose at the root of Vocabulary Practice.
- Controller test: new-practice initialize persists visible preferences before or
  during initialization.
- Helper/extension smoke: initialized practice appears in the practice list with
  dashboard counts.
- Preflight update: family-beta manual signoff starts from the practice flow rather
  than from the old flat SRS controls.
