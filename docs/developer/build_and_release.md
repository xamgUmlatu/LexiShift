# Build And Release Workflows

This page centralizes packaging/signing/release commands for developer/operator use.

## GUI App Packaging (PyInstaller)

Install packaging deps:
```bash
pip install pyside6 pyinstaller
```

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
