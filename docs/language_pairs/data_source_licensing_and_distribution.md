# Data Source Licensing And Distribution Register

Status: working legal/distribution register for all LP data sources.  
Last updated: 2026-02-23

## Scope

This document tracks, per pack:

- source URL and post-download/post-conversion artifact
- current license/copyright evidence status
- recommended distribution mode (`auto-download` vs `manual supply`)
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

If a source is manual-only, user can:

1. Acquire data externally.
2. Convert to required local format (usually SQLite) via scripts under `scripts/data/`.
3. Use `Select` in Settings -> Language Packs to link local files.

## Status Legend

- `confirmed-local`: license text found in local downloaded source/header.
- `expected-not-verified`: common/expected license, but not yet verified from local source in this workspace.
- `review-required`: legal status or redistribution conditions not yet resolved for product policy.

## Pack Register

| Pack ID | Type | Post-download/post-conversion artifact | License/copyright status | Evidence | Recommended distribution mode | Manual-supply UX |
| --- | --- | --- | --- | --- | --- | --- |
| `freq-en-coca` | frequency | `$DATA_ROOT/frequency_packs/freq-en-coca.sqlite` | review-required | source: `wordfrequency.info` sample endpoint; terms not captured in repo | manual supply until legal clearance | available |
| `freq-es-cde` | frequency | `$DATA_ROOT/frequency_packs/freq-es-cde.sqlite` | review-required | source: `wordfrequency.info` sample endpoint; terms not captured in repo | manual supply until legal clearance | available |
| `freq-ja-bccwj` | frequency | `$DATA_ROOT/frequency_packs/freq-ja-bccwj.sqlite` | review-required | source: NINJAL BCCWJ download; terms not yet codified in repo docs | manual supply until legal clearance | available |
| `freq-de-default` | frequency | `$DATA_ROOT/frequency_packs/freq-de-default.sqlite` | review-required | composite source: Leipzig corpus + LanguageTool POS data; redistribution policy not yet codified in repo docs | manual supply until legal clearance | available |
| `freedict-de-en` | translation | `$DATA_ROOT/language_packs/deu-eng.tei` (or converted SQLite) | confirmed-local | TEI header in local `deu-eng.tei`: GPLv3 + AGPLv3 references | auto-download allowed if copyleft obligations accepted | available |
| `freedict-en-de` | translation | `$DATA_ROOT/language_packs/eng-deu.tei` (or converted SQLite) | review-required | dictionary-specific FreeDict license not locally verified in this workspace | manual supply until verified | available |
| `freedict-es-en` | translation | `$DATA_ROOT/language_packs/spa-eng.tei` (or converted SQLite) | confirmed-local | TEI header in local `spa-eng.tei`: GPL v2 or later | auto-download allowed if copyleft obligations accepted | available |
| `freedict-en-es` | translation | `$DATA_ROOT/language_packs/eng-spa.tei` (or converted SQLite) | confirmed-local | TEI header in local `eng-spa.tei`: CC BY-SA 3.0 | auto-download allowed with attribution/share-alike compliance | available |
| `jmdict-ja-en` | translation | `$DATA_ROOT/language_packs/JMdict_e` | review-required | local file does not embed clear license terms in captured header area; policy decision pending | manual supply until terms are codified in docs | available |
| `cc-cedict-zh-en` | translation | `$DATA_ROOT/language_packs/cedict_ts.u8` | expected-not-verified | commonly published as CC BY-SA (not verified locally in this workspace) | manual supply until verified | available |
| `wordnet-en` | monolingual | `$DATA_ROOT/language_packs/english-wordnet-2025-json/` | review-required | local JSON pack has no bundled license file in current snapshot | manual supply until source terms are codified | available |
| `moby-en` | monolingual | `$DATA_ROOT/language_packs/mthesaur.txt` | review-required | license/provenance not captured in repo docs | manual supply until clarified | available |
| `odenet-de` | monolingual | `$DATA_ROOT/language_packs/odenet_oneline.xml` | confirmed-local | local XML root has `license="https://creativecommons.org/licenses/by-sa/4.0/"` | auto-download allowed with attribution/share-alike compliance | available |
| `openthesaurus-de` | monolingual | `$DATA_ROOT/language_packs/openthesaurus.txt` | confirmed-local | local file header states LGPL 2.1+ terms | auto-download allowed if LGPL obligations handled | available |
| `jp-wordnet-sqlite` | monolingual | `$DATA_ROOT/language_packs/wnjpn.db` | review-required | license not yet captured in repo docs | manual supply until clarified | available |
| `jp-wordnet` | monolingual | `$DATA_ROOT/language_packs/wnjpn-all.tab` | review-required | license not yet captured in repo docs | manual supply until clarified | available |
| `embed-en-cc` / `embed-de-cc` / `embed-es-cc` / `embed-ja-cc` | embeddings | `$DATA_ROOT/embeddings/*.vec(.gz)` (+ optional `.sqlite`) | expected-not-verified | fastText vectors commonly carry attribution/share-alike terms; exact obligations not codified in repo docs | manual supply until policy is codified | available |
| `embed-xling-en/de/es/ja` | embeddings | `$DATA_ROOT/embeddings/wiki.*.align.vec` (+ optional `.sqlite`) | expected-not-verified | same as above; obligations not yet codified in repo docs | manual supply until policy is codified | available |

## Current Policy Gap List

These need explicit owner decisions:

1. Whether `wordfrequency.info` sources (`freq-en-coca`, `freq-es-cde`) are legally safe for built-in auto-download.
2. Whether BCCWJ and Leipzig-based DE pipeline sources should remain auto-download or be manual-only.
3. JMDict, JP WordNet, and WordNet JSON redistribution policy in-product.
4. Embedding redistribution policy (fastText attribution/share-alike handling in product docs and UI).

## Practical Recommendation

Until unresolved rows are reviewed:

- keep existing local-link workflow as the safe default path for those packs
- treat unresolved packs as "manual supply recommended" in documentation and release notes
- avoid bundling unresolved datasets in installer artifacts
