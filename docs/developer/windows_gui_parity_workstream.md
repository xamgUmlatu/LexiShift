# Windows GUI Parity Workstream

Purpose:
- track Windows desktop parity as a workflow surface, not just a release-time surprise
- keep build/runtime/helper gaps explicit until they are implemented and verified

Primary commands:

```bash
npm --prefix scripts run check:windows:parity
npm --prefix scripts run check:windows:parity:summary
```

What the audit currently checks:
- Windows data-path coverage in GUI/helper startup paths
- Windows shell integration for open/reveal path actions
- Windows installer scaffolding
- Windows helper packaging parity in PyInstaller spec
- Windows build-output validation coverage
- Windows helper autostart coverage
- Windows frozen tray-to-main-app launch behavior
- Hosted CI Windows runner coverage

Current interpretation:
- `PASS`: parity evidence exists in code/workflow
- `FAIL`: parity gap is explicit and should remain tracked until resolved

Current known gaps:
- helper tray packaging is macOS-only in the PyInstaller spec
- build-output validation is macOS-only
- helper autostart is macOS-only
- frozen helper tray launch has no Windows-specific handoff to the main app
- hosted Windows CI validation is still advisory until a Windows lane is added and stabilized

Recommended rollout order:
1. keep the Windows parity audit green for areas that already have parity
2. add hosted Windows reporting before attempting full Windows GUI build parity
3. add Windows build validation once `.exe` / dist expectations are explicit
4. only then promote Windows GUI parity items from advisory to required workflow gates
