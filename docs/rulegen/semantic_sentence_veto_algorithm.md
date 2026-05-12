# Semantic Sentence-Veto Algorithm

Status: active reference
Role: Algorithm reference / research alignment
Last updated: 2026-05-13
Last verified: 2026-05-13 against `semantic_routing_runtime_scoring.py`, `semantic_routing_runtime_policy.py`, current decision-rule matrix manifests, latest phrasing/order plus context-conditioned evidence bakeoff artifacts, the product-scope algorithm bakeoff, the corrected product-scope candidate/band rerun, the browser extension `context_text` assembly path plus edge-case context resolver contracts, and a live fetched Castle-page DOM-split regression
Purpose: describe the semantic sentence-veto algorithm end to end so runtime behavior, source-admission work, phrase handling, and decision-rule experiments stay aligned
Source-of-truth: explanatory reference only; implementation truth lives in the code, tests, manifests, and generated artifacts named below

Primary implementation references:

- `core/lexishift_core/rulegen/semantic_routing_runtime_scoring.py`
- `core/lexishift_core/rulegen/semantic_routing_runtime_policy.py`
- `apps/chrome-extension/content/runtime/dom_scan/semantic_context.js`
- `apps/chrome-extension/content/runtime/semantic/semantic_request_context.js`
- `scripts/testing/semantic_decision_rule_matrix_en_es.py`
- `scripts/testing/semantic_decision_research_lanes_summary.py`
- `scripts/testing/semantic_routing_sentence_veto_sweep.py`
- `scripts/testing/semantic_veto_product_scope_algorithm_bakeoff_en_es.py`
- `scripts/testing/semantic_veto_product_scope_selected_candidate_surface_en_es.py`
- `scripts/testing/semantic_veto_repaired_full_band_formula_sweep_en_es.py`
- `scripts/testing/semantic_source_admission_cycle_en_es.py`
- `docs/test_inputs/semantic_decision_research_lanes_en_es.json`
- `docs/rulegen/semantic_routing_runtime_readiness.md`
- `docs/rulegen/semantic_decision_rule_comparison_plan.md`
- `docs/rulegen/semantic_source_admission_program.md`
- `docs/rulegen/semantic_veto_reconciliation_workstream.md`
- `docs/test_inputs/semantic_veto_system_registry_en_es.json`

## Core Product Goal

For each browser sentence, the user should either see the replacement or not.
There is no acceptable visible middle state in the current DOM path.

Example:

- source sentence contains `change`
- learner target is Spanish `cambio`
- the semantic gate must decide whether this local sentence supports that target
- if yes, show the replacement
- if no, leave the source text alone

The governing product rule is asymmetric:

- showing good replacements is the primary value
- hiding clearly bad replacements is useful, but not a zero-harm contract
- false abstain is visible as "nothing happened" and should be reduced when it
  costs too many good replacements
- false allow is tolerable when the replacement is not obviously destructive and
  the veto still improves over lexical allow-all

That asymmetry is why current product research ranks candidate policies by
positive allow, negative abstain, and utility versus lexical allow-all, not by a
single zero-harm gate.

## End-To-End Shape

The algorithm has two large halves:

1. offline source and competition construction
2. runtime sentence admission

The runtime admission algorithm cannot fix a missing shadow competitor. The
source-admission algorithm cannot prove the final browser decision by itself.
Keep these halves separate when reading results.

### Offline Source And Competition Construction

Offline work builds the data that runtime needs:

- an active sense for the learner target
- source evidence rows for that active sense
- a small shadow set of competing senses that can make the same English trigger unsafe
- source evidence rows for each shadow sense
- phrase/no-winner patterns that should abstain without pretending a shadow sense won

Conceptually, for one active target `a` and trigger phrase `t`:

```text
S(a, t) = {s1, s2, ..., sk}
```

`S(a, t)` is the published shadow set. It should contain real runtime hazards,
not every lexical neighbor.

The current source-admission work uses source-backed evidence families such as
reverse auxiliary text, local WordNet-style definition/example rows,
Wiktextract/Wiktionary-style examples where available, and generated or reviewed
example-frame rows only after leakage and sense-discrimination checks.

Important distinction:

- source coverage asks whether the right active/shadow/phrase evidence exists
- runtime scoring asks whether a sentence chooses correctly given that evidence

## Runtime Admission Path

The browser/helper runtime follows this shape.

### 1. Match Eligibility

A browser match is eligible for semantic gating only when the surrounding
runtime contract says it is ready:

- SRS is enabled
- the matched rule is SRS-origin
- the rule carries `metadata.semantic_admission`
- semantic capability for the pair/profile is active
- semantic inventory resolves through helper or helper-cache
- the admission record points to a ready active sense and ready competition set
- shadow senses can be resolved from the inventory
- the match has both `context_text` and `source_phrase`

If any required item is missing, runtime uses the configured fallback decision
instead of inventing a semantic answer.

### 2. Policy Resolution

Runtime resolves a named policy from `PRODUCTION_SEMANTIC_DECISION_POLICIES`.
As of this reference:

| Policy | Scorer | Context | Evidence | Thresholds | Phrase | Rescue |
| --- | --- | --- | --- | --- | --- | --- |
| `en_es_sentence_veto_v1` | `sentence_transformer_cosine` | `masked_sentence` | `gloss_text` | active `0.0`, margin `0.0` | on | on |
| `en_es_sentence_veto_v2` | `tfidf_cosine` | `masked_sentence` | `all_evidence_text` | active `0.015`, margin `0.0` | on | on |
| `en_es_sentence_veto_v3` | `sentence_transformer_cosine` | `masked_sentence` | `all_evidence_text` | active `0.0`, margin `0.0` | on | on |

The current pair default in code is:

```text
en-es -> en_es_sentence_veto_v3
```

Do not confuse this with the library fallback constants in
`semantic_routing_runtime_scoring.py`. Named policies override those constants.
Do not confuse it with the no-spend research control either; many recent matrix
experiments intentionally use `tfidf_cosine` because they are offline,
reproducible, and cheap.

### 3. Batch Fitting

For a batch of ready matches, runtime fits the selected scorer on exactly the
texts it may compare:

- context views derived from each ready match
- active evidence text
- shadow evidence text
- backup evidence text when active rescue is enabled

This matters most for `tfidf_cosine`, where adding texts can change the fitted
vocabulary and weights. Research matrices therefore support per-suite fitting so
held-out additions cannot silently move frozen-suite scores.

### 4. Context Representation

Production runtime currently exposes these context views:

- `raw_sentence`
- `masked_sentence`
- `raw_window`
- `masked_window`

For the active trigger span, masking replaces the matched source phrase with
`___`. Example:

```text
The company announced a major change in strategy.
The company announced a major ___ in strategy.
```

The matrix harness also has harness-only experimental views such as ordered
n-grams, skip-grams, before/after slots, surface frames, POS frames,
dependency-role approximations, negation/modal signals, shuffled context, and
reversed context. Those are not production runtime views.

### DOM Context Assembly

Status: implemented in the browser extension runtime with scan-local context
buffer reuse.

The browser extension still finds replacement candidates inside one raw DOM text
node, but semantic admission no longer has to use that same text-node string as
`context_text`. Inline markup can split one visible sentence into many text
nodes. On pages such as Wikipedia, a visible sentence like `A castle is a type of
fortified structure` previously reached the semantic scorer as only `castle`,
which starved the active-sense score even when the visible sentence was a clear
active context.

The runtime fix keeps DOM edits text-node-local while widening only the semantic
context sent to helper admission:

1. Match and replacement rendering remain scoped to the original text node.
2. Before semantic admission, derive a bounded visible context around the match
   from nearby DOM text nodes.
3. Send the widened `context_text` plus `match_start` / `match_end` offsets
   relative to that widened context.
4. If widened context assembly is unavailable or offset mapping is ambiguous,
   fall back to the current text-node-local context rather than guessing.

Context assembly should use two separate controls:

- a block-ish ancestor as a safety fence, so the search does not drift into
  unrelated navigation, captions, cards, or sibling blocks
- punctuation and word budgets as clipping heuristics inside that fence

Implemented runtime algorithm:

1. Walk up from the current text node to the nearest sane text container such as
   `p`, `li`, `td`, `th`, `blockquote`, `figcaption`, `dd`, `dt`, or a compact
   article/content `div`. Stop at `body` and use a small ancestor-depth cap.
2. Traverse visible text-node siblings inside that container in document order,
   skipping editable nodes, script/style/noscript content, hidden nodes, and
   existing `.lexishift-replacement` spans.
3. Build a visible text buffer with an offset map back to each participating
   text node and the text-node-local match span. During one scan, small complete
   container snapshots are cached by containing block and node-filter policy so
   multiple matched text nodes in the same visible block can reuse the same
   assembled buffer. If a container is too large, truncated, or not fully
   mappable, the resolver falls back to the per-node assembly path.
4. Clip around the mapped match span. Prefer strong sentence boundaries (`.`,
   `?`, `!`). If no strong boundary is available, use the hard word-window cap.
   Commas are not hard stops because they often carry the disambiguating
   appositive or relative clause. Semicolons and colons are not hard stops in
   the current runtime; long run-ons that use them are still bounded by the word
   cap.
5. Enforce hard caps while collecting and clipping. The implementation should
   have named constants for maximum visible words, maximum characters, maximum
   text nodes visited, and maximum ancestor depth. The search must stop when the
   word cap is reached even if no punctuation boundary was found.

The hard cap is part of the semantic policy, not just performance protection.
Longer context can drift after punctuation, and the marginal benefit usually
falls once the current sentence or sentence-like window is present. A reasonable
starting point is a hard maximum of sentence-window scale, then tune with
observed false abstains and helper latency.

Current contract coverage includes:

- split inline paragraph context, for example
  `<p>A <a>castle</a> is a type of <b>fortified</b> structure...</p>`
- hard word-cap enforcement when a container has no punctuation boundary
- helper request serialization of widened `context_text` with mapped
  `match_start` / `match_end` offsets
- comma/appositive cases where stopping at the first comma would remove useful
  disambiguating context
- repeated source phrases in one block, proving `match_start` / `match_end`
  point at the current text-node occurrence inside the widened context
- negative cases that must not cross into sibling blocks, hidden text, or
  LexiShift replacement spans
- single text nodes containing multiple sentences, proving the resolver clips to
  the sentence around the current match rather than the whole text node
- multiple ready SRS matches in one sentence, proving helper requests share the
  same sentence context while preserving independent `source_phrase`, offset,
  and decision records
- scan-local block context cache reuse, proving multiple matched text nodes in a
  small complete block reuse one assembled container buffer

Live page regression:

- `2026-05-13`: fetched `https://en.wikipedia.org/wiki/Castle` and confirmed
  the first paragraph still arrives as split text chunks such as `A `,
  `castle`, ` is a type of `, `fortified`, ` structure built during the `,
  `Middle Ages`, and later `. Scholars usually consider a `, `castle`.
- Replaying those chunks through the current resolver returned the first
  sentence for the first `castle` and `fortified`, the second sentence for the
  later `castle`, and reused one complete block buffer for all three lookups
  (`containerBuilds=1`, `recordReuses=2`, `usableReuses=3`, `bypasses=0`).

Performance instrumentation:

- Debug scan/mutation logs now include `Semantic admission performance` with
  inventory lookup count/latency, helper batch call count, helper request count,
  helper batch min/max/average size, helper latency total/max/average, and
  context-cache build/reuse/bypass counts. The same summary also includes scan
  scheduler counters: `scanNodeBatchCalls`, `scanNodeCount`,
  `scanNodeBatchMaxSize`, `scanNodeConcurrentBatches`,
  `scanNodeSerialBatches`, and `scanNodeSerialBudgetBatches`.
- Debug apply diagnostics persist the same fields under
  `srsRuntimeLastState`, including:
  `semantic_helper_batch_calls`, `semantic_helper_request_count`,
  `semantic_helper_batch_avg_size`, `semantic_helper_latency_ms_total`,
  `semantic_helper_latency_ms_avg`,
  `semantic_context_cache_container_builds`,
  `semantic_context_cache_record_reuses`,
  `semantic_context_cache_usable_reuses`, and
  `semantic_context_cache_bypasses`. Debug state also persists the scheduler
  fields as `semantic_scan_node_batch_*`,
  `semantic_scan_node_concurrent_batches`,
  `semantic_scan_node_serial_batches`, and
  `semantic_scan_node_serial_budget_batches`.
- These metrics are meant to prove user-facing performance changes against
  `first_visible_replacement_latency_ms`, not just lower internal work counts.
- Successful semantic-inventory resolution is cached inside the content-script
  semantic gate by pair/profile. That cache exists above individual text-node
  admissions, so a serial scan no longer has to pay helper inventory lookup
  latency once per ready match. Missing/error inventory responses are not
  treated as stable success. The metrics count actual inventory resolutions,
  not cache hits, so an optimized single-pair page scan should normally show
  roughly one `semantic_inventory_lookup_calls` value for the active
  pair/profile even if helper admission still evaluates many matches.
- Helper admission batching now uses explicit `fit_scope=per_match` for browser
  page batches that contain different `context_text` values. This is the
  scorer-contract guardrail: a batch can reduce native-message/helper startup
  overhead while the helper still evaluates each match with the same fit corpus
  shape it would have had as a one-match request. This matters for TF-IDF
  policies, where fitting on many unrelated browser contexts can change scores.
- Budgeted semantic scans now use a two-phase node pass. The runtime first
  preflights semantic decisions for a bounded batch of text nodes concurrently,
  then renders those nodes in DOM order with the normal page-budget state and a
  semantic-result override. The preflight sees a read-only snapshot of the
  already-consumed page budget, but it does not mutate the live budget; actual
  replacement application remains text-node-local and budget-enforced.

Current Castle measurement:

- `2026-05-13`: replayed the fetched Castle first-paragraph chunks through the
  current resolver and semantic gate with a mock helper delay to measure call
  topology. The paragraph had `32` text chunks; the measured ready nodes were
  the first `castle`, first `fortified`, and later `castle`.
- Current optimized topology for those three ready matches:
  `semantic_inventory_lookup_calls=1`, `semantic_helper_batch_calls=2`,
  `semantic_helper_request_count=3`, `semantic_helper_batch_min_size=1`,
  `semantic_helper_batch_max_size=2`, `semantic_helper_batch_avg_size=1.5`,
  helper call sizes `[2, 1]`.
- Context assembly was already reused:
  `semantic_context_cache_container_builds=1`,
  `semantic_context_cache_record_reuses=2`,
  `semantic_context_cache_usable_reuses=3`,
  `semantic_context_cache_bypasses=0`.
- Interpretation: the runtime now coalesces concurrent ready admissions when
  they resolve to the same widened `context_text`, pair/profile, and fallback
  policy. On Castle, the first `castle` and `fortified` share the first
  sentence and batch together; the later `castle` is in the next sentence and
  stays in a separate helper call. That preserves the scorer input shape that
  would have existed if the sentence had been one DOM text node, while avoiding
  broader cross-sentence batching that could change batch-sensitive scorers.
  Actual end-to-end latency impact must still be measured in a live extension
  run because mock helper latency is only a topology probe.
- A live Castle extension run before the semantic-gate inventory cache showed
  `inventoryLookupCalls=267`, `helperBatchCalls=267`,
  `helperRequestCount=267`, `helperBatchMaxSize=1`,
  `inventoryLookupLatencyMsAvg=198.3`, and `helperLatencyMsAvg=197.3`.
  Interpretation: instrumentation was live, but same-context helper coalescing
  did not materially apply in that browser run; the repeated helper inventory
  preflight was the immediate latency bug. The inventory cache is therefore the
  first live-runtime optimization to verify before broader helper request
  coalescing changes.
- A live Castle reload after the inventory-cache patch showed
  `inventoryLookupCalls=1`, `inventoryLookupLatencyMsTotal=187.6`,
  `helperBatchCalls=266`, `helperRequestCount=266`, `helperBatchMaxSize=1`,
  and `helperLatencyMsTotal=52074`. Interpretation: inventory preflight was
  fixed, and the remaining latency was isolated to one native helper admission
  request per ready match. The next optimization is therefore per-match-fit
  helper batching across different contexts, not more context-cache work.
- A follow-up live Castle reload still showed `helperBatchMaxSize=1` and added
  scan scheduler evidence:
  `scanNodeBatchCalls=6737`, `scanNodeBatchMaxSize=1`,
  `scanNodeSerialBudgetBatches=6737`. Interpretation: helper batching code was
  present, but page-budget mode was forcing every text node through the serial
  scanner, so the helper batcher never saw multiple pending semantic requests.
  The current runtime patch addresses that scheduler constraint with the
  two-phase budgeted semantic scan described above.
- A live Castle reload after the two-phase budgeted semantic scan showed the
  intended user-facing performance win:
  `inventoryLookupCalls=1`, `helperRequestCount=267`,
  `helperBatchCalls=137`, `helperBatchMaxSize=5`,
  `helperBatchAvgSize=1.95`, `helperLatencyMsTotal=26449.8`,
  `scanNodeBatchCalls=281`, `scanNodeBatchMaxSize=24`,
  `scanNodeConcurrentBatches=281`, and `scanNodeSerialBudgetBatches=0`.
  Compared with the post-inventory-cache run, the runtime still evaluated the
  same `267` semantic requests, but native-helper round trips fell from `266` to
  `137` and total helper time fell from about `52.1s` to about `26.4s`.
  Plainly: this did not make one helper call faster; it made the browser send
  the same work in fewer helper calls. The observed page experience was
  materially faster.
- Live Castle scheduler tuning then compared the default `24` semantic text-node
  batch with a larger `96` batch while keeping the helper flush window at `0`.
  The `24` run had `first_visible_replacement_latency_ms=876.9`,
  `scan_ms=28092.9`, `semantic_helper_batch_calls=139`, and
  `semantic_helper_latency_ms_total=27605.1`. The `96` run had
  `first_visible_replacement_latency_ms=859.6`, `scan_ms=9866.2`,
  `semantic_helper_batch_calls=47`, and
  `semantic_helper_latency_ms_total=9462.6`. Interpretation: on this page,
  the larger batch preserved first-visible latency while cutting whole-page
  scan/helper time by roughly two thirds, so `96` is the current default.
- A short helper flush window did not help the same Castle run. With scheduler
  batch `96`, `debugSemanticHelperBatchFlushMs=5` and `10` both produced
  `semantic_helper_batch_calls=47` and `semantic_helper_batch_avg_size=5.81`,
  while helper latency rose relative to the `0` flush run. The default remains
  `0`; keep the flush knob for controlled experiments only.

Live E2E measurement workflow:

1. Enable extension debug logging and semantic admission for a ready semantic
   pack/profile.
2. Load the target page in a fresh tab and wait for initial replacements.
3. Inspect the debug log entries named `Semantic admission performance`,
   `Semantic admission performance summary`, and `Apply timing`.
4. Read `chrome.storage.local.srsRuntimeLastState` while debug mode is enabled
   and record at least `page_url`, `first_visible_replacement_latency_ms`,
   `semantic_helper_batch_calls`, `semantic_helper_request_count`,
   `semantic_helper_batch_max_size`, `semantic_helper_batch_avg_size`,
   `semantic_helper_latency_ms_total`, `semantic_helper_latency_ms_avg`,
   `semantic_scan_node_batch_max_size`,
   `semantic_scan_node_serial_budget_batches`,
   `semantic_context_cache_container_builds`,
   `semantic_context_cache_usable_reuses`, and
   `semantic_context_cache_bypasses`.
5. Compare before/after optimization runs on the same page, profile, browser
   session shape, and semantic pack. A useful coalescing win should lower helper
   batch calls and total scan/helper time without changing replace / abstain
   decisions or materially regressing first-visible replacement latency.

Deferred performance follow-up:

- Same-context helper-call coalescing is implemented, and browser helper batches
  can now coalesce different context strings only when the helper request uses
  explicit `fit_scope=per_match`.
- Budgeted semantic pages now have a two-phase scan path, so the next live
  metric to watch is `helperBatchAvgSize` / `helperBatchMaxSize` together with
  `scanNodeBatchMaxSize` / `scanNodeSerialBudgetBatches`. On a page like Castle,
  a healthy run should no longer have `helperBatchMaxSize=1` because page-budget
  mode should no longer force semantic node scans into one-node batches.
- The first live Castle run after this patch reached `helperBatchAvgSize=1.95`
  and `helperBatchMaxSize=5`. Further tuning can experiment with larger scan
  batches or a short semantic-batch flush window, but those changes should be
  evaluated against first-visible replacement latency and page responsiveness,
  not helper-call counts alone.
- Two debug-only storage knobs exist for live tuning experiments:
  `debugSemanticScanNodeBatchSize` controls the semantic text-node scheduler
  batch size, and `debugSemanticHelperBatchFlushMs` adds a bounded helper
  admission flush delay. Defaults are `96` and `0`, matching the best measured
  Castle UX/throughput tradeoff so far.
- The remaining validation before treating `96` as universal is cross-page
  smoke, not more Castle tuning. Use one dense article, one JS-heavy page with
  navigation/sidebar text, and one long documentation page. If any page shows a
  material first-visible regression at `96`, revisit viewport-first or hybrid
  scheduling; otherwise keep the single default batch to avoid unnecessary
  scheduler complexity.
- If `helperBatchMaxSize` remains `1`, use the scan scheduler counters:
  - if `scanNodeBatchMaxSize` is also `1` and
    `scanNodeSerialBudgetBatches > 0`, the browser is still running an older
    build or the budgeted preflight method was unavailable
  - if `scanNodeBatchMaxSize` is larger than `1` while
    `helperBatchMaxSize` remains `1`, the semantic-gate/helper batching path is
    failing after node scheduling
  - if the scan scheduler counters are missing entirely, the browser did not
    load this instrumentation revision
- If semicolon/colon clipping becomes necessary for long run-ons, implement it
  as a separate boundary-policy change with examples proving that definitions
  after `:` and closely related clauses after `;` are not accidentally removed.

### 5. Evidence Representation

For each sense, runtime resolves one evidence view from `evidence_views`:

- `sense_label`
- `gloss_text`
- `sense_gloss_bundle`
- `qualifier_text`
- `all_evidence_text`

If the requested view is missing, runtime falls back through broader evidence
views and finally to the sense label or target lemma.

The matrix harness can split evidence into rows, score definitions/examples
separately, test ordered evidence, test canonical templates, test paraphrase
variants, load admitted source rows, select evidence rows based on a separate
selector context, and run source-family dropout. Those are research surfaces
unless a candidate is promoted later.

### 6. Similarity Scoring

For context `c`, active sense `a`, and shadows `s_i`, production scoring is:

```text
active_score = similarity(context_text(c), evidence_text(a))

shadow_score_i = similarity(context_text(c), evidence_text(s_i))

strongest_shadow_score = max_i shadow_score_i

margin = active_score - strongest_shadow_score
```

Supported runtime scorers are:

- `token_jaccard`
- `tfidf_cosine`
- `sentence_transformer_cosine`

`sentence_transformer_cosine` normalizes cosine into the `[0, 1]` range. TF-IDF
and token overlap are no-spend controls and useful for exposing whether a result
is mostly word-presence behavior.

### 7. Primary YES/NO Decision

The primary decision is:

```text
replace if:
  active_score >= min_active_score
  and active_score - strongest_shadow_score >= min_margin

abstain otherwise
```

This is better described as a one-versus-strongest-competitor decision rule, not
as a metric. Evaluation metrics are separate things such as harmful replacement
count, false abstain count, winner accuracy, ROC AUC, and average precision.

### 8. Phrase Preemption

Phrase preemption is not just another shadow score. It handles no-winner cases
where the source phrase belongs to a local construction that should not become
the learner target.

Examples from the current family of concerns:

- `bank on`
- `file past`
- `play out`
- `report back`
- noun-frame expressions such as `the rest of`

Production phrase control currently applies only when the family POS tags are
noun-like. It inspects local tokens around the trigger for frames such as:

- modal + trigger
- `to` + trigger
- subject + trigger + object
- trigger + particle
- selected idiom or noun-of frames

If phrase preemption hits, the policy forces `abstain`. This keeps phrase/no-
winner behavior visible and separately testable instead of burying it inside
ordinary active-vs-shadow scoring.

### 9. Active Rescue

Active rescue is a narrow recovery path for near-tie abstains. It is deliberately
not a general permission to replace.

It can run only when:

- the primary decision abstained
- phrase preemption did not hit
- the primary margin is close enough to the active side
- a backup scorer is available

The backup pass uses `sense_label` evidence. It can rescue only if the backup
decision is `replace`, the backup winner is active, and the backup margin clears
the rescue floor.

This is a bounded false-abstain reducer. It is not allowed to override phrase
preemption.

### 10. Runtime Output

The helper returns a decision record with:

- `decision`
- `reason_codes`
- active score
- top shadow score
- score margin
- shadow winner sense id
- phrase preemption flag
- policy id and selection metadata

Today only `decision=replace` survives into the DOM apply path. `abstain` leaves
the original text visible. `soft_affordance` is reserved by the contract but is
not a current visible product behavior.

## Current Research Controls

Recent decision research deliberately decomposes the algorithm instead of asking
one opaque question.

### Current Incumbent Shape

The oldest control is:

```text
c = masked sentence
a = concatenated all-evidence text
s_i = concatenated all-evidence text for each shadow
score = TF-IDF cosine or sentence-transformer cosine depending on lane
decision = active_score - strongest_shadow_score
phrase = phrase override / phrase guard
```

This is a valid baseline, not a proof of optimality.

### Decision-Rule Matrix

`scripts/testing/semantic_decision_rule_matrix_en_es.py` compares:

- context representation
- sense/evidence representation
- scoring backend
- aggregation rule
- final YES/NO rule
- phrase handling
- negative controls
- threshold sensitivity
- source-family dropout
- discovery-vs-locked summaries

Important negative controls include:

- active-only source
- shadow-only source
- no-shadow competition
- shuffled active/shadow labels
- target-lemma-only evidence
- shuffled/reversed context and evidence for order probes

### Current No-Spend Findings

The active-score surface bakeoff found the first small fixed-source improvement:

- `definition_and_example_rows_separate`
- `max_row_score` or `top_k_mean`
- `0` harmful replacements
- `45` false abstains

The comparable current all-evidence control had:

- `1` harmful replacement
- `46` false abstains

The phrasing/order bakeoff added ordered n-grams, skip-grams, before/after slots,
surface frames, POS frames, heuristic dependency-role frames, negation/modal
signals, ordered evidence, template evidence, paraphrase evidence, and
shuffled/reversed controls.

That bakeoff did not beat the row-level evidence control:

- best row-level evidence control: `0` harmful, `45` false abstains
- best dependency-role approximation: `0` harmful, `55` false abstains
- best pure phrase/frame surfaces also over-abstained at roughly the same level

The context-conditioned evidence bakeoff then loaded the admitted WordNet
definition/example source batch and attached all `87` source rows. It tested
whether `a` should be chosen dynamically from source rows using masked-sentence,
window, before/after, surface-frame, or dependency-role selector contexts.

That first dynamic-`a` pass also did not beat the row-level evidence control:

- best prior separate-row max control: `0` harmful, `45` false abstains
- best source-plus-definition selector: `0` harmful, `53` false abstains
- best pure source-row selector: `0` harmful, `55` false abstains
- sentence-transformer source-row probes reduced false abstains but introduced
  harmful replacements, so they are diagnostic only

The source-row alignment audit explains the limitation of that result:

- `16/87` admitted rows contained the trigger at all
- `7/87` had a two-sided trigger frame
- only `5` families had both active and shadow selector-ready rows

The source-frame gap plan now converts that limitation into a source queue:

- `38` active/shadow sense slots
- `23` missing selector-ready active/shadow slots
- `97` planned candidate requests for trigger-bearing sentence-frame rows
- request rows are compatible with the existing spend-guarded generation runner
- prompts use sense labels and glosses only, not reviewed evaluation sentences

The first live aligned-frame run executed that queue under cost caps. It
generated `97` rows, admitted `36` after leakage/duplicate and
sense-discrimination filtering, and improved the source-admission ablation to
`0` harmful replacements and `1` false abstain on frozen v10 when merged into
the prior `87`-row source control. Active/shadow held-out v2 still had `1`
false abstain, so the result is a research improvement, not a promotion.

The first live run also showed that repeated prompts can collapse into
near-duplicate sentence frames. The planner now emits
`aligned-sentence-frame-v2` prompts with candidate-specific diversity frames.
After the v1 admitted rows were audited, only one selector-ready slot remained
missing. The v2 micro-run requested `5` board-shadow rows, admitted `3`, and
produced a `126`-row composite where all `19` families have both active and
shadow selector-ready rows.

The fully selector-ready v2 context-conditioned bakeoff improved the best
source-plus-definition selector from `0` harmful and `53` false abstains to
`0` harmful and `47` false abstains. The row-level definition/example control
still leads at `0` harmful and `45` false abstains. That means source-aligned
phrasing is helping, but the final dynamic selector is not yet the best
decision surface.

The next source-scope margin bakeoff corrected an important representation
problem: source rows were tested both as partial replacements for the incumbent
row-level evidence and as true additive evidence. The additive surface won:

- `definition_example_plus_source_rows_separate`
- combined LLM-v2 source rows plus the existing WordNet active-related
  reference rows
- `max_row_score`
- `0` harmful replacements
- `37` false abstains across frozen v10, source-heldout v2, phrase-heldout v2,
  and phrase challenge

The no-source definition/example row control on the same four suites was
`0` harmful and `44` false abstains. Source-heldout v2 improved from `0/17` to
`0/12`, and phrase suites stayed clean. The earlier source-plus-definition rows
looked weaker because they omitted the incumbent auxiliary/example rows; that
was a test-surface issue, not proof that source rows were unhelpful.

So this is not a global rejection of dynamic evidence selection. It says the
best current no-spend evidence surface is additive source evidence over the
row-level control, while context-conditioned row selection is still research
infrastructure rather than the leading candidate.

Interpretation:

- shallow frame labels over gloss text are not enough
- the first admitted source batch and first aligned-frame expansion are not
  enough to make dynamic row selection win by itself
- source rows are materially useful when they supplement, rather than replace,
  incumbent definition/example evidence
- order and frame are still worth testing, but they need source/example rows
  whose wording directly resembles runtime contexts
- the current best no-spend path is additive row-level evidence, not another
  threshold tweak

## What Is Not Set In Stone

The current production and research surfaces are intentionally malleable.

Open design choices include:

- the definition of `c`
  - sentence, window, masked view, phrase-risk view, multi-context bundle
- the definition of `a`
  - concatenated evidence, row set, source-weighted rows, examples only,
    context-conditioned rows
- the scoring function
  - lexical overlap, TF-IDF, sentence transformer, cross-encoder, entailment, or
    learned reranker
- aggregation
  - max row, top-k mean, agreement count, source-family agreement, calibrated
    row weighting
- phrase handling
  - phrase-first, phrase override, phrase-as-shadow, separate phrase classifier
- fallback behavior
  - abstain, legacy replace, or future visible soft affordance

None of those should be promoted because they feel elegant. Each needs a frozen
suite, held-out suite, negative controls, and a clear comparison against the
incumbent.

## Current Best Path Forward

The latest evidence points to this order:

1. Keep the production runtime policy unchanged while research continues.
2. Preserve the row-level evidence control as the no-spend incumbent.
3. Treat additive definition/example plus admitted source rows as the leading
   research candidate, while keeping production policy unchanged.
4. Expand aligned evidence rows, especially real examples and admitted source
   rows whose phrasing can match browser contexts.
5. Use the context-conditioned selector machinery as a research tool, but do
   not promote the current source-row result.
6. Mine the remaining active/shadow held-out false abstains and test whether
   each is a source row problem, a scorer/threshold problem, or an aggregation
   problem.
7. Build richer source-aligned examples and re-run the selector/order surfaces
   before changing runtime policy.
8. Reuse the existing matrix harness to compare those new `c` and `a` choices
   on frozen plus held-out suites.
9. Only after a candidate beats the incumbent, consider runtime policy changes
   and run the rulegen quality loop required by `AGENTS.md`.

Process rule:

- keep every active idea in
  `docs/test_inputs/semantic_decision_research_lanes_en_es.json`
- regenerate `docs/test_outputs/semantic_decision_research_lanes_latest.md`
  after changing a lane state
- never use a generic `done` state; distinguish idea, partial harness,
  unswept-ready harness, completed sweep, source-program lane, and parked
  second-lane candidate

This is not handcrafting every case if the promoted rule is general:

- source rows must come from repeatable source adapters or documented admission
  contracts
- phrase rules must be framed as reusable local constructions
- thresholds must be selected outside the exact cases used for final claims
- failure classes must be promoted into held-out coverage before being used as
  evidence of broad progress

## Promotion Criteria

A new setup is promotable only if it:

- keeps harmful replacements at `0` on frozen and held-out suites
- matches or improves false abstains versus the incumbent
- improves or preserves active/shadow/no-winner winner accuracy
- passes negative controls
- beats the incumbent outside the threshold-selection cases
- keeps phrase/no-winner behavior visible separately
- is simpler, or clearly more accurate enough to justify complexity

If no candidate beats the incumbent, that is still useful. It means the bottleneck
is probably source coverage, evidence representation, or evaluation coverage
rather than the final comparison formula.
