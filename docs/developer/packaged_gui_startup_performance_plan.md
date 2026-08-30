# Packaged GUI Startup Performance Plan

Status: implemented and locally verified; signed-release verification remains
Role: Planning / WIP
Last updated: 2026-08-27
Last verified: 2026-08-27 installed-bundle rebuild, blocking theme-I/O diagnosis and fix, 3-run cold/activation budget measurements, and focused GUI/startup tests
Purpose: make the packaged LexiShift GUI open quickly enough from extension-driven language-data recovery flows without changing the architecture stack prematurely
Source-of-truth: planning doc only; current behavior lives in `scripts/helper/lexishift_native_host.py`, `core/lexishift_core/helper/gui_app_launch.py`, `apps/gui/src/main.py`, `apps/gui/src/main_runtime.py`, `apps/gui/packaging/pyinstaller.spec`, `scripts/build/gui_app.py`, and `scripts/build/installer.py`.

## Problem

The Chrome extension can now deep-link a missing-language-data SRS setup flow
into the packaged LexiShift GUI. That is the right product shape: the extension
does not own language-pack installation, and the GUI provides the managed
Learning Languages view.

The current packaged launch experience can still feel too slow. A user observed
roughly `12` seconds from pressing the extension button to LexiShift becoming
usable. That is not acceptable as the long-term product experience. The target
is a fast, direct, recoverable language-data setup path without adding a spinner
as a substitute for performance work.

## Product Goal

When the user needs language data from the SRS story setup flow:

1. if LexiShift is already running, the extension should focus the existing GUI
   and open the relevant Learning Languages card almost immediately;
2. if LexiShift is closed, the installed app should cold-launch to the same view
   quickly enough that it feels like a native settings handoff;
3. the user should not need to understand pack filenames, manual paths, or
   developer logs to continue setup;
4. performance fixes should preserve the current GUI/helper/native-messaging
   ownership boundaries.

## Targets

Primary targets for the resource-settings handoff:

| Scenario | Target | Release gate |
| --- | ---: | --- |
| Existing GUI activation | `p50 <= 500 ms`, `p95 <= 1000 ms` | required before beta handoff unless a current-machine exception is documented |
| Cold packaged app to first visible window | `p50 <= 3000 ms`, `p95 <= 5000 ms` | required for product-ready beta packaging |
| Cold packaged app to Learning Languages card focused | `p50 <= 3500 ms`, `p95 <= 6000 ms` | required for product-ready beta packaging |
| Native-host response to extension | `<= 250 ms` for fire-and-forget launch acknowledgement | required so extension UI does not appear stuck |

Secondary targets:

- reduce installed app bundle size and file count when the payload is
  demonstrably irrelevant to runtime;
- avoid duplicate cold launches when an existing GUI can be activated;
- keep Windows launch and native-host parity explicit even if the first
  performance measurements are macOS-focused.

## Current Evidence

These observations were refreshed locally on 2026-08-27.

| Evidence | Current observation | Interpretation |
| --- | --- | --- |
| Previously intermittent hang | fine-grained checkpoints stopped after `main_window.window_state_restored`; a process stack sample showed the GUI thread in `QPixmap::load -> QFile::open` for the active custom-theme background under `~/Downloads` | the multi-minute stall was external theme-image file I/O, not installed dictionary inventory |
| Theme-image fix | background file reads and `QImage` decoding now run through a shared daemon loader; GUI-thread `QPixmap` creation occurs only after a decoded result arrives | slow, protected, or unavailable custom image paths no longer block first paint or Resource Settings |
| Cold installed bundle to Resource Settings | three `open /Applications/LexiShift.app` runs reached `settings_dialog.shown` at `1515.1-2396.0 ms`, median `1573.5 ms`, measured p95 `2313.8 ms` | passes the `3500 ms` median and `6000 ms` p95 resource-settings budgets on the current machine |
| Cold timing split | pre-entry median `559.5 ms`; process-entry-to-dialog median `1014.0 ms` | both macOS/bootloader and application work are bounded; no current multi-minute in-process block remains |
| Existing-GUI activation to visible Resource Settings | three runs measured `107.9-797.6 ms`, median `254.4 ms`, measured p95 `743.3 ms` | passes the `500 ms` median and `1000 ms` p95 activation budgets while including first dialog construction plus subsequent dialog reuse |
| Resource panel construction | instrumented live runs complete Language Pack panel construction in tens of milliseconds and the full Settings dialog in roughly `0.6-0.8 s` after it is requested | the installed large dictionary state is not the current blocker |
| Repeatability tooling | measurement output now includes structured checkpoints, p95, optional budget failure, and exact session app-PID cleanup for cold repetitions | cold samples no longer accidentally become singleton activation samples |
| Installed main app size | `/Applications/LexiShift.app` is `185M` after the onedir EXE payload split | down from `692M`; the prior executable/data duplication was a real packaging defect |
| Installed helper app size | `/Applications/LexiShift Helper.app` is `115M` after the onedir EXE payload split | down from `494M`; dual-bundle runtime remains a size concern, but much less urgent |
| Installed main app file count | `809` files | down from `1258`; file-count pressure is lower, but release signing/notarization still needs measurement |
| Main executable | `7.1M` | down from `100M`; the executable now looks like a normal onedir launcher instead of carrying a duplicated payload archive |
| Signing | ad-hoc signed, no TeamIdentifier, `537` sealed resources | release signing/notarization may affect first-run trust and scanning behavior |
| Current packaging mode | PyInstaller onedir/`COLLECT` app bundles with `EXE(..., exclude_binaries=True)` and configurable UPX | main/helper executables no longer embed the collected payload; `scripts/build/gui_app.py --no-upx` remains available for later comparison |
| Current launch command | native host calls `open /Applications/LexiShift.app --args --open-resource-settings --resource-pair en-es` | product-correct path, but `open`/LaunchServices overhead must be measured against direct executable launch |
| Process list | parent/child main-app and helper processes appear | likely PyInstaller parent/child behavior, but duplicate cold-launch behavior must be distinguished from normal bootloader process structure |

The important current read: the current architecture meets the local beta
targets. The measured pathological block was a synchronous custom-theme image
open, and moving that work off the GUI thread restored bounded startup without
removing theme support or changing dictionary ownership. The remaining
uncertainty is release signing/notarization and tester-machine behavior, not a
known in-process startup blocker.

## Working Hypotheses

Ranked by likely product impact:

1. **Pre-`main()` macOS packaged launch overhead dominates the bad case.**
   Current app logging starts after Python has entered `main()`, so it misses
   LaunchServices, code-sign verification, PyInstaller bootloader work, and
   early import overhead.
2. **Existing-GUI activation is the biggest cheap win.** If LexiShift is already
   open, the native host should send a local activation message and should not
   spawn a cold app instance.
3. **Bundle payload is heavier than necessary.** The app and helper likely carry
   broad Qt/PySide, Python, resource, and dictionary payloads. Some of that may
   be removable or lazy-loaded.
4. **UPX may hurt startup.** Compressed binaries can reduce size but increase
   decompression and security-scanning costs. The current spec uses `upx=True`
   for main, helper, and collect steps.
5. **Full `MainWindow` construction does too much before first paint.** It
   initializes rules UI, replacement panel, utility/log dock, helper labels,
   helper auto-install, embedding index refresh, profile/ruleset state, theme,
   and splitters before the window is shown.
6. **The resource-settings route can be lighter than the whole editor route.**
   The user clicked a language-data recovery action; the first useful screen is
   Learning Languages, not the full rules editor.
7. **Signing/notarization posture affects real user launches.** Ad-hoc local
   signing may behave differently from a properly signed/notarized release
   artifact.

2026-08-27 diagnosis result: hypothesis 5 contained the current pathological
case, but the blocking work was specifically synchronous custom-theme image
opening inside `_apply_theme()`, not rules, embeddings, or resource inventory.
Hypotheses 1 and 7 remain relevant to release-candidate variance; the latest
local measurements are within budget.

## Non-Goals

- Do not add an extension loading spinner as the main fix.
- Do not replace PyInstaller or the GUI stack before measuring the real
  bottleneck.
- Do not move language-pack installation into the Chrome extension.
- Do not introduce a separate resource manager executable until the cheaper
  launch, bundle, and lazy-start paths are exhausted.
- Do not optimize by deleting bundled resources without bundle validation,
  native-host validation, and resource-install smoke coverage.

## Phase 0: Measurement And Telemetry

Goal: make every observed launch explainable before changing behavior.

Implementation checkpoint:

- 2026-06-01: native-host resource-settings requests now generate a startup
  session, log activation/launch timing, pass session/timing context into cold
  GUI launch environment variables, and include command-class/Popen timing in
  `logs/native_host.log`.
- 2026-06-01: GUI startup logs now include a pre-Qt-import process-entry
  checkpoint plus session id, PID/PPID, argv mode, launch source, launch mode,
  resource pair, UTC timestamps, and request-to-checkpoint timing.
- 2026-06-01: `scripts/dev/packaged_gui_startup_measure.py` can measure
  `open`, bundle-id, direct executable, and existing-GUI activation paths and
  write JSON/Markdown artifacts for comparison.
- 2026-06-01: first installed-bundle measurements after rebuilding with
  telemetry showed existing-GUI activation at about `167 ms`, warm cold-launch
  `open /Applications/LexiShift.app` at about `9507 ms`, bundle-id launch at
  about `12057 ms`, and direct executable launch at about `14735 ms`. The
  `open` warm cold-launch split was about `3327 ms` after process entry and
  about `6180 ms` before the first Python checkpoint, so the largest remaining
  warm-launch gap is still pre-GUI/PyInstaller/LaunchServices territory. The
  first launch immediately after reinstall also showed a one-off slower sample
  around `42238 ms`, which should be treated as a first-run/install-verification
  datapoint until repeated.
- 2026-06-01: the PyInstaller spec was corrected to use the canonical onedir
  split for EXE targets (`exclude_binaries=True`, with binaries/zipfiles/datas
  owned by `COLLECT`), and the build wrapper gained a `--no-upx` comparison
  switch. Rebuilt/installed measurements then showed warm relaunch through
  `open` at about `1041.5 ms` (`584.4 ms` pre-entry, `457.1 ms`
  process-entry-to-window), bundle-id launch at about `1050.9 ms`, direct
  executable launch at about `1065.0 ms`, and existing-GUI activation at about
  `196.5 ms`.
- 2026-08-27: structured checkpoints were added across `MainWindow`, Settings,
  and the Language Pack panel. A previously reproducible timeout stopped at
  theme application, and a stack sample isolated the GUI thread in Qt file-open
  code for an active external theme image.
- 2026-08-27: theme image reads/decoding moved to a shared background loader;
  startup log paths are deduplicated; repeated resource activation reuses and
  focuses the visible Settings dialog; and activation-session checkpoints now
  continue through `settings_dialog.shown`.
- 2026-08-27: the measurement command gained exact measured-app PID cleanup,
  structured checkpoint capture, p95 reporting, and optional median/p95 budget
  enforcement. Three installed cold runs and three activation runs passed the
  owning budgets; canonical artifacts are under
  `docs/test_outputs/dev_workflow/gui_startup_performance_{open,activation}_latest.*`.

Implementation plan:

1. Add a stable startup session id shared across native-host logs and GUI logs
   when the native host launches the GUI.
2. Extend native-host resource-setting logs with:
   - request received timestamp,
   - activation attempt start/end/result/duration,
   - resolved launch mode,
   - launch command class, not sensitive raw payloads,
   - `subprocess.Popen` return timing and PID when available.
3. Add pre-Qt/import startup checkpoints:
   - a tiny startup probe at the very top of `apps/gui/src/main.py`, before
     PySide imports;
   - a PyInstaller runtime hook checkpoint if needed, so packaged runs record
     earlier than `main()`.
4. Extend `StartupLogger` records with:
   - ISO timestamp,
   - session id,
   - PID and parent PID,
   - `sys.frozen`,
   - `sys.executable`,
   - app bundle path when detectable,
   - argv mode such as ordinary launch vs `--open-resource-settings`.
5. Add finer `MainWindow` construction checkpoints around:
   - settings load and migrations,
   - rules model/proxy/table construction,
   - replacement panel construction,
   - utility/log dock construction,
   - action/menu construction,
   - helper auto-install,
   - embedding index refresh,
   - active profile/ruleset load,
   - theme and window restore.
6. Add a developer measurement command that writes JSON and Markdown under
   `docs/test_outputs/dev_workflow/`, for example:

```bash
python3 scripts/dev/packaged_gui_startup_measure.py \
  --app /Applications/LexiShift.app \
  --pair en-ja \
  --repetitions 3 \
  --terminate-launched-app \
  --max-median-ms 3500 \
  --max-p95-ms 6000 \
  --json-out docs/test_outputs/dev_workflow/gui_startup_performance_open_latest.json \
  --markdown-out docs/test_outputs/dev_workflow/gui_startup_performance_open_latest.md
```

The measurement command should support:

- cold launch repetitions,
- existing-GUI activation repetitions,
- direct executable vs `open` launch mode,
- installed `/Applications` app vs local `apps/gui/dist/LexiShift.app`,
- optional cleanup of only LexiShift processes that it started.

Acceptance for Phase 0:

- One launch attempt can be traced from extension/native-host request to first
  GUI paint with no manual timestamp matching.
- Measurement artifacts separate browser/native-host acknowledgement time,
  activation time, pre-`main()` time, post-`main()` time, first paint time, and
  resource-card focus time.
- Duplicate launches are visible as duplicate session ids or duplicate cold
  sessions, not as ambiguous interleaved startup log lines.

Validation:

```bash
PYTHONPATH=core python3 -m pytest core/tests/dev/test_native_host_resource_settings.py -q
PYTHONPATH=apps/gui/src:core python3 -m pytest core/tests/dev/test_native_host_startup_logging.py -q
npm --prefix scripts run check:changed:local
```

## Phase 1: Launch Path Experiments

Goal: identify the fastest safe route to open the installed GUI.

Experiments:

1. Compare LaunchServices:
   - `open /Applications/LexiShift.app --args ...`
   - `/Applications/LexiShift.app/Contents/MacOS/LexiShift --open-resource-settings ...`
   - `open -b com.lexishift.app --args ...`
2. Compare installed vs local build artifact:
   - `/Applications/LexiShift.app`
   - `apps/gui/dist/LexiShift.app`
3. Compare activation vs cold launch:
   - GUI already running and singleton server ready;
   - GUI closed.
4. Compare bundle trust states:
   - ad-hoc signed current local install;
   - properly signed local release candidate when available;
   - quarantine/provenance attributes observed only, not removed as a hidden fix.
5. Confirm process behavior:
   - distinguish normal PyInstaller parent/child process structure from true
     duplicate application instances;
   - ensure repeated extension clicks while launch is in progress do not create
     multiple cold launches.

Potential changes:

- Prefer direct executable launch if it is materially faster and still keeps
  correct Dock/app activation behavior.
- Keep `open` if direct executable has worse UX, focus behavior, or platform
  risks.
- Add an in-flight launch lock in the native host or GUI activation layer if
  repeated extension clicks can spawn duplicate cold launches before singleton
  server readiness.

Acceptance for Phase 1:

- The chosen macOS launch path is selected by measured p50/p95 behavior, not
  assumption.
- Existing-GUI activation is reliably below target.
- Repeated extension clicks do not create multiple useful GUI instances.
- The native-host unit tests cover the selected route and fallback order.

Validation:

```bash
PYTHONPATH=core python3 -m pytest core/tests/dev/test_native_host_resource_settings.py -q
PYTHONPATH=core python3 -m pytest core/tests/dev/test_helper_installer_native_messaging.py -q
npm --prefix scripts run check:windows:parity
```

Measurement checkpoint:

- 2026-06-01: after the onedir payload split, the launch paths are effectively
  tied on the current machine: `open` about `1041.5 ms`, bundle-id about
  `1050.9 ms`, direct executable about `1065.0 ms`. Because `open` preserves
  normal Dock/focus semantics and is no longer materially slower, keep the
  native-host launch route on the installed app bundle unless release-candidate
  measurements regress.
- 2026-08-27: existing-GUI measurement now ends at the visible Resource
  Settings outcome rather than the earlier socket-receipt checkpoint. The
  current installed app passed three runs at `254.4 ms` median / `743.3 ms`
  measured p95; repeated requests focus the existing modal instead of nesting
  additional Settings dialogs.

## Phase 2: Bundle Audit And Slimming

Goal: remove startup-relevant payload only when evidence shows it is not needed.

Audit commands:

```bash
du -sh /Applications/LexiShift.app /Applications/'LexiShift Helper.app'
du -sh /Applications/LexiShift.app/Contents/* | sort -h
du -sh /Applications/'LexiShift Helper.app'/Contents/* | sort -h
find /Applications/LexiShift.app -type f -exec stat -f '%z %N' {} + | sort -nr | head -n 50
find /Applications/LexiShift.app -type f | wc -l
find /Applications/LexiShift.app -type l | wc -l
```

Candidate reductions, in preferred order:

1. Keep the canonical PyInstaller onedir EXE payload split:
   - `EXE` owns only the bootloader/scripts/PYZ and uses
     `exclude_binaries=True`;
   - `COLLECT` owns binaries, zipfiles, and datas;
   - this is already implemented and validated locally, and reduced the main
     app from `692M` to `185M`.
2. Turn off UPX and compare startup, size, and validation:
   - change `upx=True` to `upx=False` only if measurements improve or security
     scanning behavior is cleaner;
   - measure both main and helper.
3. Exclude unused Qt modules/plugins:
   - likely candidates include QML/Quick/VirtualKeyboard/WebEngine only if the
     built GUI does not use them;
   - verify actual bundled paths before editing the spec.
4. Prune unused Python dependency payloads:
   - use PyInstaller analysis artifacts and file inventory to identify heavy
     modules not imported by GUI/helper/native host.
5. Limit bundled `simplemma` dictionaries and similar lexical data:
   - keep only languages supported by current product flows unless the resource
     is intentionally part of offline fallback behavior.
6. Remove duplicate helper payload from the main app only if the native-host
   install and packaged-helper contracts still have a stable host path.
7. Preserve symlinks in DMG staging:
   - `scripts/build/gui_app.py --install` already uses `symlinks=True`;
   - `scripts/build/installer.py` DMG staging currently uses plain
     `shutil.copytree(...)` and should be fixed for installer size, even though
     it may not be the direct cause of local launch latency.

Acceptance for Phase 2:

- Each removed payload has a before/after measurement and a validation command.
- Bundle size/file-count changes are recorded in a generated performance report.
- App-managed language-data install still works for `wiktionary-es-en` and
  `freedict-es-en`.
- License-restricted `freq-es-cde` remains a manual setup path unless licensing
  changes.
- Windows build parity is not silently regressed.

Validation:

```bash
python3 scripts/build/gui_app.py --validate
npm --prefix scripts run build
npm --prefix scripts run check:windows:parity
PYTHONPATH=apps/gui/src:core python3 -m pytest apps/gui/tests/test_language_pack_translation_frequency_lifecycle.py -q
PYTHONPATH=core python3 -m pytest core/tests/dev/test_validate_app_bundle.py core/tests/dev/test_gui_app_build.py -q
```

## Phase 3: First-Paint And Resource-Settings Deferral

Goal: make the first useful GUI screen appear before nonessential main-window
work.

Implementation checkpoint:

- 2026-08-27: the proven blocking first-paint work was removed without broader
  UI deferral: custom-theme file I/O and image decoding no longer execute on the
  GUI thread. Main-window construction, resource inventory, and Settings
  construction are now separately checkpointed and the current installed app
  meets both cold and activation targets. The remaining deferral options below
  are optional optimization work unless release-candidate measurements regress.

Implementation options:

1. Defer `auto_install_helper(...)` until after first paint unless the current
   action needs helper installation immediately.
2. Defer `_refresh_embedding_index()` until after first paint or until the
   replacement panel needs it.
3. Defer log/utility dock heavy setup if the dock starts collapsed.
4. Load active profile/ruleset data after showing a lightweight shell when the
   launch mode is `--open-resource-settings`.
5. For resource-settings launch only, open the Settings/Learning Languages view
   as the first useful surface, then let the rest of the main workspace settle.
6. Keep ordinary app launch behavior unchanged unless the deferral is generally
   beneficial and covered by tests.

Acceptance for Phase 3:

- `--open-resource-settings --resource-pair en-es` reaches the Learning
  Languages card faster than ordinary full editor readiness.
- Deferred tasks do not change saved settings, profile selection, helper
  installation, or resource installation behavior.
- The app remains usable if deferred work fails; errors should appear in the
  normal diagnostics/log surfaces.

Validation:

```bash
PYTHONPATH=apps/gui/src:core python3 -m pytest apps/gui/tests -q
PYTHONPATH=core python3 -m pytest core/tests/dev/test_native_host_resource_settings.py -q
npm --prefix scripts run check:changed:local
```

If Phase 3 touches SRS setup surfaces, also run:

```bash
npm --prefix scripts run preflight:srs:beta:en-es
```

## Phase 4: Release Trust And Platform Hardening

Goal: ensure the measured improvement survives real packaging and install
conditions.

Work:

1. Measure ad-hoc, signed, and notarized macOS artifacts when signing
   credentials are available.
2. Confirm the Dock icon, app name, and focus behavior use `LexiShift.app`, not
   a Python executable identity.
3. Confirm first-run behavior after a clean install into `/Applications`.
4. Confirm Windows launch behavior with the packaged `LexiShift.exe` and native
   host executable path.
5. Document whether release signing changes startup latency materially.

Validation:

```bash
npm --prefix scripts run build:report
npm --prefix scripts run build:ci:report
npm --prefix scripts run check:windows:parity
```

Release validation may also need manual macOS notarization checks through
`scripts/build/installer.py` when credentials are available.

## Phase 5: Structural Fallbacks

Use these only if Phases 0-4 cannot reach the target.

Fallback options:

1. Build a small resource-manager executable that opens only Learning Languages.
   This is faster only if it avoids most PySide/main-window payload.
2. Split the helper/resource manager from the full GUI runtime.
3. Replace the packaging stack if PyInstaller boot and bundle scanning remain
   the dominant cost after bundle slimming and signing.
4. Keep the GUI app resident as a background agent after helper startup. This
   improves handoff speed but changes product lifecycle expectations, so it
   requires explicit UX and resource-use approval.

Do not start here. These are architecture changes, not first-pass performance
fixes.

## Implementation Order

Recommended sequence:

1. Phase 0 telemetry and measurement command.
2. Phase 1 launch-path comparison and duplicate-launch protection if needed.
   Current result: keep installed-bundle `open` because it is fast enough and
   preserves normal app semantics.
3. Phase 2 UPX comparison and bundle inventory-driven exclusions.
   Current result: canonical onedir payload split is complete; UPX comparison
   is now optional follow-up rather than the main launch blocker.
4. Phase 3 first-paint/resource-settings deferral.
   Current result: the targeted async theme-image fix was sufficient for the
   current machine; broader workspace deferral is not a beta blocker.
5. Phase 4 signed/notarized release measurement.
6. Phase 5 only if the target is still out of reach.

## Open Decisions

| Decision | Default recommendation | When to revisit |
| --- | --- | --- |
| Keep PyInstaller? | Yes | only if measured pre-`main()` overhead remains above target after launch-path, UPX, bundle, and signing work |
| Keep GUI-owned language data setup? | Yes | only if a future cloud/runtime-data model changes pack ownership |
| Prefer direct executable launch? | No for now | revisit only if release-candidate measurements show `open` regressing materially |
| Add in-extension loading state? | No as primary fix | consider only as a small affordance after launch performance is already acceptable |
| Add resource-only executable? | No | consider only after Phases 0-4 fail |

## Beta Readiness Impact

Before giving the SRS setup flow to testers, the en-es beta preflight should
include one manual resource-data recovery smoke:

1. remove only the relevant test-profile en-es resource packs;
2. open `options.html`;
3. start the en-es SRS story flow;
4. trigger the missing-data recovery link;
5. confirm LexiShift opens or activates to Learning Languages quickly;
6. install app-managed dictionary resources;
7. retry SRS initialization from the extension.

Current local installed-bundle evidence is under both cold and activation
targets. Beta can proceed on startup performance after the manual extension to
Resource Settings smoke; signed/notarized and tester-machine measurements remain
release-hardening follow-up rather than a known local blocker.

## Related Docs

- `docs/developer/build_and_release.md`
- `docs/runbooks/app_size_reduction.md`
- `docs/runbooks/srs_beta_preflight_en_es.md`
- `docs/language_pairs/lp_resource_requirements.md`
- `docs/language_pairs/data_source_licensing_and_distribution.md`
