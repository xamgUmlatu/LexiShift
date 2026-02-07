# Helper Tray + Native Messaging Debug Summary (for external review)

This document summarizes the current issues, observed logs, and build/runtime behaviors for the LexiShift helper tray + native messaging integration. It is intended for a fresh external review.

## Scope / Components
- GUI app (PySide6, PyInstaller one‑file build)
- Native messaging helper host (`lexishift_native_host.py`)
- Helper tray app (`LexiShift Helper.app`) that spawns the daemon
- Chrome extension (options.html debug buttons)

## Key files involved
- `apps/gui/src/helper_installer.py` (bundle resolution + manifest install)
- `apps/gui/src/helper_ui.py` (Install Helper flow + prompting)
- `apps/gui/src/helper_tray.py` (tray icon + tray log)
- `apps/gui/src/helper_daemon.py` (background rulegen loop + status file)
- `apps/gui/src/helper_app.py` (helper tray entrypoint)
- `apps/gui/src/main.py` (main GUI entrypoint, includes `--helper-daemon`)
- `core/lexishift_core/helper_engine.py` (rulegen job + status writes)
- `core/lexishift_core/helper_paths.py` (data root + paths)
- `scripts/helper/lexishift_native_host.py` (native messaging host)
- `apps/gui/packaging/pyinstaller.spec` (bundling resources)
- Chrome extension: `apps/chrome-extension/shared/helper_client.js`, `apps/chrome-extension/shared/helper_transport_extension.js`, `apps/chrome-extension/options.js`

## Primary problem statements
1) **Tray icon visible according to Qt logs but not visible in macOS menubar.**
2) **Native messaging manifest missing after cleanup, causing “Specified native messaging host not found”.**
3) **“Install Helper” sometimes triggers file picker (host path not resolved).**
4) Confusion about app bundle contents: `/Applications/LexiShift.app/Contents/Resources` only contains icon, not helper files.

## Observed terminal outputs & logs

### Helper tray logs (most recent)
```
Helper tray starting.
System tray available: True
Tray icon null: False, sizes: [PySide6.QtCore.QSize(36, 36)]
Tray visible: True
Helper tray starting.
System tray available: True
Tray icon null: False, sizes: [PySide6.QtCore.QSize(22, 22)]
Tray visible: True
```

Despite these logs, **tray icon was not visible** until user removed menu bar icons (icon overflow/hiding).

### SRS status file (after tray + daemon fix)
```
{
  "helper_version": "0.1.0",
  "last_error": null,
  "last_pair": "en-ja",
  "last_rule_count": 4695,
  "last_run_at": "2026-02-04T05:34:15.606316+00:00",
  "last_target_count": 1589,
  "version": 1
}
```

### Missing manifest (causing helper status error)
```
ls -la "$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts/com.lexishift.helper.json"
ls: ... No such file or directory
```
This yields **“Specified native messaging host not found.”** in the extension.

## Runtime behaviors / findings

### Tray icon visibility
- Qt reports `QSystemTrayIcon.isSystemTrayAvailable() = True`
- Icon is not null and has sizes
- `tray.isVisible() == True`
- Still not visible in menu bar until user removed extra menu bar icons (icon overflow/hiding).

### srs_status.json missing initially
`~/Library/Application Support/LexiShift/LexiShift/srs/` was empty, so status file didn’t exist.
Fix: daemon now writes status immediately on start.

### Resources inside .app
User reports:
```
ls /Applications/LexiShift.app/Contents/Resources/
ttbn.icns
```
No `resources/helper/lexishift_native_host.py` found under `.app` or `dist`.
This is a **one‑file PyInstaller build**: resources live under `_MEI...` at runtime, not inside the `.app` bundle. This explains why `/Applications/.../Resources/` only shows icons.

### File picker on “Install Helper”
Triggered when helper host path cannot be resolved:
`default_host_script()` falls back to a path that does not exist (e.g. missing bundle or stale host_path in settings).
Added logs in helper installer/UI to explain resolution and fallback.

## Commands used in debugging
Stop processes:
```
pkill -f "/Applications/LexiShift Helper.app/Contents/MacOS/LexiShiftHelper"
```

Start tray helper directly:
```
/Applications/LexiShift\ Helper.app/Contents/MacOS/LexiShiftHelper
```

Check logs:
```
cat "$HOME/Library/Application Support/LexiShift/LexiShift/helper_tray.log"
cat "$HOME/Library/Application Support/LexiShift/LexiShift/srs/srs_status.json"
```

## Known scripts added for cleanup / diagnostics
- `scripts/cleanup_helper.sh`
- `scripts/check_helper_status.sh`
- `scripts/dev_cycle.sh`

These were added to simplify clean/build/check workflows.

## Additional context
- Extension debug button exists in options.html (Run rulegen debug), now calls helper `trigger_rulegen` + `get_snapshot`.
- Native messaging host lives at `scripts/helper/lexishift_native_host.py` and expects manifest in Chrome NativeMessagingHosts directory.
- Helper tray/daemon is started by LaunchAgent when installed.
- A new tray icon debug fallback was added to force a visible icon (blue “L” square).

## Current hypotheses
- Tray icon actually works, but macOS menu bar overflow hides it.
- One‑file build behavior is confusing because helper resources are extracted at runtime to `_MEI...`.
- File picker appears due to missing helper host path resolution or stale cached path from earlier dev builds.

## Desired outcomes
- Ensure helper host is bundled/resolved without file picker.
- Ensure helper manifest exists reliably.
- Ensure tray icon always visible or provide test notification.
- Provide a deterministic dev/build/cleanup workflow.
