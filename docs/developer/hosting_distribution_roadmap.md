# Hosting And Distribution Roadmap

Status: active roadmap
Role: Planning / WIP
Last updated: 2026-06-04
Last verified: 2026-06-04 repo-side domain/page/manifest scaffolding and macOS GUI build/report review; Cloudflare resources, DNS records, and release assets not created
Purpose: sequence LexiShift's indie-friendly hosting, installer distribution, release metadata, and future hosted app-data rollout
Source-of-truth: roadmap only; operational setup lives in `../runbooks/cloudflare_distribution_setup.md`, hosted docs behavior lives in `.github/workflows/pages.yml`, and current build/signing behavior lives in `build_and_release.md`.
Related docs:
- `build_and_release.md`
- `../runbooks/cloudflare_distribution_setup.md`
- `../runbooks/github_pages_setup.md`
- `../language_pairs/data_source_licensing_and_distribution.md`
- `../language_pairs/lp_data_inventory_matrix.md`
- `feature_state_matrix.md`

## Product Goal

Create a low-cost distribution system that starts small enough for an indie beta
but does not need to be replaced when LexiShift grows.

The target shape:

1. users see a stable product domain, not a repository URL;
2. installers and app data are served from scalable object storage;
3. GitHub Pages remains useful for docs/manual pages while it is good enough;
4. beta gating can stay simple for fewer than `100` users;
5. paid backend/database products are added only when user-specific cloud data
   exists;
6. language-resource hosting stays aligned with the distribution/licensing
   register.

## Domain Model

Assumed product domain:

```text
lexishift.app
```

Planned routes:

| Host/path | Role | Initial backend | Notes |
| --- | --- | --- | --- |
| `lexishift.app` | public product site, manual, download page | GitHub Pages custom domain | Keep the domain product-level, not distribution-specific. |
| `www.lexishift.app` | redirect to apex | DNS/Page redirect | Do not maintain a separate content copy. |
| `lexishift.app/beta/` | public or lightly gated beta page | GitHub Pages | Preferred first beta page if visuals/docs stay on Pages. |
| `beta.lexishift.app` | optional beta entrypoint | redirect or Cloudflare Pages later | Use only if beta needs a distinct hostname. |
| `downloads.lexishift.app` | installers, checksums, release manifests | Cloudflare R2 | Versioned immutable assets plus short-cache channel pointers. |
| `data.lexishift.app` | hosted app/resource packs | Cloudflare R2 | Keep public assets legally bundleable/hostable. |
| `api.lexishift.app` | dynamic release metadata, signed links, future app API | parked DNS, then Worker | Add only when static R2 JSON is insufficient. |

## Cost Model

These are planning estimates. Check live provider pricing before committing to a
paid plan or a hosted-data expansion.

| Stage | Expected monthly hosting | What is included | Upgrade trigger |
| --- | ---: | --- | --- |
| Static beta | `$0` | GitHub Pages custom domain, Cloudflare DNS, public docs/download page | Need private/signed downloads or hosted app data. |
| R2 distribution beta | `$0-$2` | R2 installers, checksums, `latest.json`, small hosted data packs | R2 free limits are exceeded or operational automation needs Worker Paid. |
| Worker comfort tier | about `$5` | Worker for signed links, invite-code gate, dynamic manifests | Dynamic requests exceed free limits or production logging/limits matter. |
| Early user backend | `$0-$25` | Supabase/Firebase-style experiment or Pro backend for user-specific data | Accounts/sync/support dashboards become product requirements. |
| Growth, read-mostly data | `$5-$50` | More R2 storage/reads, Worker overages if used | Many pack downloads, many release checks, or app data gets larger. |
| Growth, user-specific sync | `$25-$300+` | Managed DB/auth/storage, backups, logs, support tooling | DB/API behavior, not downloads, becomes the main cost driver. |

Cost guardrail:

- distribution cost should remain near `$0-$5/month` until LexiShift has either
  meaningful hosted app data volume or user-specific cloud features.

Non-hosting costs:

- domain registration is separate from hosting;
- Apple Developer Program and Windows code-signing costs are separate from
  hosting;
- paid analytics, email, monitoring, and support tooling are intentionally out
  of scope until a real beta operations need appears.

## Phase 0: Repo Alignment

Status: started.

Goal:
- make the intended hosting/distribution model explicit in the repo before any
  external account work.

Tasks:

1. Add the Cloudflare setup runbook. Done.
2. Add this roadmap. Done.
3. Link the roadmap from developer release routing. Done.
4. Keep GitHub Pages setup documentation intact. Done.
5. Keep language-resource distribution caveats visible. Done.
6. Add `docs/CNAME` for `lexishift.app`. Done.
7. Add public beta/download/privacy/support/release route skeletons. Done.
8. Add release manifest/checksum generation tooling. Done.

Acceptance:

- docs build locally;
- doc-reference check passes;
- no Cloudflare credentials, account IDs, or tokens are committed.

Validation:

```bash
cd docs
bundle exec jekyll build --trace
npm --prefix ../scripts run check:docs:report
```

## Current Beta RC Gate

Status: local RC branch assembled.

Current integration branch:

```text
codex/beta-app-rc
```

Current branch includes:

1. app-code baseline from `codex/veto-data-sources-exp`;
2. live GitHub Pages custom-domain/beta/download work from `origin/main`;
3. distribution roadmap, Cloudflare/R2 runbook, and release-manifest tooling.

Validated for the hosting/distribution slice:

```bash
cd docs
bundle exec jekyll build --trace
npm --prefix ../scripts run check:docs:report
cd ..
npm --prefix scripts run release:manifest -- \
  --version 0.1.0 \
  --channel beta \
  --asset macos=/path/to/LexiShift-0.1.0.dmg \
  --print-wrangler-commands
npm --prefix scripts run build:report
python scripts/build/installer.py \
  --skip-build \
  --out /tmp/lexishift-beta-installers \
  --dmg-name LexiShift-0.1.0
```

Known branch-level blocker:

- The local macOS installer smoke produced an unsigned, unnotarized DMG around
  `576 MB`. That is adequate evidence that the installer path works, but it is
  not broad-beta trust evidence; signing/notarization and app-size review stay
  open release tasks.
- `npm --prefix scripts run check` currently fails at `mypy` before reaching
  later checks. The same `409` mypy errors in `46` files are present on the
  raw app-code baseline before the Pages/distribution merge, so this is
  inherited app-branch type debt, not a website/distribution regression.
- `npm --prefix scripts run check:changed:report` is not a useful green gate
  for this integration branch against `origin/main` because the app-code
  baseline differs by thousands of files. Use slice-local validation until the
  app branch has a clean baseline or a deliberate beta exception is recorded.

Do not bypass the pre-push safety hook for this branch without an explicit
decision. If a remote PR is needed before the inherited full-check debt is
fixed, mark it as WIP and call out the failed full gate in the PR body.

## Phase 1: Domain And Public Pages

Goal:
- put the human-facing site on the product domain while preserving the current
  GitHub Pages workflow.

Tasks:

1. Register or confirm `lexishift.app`. Done.
2. Add the domain to Cloudflare DNS.
3. Move nameservers to Cloudflare.
4. Configure GitHub Pages custom domain for `lexishift.app`.
5. Add `www.lexishift.app` redirect behavior.
6. Add or reserve `/beta/`, `/download/`, `/privacy/`, `/support/`, and
   `/releases/` paths. Done in repo.
7. Keep repository Pages fallback available during the transition.

Acceptance:

- `https://lexishift.app/` loads the existing Pages site;
- `https://www.lexishift.app/` redirects to `https://lexishift.app/`;
- `https://xamgUmlatu.github.io/LexiShift/` still works or redirects safely;
- no installer binary is hosted from the Pages site itself.

Cost:

- hosting: `$0/month`;
- domain: registrar/TLD cost only.

## Phase 2: R2 Download Bucket

Goal:
- move installer and release-metadata hosting to scalable object storage.

Tasks:

1. Create R2 bucket `lexishift-distribution`.
2. Attach `downloads.lexishift.app`.
3. Define R2 object layout:

```text
installers/beta/<version>/macos/
installers/beta/<version>/windows/
checksums/beta/<version>/
releases/beta/latest.json
releases/stable/latest.json
```

4. Generate `SHA256SUMS.txt` for each release payload.
5. Publish the first static beta `latest.json`.
6. Link the beta download page to the manifest and direct installer asset.
7. Verify cache headers:
   - long immutable cache for versioned installers;
   - short cache for `latest.json`.

Acceptance:

- `https://downloads.lexishift.app/releases/beta/latest.json` returns valid
  JSON;
- installer URLs in the manifest resolve;
- checksums are visible and match local artifacts;
- the Pages site links to R2 assets, not repository-hosted binaries.

Cost:

- expected `$0/month` for the first small beta;
- cost should remain low as long as the release assets are few and app data is
  bundled into coarse files.

## Phase 3: Beta Gating

Goal:
- keep beta distribution controlled without choosing an expensive per-user auth
  model too early.

Preferred order:

1. use an obscure beta URL for family/friends testing;
2. add a shared beta password or invite phrase if needed;
3. add a Worker-based invite-code gate if direct links need protection;
4. add signed R2 links only if download leakage becomes a practical concern.

Avoid:

- long-term product-user auth through Cloudflare Access;
- per-user paid access tooling for a small indie beta;
- adding a database solely to protect a beta download link.

Acceptance:

- tester can reach the beta page and download without a GitHub account;
- non-testers do not have obvious public direct links if the beta is intended
  to be semi-private;
- support instructions explain how to recover if the link expires or the gate
  fails.

Cost:

- `$0/month` if static/simple;
- about `$5/month` once Workers Paid is intentionally enabled.

## Phase 4: Hosted App Data

Goal:
- support app-accessible resource data without turning data distribution into a
  backend project prematurely.

Tasks:

1. Attach `data.lexishift.app` to R2.
2. Define a pack manifest shape for app data.
3. Use immutable versioned pack paths.
4. Keep a short-cache channel/index file for current recommended packs.
5. Bundle data into fewer larger files instead of many tiny objects.
6. Add app-side download/update logic only after the hosted manifest contract is
   stable.
7. Check each hosted resource against
   `../language_pairs/data_source_licensing_and_distribution.md`.

Acceptance:

- only legally hostable/bundleable resources are public;
- app data manifest includes version, source, checksum, size, and compatibility
  fields;
- manual-supply resources are not exposed through public R2 paths unless the
  distribution register changes;
- the app can continue to work with locally installed packs if hosted data is
  unavailable.

Cost:

- expected `$0-$2/month` for small beta pack distribution;
- growth cost depends mostly on object count and read pattern, not egress.

## Phase 5: Release Automation

Goal:
- reduce manual release mistakes once beta packaging repeats.

Tasks:

1. Add a local script that creates:
   - checksums,
   - release manifest,
   - upload command preview.
2. Add a dry-run mode that validates object paths and cache policy.
3. Add a GitHub Actions workflow only after manual upload has worked at least
   once.
4. Store Cloudflare API token in GitHub Actions secrets, not in the repo.
5. Keep signing/notarization credentials separate from hosting credentials.

Acceptance:

- release manifest is generated from actual installer files;
- checksum mismatch fails before upload;
- upload paths are deterministic;
- beta and stable channels cannot overwrite each other accidentally.

Validation:

```bash
python scripts/build/installer.py --validate
curl https://downloads.lexishift.app/releases/beta/latest.json
```

## Phase 6: App Update And Trust Layer

Goal:
- make installed app update checks and user trust compatible with the hosted
  distribution lane.

Tasks:

1. Decide whether the first app update flow is manual notification or automatic
   updater.
2. Keep `latest.json` schema compatible with both the website and future app
   update checks.
3. Add macOS signing/notarization before a serious external beta.
4. Add Windows signing or clearly document Windows warning behavior before a
   broad Windows beta.
5. Add privacy/support pages before public production downloads.

Acceptance:

- users can see installed version vs latest version;
- release notes are linked from both site and manifest;
- signed/notarized status is represented honestly in release metadata;
- beta support instructions are clear enough for non-developers.

Cost:

- hosting remains low;
- signing programs/certificates become the main trust-related cost.

## Phase 7: User-Specific Backend

Goal:
- add a real backend only when product behavior requires user-specific cloud
  state.

Add this phase only for features such as:

1. account login;
2. cloud sync;
3. user-specific SRS progress;
4. paid entitlements;
5. support dashboards;
6. user-facing cloud backup/restore.

Preferred first backend:

- managed service such as Supabase/Firebase/Neon plus a small API surface;
- choose based on the data model at that time, not on distribution needs.

Acceptance:

- privacy policy covers stored user data;
- export/delete path is defined;
- backups and incident handling are documented;
- app still has a sensible offline/local mode where possible.

Cost:

- start with free experimentation if possible;
- expect about `$25/month` once production-grade managed backend behavior is
  needed.

## Scaling Triggers

Upgrade only when one of these is true:

| Trigger | Likely action |
| --- | --- |
| R2 storage exceeds free tier | keep R2; pay storage/ops overage. |
| R2 object reads become noisy | bundle packs, improve cache headers, reduce tiny fetches. |
| Dynamic beta gate needs reliability | enable Workers Paid. |
| App needs per-user state | add managed backend. |
| Support burden rises | add logging/analytics/support tooling. |
| Public production launch begins | finalize signing, privacy, support, release-note flow. |

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Domain chosen for downloads only becomes awkward later | keep domain product-level: `lexishift.app`. |
| R2 bill grows from many tiny reads | bundle data packs and cache immutable assets. |
| Manual-supply language resources leak into public hosting | gate all hosted-resource work through the distribution register. |
| Beta auth becomes overbuilt | start with simple gates; add Worker before database. |
| GitHub Pages and product domain diverge | use custom domain and keep Pages fallback documented. |
| Signing/notarization is confused with hosting | track signing as release trust work, not hosting work. |

## Immediate Next Actions

1. Choose and register the product domain.
2. Configure GitHub Pages custom domain.
3. Add/verify the domain in Cloudflare DNS.
4. Create R2 bucket `lexishift-distribution`.
5. Attach `downloads.<domain>` to R2.
6. Upload a placeholder `releases/beta/latest.json`.
7. Replace staging copy on beta/download/support/privacy pages.
8. Verify with `curl` and a browser.

## Definition Of Done For Initial Beta Hosting

Initial beta hosting is ready when:

1. `lexishift.app` loads the LexiShift site;
2. `/beta/` has a tester-facing install page;
3. `downloads.lexishift.app/releases/beta/latest.json` exists;
4. at least one installer asset is available from R2;
5. checksum verification instructions are present;
6. unsupported or manual-supply data is not publicly hosted by accident;
7. the release runbook points to the correct hosted asset flow.
