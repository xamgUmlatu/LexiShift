# Chrome Web Store Review Working Doc (Open Questions)

Status: Draft  
Scope: Resolve five known review concerns for LexiShift Chrome extension submission.

## 2026-02-18 Discussion Notes (Current Decisions)

These points are confirmed from product discussion and should be treated as baseline unless changed:

1. `nativeMessaging` is required for SRS value:
   - Extension must connect to helper to use installed dictionaries and update SRS.
2. Install order:
   - Desktop app first or extension first can both work technically.
   - Current UX likely does not make the sequence obvious enough.
3. Missing helper behavior:
   - Show much stronger warning in SRS area and extension status.
   - Handcrafted JSON rulesets should still work without helper (non-SRS path remains functional).
4. Site coverage intent:
   - Product vision is full browsing experience, not limited-site experience.
   - Launch decision: all-sites out-of-box.
5. Sensitive sentence storage:
   - Launch decision: sentence-history storage defaults OFF and needs additional research.
   - Sentence-history module records: no URL field.
   - Exposure telemetry (`srsExposureLog`) currently retains URL field (for now).
6. Platform scope:
   - Roadmap target is macOS + Windows.
   - Current implementation maturity is higher on macOS.
7. Team/approval reality:
   - Current release decision-making is effectively the two maintainers.
8. Project staffing reality:
   - This is a personal/solo project, so release process must remain lightweight.

## Why this document exists

This document is the formal source of truth for:
- what we already know from the current codebase,
- what is still uncertain,
- what product decisions are required from the app vision side,
- what technical implementation decisions follow from those product decisions.

## Concern 1: High-risk permission (`nativeMessaging`)

### What we know
- Extension requests `nativeMessaging` in `apps/chrome-extension/manifest.json`.
- Extension background service worker uses `chrome.runtime.sendNativeMessage(...)`.
- Missing helper host errors are handled and returned as structured errors (no hard crash).
- Native host install depends on extension ID mapping and host manifest install.

### Open doubts to resolve
- Is native helper support a hard requirement for first Chrome Web Store release, or can it be optional/disabled at launch?
- If required, what exact user value cannot be delivered without native messaging?
- What installation path do we want to support for users who install only from CWS (without desktop app first)?

### Product decisions needed from you
1. Should CWS v1 require the desktop app/helper, or should extension run in a meaningful "no-helper mode"?
2. If helper is required, what is the intended user onboarding sequence?
3. What is the minimum acceptable degraded behavior when helper is missing?

### Current decision state
- Resolved:
  - CWS v1 helper role: required for SRS functionality.
  - Degraded mode: non-SRS handcrafted JSON rules continue to function.
- Still open:
  - Final onboarding UX/flow copy and sequence guidance.
  - Exact warning severity and placement in options/content surfaces.

### Technical follow-up after decision
- Finalize justification text for CWS reviewer notes.
- Align helper install UX with fixed production extension ID.
- Add explicit missing-host UX states in options/content diagnostics if needed.

## Concern 2: Broad host permission (`<all_urls>`)

### What we know
- Content scripts run on `<all_urls>`, all frames, and about:blank frames.
- Runtime performs text-node scanning/replacement and local storage writes.
- No remote telemetry/exfiltration endpoints are currently used by extension runtime.

### Open doubts to resolve
- Do we truly need all websites, all frames, and about:blank for v1 experience?
- Should we narrow scope by default and require opt-in expansion?
- Which page classes should be explicitly excluded for trust/safety (banking, auth, internal corp tools, etc.)?

### Product decisions needed from you
1. What is the intended default site coverage policy at launch?
2. Are we willing to ship with narrower defaults to reduce review risk?
3. What categories/domains should be blocked by policy even if technically possible?

### Current decision state
- Resolved:
  - Long-term product intent is broad/full-site behavior.
  - Launch permission model: all-sites out-of-box.
  - Provisional exclusion policy: no explicit category/domain exclusions for launch.
- Still open:
  - Whether policy review or implementation constraints force targeted exclusions later.

### Technical follow-up after decision
- Manifest match narrowing or runtime domain exclusion policy.
- Reviewer-facing privacy explanation of data flow and local-only processing.
- Potential split between "core mode" and "advanced everywhere mode".

## Concern 3: Native app protocol framing

### What we know
- Native host reads/writes 4-byte length-prefixed JSON frames.
- Implementation currently uses explicit little-endian (`<I`) framing.

### Open doubts to resolve
- Do we need strict cross-platform/native-endian interpretation for future environments, or is current target matrix fixed to little-endian platforms?
- Do we want protocol versioning and compatibility policy documented for external integrators?

### Product decisions needed from you
1. What platforms are officially supported for CWS launch?
2. Do we need to support any non-little-endian environments in roadmap scope?

### Current decision state
- Resolved:
  - Roadmap platforms: macOS and Windows.
- Still open:
  - Non-little-endian compatibility requirement (likely no for launch, but needs explicit call).

### Technical follow-up after decision
- Keep current framing with documented platform assumptions, or
- adjust to native-endian framing policy and document migration/versioning.

## Concern 4: MV3 service worker lifecycle

### What we know
- Background is MV3 service worker.
- Bridge is request/response (`sendNativeMessage`), not persistent `connectNative` port.
- This reduces reconnect-state complexity compared to persistent ports.

### Open doubts to resolve
- What reliability SLA do we want for helper-dependent actions after browser idle/sleep cycles?
- Do we need explicit retry/backoff policy for all helper actions, or only feedback queue/sync paths?

### Product decisions needed from you
1. What user experience is acceptable when service worker wakes and helper is unavailable?
2. Which operations must be guaranteed (eventual success) vs best-effort?

### Current decision state
- Resolved:
  - Manual JSON rules path must remain available without helper.
  - SRS control actions should fail fast when helper is unavailable, with strong warning and fix guidance.
  - Feedback sync should use eventual retry via extension-side queue persistence until helper is available.
- Still open:
  - Queue bounds/retention numbers and user-visible diagnostics detail level.

### Technical follow-up after decision
- Formal reliability policy by operation type.
- Expand test matrix for wake/sleep/host-restart scenarios.

## Concern 5: Asset completeness and localization

### What we know
- Manifest icon files and locale files currently exist in repo.
- `__MSG_app_name__` and `__MSG_app_description__` are present in locale message files.

### Open doubts to resolve
- What is our release packaging gate to prevent accidental missing assets at zip/upload time?
- Who owns final pre-upload validation and sign-off checklist?

### Product decisions needed from you
1. Do you want a mandatory release checklist gate for extension packaging?
2. Who is final approver for CWS upload readiness?

### Current decision state
- Resolved:
  - Final approvers are the two maintainers.
  - Use a lightweight-but-required pre-upload gate suitable for a solo project.
- Still open:
  - Final exact checklist text/versioning policy over time.

### Technical follow-up after decision
- Add automated preflight script/checklist used before every upload.

### Implementation status (2026-02-18)
- Added automated preflight command:
  - `npm --prefix scripts run preflight:cws`
- Added gate script:
  - `scripts/dev/cws_preflight.js`
- Added gate runbook:
  - `docs/runbooks/cws_upload_gate.md`
- Added report artifact folder:
  - `docs/runbooks/cws_preflight_reports/`

## Cross-cutting privacy/trust questions (needs product stance)

Current runtime stores page-derived data locally (for diagnostics/feedback history), including URL/source/excerpt fields.  
We need explicit product policy on this.

### Product decisions needed from you
1. What exact data classes are acceptable to persist locally by default?
2. Should any of this be disabled by default and enabled only via explicit opt-in?
3. What user-facing transparency text should appear in options/privacy docs?

### Current decision state
- Resolved:
  - Team recognizes sentence excerpt storage as sensitive-risk area needing policy clarity.
  - Sentence history default: OFF (opt-in).
  - Sentence-history module records: no URL field.
  - Exposure telemetry (`srsExposureLog`) currently retains URL field (for now).
- Still open:
  - Exact retention/minimization policy and disclosure copy.
  - Whether sentence excerpt storage remains enabled behind opt-in after additional research.

### Technical follow-up after decision
- Data minimization pass.
- Default settings alignment.
- Reviewer note + privacy disclosure alignment.

## Decision log (to fill during discussion)

Use this table as we resolve each question.

| Date | Topic | Decision | Owner | Notes |
|---|---|---|---|---|
| 2026-02-18 | Concern 1 (`nativeMessaging`) | Required for SRS; non-SRS manual JSON rules remain functional without helper | Product + Eng | Onboarding UX still open |
| 2026-02-18 | Concern 2 (`<all_urls>`) | All-sites out-of-box at launch; provisional no explicit exclusions | Product + Eng | Revisit only if policy/testing requires |
| 2026-02-18 | Concern 3 (protocol) | Roadmap platforms: macOS + Windows | Eng | Endianness requirement still open |
| 2026-02-18 | Concern 4 (MV3 lifecycle) | Manual rules guaranteed without helper; SRS actions fail-fast on helper loss; feedback queue retries eventually | Product + Eng | Queue limits/diagnostics tuning remains |
| 2026-02-18 | Concern 5 (asset completeness) | Final approver pool = two maintainers; lightweight mandatory pre-upload gate adopted | Product + Eng | Checklist refinement remains |
| 2026-02-18 | Privacy data policy | Sentence history default OFF; no URL retention in sentence/history data | Product + Eng | Additional research still required |

## Engineering guidance requested in discussion

### A) "All pages" default vs extra enable step

Your instinct is valid in both directions:
- Out-of-box broad access is common for extensions whose core value is page-wide behavior.
- Runtime-granted host access can reduce user trust friction and can help with review narrative ("minimum permissions by default, escalate only when needed").

Practical launch options:
1. Keep current model:
   - `host_permissions` / `content_scripts.matches` include broad scope from install.
   - Lowest UX friction.
   - Highest review scrutiny.
2. Runtime grant model:
   - Move broad host scope into `optional_host_permissions`.
   - Request access during onboarding/user gesture.
   - Slightly higher UX friction, stronger policy posture.

### B) "Do we have to exclude sites?" and AdBlock-style comparison

Not strictly required by policy as a blanket rule.  
But minimization is required: permissions and data handling should be no broader than the stated user-facing purpose.

Ad blockers can justify broad scope because their single purpose is global page/request filtering.  
LexiShift can also justify broad scope, but should clearly document:
- single purpose,
- what data is read,
- what is persisted,
- what is never transmitted.

### C) Sensitive field expectations (legal/policy + best practice)

Important policy baseline:
- Website content, form data, and web browsing activity (including URLs/domains) are treated as sensitive user data in CWS user-data guidance.
- A privacy policy is required if sensitive user data is handled, even if data is stored only locally.
- If handling is not closely related to prominently described functionality, prominent disclosure + affirmative consent is required.

Best-practice recommendation for current sentence-history feature:
1. Default `off` for sentence excerpt storage until explicit user opt-in.
2. Keep strict retention bounds and easy clear/reset control.
3. Consider storing reduced context (short excerpt + origin/domain only) rather than full URL/path.
4. Incognito-safe behavior:
   - no persistence from incognito sessions unless explicitly enabled.
5. Explicit in-product disclosure text near the setting and in privacy policy.

### D) Non-little-endian protocol explanation

Native messaging frames require a 32-bit length prefix in native byte order.
- Current host uses fixed little-endian framing.
- On macOS/Windows target CPUs this is effectively fine today (little-endian).
- On a hypothetical big-endian target, fixed little-endian would break.

Recommended policy:
- For launch scope (macOS + Windows), keep implementation as-is and explicitly document little-endian assumption.
- If any non-little-endian platform enters roadmap, schedule protocol compatibility update.

### E) What a pre-upload gate would include

A pre-upload gate is a required validation step (script + checklist) before publishing.

Suggested checks:
1. Manifest integrity:
   - all referenced files exist,
   - icon dimensions match declared sizes,
   - locale placeholders resolve.
2. Permission posture:
   - diff/report permissions and host patterns vs previous release.
3. CWS metadata consistency:
   - single-purpose text, data-use declarations, privacy policy link.
4. Native helper readiness:
   - production extension ID not placeholder,
   - helper install docs match release build.
5. Policy lint:
   - no unexpected remote endpoints,
   - no debug/dev artifacts in package.
6. Release sign-off record:
   - reviewer initials/date (two maintainers).

### F) Helper unavailability: practical scenarios and implications

When helper can be unavailable:
1. Helper not installed or host manifest missing.
2. Helper process crashed or not running.
3. Browser/service-worker wake after sleep while helper startup lags.
4. Extension ID/host mismatch after reinstall/update.

User-visible impact categories:
1. Must work offline from helper:
   - manual JSON rules and local replacement runtime.
2. Best-effort with warning when helper missing:
   - SRS refresh/init/rulegen actions.
3. Eventual consistency:
   - feedback queue should retry until helper returns.

Suggested default reliability policy (engineering recommendation):
1. Manual rules path: guaranteed available without helper.
2. SRS control actions: fail-fast with explicit blocking warning + one-click "fix helper" guidance.
3. Feedback sync: eventual retry with bounded queue and visible queue health in diagnostics.

### G) Lightweight gate for solo project (recommended)

Instead of a heavy formal process, use a single command + short checklist:
1. Run preflight script (`npm run preflight:cws` or equivalent) that checks:
   - manifest references,
   - icon/locale integrity,
   - placeholder extension IDs,
   - known policy-sensitive settings.
2. Generate one markdown report in `docs/runbooks/` with timestamp.
3. Manual yes/no checklist (5 lines) before upload:
   - privacy text reviewed,
   - permissions unchanged or intentionally updated,
   - helper onboarding tested,
   - no debug artifacts,
   - package hash recorded.

This keeps quality high without enterprise-style ceremony.

## Policy references (review baseline)

- Chrome Web Store Program Policies:
  - https://developer.chrome.com/docs/webstore/program-policies/policies
- User Data FAQ (sensitive data categories, local-only still requiring privacy policy):
  - https://developer.chrome.com/docs/webstore/program-policies/user-data-faq
- Declare Permissions (`optional_host_permissions`, minimum-permission guidance):
  - https://developer.chrome.com/docs/extensions/develop/concepts/declare-permissions
- Permissions API (runtime permission request flow):
  - https://developer.chrome.com/docs/extensions/reference/api/permissions
- Native messaging protocol details:
  - https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging
