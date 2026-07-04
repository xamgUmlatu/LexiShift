# SRS Browsing Admission Live Runtime Test

Use this after the GUI app and Chrome extension are reloaded from a build that
contains the browsing source-index runtime work.

## Local Fixture Server

```bash
python3 -m http.server 8765 --directory docs/test_inputs/srs_browsing_admission_live_pages
```

## Pages

- `http://127.0.0.1:8765/index.html`
- `http://127.0.0.1:8765/source-interest-a.html`
- `http://127.0.0.1:8765/source-interest-b.html`
- `http://127.0.0.1:8765/target-ruby-ja.html`
- `http://127.0.0.1:8765/iframe-parent.html`
- `http://127.0.0.1:8765/spa-route.html`

## Expected Signals

- Source pages intentionally use inflected source-index terms such as
  `companies`, `schools`, `researched`, `technologies`, `teachers`, `reports`,
  `universities`, `cultures`, `countries`, and `cooked`.
- These forms should mine the corresponding en-ja source-index terms without
  colliding with exact active replacements that can rewrite singular source
  phrases before the page miner scans visible text.
- Expected source-mined target words include `会社`, `学校`, `研究`, `技術`,
  `先生`, `報告`, `大学`, `文化`, `国`, and `料理`.
- Expected source-mapping confidence for these rows may be lower than exact
  source hits because the miner applies inflection/derivation confidence
  multipliers.
- Exact source phrases such as `company`, `school`, `research`, and `cooking`
  are poor live fixture terms when those same words are active replacement
  rules; the test page can then verify replacement timing instead of source
  mining.
- The ruby page should mine reading-aware target evidence for those same words.
- The iframe page should not cause repeated source-index generation from the
  subframe.
- The SPA page should mine the initial route text and should also mine route
  text inserted by the button-triggered mutation before normal replacement
  processing rewrites eligible source phrases.

## Checks

- With browsing admission disabled, visiting these pages should not update the
  helper browsing signal store.
- With browsing admission enabled, visiting source A, source B, and target ruby
  should update `srs_browsing_signals_en-ja.json` for the selected profile.
- Source-index loading should be `helper-cache` after the first load.
- Debug logs should not show repeated expensive source-index generation.
