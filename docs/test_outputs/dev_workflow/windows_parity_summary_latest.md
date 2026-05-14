# Windows GUI Parity Audit

Generated: 2026-05-14T21:11:20.678929+00:00

- Status: PASS
- Counts: PASS=9 WARN=0 FAIL=0

## Checks
- `PASS` Windows Data Paths: Windows AppData / Roaming path handling exists in helper and GUI startup paths.
- `PASS` Windows Shell Integration: Windows shell integration exists for open/reveal path actions.
- `PASS` Windows Installer Scaffolding: Windows installer scaffolding exists via Inno Setup and signing hooks.
- `PASS` Windows Helper Packaging: PyInstaller packaging includes Windows helper parity.
- `PASS` Windows Build Validation: Build output validation includes Windows checks.
- `PASS` Windows Helper Autostart: Helper autostart includes a Windows path.
- `PASS` Windows Native Messaging Install: Windows native-messaging install includes manifest and registry registration.
- `PASS` Windows Tray Launch Path: Frozen helper tray launch includes Windows-specific handling.
- `PASS` Hosted Windows Validation: Hosted CI includes a Windows runner for parity reporting.
