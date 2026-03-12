# Windows GUI Parity Audit

Generated: 2026-03-12T00:08:38.994036+00:00

- Status: FAIL
- Counts: PASS=4 WARN=0 FAIL=4

## Checks
- `PASS` Windows Data Paths: Windows AppData / Roaming path handling exists in helper and GUI startup paths.
- `PASS` Windows Shell Integration: Windows shell integration exists for open/reveal path actions.
- `PASS` Windows Installer Scaffolding: Windows installer scaffolding exists via Inno Setup and signing hooks.
- `FAIL` Windows Helper Packaging: PyInstaller packaging only builds the helper app in the macOS branch; Windows packaging currently emits the main app only.
- `FAIL` Windows Build Validation: Build output validation is macOS-only today; there is no Windows dist/exe validator.
- `FAIL` Windows Helper Autostart: Helper autostart is implemented for macOS LaunchAgent only; no Windows startup-registration path is tracked in code.
- `FAIL` Windows Tray Launch Path: Frozen helper tray launch has macOS-specific app-bundle handoff, but no Windows-specific main-app launch path.
- `PASS` Hosted Windows Validation: Hosted CI includes a Windows runner for parity reporting.
