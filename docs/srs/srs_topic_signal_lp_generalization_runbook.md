# SRS Topic-Signal LP Generalization Runbook

Status: active planning runbook
Role: Cross-LP operating guide
Last updated: 2026-05-19
Last verified: 2026-05-19 en-es animals/plants audit and review-packet artifacts, food/cooking existing-signal audits, food/cooking overlay PoC, food/cooking full-source labels, SPALEX 10k food/cooking packet, focused tests, SRS quality harness, changed-file gate
Purpose: preserve reusable lessons from the en-es interest-topic source work so future language pairs do not repeat avoidable source, policy, and review mistakes
Source-of-truth: process guide only; pair-specific truth remains in the pair's source-readiness audits, policy files, generated review packets, tests, and current LP capability/resource code.

## Scope

This runbook applies when adding or improving SRS topic-preference evidence for a
new or existing language pair. It is currently grounded in the en-es
animals/plants and food/cooking passes, but the rules below are meant to
generalize to other LPs.

Do not use this file to claim that a topic family is implemented, default-on, or
verified for an LP. It describes the safe method for getting from source data to
reviewable topic candidates.

## Best Current Topic-Addition Flow

For each new user-facing topic or register preference, use the lightest version
of this flow that still creates evidence before product lift.

1. Define the product family first.
   Start from the user-facing intent, such as `food_cooking`, `animals`, or
   `medicine_health`. Do not let source labels become UX labels directly. If the
   topic is really a register/style preference, keep it on a separate internal
   axis even if UX shows it beside interests.

2. Confirm source and license posture.
   Record which target-language lemma frontier and lexical sources can be used.
   If a license requires manual external selection, keep the picker narrow and
   require the exact expected pack shape.

3. Audit coverage before promotion.
   Generate a read-only inventory with full candidate rows, tier/band counts,
   top source labels, and limitations. This is where we find whether the topic
   is source-ready, source-thin, or legally blocked.

4. Sample review packets from the real candidate universe.
   If the current frontier is small enough, review all candidates. If the topic
   has broader local source supply outside the current frontier, exclude already
   reviewed rows and sample a stratified full-source packet. Do not promote rows
   directly from the audit.

5. Store labels separately.
   Labels belong in `docs/test_inputs/`, not hand-edited generated outputs.
   Keep decisions structured as strong accept, light accept, wrong-topic reject,
   secondary/obscure reject, or uncertain.

6. Summarize precision and policy risk.
   Generate a compact precision summary by tier, confidence band, and source
   label. Use rejects as policy evidence: they show which source labels need
   guards before broad promotion.

7. Build a diagnostic overlay only after review.
   Strong accepted rows can become prototype overlay rows. Light accepted rows
   should carry lower membership or remain scalar-ready. Rejected rows must be
   excluded and counted.

8. Validate admission behavior separately.
   Run profile/admission preview checks to see whether the topic actually moves
   samples at useful proficiency bands. If it fails, distinguish scorer issues
   from source-depth issues.

9. Promote only with an explicit product contract.
   Runtime admission lift needs a versioned, provenance-bearing overlay or pack,
   rollback path, focused tests, and SRS quality gates. Default-on behavior is a
   later decision, not a consequence of a good audit.

This is the right current direction. The food/cooking pass is the strongest
evidence so far: the guarded broad full-source sample accepted `91 / 96` rows,
but the `5` rejects still exposed botanical/fodder overlap, zoological fish
terms, proper-name-first entries, and eater-not-food gloss matches before they
could reach product admission. The next product-scale check is the SPALEX 10k
food/cooking packet, not the 2k/current baseline alone.

## Topic Flow Variants

| Topic Type | Best Flow | Promotion Posture |
| --- | --- | --- |
| Source-ready utility topics | Taxonomy mapping -> broad depth audit -> small precision sample -> diagnostic profile lift. | Can move faster, but still needs review before default lift. |
| P0 enrichment topics | Custom signal policy -> full inventory -> stratified review packet -> precision summary -> diagnostic overlay. | Usually needs overlay or extra source data before product claims. |
| Register/style preferences | Separate register signal policy -> conservative review packet -> no default lift until precision is clear. | Start review-only; source tags are often noisy. |
| Legal/source-gated topics | Resolve allowed source/license first, then run the normal flow. | Do not surface as selectable until source path is legal. |
| New LP parity work | Source-readiness audit -> pair-local taxonomy/policy -> current-frontier packet -> full-source packet if needed. | Pair-specific evidence required; do not copy en-es status. |

## Reusable Lessons From en-es

1. Product taxonomy and source labels are separate layers.
   User-facing preferences should be product-owned families such as `animals`,
   `plants_nature`, `medicine_health`, or `food_cooking`. Source labels such as
   Wiktionary topics, categories, tags, gloss phrases, or external-list classes
   are evidence. They should map into product families through an explicit
   policy, not become UX labels directly.

2. Start with source-readiness before topic confidence.
   For each LP, first record row count, distinct non-empty lemmas, rank/order
   column, frequency column, POS coverage, topic/domain metadata coverage,
   licensing posture, and whether the source can support the desired frontier
   size. The en-es current CDE source was clean structurally but had no native
   topic/domain metadata, which shaped the whole enrichment path.

3. Keep frequency expansion, topic overlays, and veto readiness distinct.
   A larger frequency frontier can give more absolute candidates without making
   topic coverage dense. In the en-es SPALEX 10k pass, the frontier produced
   `172` animal and `138` plants/nature candidates, but coverage stayed sparse.
   That is useful for validation and overlay design, not proof that
   personalization is product-ready.

4. Treat high-coverage noisy channels as inventory until sampled.
   Tags and categories can cover most lemmas, but they mix true domains,
   grammar, register, maintenance labels, and broad parent topics. They are good
   mining inputs only after allowlisting, scoring, and review sampling.

5. Split adjacent product families early.
   `animals` and `plants_nature` should not be one catch-all nature topic. The
   split matters for user preference quality, source policy, confidence scoring,
   and review. Apply the same discipline to future pairs and topics that sound
   adjacent but have different user intent.

6. Use tiers rather than a single binary tag.
   The en-es policy uses Tier A explicit topics, Tier B primary-sense exact noun
   translations, Tier C allowlisted categories/tags, and Tier D narrow
   gloss/translation patterns. Other LPs can use the same tier idea even when
   the concrete source fields differ.

7. Primary-sense and POS checks prevent easy false positives.
   Exact translations are not automatically safe. Require primary-sense ordering
   and noun POS when the signal is a noun-topic label. Penalize secondary senses
   and ambiguous context labels so real but obscure senses do not look like
   dominant learner-facing topics.

8. Polysemy is a policy problem, not just a scoring problem.
   False positives can come from words like animal names used as tools, people,
   places, body parts, or idioms. For future LPs, expect to remove or penalize
   ambiguous exact triggers after sampling rather than assuming the first
   allowlist is final.

9. Topic overlap is allowed, but it must be evidence-specific.
   Food/cooking can legitimately overlap animals or plants/nature when a lemma
   has a culinary sense. That does not mean animal or plant evidence should
   imply food by default. Treat overlap as multiple source-backed memberships,
   and keep noisy category/gloss overlap review-required until sampled.

10. Rejected review labels are reusable policy evidence.
    The en-es food/cooking packet rejected `6` secondary/obscure senses and `3`
    wrong-topic rows. Those rejects showed that generic verbs, incidental gloss
    examples, and noisy overlap categories should stay discovery-only until a
    review label or stronger primary-sense evidence promotes them.

11. Audits must retain the full candidate inventory.
   Top previews are not enough for review or precision estimates. The audit
   artifact should keep all candidates plus small human-readable previews, so a
   review packet can sample the actual candidate universe.

12. Review packets are QA surfaces, not promotion artifacts.
    Every selected row should remain `pending_user_review` until explicitly
    labeled. Manual decisions should be structured and limited, for example
    `accept_strong_topic`, `accept_light_topic`, `reject_wrong_topic`,
    `reject_secondary_or_obscure_sense`, or
    `uncertain_needs_source_check`.

13. Sampling should be deterministic and stratified.
    Stable-hash selection by family, tier, band, review flag, and evidence
    source makes packets reproducible. Balance families before spending the
    review budget on large high-cardinality families, otherwise one family can
    crowd out another.

14. No raw-source download belongs in the repo by accident.
    If a license or size constraint requires local/manual source handling, keep
    raw source and rebuilt research packs outside tracked files unless the
    distribution policy explicitly allows committing them. Generated audit
    artifacts can record paths and source facts without bundling source data.

## Cross-LP Procedure

Use this sequence for each future LP topic-signal pass.

1. Define the target side and direction.
   Spell out `source->target`. SRS topic admission usually needs topic evidence
   on target-language lemmas, even when the LP key starts with a different source
   language.

2. Confirm source legality and install posture.
   Record license, redistribution limits, whether automatic installation is
   allowed, and whether external/manual pack selection is required.

3. Audit the base frequency source.
   Resolve lemma, rank/order, frequency, POS, and topic/domain columns. Count
   rows and distinct lemmas. Record frontier limits such as 2k, 5k, or 10k.

4. Inventory existing lexical-topic sources.
   For the target language, inspect trusted topics first, then review-only
   categories/tags, then glosses/translations/examples. Do not promote broad
   labels such as `sciences`, `natural_sciences`, `hobbies`, or maintenance
   categories without sampling.

5. Write a pair-local signal policy.
   Keep source-label allowlists, primary translations, ambiguous-context
   labels, and pattern rules in data. Prefer a file under `docs/test_inputs/`
   so the policy can be reviewed without editing executable code.

6. Generate a read-only audit.
   The audit may read local packs and generated research packs, but it should
   not mutate installed data, write overlays, or change admission behavior.
   Include full candidate inventory, counts by family/tier/band, top previews,
   review-required rows, limitations, and input paths.

7. Build a deterministic review packet.
   Sample from the full candidate inventory across family, tier, confidence
   band, review-required flag, and evidence source. Keep all manual labels
   pending.

8. Review and calibrate.
   Estimate precision by tier and source label. Tighten or remove noisy labels,
   add ambiguity penalties, and decide which bands are safe for a prototype
   overlay. Do not infer safety from aggregate counts alone.

9. Promote only through an overlay contract.
   Promotion should produce a sourced overlay or topic-membership artifact with
   provenance, confidence, source policy id, review state, and rollback path.
   Promotion is separate from audit and review-packet generation.

10. Run the right gates.
    Topic-signal data acquisition is SRS work. Run the SRS quality harness and
    focused tests. If a change touches rulegen scoring, candidate filtering, POS
    normalization, or LP tuning, also run the rulegen quality loop required by
    `AGENTS.md`.

## Suggested Artifact Names

Use pair-specific names rather than reusing `en_es` artifacts for other LPs:

| Artifact Type | Suggested Shape |
| --- | --- |
| source-readiness audit | `scripts/testing/srs_<topic>_source_audit_<pair>.py` |
| product taxonomy | `docs/test_inputs/srs_topic_preference_taxonomy_<pair>.json` |
| broad family-depth audit | `scripts/testing/srs_topic_family_depth_audit_<pair>.py` |
| broad family-depth output | `docs/test_outputs/srs_topic_family_depth_audit_<pair>_latest.{json,md}` |
| topic-signal policy | `docs/test_inputs/srs_<topic>_signal_policy_<pair>.json` |
| confidence audit output | `docs/test_outputs/srs_<topic>_signal_audit_<pair>_<source>_latest.{json,md}` |
| review packet script | `scripts/testing/srs_<topic>_signal_review_packet_<pair>.py` |
| review packet output | `docs/test_outputs/srs_<topic>_signal_review_packet_<pair>_<source>_latest.{json,md}` |
| focused tests | `core/tests/dev/test_srs_<topic>_signal_<purpose>_<pair>.py` |

The exact names can vary, but they must encode the LP and source family clearly
enough that later agents do not confuse one pair's evidence with another's.

## Promotion Readiness Checklist

A topic family is not ready for product admission lift in an LP until:

- the LP has a legally usable target-language frequency source at the required
  frontier size;
- POS and function-word controls are present or the missing coverage is
  explicitly bounded;
- topic evidence is mapped through a product-owned taxonomy and source policy;
- the audit retains a full candidate inventory;
- a deterministic review packet has sampled the candidate universe;
- review results show acceptable precision for the intended band or tier;
- agent/manual labels are stored as a separate input artifact rather than
  hand-editing generated review outputs;
- promotion writes a provenance-bearing overlay rather than mutating raw source
  rows silently;
- SRS quality and focused tests pass;
- any rulegen/POS/LP-tuning changes also pass the rulegen quality loop.

## Current en-es Evidence Trail

- Product taxonomy:
  `docs/test_inputs/srs_topic_preference_taxonomy_en_es.json`
- Broad family-depth audit:
  `docs/test_outputs/srs_topic_family_depth_audit_en_es_latest.md`
- Editable animals/plants policy:
  `docs/test_inputs/srs_animals_plants_signal_policy_en_es.json`
- Current CDE audit:
  `docs/test_outputs/srs_animals_plants_existing_signal_audit_en_es_current_latest.md`
- Editable food/cooking policy:
  `docs/test_inputs/srs_food_cooking_signal_policy_en_es.json`
- Current CDE food/cooking audit:
  `docs/test_outputs/srs_food_cooking_existing_signal_audit_en_es_current_latest.md`
- Current CDE food/cooking review packet:
  `docs/test_outputs/srs_food_cooking_signal_review_packet_en_es_current_latest.md`
- Current CDE food/cooking review labels:
  `docs/test_inputs/srs_food_cooking_signal_review_labels_en_es_current.json`
- Food/cooking source-capacity audit:
  `docs/test_outputs/srs_food_cooking_source_capacity_audit_en_es_latest.md`
- Food/cooking review and coverage plan:
  `docs/srs/srs_food_cooking_signal_review_and_coverage_plan_en_es.md`
- Current CDE food/cooking topic-overlay PoC:
  `docs/test_outputs/srs_food_cooking_topic_overlay_poc_en_es_current_latest.md`
- Full-source food/cooking review packet:
  `docs/test_outputs/srs_food_cooking_full_source_review_packet_en_es_latest.md`
- Full-source food/cooking review labels:
  `docs/test_inputs/srs_food_cooking_full_source_review_labels_en_es.json`
- Full-source food/cooking precision summary:
  `docs/test_outputs/srs_food_cooking_full_source_review_precision_summary_en_es_latest.md`
- SPALEX 10k food/cooking audit:
  `docs/test_outputs/srs_food_cooking_existing_signal_audit_en_es_spalex_10k_latest.md`
- SPALEX 10k food/cooking source-capacity audit:
  `docs/test_outputs/srs_food_cooking_source_capacity_audit_en_es_spalex_10k_latest.md`
- SPALEX 10k food/cooking review packet:
  `docs/test_outputs/srs_food_cooking_signal_review_packet_en_es_spalex_10k_latest.md`
- SPALEX 10k audit:
  `docs/test_outputs/srs_animals_plants_existing_signal_audit_en_es_spalex_10k_latest.md`
- SPALEX 10k review packet:
  `docs/test_outputs/srs_animals_plants_signal_review_packet_en_es_spalex_10k_latest.md`
- SPALEX 10k review labels:
  `docs/test_inputs/srs_animals_plants_signal_review_labels_en_es_spalex_10k.json`
- SPALEX 10k topic-overlay PoC:
  `docs/test_outputs/srs_animals_plants_topic_overlay_poc_en_es_spalex_10k_latest.md`

The topic-overlay PoC turns accepted review labels into a provenance-bearing
candidate overlay, injects strong accepted rows into `profile_topics`, and runs
the existing profile-bootstrap reranker. This is still diagnostic-only: it does
not install a pack, mutate helper state, or enable default runtime admission.

The food/cooking review packet currently covers the full conservative
candidate universe (`46 / 46`) because the set is small. Future LPs should use
that pattern when candidate count is reviewable, then switch to stratified
sampling only after broader source discovery makes the universe too large for
complete inspection.

The first food/cooking labels accepted `37 / 46` rows (`19` strong and `18`
light), which supports the audit policy as a precision screen. The current-CDE
source-capacity audit found `2,122` local Kaikki/Wiktionary food-signal lemmas
but only `46` inside the current CDE frequency frontier. For future LPs, this
is a general warning: topic recall may be bottlenecked by the admitted
frequency frontier even when the lexical source has enough topic candidates.

The food/cooking overlay PoC converts those `37` accepted labels into an
overlay candidate and excludes all `9` rejected labels. It moves reviewed
food/cooking hits in the existing profile-bootstrap preview by `+7`, proving
the reviewed-label-to-admission-preview path while keeping runtime admission
unchanged.

The guarded full-source food/cooking review packet then samples the broader
installed local candidate pool: `96` rows from `2,076` outside-current-frontier
food/cooking candidates. The guarded label pass accepts `91 / 96` rows (`54`
strong, `37` light) and rejects `5`. Future LPs should use this pattern when
the current frontier is too small: exclude already-reviewed frontier rows,
sample the broader installed source supply, and calibrate precision before
promoting a larger overlay or source policy.

The SPALEX 10k food/cooking audit is the current product-facing frontier check.
It finds `265 / 10,000` food/cooking candidates and a deterministic review
packet of `96` rows covering `62 / 62` evidence cells. Prior food/cooking labels
match `42 / 96` packet lemmas by lemma, but the packet is still pending review
and should not be treated as approved overlay data. This corrects the earlier
tendency to reason from the 2k/current baseline when evaluating product-scale
food/cooking behavior.

The precision summary adds the current decision point: the flow is directionally
right, and the next action should be narrow policy guards for the observed
false-positive classes rather than immediate broad promotion.
