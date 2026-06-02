# Vocabulary Library And Word Info Plan

Status: active implementation plan
Role: Product/UX plan, backend read-model contract, and implementation sequence
Last updated: 2026-06-02
Last verified: 2026-06-02 helper/native-host/shared-extension word-info API foundation tests, enriched quick-definition popup render/registry tests, dedicated Vocabulary Library page script-order/i18n tests, and library model/view helper tests
Purpose: define the shared word-info capability that should power both a richer Vocabulary Practice library and a built-in popup definition module
Source-of-truth: mixed implementation plan plus current API contract; current implemented state is tracked in `docs/developer/feature_state_matrix.md`.

## Product Goal

After a learner starts Vocabulary Practice, LexiShift should make the admitted
words feel inspectable and understandable, not only schedulable.

Two first-release surfaces need the same underlying data:

1. A richer Vocabulary Library where the learner can review admitted, active,
   upcoming, removed, and eventually completed words for a profile/language
   pair.
2. A built-in popup module that appears when the learner right-clicks a replaced
   browser word and shows a quick definition/gloss.

Both surfaces should use one shared helper-backed `word info` read model. The
dashboard/library and popup should not each invent their own dictionary lookup,
fallback policy, definition filtering, or external-link construction.

## Product Decisions

1. Build a shared `word info` service first.
   - The service is read-only.
   - It accepts a profile, language pair, and target lemma/display value.
   - It returns learner-facing word metadata, compact glosses, SRS state when
     available, rule/source phrase summaries, and external dictionary links.

2. Promote the current admitted-words dashboard into a Vocabulary Library
   surface instead of creating a second unrelated learned-words product.
   - The current Options dashboard remains a good embedded beta surface.
   - First release should add a dedicated page/view for deeper inspection.
   - The dedicated page should reuse the current dashboard read model and
     controls where possible.

3. Add `quick-definition` as a built-in popup module.
   - It should be default-on for supported pairs when language data is present.
   - It should render above history/feedback modules because definition is the
     first question a learner usually has.
   - It should use the shared `word info` service.

4. Keep definitions local-first.
   - Installed local language packs are the source of definition/gloss text.
   - Runtime web scraping is out of scope.
   - External dictionary links are allowed, but only as user-clicked outbound
     links. They are not runtime dependencies for the feature.

5. Support both SRS-origin and ruleset-origin replacements, with different
   enrichment levels.
   - SRS-origin replacements can include SRS status, due timing, review count,
     exposure count, and active/upcoming/removed practice state.
   - Ruleset-origin replacements may only have replacement metadata, source
     phrase, rule metadata, and local dictionary glosses.
   - The popup should fail gracefully when the word is not in Vocabulary
     Practice.

## Current Implementation State

As of 2026-06-02, the shared word-info API foundation and built-in
`quick-definition` popup consumer are implemented and verified:

- helper/core read model: `core/lexishift_core/helper/use_cases/word_info.py`;
- engine entrypoint: `lookup_word_info(...)`;
- native-host route: `word_info_lookup`;
- extension helper client method: `HelperClient.lookupWordInfo(...)`;
- shared extension API wrapper: `LexiShift.wordInfoApi`;
- Options convenience method: `HelperManager.lookupWordInfo(...)`;
- content singleton configuration for popup modules;
- built-in `quick-definition` popup module:
  `apps/chrome-extension/content/ui/popup_modules/quick_definition_module.js`;
- default-on module registry entry, runtime descriptor wiring, manifest load
  order, and locale coverage for `en`, `ja`, `zh`, and `de`.

This implemented slice is still mostly read-only, but `quick-definition` is now
user-facing in the replacement popup and the dedicated `learning_dashboard.html`
Vocabulary Library page is available from the active Vocabulary Practice card.
The helper preserves safe Kaikki/Wiktionary sense detail and short examples when
those fields are present in the installed pack, while still falling back to
compact FreeDict-style glosses.

Current Vocabulary Library page behavior:

- resolves the current selected SRS profile and language pair from extension
  storage, with optional `profileId`/`pair` URL overrides;
- calls the existing read-only `srs_items_list` helper route;
- reuses the existing dashboard search/status/sort semantics;
- shows summary cards, pagination, a table with word/meaning/progress/activity/
  topic/action columns, and a detail panel;
- loads definition/gloss previews only for the current page, capped at 25 words
  per render, then loads the selected row on demand;
- shows local definition/glosses, dictionary links, and page-replacement source
  phrases in the detail panel;
- exposes advanced scheduler/page-replacement details behind an Advanced toggle;
- reuses confirmed dashboard discard as the only mutation.

## Non-Goals For MVP

- No live web lookup for definition text.
- No LLM-generated definitions.
- No cloud dependency.
- No public third-party popup-module API expansion in this slice.
- No full mastered/completed lifecycle semantics unless the SRS lifecycle slice
  lands separately.
- No requirement that every language pair has equally rich dictionary detail on
  day one.

## Definition Data Recommendation

Recommended source:

- Use installed local target-to-source lexical packs as the canonical source of
  learner-facing gloss text.
- Resolve those packs through language-pair capability and managed/manual pack
  configuration, not through hard-coded extension paths.
- Treat SRS item metadata and published rules as context/enrichment, not as the
  primary definition source.
- Treat external dictionary URLs as optional outbound links, never as data that
  LexiShift fetches to build the popup or library response.

For `en-es`, the learner sees Spanish target words and usually needs English
glosses. The lookup should therefore prefer installed Spanish-to-English
resources resolved for the pair, currently the managed `wiktionary-es-en` pack
with `freedict-es-en` as a fallback family when present. The extension should
not know those filenames. It should ask the helper for word info for
`pair=en-es`, and the helper should resolve the best installed pack using the
same pair-readiness rules that already govern rulegen/SRS setup.
The resolver supports both manifest-backed pack roots and legacy/manual
`language_packs/<pack-id>/main.sqlite` installs so the intended Wiktionary-first
priority does not silently fall through to FreeDict when the richer pack lacks a
manifest.

For other language pairs, the same service boundary applies:

- `en-ja` should resolve JMDict/Japanese resources through pair capability.
- `en-de` should resolve German-to-English translation/gloss packs.
- future pairs should add provider/capability support in helper/core code
  without changing the popup module or Vocabulary Library controller.

Terminology:

- Internal API field: `glosses`.
- User-facing label: `Definition`.

This distinction matters because many available resources are bilingual
dictionaries. Showing "Definition" in UI is fine, but the backend contract
should remain honest that it may be returning short glosses rather than full
monolingual dictionary definitions.

Gloss resolution priority inside the helper should be:

1. exact normalized target lemma;
2. display/surface fallback when it differs from lemma;
3. script/form variants from `word_package` where the pair provider supports
   them;
4. rule source phrase fallback only as context, not as a claimed dictionary
   definition.

The response may include provider names and pack ids, but it must not leak local
filesystem paths into learner-facing payloads.

## Shared Word Info Contract

The helper should expose a read-only endpoint, tentatively:

```json
{
  "type": "word_info_lookup",
  "pair": "en-es",
  "profile_id": "default",
  "lemma": "perro",
  "display": "perro",
  "origin": "srs",
  "source_phrase": "dog",
  "word_package": {}
}
```

Recommended response shape:

```json
{
  "status": "ok",
  "pair": "en-es",
  "profile_id": "default",
  "source_language": "en",
  "target_language": "es",
  "lemma": "perro",
  "display": "perro",
  "normalized_lemma": "perro",
  "pos": {
    "canonical": "noun",
    "label": "noun",
    "source": "word_package"
  },
  "glosses": [
    {
      "text": "dog",
      "language": "en",
      "source": "wiktionary-es-en",
      "source_kind": "installed_translation_pack",
      "rank": 1,
      "confidence": 0.9,
      "sense_id": "optional",
      "details": ["dog (the species Canis familiaris)"],
      "examples": [{"text": "perro callejero", "translation": "stray dog"}]
    }
  ],
  "source_phrases": ["dog"],
  "rule_summary": {
    "rule_count": 3,
    "enabled_rule_count": 3,
    "source_phrase_count": 2
  },
  "srs": {
    "present": true,
    "status": "learning",
    "status_label": "Learning",
    "serving_state": "replacing_now",
    "next_due": null,
    "review_count": 0,
    "exposures": 2,
    "lifecycle_state": "active"
  },
  "external_links": [
    {
      "label": "Wiktionary",
      "url": "https://en.wiktionary.org/wiki/perro#Spanish"
    }
  ],
  "diagnostics": {
    "resolution_sources": ["srs_store", "published_ruleset", "installed_translation_pack"],
    "missing_resources": []
  }
}
```

Notes:

- Use `glosses` rather than over-promising high-quality monolingual definitions.
  Many current resources are bilingual dictionaries, so "definition" in UI may
  often mean a short learner-facing gloss.
- Kaikki/Wiktionary auxiliary fields may add short `details` and `examples`
  under each gloss. Those fields are optional and must stay compact and free of
  local filesystem paths.
- The compact word-info view prefers unrestricted senses and the first dictionary
  POS group. Restricted usage senses, such as slang/vulgar/obsolete/derogatory
  entries, are fallback-only when no unrestricted sense is available. A fuller
  Vocabulary Library can later expose POS sections and advanced sense browsing.
- `source_phrases` should come from published ruleset summaries/details when
  available.
- `srs.present` is false for ruleset-only words or words not admitted to the
  selected Vocabulary Practice.
- The endpoint must avoid returning local filesystem paths in learner-facing
  payloads.

## API-Ready Boundary

The implementation should expose one logical API and several thin adapters:

1. helper/native host route: `word_info_lookup`;
2. shared extension client method: `HelperClient.lookupWordInfo(payload)`;
3. page/content service: `LexiShift.wordInfoApi.lookup(request, options)`;
4. consumer APIs for Options pages, Vocabulary Library rows, and popup modules.

Options code and popup module code should both call the page/content service.
They should not duplicate native-host message names, pack selection, dictionary
fallbacks, URL-template construction, or SRS/ruleset enrichment rules.

Recommended JavaScript service shape:

```js
const result = await LexiShift.wordInfoApi.lookup({
  profileId: "default",
  pair: "en-es",
  lemma: "perro",
  display: "perro",
  origin: "srs",
  sourcePhrase: "dog",
  wordPackage: {}
}, {
  timeoutMs: 4000,
  signal
});
```

Recommended guarantees:

- read-only;
- local-first;
- no page URL required;
- stable enough for internal modules and future trusted modules;
- returns `status: "ok"` with empty `glosses` plus `missing_resources` when
  local data is absent;
- returns localization-neutral structured data, leaving final strings to the UI
  layer;
- caches successful lookups for the current extension session by
  `(profile_id, pair, normalized_lemma, display)` so the popup does not repeat a
  helper lookup every time the same word is opened.

The helper response should be the canonical data contract. The JavaScript
service can normalize naming conventions (`profile_id` to `profileId`, for
example) for ergonomics, but it should preserve the same conceptual fields.

## Popup Module Implementation Model

The `quick-definition` popup module should be generic and service-driven.

It should not:

- hard-code `en-es`;
- open SQLite files;
- know the pack filename for a pair;
- fetch external dictionary pages;
- call `chrome.runtime.sendMessage` or the native-host route directly.

It should:

- receive a normalized popup context with target word metadata;
- receive a narrowed `api.wordInfo` service object from popup core;
- render immediately with a compact loading state;
- update its own module body when the lookup resolves;
- show a graceful fallback when the helper is unavailable or local data is
  missing;
- remain optional/default-on through the popup module registry.

Current implementation note:

- The module follows the same boundaries, but uses the existing internal
  descriptor/context runtime rather than the future public module API. The
  current descriptor injects both `wordInfo` and `wordInfoApi` references backed
  by `LexiShift.wordInfoApi`.
- It parses clicked replacement metadata from the existing replacement span
  dataset, including `languagePair`, replacement/display values, `origin`,
  source phrase, and optional serialized `wordPackage`.
- It renders immediately with localized loading text and updates its own module
  body asynchronously when the lookup returns.

Target internal module shape:

```js
registerPopupModule({
  id: "quick-definition",
  priority: 20,
  supports(context) {
    return Boolean(context.languagePair && context.replacement);
  },
  render(context, api) {
    const node = api.createModuleContainer("lexishift-quick-definition");
    node.textContent = api.t("popup_definition_loading", null, "Loading definition...");
    api.wordInfo.lookup({
      profileId: context.profileId,
      pair: context.languagePair,
      lemma: context.replacement,
      display: context.displayReplacement,
      origin: context.origin,
      sourcePhrase: context.sourcePhrase,
      wordPackage: context.wordPackage
    }).then((result) => {
      // Render glosses, source phrase, SRS state, and links from result.
    }).catch(() => {
      // Render localized fallback.
    });
    return node;
  }
});
```

The current popup implementation still uses internal `build(target, debugLog, context)`
style descriptors. The implementation slice can bridge that shape first by
passing a service object to internal descriptors, then migrate toward the fuller
`render(context, api)` registry shape as the public module API matures.

## Generalization Rules For Language Pairs

The feature is product-ready for `en-es` first, but the code path should be
pair-generic from the start.

Rules:

- Pair-specific data resolution belongs in helper/core provider code.
- UI modules receive `pair`, `source_language`, `target_language`, and resolved
  structured results.
- Missing provider support is a normal response state, not an exception path.
- Provider-specific fields may live under `diagnostics` or `advanced`, not in
  the core render contract.
- External link templates are selected by target language/pair in a shared
  provider, not inside the popup module.
- Tests may use `en-es` as the first production fixture while also asserting
  that no popup/options code hard-codes Spanish-specific pack filenames.

## Resolution Order

For a lookup `(profile_id, pair, lemma)`:

1. Normalize the pair, profile id, target lemma/display value, and optional span
   `word_package`.
2. Read the profile-local SRS store for the pair.
   - If the item exists, include SRS lifecycle/scheduler/exposure/review fields.
   - Include the SRS item `word_package` as the primary word metadata source.
3. Read the profile/pair published ruleset.
   - Include compact rule counts and source phrase previews.
   - Use rule details only when a detailed view asks for them.
4. Query installed target-to-source translation packs for glosses.
   - For `en-es`, the target word is Spanish and the learner-facing glosses are
     English, so the relevant installed pack family is `es-en`.
   - The lookup should use the same pack-resolution policy as rulegen/SRS pack
     readiness instead of hard-coding paths in the extension.
5. Use the incoming `word_package` only as a fallback or supplement.
6. Construct external dictionary links from safe, deterministic URL templates.
   - Do not fetch those links.
   - Do not require them for a successful response.

## Vocabulary Library UX

The dedicated Vocabulary Library should answer:

- What words are in this Vocabulary Practice?
- What do they mean?
- Which are active, upcoming, due, removed, or eventually completed?
- Which words can currently appear as page replacements?
- Which source phrases/rules cause the word to appear?
- Where can I inspect the word in an external dictionary?

Recommended first-release shape:

- Entry point from the active Vocabulary Practice card: `Open Vocabulary Library`.
- Dedicated extension page or full-page view rather than another large surface
  permanently expanded in Options.
- Profile and language-pair scope visible at the top.
- Current pair/profile first; cross-pair "all practice words" can follow after
  full practice enumeration is implemented.
- Tabs or segmented views:
  - `Words`
  - `Due`
  - `Upcoming`
  - `Removed`
  - future `Completed`
- Default table columns:
  - `Word`: target word, reading/pronunciation when available, and compact POS.
  - `Meaning`: compact local gloss from the shared word-info API, lazy-loaded
    for expanded/current-page rows rather than prefetched for the full store.
  - `Progress`: learner-facing practice state such as `Learning`, `Due now`,
    `Reviewing`, `Upcoming`, or `Removed`.
  - `Activity`: recent exposure/review counts in learner language, not raw
    scheduler internals.
  - `Topic`: primary topic/register label when available, otherwise `General`.
  - `Actions`: a quiet overflow/discard affordance; normal viewing opens by
    row expansion/double-click, not by a competing `View` button.
- Advanced table/detail labels:
  - use `Practice state`, not `Lifecycle`;
  - use `Page replacement`, not `Serving`;
  - use `Admission source` and `Watch note` for explanation fields;
  - keep raw ids out of the normal advanced view unless a separate developer
    diagnostic mode is added.
- Existing controls from the admitted-words dashboard:
  - search
  - status filter
  - sorting
  - pagination/page size
  - advanced details toggle
  - discard action
- New word-info controls:
  - expand row for definition/glosses
  - external dictionary links
  - rule/source phrase details
  - optional "copy word" and "copy definition" actions later

Performance policy:

- The list endpoint should stay compact.
- Word-info details can load lazily when a row expands.
- A later batch endpoint may load word info for the current page only.
- Do not prefetch definitions for thousands of words at page load.

## Quick Definition Popup UX

The existing replacement right-click popup is the correct host for definition.

Recommended first-release behavior:

1. User right-clicks a `.lexishift-replacement`.
2. Popup opens immediately with a compact loading row if definition data is not
   already available.
3. `quick-definition` shows:
   - target word/display form,
   - part of speech when known,
   - one to three compact glosses,
   - a source phrase such as `Matches: dog` when useful,
   - external dictionary link(s),
   - unobtrusive "No definition available" fallback if local data is missing.
4. SRS feedback buttons remain available and separate.

The popup module should be:

- default-on where local word-info lookup is supported;
- controlled by the popup module registry alongside existing modules;
- language-aware but not limited to Japanese;
- asynchronous and non-blocking;
- cached per `(profile_id, pair, lemma)` for the current extension session.

## Data And Privacy Policy

- Looking up word info is local: extension -> background/native bridge -> local
  helper -> installed local resources.
- The clicked word, language pair, and profile id may be sent to the local
  helper.
- No page URL is required for definition lookup.
- No external dictionary site is contacted unless the learner clicks a link.
- The popup should not log full page text for this feature.

## Implementation Sequence

### Slice 1: Contract And Helper Read Model

Status: implemented and verified on 2026-06-02.

Files involved:

- `core/lexishift_core/helper/use_cases/word_info.py`
- `core/lexishift_core/helper/engine.py`
- `scripts/helper/lexishift_native_host.py`
- `apps/chrome-extension/shared/helper/helper_client.js`
- `apps/chrome-extension/shared/helper/word_info_api.js`
- `apps/chrome-extension/options/core/helper/srs_set_methods.js`
- `apps/chrome-extension/content_script.js`
- `apps/chrome-extension/manifest.json`
- `apps/chrome-extension/options.html`

Tests:

- `core/tests/helper/test_helper_word_info.py` covers:
  - SRS item present with word package,
  - ruleset source phrase summary present,
  - installed translation-pack glosses present,
  - missing language data graceful response,
  - no local path leakage in learner payload.
- `core/tests/dev/test_helper_browsing_admission_entrypoints.py` covers the
  native-host route.
- `core/tests/dev/test_extension_helper_status_profile_contract.py` covers the
  helper-client route, shared JS API normalization/cache behavior, and Options
  manager convenience method.
- `core/tests/architecture/test_extension_structure.py` covers content/options
  script ordering.

### Slice 2: Vocabulary Library Page

Status: implemented and verified on 2026-06-02 for the first dedicated page
slice.

Files involved:

- `apps/chrome-extension/learning_dashboard.html`
- `apps/chrome-extension/learning_dashboard.css`
- `apps/chrome-extension/learning_dashboard_model.js`
- `apps/chrome-extension/learning_dashboard_view.js`
- `apps/chrome-extension/learning_dashboard.js`
- `apps/chrome-extension/options.html`
- `apps/chrome-extension/options.css`
- existing dashboard modules in
  `apps/chrome-extension/options/controllers/srs/actions/words_dashboard_*.js`

Tests:

- `core/tests/architecture/test_extension_structure.py` covers page script order
  and locale-key coverage.
- `core/tests/dev/test_extension_learning_dashboard_page.py` covers word-info
  request construction, topic/source helpers, activity formatting, gloss
  preview, and detail-view gloss normalization.

Known limits:

- The page is scoped to the selected/current profile and language pair.
- Definition previews are current-page scoped and capped; the page does not
  prefetch definitions for the entire SRS store.
- The page does not implement completed/mastered lifecycle UX.
- Discard remains the only shipped library mutation.

### Slice 3: Quick Definition Popup Module

Status: implemented for the built-in internal module; public third-party popup
module API remains future work.

Files likely involved:

- `apps/chrome-extension/content/ui/popup_modules/quick_definition_module.js`
- `apps/chrome-extension/content/ui/ui.js`
- `apps/chrome-extension/shared/srs/popup_modules_registry.js`
- `apps/chrome-extension/manifest.json`
- locale files under `apps/chrome-extension/_locales/*/messages.json`

Tests:

- popup module render tests:
  - loading state,
  - gloss render,
  - missing definition fallback,
  - external-link rendering,
  - missing-helper fallback.
- popup registry/default-order tests.
- content script/manifest ordering tests.

### Slice 4: Verification And Beta Checklist

Run focused tests for changed helper/extension modules.

Run the SRS quality harness if helper SRS item payloads, SRS store reads, rule
publication, or runtime serving behavior changes:

```bash
python3 scripts/testing/srs_quality_harness.py \
  --json-out docs/test_outputs/srs_quality_latest.json
```

For docs and extension structure:

```bash
python3 scripts/dev/check_doc_references.py
git diff --check
npm --prefix scripts run check:changed:local
```

Manual beta checks:

- Start Vocabulary Practice.
- Open Vocabulary Library from the practice card.
- Expand several words and confirm glosses/source phrases are plausible.
- Right-click SRS replacements on a webpage and confirm `quick-definition`
  appears without delaying feedback controls.
- Right-click ruleset-only replacements and confirm graceful reduced detail.
- Disconnect or stop the helper and confirm the popup/dashboard degrade clearly.

## Open Product Decisions

1. Page name:
   - Recommended: `Vocabulary Library`.
   - Keep `Learning dashboard` as the compact Options card label if it still
     reads better there.

2. Initial scope:
   - Recommended MVP: selected profile plus selected/current language pair.
   - Future: all Vocabulary Practice words across pairs after full practice
     enumeration is implemented.

3. Definition copy:
   - Recommended UI copy: `Definition` for learner-facing labels.
   - Internal payload should use `glosses` to avoid pretending every source is
     a full dictionary definition.

4. External links:
   - Recommended MVP: deterministic links for Wiktionary and any pair-specific
     high-value dictionary templates we can safely construct.
   - Do not fetch or scrape those links.

5. Module settings:
   - Recommended MVP: default-on `quick-definition`, visible in module settings
     when the generalized popup-module settings surface is ready.

## Release Boundary

This feature is acceptable for first release when:

- the helper word-info endpoint is read-only, local-first, and covered by tests;
- the extension can display word info in the dedicated library and popup module
  without runtime web dependencies;
- missing local data produces clear fallback UI rather than broken controls;
- learner payloads do not expose local filesystem paths;
- popup definition loading does not block the feedback popup from opening;
- the Vocabulary Library can inspect admitted words without mutating SRS state
  except for existing explicit actions such as confirmed discard;
- current docs route implemented/default-on claims back through
  `docs/developer/feature_state_matrix.md`.
