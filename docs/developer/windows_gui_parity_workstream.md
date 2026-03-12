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
- native-messaging install and browser-host registration are now tracked explicitly and remain unimplemented on Windows
- the current audit should remain `FAIL` until Windows native-messaging manifest and registry installation are implemented in the GUI helper flow
- full Windows release confidence still depends on hosted build stability over time, not just one green audit snapshot

Recommended rollout order:
1. keep the packaged GUI/helper parity checks green while tracking Windows native-messaging install as an explicit failure
2. keep the hosted Windows full-build lane stable enough to become a trusted release signal
3. expand the audit beyond packaging/runtime parity into Windows native-messaging install coverage
4. only then promote Windows GUI parity items from advisory to required workflow gates
