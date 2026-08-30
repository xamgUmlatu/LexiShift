# Data Source Licensing And Distribution Register

Status: working legal/distribution register for all LP data sources.
Role: Planning / WIP
Purpose: track per-pack licensing evidence, redistribution posture, and recommended distribution mode so product data delivery decisions stay explicit and auditable
Last updated: 2026-06-09

## Scope

This document tracks, per pack:

- source URL and post-download/post-conversion artifact
- current license/copyright evidence status
- recommended source-acquisition mode (`auto-download` vs `manual-supply`)
- whether manual-supply UX exists in app

This is an engineering tracking doc, not legal advice.

## Primary Inventory Docs

- Full source + schema + path inventory:
  - `docs/language_pairs/lp_data_inventory_matrix.md`
- URL and file layout registry:
  - `docs/language_pairs/language_pack_urls.txt`
- POS source/pipeline behavior:
  - `docs/language_pairs/pos_source_and_pipeline_reference.md`
- Generated product/source notice index:
  - `docs/language_pairs/THIRD_PARTY_DATA_NOTICES.md`
- Hybrid hosted/local future posture:
  - `docs/language_pairs/hybrid_data_distribution_north_star.md`

## Current vs Future Distribution Posture

Two postures should stay explicit in repo terms.

Current `v1` posture:

- all compile inputs are local
- all emitted rulegen and semantic artifacts are local
- no cloud-hosted data path is required

Future north star:

- allow a hosted/open baseline lane where policy permits it
- allow local/manual-supply augmentation where policy requires it
- merge those lanes at compile time
- and compute artifact distribution rights from pack provenance

That future posture is described in:

- `docs/language_pairs/hybrid_data_distribution_north_star.md`

## Manual-Supply UX (Current State)

Manual linking is implemented in Settings UI:

- Language packs: `apps/gui/src/settings_language_packs.py` (`_select_language_pack_path`)
- Frequency packs: `apps/gui/src/settings_language_packs.py` (`_select_frequency_pack_path`)
- Embedding packs: `apps/gui/src/settings_language_packs.py` (`_select_embedding_pack_path`)
- POS overlays: `apps/gui/src/settings_language_packs.py` (`_select_pos_overlay_pack_path`)

Learning-pair setup cards are generated from
`core/lexishift_core/helper/source_stacks.py` and currently surface
download/manual setup paths for `language`, `frequency`, `pos_overlay`, and
`semantic_pack` resources. POS overlays and semantic packs are recommended
enrichment rather than hard pair-readiness gates unless the source stack marks
them required. The current `en-es` semantic pack setup installs a pair-level
local reference copy for later rule publication enrichment; `en-de` displays an
explicit pending semantic row because no default semantic reference pack is
declared yet.

Each detailed resource row and Learning Languages resource slot now exposes a
non-blocking "Source & license" detail action. It shows provider, source URL,
license name/link, distribution mode, local installed path when available, and
the generated notices path. This is informational for auto-downloadable sources
and does not add a confirmation step to normal setup.

Frequency manual-link validation now requires:

- valid SQLite header
- `frequency` table present

If a source is `manual-supply`, user can:

1. Open the provider/license page from the Learning Languages resource slot.
2. Review the provider terms and acquire the source externally.
3. Import the provider-native source file from Settings. For supported
   frequency-source builders, Learning Languages detects the expected source
   filename in the user's Downloads folder and offers an "Import downloaded"
   action; otherwise the user can choose the file manually.
4. Let the GUI validate/convert the source into a managed local pack artifact
   under the app data root, with manifest/provenance sidecars. Browser or
   extension-level download interception is not part of this baseline.

### Distribution Mode Legend
* `auto-download`: The license basis (local header and/or authoritative upstream license page) permits user-initiated app download/build, and required obligations are understood enough to surface in product docs/UI. This does not automatically mean LexiShift may bundle or host the converted artifact.
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
| `freq-en-coca` | frequency | `$DATA_ROOT/frequency_packs/freq-en-coca/main.sqlite` | review-required | Proprietary restrictions prohibit redistribution beyond the purchasing organization and restrict exact rank/frequency exposure. | `https://www.wordfrequency.info/license.asp` | 2026-05-31 | `manual-supply` | available |
| `freq-en-leipzig-default` | frequency | `$DATA_ROOT/frequency_packs/freq-en-leipzig-default/main.sqlite` | expected-not-verified | App-managed replacement for English source/target frequency defaults. Leipzig downloadable text corpora are listed as CC BY, and a 2026-06-09 temporary local build from `eng_news_2025_1M` produced `113,401` kept English lemmas with materially better en-de benchmark behavior than the sparse `freq-en-coca` sample. Source auto-download/local build appears compatible with the existing `freq-de-default` posture; bundling or hosting the converted SQLite remains a separate review item. | `https://wortschatz.informatik.uni-leipzig.de/en/download/eng`; `https://wortschatz.informatik.uni-leipzig.de/en/usage` | 2026-06-09 | `auto-download` | available |
| `freq-es-cde` | frequency | `$DATA_ROOT/frequency_packs/freq-es-cde/main.sqlite` | review-required | Proprietary restrictions prohibit redistribution beyond the purchasing organization and restrict exact rank/frequency exposure; the GUI must route this through manual setup unless a separate redistribution license is obtained. | `https://www.wordfrequency.info/license.asp` | 2026-05-31 | `manual-supply` | available |
| `freq-es-spalex-v1` | frequency | `$DATA_ROOT/frequency_packs/freq-es-spalex-v1/main.sqlite` | expected-not-verified | SPALEX `word_info.csv` is now the app-managed en-es/es-es Spanish frequency default. `freq-es-cde` is retired from runtime fallback and retained only as a historical/manual benchmark artifact. SPALEX evidence indicates CC BY 4.0; generated packs must preserve attribution, source version/DOI, raw checksums, and any optional Kaikki enrichment obligations. | `https://figshare.com/projects/SPALEX/29722` / `https://doi.org/10.3389/fpsyg.2018.02156` | 2026-06-08 | `auto-download` | available |
| `pos-es-ud-ancora-v1` | POS overlay | `$DATA_ROOT/pos_packs/pos-es-ud-ancora-v1/main.sqlite` | expected-not-verified | UD Spanish AnCora is listed by Universal Dependencies as CC BY 4.0. The generated overlay stores majority UPOS by Spanish word form so it can enrich SPALEX without inheriting `freq-es-cde` licensing limits; generated packs must preserve attribution, source URL, raw checksums, and source-bundle hash. | `https://universaldependencies.org/treebanks/es_ancora/index.html` | 2026-06-08 | `auto-download` | available |
| `freq-ja-bccwj` | frequency | `$DATA_ROOT/frequency_packs/freq-ja-bccwj/main.sqlite` | review-required | Quality-preferred `en-ja` target-frequency source. NINJAL's public BCCWJ word-list page says the frequency list is public and free for research or educational use; this is not treated as permission to bundle, host, or redistribute converted LexiShift artifacts without policy review. | `https://clrd.ninjal.ac.jp/bccwj/en/freq-list.html` | 2026-06-09 | `manual-supply` | available |
| `freq-de-default` | frequency | `$DATA_ROOT/frequency_packs/freq-de-default/main.sqlite` | expected-not-verified | Current app-managed local build downloads Leipzig downloadable corpora, German POS dictionary data, Morfologik tools, and German lexicon whitelist inputs. Leipzig distinguishes WWW/query data as CC BY-NC but downloadable text corpora as CC BY; german-pos-dict carries CC BY-SA 4.0. Source auto-download/local build is acceptable with attribution/share-alike notices, but bundling or hosting the converted SQLite remains a separate review item because the composite artifact mixes several upstream obligations. | `https://wortschatz.uni-leipzig.de/en/usage`; `https://raw.githubusercontent.com/languagetool-org/german-pos-dict/master/LICENSE` | 2026-06-08 | `auto-download` | available |
| `freedict-de-en` | translation | `$DATA_ROOT/language_packs/deu-eng.tei` (or converted SQLite) | confirmed-local | TEI header in local `deu-eng.tei`: GPLv3 + AGPLv3 references. | `local file` | 2026-02-22 | `auto-download` | available |
| `freedict-en-de` | translation | `$DATA_ROOT/language_packs/eng-deu.tei` (or converted SQLite) | expected-not-verified | Source archive URL used by app/runtime (`eng-deu.tei` inside). Local artifact verification still pending in this workspace, but FreeDict-style copyleft obligations are compatible with user-initiated app download/build when notices are preserved. | `https://download.freedict.org/dictionaries/eng-deu/1.9-fd1/freedict-eng-deu-1.9-fd1.src.tar.xz` | 2026-06-08 | `auto-download` | available |
| `freedict-es-en` | translation | `$DATA_ROOT/language_packs/spa-eng.tei` (or converted SQLite) | confirmed-local | TEI header in local `spa-eng.tei`: GPL v2 or later. | `local file` | 2026-02-22 | `auto-download` | available |
| `freedict-en-es` | translation | `$DATA_ROOT/language_packs/eng-spa.tei` (or converted SQLite) | confirmed-local | TEI header in local `eng-spa.tei`: CC BY-SA 3.0. | `local file` | 2026-02-22 | `auto-download` | available |
| `wiktionary-es-en` | translation | `$DATA_ROOT/language_packs/wiktionary-es-en.sqlite` | expected-not-verified | App-managed user-initiated download/build is supported from Kaikki/Wiktextract data. Kaikki identifies the data as Wiktionary-derived under CC-BY-SA and GFDL, so release packaging still must preserve attribution/share-alike notices and must not silently bundle the converted artifact without policy review. | `https://kaikki.org/dictionary/rawdata.html` | 2026-05-31 | `auto-download` | available |
| `wiktionary-en-es` | translation | `$DATA_ROOT/language_packs/wiktionary-en-es.sqlite` | expected-not-verified | Reverse-check slice converts the same English-edition Kaikki raw dump into an EN->ES compatibility SQLite artifact. App-managed user-initiated source download/build can follow the same attribution/share-alike notice posture as other Kaikki/Wiktionary packs; bundled or hosted converted artifacts still need policy review. | `https://kaikki.org/dictionary/rawdata.html` | 2026-06-08 | `auto-download` | available |
| `jmdict-ja-en` | translation | `$DATA_ROOT/language_packs/JMdict_e` | verified-from-upstream | EDRDG official licensing statement says JMdict/EDICT dictionary files are made available under Creative Commons Attribution-ShareAlike 4.0. Obligations: `OD-ATTR`, `OD-SA`; app/package documentation must acknowledge source and provide license/documentation links. | `https://www.edrdg.org/edrdg/licence.html` | 2026-06-09 | `auto-download` | available |
| `cc-cedict-zh-en` | translation | `$DATA_ROOT/language_packs/cedict_ts.u8` | expected-not-verified | Source archive URL used by app/runtime (`cedict_ts.u8` inside). Latest downloaded header in dev audit reports CC BY-SA 4.0; source auto-download can be enabled with attribution/share-alike notices, while bundled/hosted converted artifacts remain policy-review items. | `https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip` | 2026-06-08 | `auto-download` | available |
| `wordnet-en` | monolingual | `$DATA_ROOT/language_packs/english-wordnet-2025-json/` | expected-not-verified | Master repository `LICENSE.md` grants CC BY 4.0. Obligations: `OD-ATTR`. Local JSON snapshot in this workspace does not include a bundled license file. | `https://raw.githubusercontent.com/globalwordnet/english-wordnet/master/LICENSE.md` | 2026-02-23 | `auto-download` | available |
| `moby-en` | monolingual | `$DATA_ROOT/language_packs/mthesaur.txt` | expected-not-verified | Project Gutenberg distribution contains Grady Ward's public-domain declaration. No mandatory copyleft obligation; preserve provenance note in docs/releases. | `https://www.gutenberg.org/ebooks/3202.txt.utf-8` | 2026-02-23 | `auto-download` | available |
| `odenet-de` | monolingual | `$DATA_ROOT/language_packs/odenet_oneline.xml` | confirmed-local | local XML root has `license="https://creativecommons.org/licenses/by-sa/4.0/"`. | `local file` | 2026-02-22 | `auto-download` | available |
| `openthesaurus-de` | monolingual | `$DATA_ROOT/language_packs/openthesaurus.txt` | confirmed-local | local file header states LGPL 2.1+ terms. | `local file` | 2026-02-22 | `auto-download` | available |
| `jp-wordnet-sqlite` | monolingual | `$DATA_ROOT/language_packs/wnjpn.db` | confirmed-local | JP WordNet official license grants use/copy/modify/distribute without fee, with copyright/license notice retention requirement (BSD-like terms). | `https://bond-lab.github.io/wnja/license.txt` | 2026-02-23 | `auto-download` | available |
| `jp-wordnet` | monolingual | `$DATA_ROOT/language_packs/wnjpn-all.tab` | confirmed-local | JP WordNet official license grants use/copy/modify/distribute without fee, with copyright/license notice retention requirement (BSD-like terms). | `https://bond-lab.github.io/wnja/license.txt` | 2026-02-23 | `auto-download` | available |
| `embed-en-cc` / `embed-de-cc` / `embed-es-cc` / `embed-ja-cc` | embeddings | `$DATA_ROOT/embeddings/*.vec(.gz)` (+ optional `.sqlite`) | expected-not-verified | fastText official documentation for Common Crawl vectors explicitly declares CC BY-SA 3.0. Source auto-download is acceptable with attribution/share-alike notices; shipping generated SQLite derivatives remains a separate review item. | `https://fasttext.cc/docs/en/crawl-vectors.html` | 2026-06-08 | `auto-download` | available |
| `embed-xling-en/de/es/ja` | embeddings | `$DATA_ROOT/embeddings/wiki.*.align.vec` (+ optional `.sqlite`) | expected-not-verified | fastText official documentation for aligned word vectors explicitly declares CC BY-SA 3.0. Source auto-download is acceptable with attribution/share-alike notices; shipping generated SQLite derivatives remains a separate review item. | `https://fasttext.cc/docs/en/aligned-vectors.html` | 2026-06-08 | `auto-download` | available |

## Current Policy Gap List

These need explicit owner decisions:

1. Whether any separate license can make `wordfrequency.info` sources (`freq-en-coca`, `freq-es-cde`) safe for built-in auto-download.
2. Whether `wordfreq` should remain research-only or become a packaged library
   dependency. Do not flatten/export its data into a standalone LexiShift pack
   without a specific attribution/license design because upstream docs state
   that flat conversion does not preserve the needed license context.
3. Whether BCCWJ should remain manual-supply or can move to a licensed auto-download lane.
4. Embedding redistribution policy (fastText attribution/share-alike handling in product docs and UI).
5. Hosted/bundled redistribution of generated composite packs, especially
   `freq-de-default`, remains separate from user-initiated source auto-download.

## Practical Recommendation

Until unresolved rows are reviewed:

- keep existing local-link workflow as the safe default path for those packs
- treat unresolved packs as "`manual-supply` recommended" in documentation and release notes
- avoid bundling unresolved datasets in installer artifacts
- keep `docs/language_pairs/THIRD_PARTY_DATA_NOTICES.md` regenerated from
  `scripts/data/generate_third_party_data_notices.py` whenever catalog source or
  license metadata changes
