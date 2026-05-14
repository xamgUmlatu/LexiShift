# Windows GUI Parity Workstream

Status: active parity workstream
Role: Planning / WIP
Last updated: 2026-05-15
Last verified: 2026-05-15 Lane 3 packaging/platform parity truth pass, Windows parity audit, parity summary render, focused workflow/build/parity tests, doc-reference check, state check, and diff hygiene
Purpose: track remaining Windows parity confidence gaps and rollout priorities without redefining the active parity gate
Source-of-truth: current parity gate behavior lives in `feature_state_matrix.md`, `scripts/dev/windows_parity_audit.py`, and `scripts/package.json`.

Use this doc as planning delta only.
The current workflow contract already treats the Windows parity audit as required; this file tracks the remaining confidence-building work around that gate.

Planning focus:
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
3. close remaining release-confidence gaps surfaced by installer/native-host/browser coverage
4. expand the audit further only when new Windows-specific surfaces are added
