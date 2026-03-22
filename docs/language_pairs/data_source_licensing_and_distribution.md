# Data Source Licensing And Distribution Register

Status: working legal/distribution register for all LP data sources.
Last updated: 2026-02-23

## Scope

This document tracks, per pack:

- source URL and post-download/post-conversion artifact
- current license/copyright evidence status
- recommended distribution mode (`auto-download` vs `manual-supply`)
- whether manual-supply UX exists in app

This is an engineering tracking doc, not legal advice.

## Primary Inventory Docs

- Full source + schema + path inventory:
  - `docs/language_pairs/lp_data_inventory_matrix.md`
- URL and file layout registry:
  - `docs/language_pairs/language_pack_urls.txt`
- POS source/pipeline behavior:
  - `docs/language_pairs/pos_source_and_pipeline_reference.md`

## Manual-Supply UX (Current State)

Manual linking is implemented in Settings UI:

- Language packs: `apps/gui/src/settings_language_packs.py` (`_select_language_pack_path`)
- Frequency packs: `apps/gui/src/settings_language_packs.py` (`_select_frequency_pack_path`)
- Embedding packs: `apps/gui/src/settings_language_packs.py` (`_select_embedding_pack_path`)

Frequency manual-link validation now requires:

- valid SQLite header
- `frequency` table present

If a source is `manual-supply`, user can:

1. Acquire data externally.
2. Convert to required local format (usually SQLite) via scripts under `scripts/data/`.
3. Use `Select` in Settings -> Language Packs to link local files.

### Distribution Mode Legend
* `auto-download`: The license basis (local header and/or authoritative upstream license page) permits redistribution, and required obligations are understood and can be surfaced in product docs/UI.
* `manual-supply`: Redistribution is prohibited/unclear, obligations are unresolved, or the policy owner has chosen not to auto-fetch yet.

### Status Legend
* `confirmed-local`: license text found directly in local downloaded source/header.
* `expected-not-verified`: license appears clear from upstream evidence, but local artifact/header confirmation in this workspace is incomplete.
* `review-required`: legal status or obligations are not resolved enough for product policy.

### Obligation Legend
* `OD-ATTR`: attribution required (source + license link in product/docs).
* `OD-SA`: share-alike requirement applies to redistributed derivatives.
* `OD-COPYLEFT`: GPL/AGPL/LGPL terms apply; provide required notices/license texts and preserve terms.
* `OD-NOTICE`: preserve copyright/license notices in redistributed data and docs.

## Pack Register

| Pack ID | Type | Post-download/post-conversion artifact | License/copyright status | Evidence Details | Evidence URL | Verified On | Recommended distribution mode | Manual-supply UX |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `freq-en-coca` | frequency | `$DATA_ROOT/frequency_packs/freq-en-coca.sqlite` | review-required | Proprietary EULA explicitly prohibits redistribution. | `https://www.wordfrequency.info/eula.asp` | 2026-02-22 | `manual-supply` | available |
| `freq-es-cde` | frequency | `$DATA_ROOT/frequency_packs/freq-es-cde.sqlite` | review-required | Proprietary EULA explicitly prohibits redistribution. | `https://www.wordfrequency.info/eula.asp` | 2026-02-22 | `manual-supply` | available |
| `freq-ja-bccwj` | frequency | `$DATA_ROOT/frequency_packs/freq-ja-bccwj.sqlite` | review-required | Institutional/NINJAL agreement prohibits third-party distribution. | `https://clrd.ninjal.ac.jp/bccwj/en/doc.html` | 2026-02-22 | `manual-supply` | available |
| `freq-de-default` | frequency | `$DATA_ROOT/frequency_packs/freq-de-default.sqlite` | review-required | Leipzig site/app queries are CC BY-NC (though downloadable bulk corpora are CC BY). Combined with LanguageTool LGPL, composite carries too much NC friction. | `https://wortschatz.uni-leipzig.de/en/usage` | 2026-02-22 | `manual-supply` | available |
| `freedict-de-en` | translation | `$DATA_ROOT/language_packs/deu-eng.tei` (or converted SQLite) | confirmed-local | TEI header in local `deu-eng.tei`: GPLv3 + AGPLv3 references. | `local file` | 2026-02-22 | `auto-download` | available |
| `freedict-en-de` | translation | `$DATA_ROOT/language_packs/eng-deu.tei` (or converted SQLite) | expected-not-verified | Source archive URL used by app/runtime (`eng-deu.tei` inside). Local artifact verification still pending in this workspace. | `https://download.freedict.org/dictionaries/eng-deu/1.9-fd1/freedict-eng-deu-1.9-fd1.src.tar.xz` | 2026-02-22 | `manual-supply` | available |
| `freedict-es-en` | translation | `$DATA_ROOT/language_packs/spa-eng.tei` (or converted SQLite) | confirmed-local | TEI header in local `spa-eng.tei`: GPL v2 or later. | `local file` | 2026-02-22 | `auto-download` | available |
| `freedict-en-es` | translation | `$DATA_ROOT/language_packs/eng-spa.tei` (or converted SQLite) | confirmed-local | TEI header in local `eng-spa.tei`: CC BY-SA 3.0. | `local file` | 2026-02-22 | `auto-download` | available |
| `wiktionary-es-en` | translation | `$DATA_ROOT/language_packs/wiktionary-es-en.sqlite` | review-required | First rollout converts the English-edition Kaikki raw dump into a pair-specific SQLite artifact. Final attribution/share-alike policy for the converted artifact is not yet captured as a settled repo distribution rule, so keep manual-supply posture until policy owner review. | `https://kaikki.org/dictionary/rawdata.html` | 2026-03-22 | `manual-supply` | available |
| `wiktionary-en-es` | translation | `$DATA_ROOT/language_packs/wiktionary-en-es.sqlite` | review-required | Reverse-check slice converts the same English-edition Kaikki raw dump into an EN->ES compatibility SQLite artifact. Attribution/share-alike policy for converted artifacts is still pending policy-owner review, so keep manual-supply posture until settled. | `https://kaikki.org/dictionary/rawdata.html` | 2026-03-23 | `manual-supply` | available |
| `jmdict-ja-en` | translation | `$DATA_ROOT/language_packs/JMdict_e` | expected-not-verified | EDRDG official licensing statement says dictionary files are CC BY-SA 4.0. Obligations: `OD-ATTR`, `OD-SA`. Local `JMdict_e` header does not embed license text in this workspace. | `https://www.edrdg.org/edrdg/licence.html` | 2026-02-23 | `auto-download` | available |
| `cc-cedict-zh-en` | translation | `$DATA_ROOT/language_packs/cedict_ts.u8` | expected-not-verified | Source archive URL used by app/runtime (`cedict_ts.u8` inside). Latest downloaded header in dev audit reports CC BY-SA 4.0; policy remains `manual-supply` until owner confirms final handling of attribution/share-alike obligations. | `https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip` | 2026-02-23 | `manual-supply` | available |
| `wordnet-en` | monolingual | `$DATA_ROOT/language_packs/english-wordnet-2025-json/` | expected-not-verified | Master repository `LICENSE.md` grants CC BY 4.0. Obligations: `OD-ATTR`. Local JSON snapshot in this workspace does not include a bundled license file. | `https://raw.githubusercontent.com/globalwordnet/english-wordnet/master/LICENSE.md` | 2026-02-23 | `auto-download` | available |
| `moby-en` | monolingual | `$DATA_ROOT/language_packs/mthesaur.txt` | expected-not-verified | Project Gutenberg distribution contains Grady Ward's public-domain declaration. No mandatory copyleft obligation; preserve provenance note in docs/releases. | `https://www.gutenberg.org/ebooks/3202.txt.utf-8` | 2026-02-23 | `auto-download` | available |
| `odenet-de` | monolingual | `$DATA_ROOT/language_packs/odenet_oneline.xml` | confirmed-local | local XML root has `license="https://creativecommons.org/licenses/by-sa/4.0/"`. | `local file` | 2026-02-22 | `auto-download` | available |
| `openthesaurus-de` | monolingual | `$DATA_ROOT/language_packs/openthesaurus.txt` | confirmed-local | local file header states LGPL 2.1+ terms. | `local file` | 2026-02-22 | `auto-download` | available |
| `jp-wordnet-sqlite` | monolingual | `$DATA_ROOT/language_packs/wnjpn.db` | confirmed-local | JP WordNet official license grants use/copy/modify/distribute without fee, with copyright/license notice retention requirement (BSD-like terms). | `https://bond-lab.github.io/wnja/license.txt` | 2026-02-23 | `auto-download` | available |
| `jp-wordnet` | monolingual | `$DATA_ROOT/language_packs/wnjpn-all.tab` | confirmed-local | JP WordNet official license grants use/copy/modify/distribute without fee, with copyright/license notice retention requirement (BSD-like terms). | `https://bond-lab.github.io/wnja/license.txt` | 2026-02-23 | `auto-download` | available |
| `embed-en-cc` / `embed-de-cc` / `embed-es-cc` / `embed-ja-cc` | embeddings | `$DATA_ROOT/embeddings/*.vec(.gz)` (+ optional `.sqlite`) | expected-not-verified | fastText official documentation for Common Crawl vectors explicitly declares CC BY-SA 3.0. | `https://fasttext.cc/docs/en/crawl-vectors.html` | 2026-02-22 | `manual-supply` | available |
| `embed-xling-en/de/es/ja` | embeddings | `$DATA_ROOT/embeddings/wiki.*.align.vec` (+ optional `.sqlite`) | expected-not-verified | fastText official documentation for aligned word vectors explicitly declares CC BY-SA 3.0. | `https://fasttext.cc/docs/en/aligned-vectors.html` | 2026-02-22 | `manual-supply` | available |

## Current Policy Gap List

These need explicit owner decisions:

1. Whether `wordfrequency.info` sources (`freq-en-coca`, `freq-es-cde`) are legally safe for built-in auto-download.
2. Whether BCCWJ and Leipzig-based DE pipeline sources should remain auto-download or be manual-supply.
3. Embedding redistribution policy (fastText attribution/share-alike handling in product docs and UI).

## Practical Recommendation

Until unresolved rows are reviewed:

- keep existing local-link workflow as the safe default path for those packs
- treat unresolved packs as "`manual-supply` recommended" in documentation and release notes
- avoid bundling unresolved datasets in installer artifacts
