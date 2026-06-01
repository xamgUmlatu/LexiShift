# Build And Release Workflows

Status: active runbook
Role: Runbook / operational
Last updated: 2026-06-01
Last verified: 2026-06-01 startup-performance plan routing review and doc-reference check; build not rerun
Purpose: current build, packaging, signing, and release entrypoints for maintained surfaces
Source-of-truth: build/release runbook; operational behavior is defined by `scripts/package.json`, `scripts/dev/dev_workflow_build.py`, `scripts/build/gui_app.py`, and `scripts/build/installer.py`.

This page centralizes packaging/signing/release commands for developer/operator use.

## Developer Safety Entry Points

Quick local safety commands:

```bash
npm --prefix scripts run check
npm --prefix scripts run build
```

Notes:
- `check` is the stable non-mutating repo safety loop and now includes the strict Windows parity audit.
- `build` is the local build smoke for surfaces with maintained build paths.
- `build:report` is the full build contract and is what hosted macOS and Windows CI run.
- `build:ci` / `build:ci:report` run the same build workflow in CI-safe mode and explicitly record GUI-validation skips on unsupported hosts.
- Repo-wide style lint is now part of `check`; use `check:style:report` / `check:style:summary` when you want durable style artifacts without running the full safety loop.

## GUI App Packaging (PyInstaller)

Install packaging deps:
```bash
pip install -r requirements-build.txt
```

This installs the shared developer tools plus the maintained GUI packaging deps used by hosted macOS build validation.

Build app bundles:
```bash
python scripts/build/gui_app.py
```

Validate bundle resources:
```bash
python scripts/build/gui_app.py --validate
```

Install app bundles into `/Applications` on macOS:
```bash
python scripts/build/gui_app.py --install
```

Direct PyInstaller invocation:
```bash
pyinstaller --clean --noconfirm apps/gui/packaging/pyinstaller.spec
```

Expected outputs:
- macOS: `dist/LexiShift.app` and `dist/LexiShift Helper.app`
- Windows: `dist/LexiShift.exe`

Startup-performance planning:
- `packaged_gui_startup_performance_plan.md` owns the packaged GUI launch
  performance workstream, including extension-to-GUI resource-settings handoff
  timing, PyInstaller bundle slimming, launch-path comparison, and first-paint
  deferral planning.

## Installer Packaging (DMG/EXE)

Build installers:
```bash
python scripts/build/installer.py
```

Optional validation before packaging:
```bash
python scripts/build/installer.py --validate
```

Notes:
- macOS output: `.dmg` under `apps/gui/dist/installers/`
- Windows output: Inno Setup `.exe` under `apps/gui/dist/installers/`
- Build Windows binaries/installers on Windows hosts.

## Code Signing And Notarization

### macOS signing

```bash
python scripts/build/installer.py --mac-sign-identity "Developer ID Application: Your Name (TEAMID)"
```

### macOS notarization

```bash
python scripts/build/installer.py \
  --mac-sign-identity "Developer ID Application: ..." \
  --notarize \
  --apple-id you@domain.com \
  --team-id TEAMID \
  --notary-password APP_SPECIFIC_PASSWORD
```

### Windows Authenticode signing

```bash
python scripts/build/installer.py \
  --win-sign-pfx C:\\path\\cert.pfx \
  --win-sign-password YOUR_PASSWORD
```

## Chrome Web Store Upload Gate

Run preflight:
```bash
npm --prefix scripts run preflight:cws
```

Runbook:
- `../runbooks/cws_upload_gate.md`

Reports folder:
- `../runbooks/cws_preflight_reports/`

## Release References

- Architecture + policy status: `../architecture/chrome_web_store_review_working_doc.md`
- Native messaging checklist: `../architecture/native_messaging_checklist.md`
- Full scripts map: `../../scripts/README.md`
