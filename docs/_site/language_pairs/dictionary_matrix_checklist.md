# Dictionary Matrix Checklist

Goal: support EN→JP, JP→EN, EN→DE, DE→EN, EN→ES, ES→EN, JP→JP, and ES→ES with clear synonym vs translation separation, feature gating, and graceful fallbacks.

## 1) Inventory & Capability Matrix
- [ ] List all current language packs and classify:
  - [ ] Monolingual synonyms
  - [ ] Cross‑lingual translations
- [x] OdeNet sample XML captured (`/Users/takeyayuki/Documents/odenet_oneline.xml`)
- [x] FreeDict TEI sample located (`/Users/takeyayuki/Documents/deu-eng/deu-eng.tei`)
- [x] OdeNet parser wired (monolingual DE synonyms)
- [x] FreeDict TEI parser wired (DE→EN, EN→DE, ES→EN, and EN→ES)
- [ ] Map each pack to supported language pairs.
- [ ] Identify missing packs for required pairs.
- [ ] Decide primary/secondary sources per pair.
- [x] Primary DE synonyms: OdeNet (OpenThesaurus remains optional)
- [x] Primary JP synonyms: JP WordNet SQLite

## 2) Required Language Pairs
- [ ] EN → JP
- [ ] JP → EN
- [ ] EN → DE
- [ ] DE → EN
- [ ] EN → ES
- [ ] ES → EN
- [ ] JP → JP (synonyms)
- [ ] ES → ES (synonyms)

## 3) Pack Selection Rules
- [ ] Synonym generation uses **monolingual** packs only.
- [ ] Translation generation uses **cross‑lingual** packs only.
- [ ] UI clearly separates the two sections (checkbox groups).
- [ ] Persist per‑profile selection of packs.

## 4) Similarity Ranking Coverage
- [ ] EN→EN embeddings ranking (existing).
- [ ] JP→JP ranking strategy decided (monolingual JP embeddings?).
- [ ] DE→DE ranking strategy decided (monolingual DE embeddings?).
- [ ] Cross‑lingual ranking (optional) decided (multilingual model or disabled).
- [ ] Feature‑gate ranking per language pair (show unavailable).

## 5) Language Detection & Routing
- [ ] Detect language of replacement word (unicode ranges + stopwords).
- [ ] Fallback to “unknown” when ambiguous.
- [ ] Route to correct pack category based on detection and user selection.
- [ ] If detection fails, use a safe fallback (no ranking, substring mode allowed).

## 6) UX & Failure Modes
- [ ] If a pack is missing, warn and continue with remaining packs.
- [ ] If embeddings missing, show “ranking unavailable” and keep unranked candidates.
- [ ] If no results, log which packs were tried.

## 7) Testing
- [ ] EN→JP example set
- [ ] JP→EN example set
- [ ] EN→DE example set
- [ ] DE→EN example set
- [ ] EN→ES example set
- [ ] ES→EN example set
- [ ] JP→JP example set
- [ ] ES→ES example set

## 8) Documentation
- [ ] Update README with capability matrix.
- [ ] Explain synonym vs translation modes.
- [ ] Document ranking availability per language.
