# SRS Resource Budget And Load Audit

Status: active audit lane
Role: Current plus near-term readiness plan
Last updated: 2026-05-27
Last verified: 2026-05-27 by source inspection of SRS settings, extension storage caps, page replacement budgets, browsing-signal bounds, helper artifact readers, and the first resource-budget audit script
Purpose: keep SRS personalization, browsing signals, replacement runtime, and admitted-word dashboards bounded enough for MVP testing without overloading user cognition, extension storage, helper files, or page runtime
Source-of-truth: this audit is a routing and measurement surface; executable truth lives in helper/core SRS modules, extension runtime code, generated audit artifacts, and tests.

## Product Concern

Personalized SRS admission can branch into many load problems:

- too many active words for the learner to remember;
- too many replacements on a page;
- rare active words that are never encountered and never receive feedback;
- browser storage growing from logs, local projections, helper caches, or
  semantic inventories;
- helper-side stores and generated rulesets growing without explicit review
  thresholds;
- diagnostics becoming too large or too technical for ordinary users.

The MVP target is not "store everything and tune later." The target is sparse,
bounded state:

```text
full candidate universe U -> computed on demand
admitted study inventory S -> sparse persisted helper store
runtime due/replacement view -> bounded projection
browsing signals -> opt-in decayed aggregate
diagnostics -> capped summaries and on-demand details
```

## Current Bounded Surfaces

| Surface | Current Bound | Owner | Notes |
| --- | ---: | --- | --- |
| Active SRS items | `40` default | helper | `SrsSettings.max_active_items`; capacity gate for refresh. |
| New items per refresh | `8` default | helper | Stored as `max_new_items_per_day`, currently enforced as per-refresh cap. |
| Page replacements | `20` per page | extension | Standard replacement density default. |
| Replacements per lemma | `2` per page | extension | Prevents one learned word from dominating a page. |
| Extension SRS projection | `8000` items | extension | Local projection, not helper authority. |
| Extension SRS history | `50` entries per item | extension | Local history clamp. |
| Extension exposure log | `2000` entries | extension | Telemetry log ring buffer. |
| Extension browsing-signal packet | `50` signals | extension | Pending signal flush payload cap. |
| Helper browsing-signal packet | `200` signals | helper | Ingest cap. |
| Helper browsing aggregate store | `5000` lemmas | helper | Decayed and pruned aggregate per pair/profile. |
| Helper signal queue | `5000` events | helper | Bounded on save/append. |

These limits are good first-release shape because they keep the hot paths sparse
and prevent page replacement from turning every page into a wall of substitutions.

## Current Gaps

1. Helper-side long-term SRS store growth is bounded indirectly by active
   capacity, lifecycle state, and refresh rules, but there is no explicit
   archive/prune policy for years of completed, discarded, or parked items.
2. Helper ruleset, snapshot, and semantic-inventory caches are generated from
   active/admitted state, but extension helper cache entries do not yet expose
   a source-level TTL or max-profile/pair policy.
3. Encounter starvation is documented, but tester-facing diagnostics are still
   needed for active words with zero exposure and zero feedback.
4. We do not yet have a browser-profile storage audit. The new script measures
   source constants and helper data-root artifacts, not live `chrome.storage`
   bytes.

## Audit Artifact

Executable report:

```bash
python3 scripts/testing/srs_resource_budget_audit.py \
  --pair en-es \
  --profile-id default \
  --json-out docs/test_outputs/srs_resource_budget_audit_latest.json \
  --markdown-out docs/test_outputs/srs_resource_budget_audit_latest.md
```

The report is read-only. It does not mutate helper state, does not inspect
private browser storage directly, and does not download data.

It records:

- code-level budget constants;
- helper artifact file sizes;
- SRS item counts by pair/profile;
- active inventory count;
- ruleset rule counts;
- signal queue event counts;
- browsing aggregate counts;
- zero-exposure/zero-feedback active item preview.

## MVP Readiness Policy

Before broad SRS testers:

1. Keep `S` sparse. Do not persist dense per-word admission probabilities for
   the full corpus.
2. Keep browsing-based admission opt-in and aggregate-only.
3. Keep passive exposure non-authoritative for FSRS scheduling.
4. Show stale-active diagnostics before adding any automatic stale-clear action.
5. Add TTL/pruning policy for extension helper caches before relying on many
   profiles or language pairs.
6. Treat helper artifact size review findings as release blockers only if they
   occur under normal MVP flows, not synthetic stress fixtures.

## Near-Term Work

1. Run the resource-budget audit against the current local helper data root.
2. Add the stale-active summary to the admitted-words dashboard or refresh
   diagnostics so testers can see whether active words are encounterable.
3. Decide extension helper cache policy:
   - keep latest per profile/pair only;
   - or keep a small LRU across profile/pair scopes;
   - optionally include TTL for stale generated artifacts.
4. Decide helper lifecycle policy for zero-exposure/zero-feedback active items:
   diagnostics first, then explicit clear/release policy only after testing.
5. Re-run SRS quality harness after any code path changes.
