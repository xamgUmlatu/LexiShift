# Windows GUI Parity Workstream

Purpose:
- track Windows desktop parity as a workflow surface, not just a release-time surprise
- keep build/runtime/helper gaps explicit until they are implemented and verified

Primary commands:

```bash
npm --prefix scripts run check
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
- Windows native-messaging manifest + registry installation coverage
- Windows frozen tray-to-main-app launch behavior
- Hosted CI Windows runner coverage

Current interpretation:
- `PASS`: parity evidence exists in code/workflow
- `FAIL`: parity gap is explicit and should remain tracked until resolved

Current known gaps:
- full Windows release confidence still depends on hosted build stability over time, not just one green audit snapshot
- the parity audit is now a required workflow gate in `check` / pre-push / Windows CI, but it is not by itself a full release certification
- browser-specific install coverage is currently limited to the supported GUI environments (`chrome`, `chromium`, `brave`)

Recommended rollout order:
1. keep the packaged GUI/helper/native-host parity checks green
2. keep the hosted Windows full-build lane stable enough to become a trusted release signal
3. expand the audit further only when new Windows-specific surfaces are added
4. then decide whether to promote Windows GUI parity items from advisory to required workflow gates
