# Language Difficulty And Proficiency Model

Status: active proposal
Role: planning / cross-cutting design
Purpose: define a shared conceptual model for lexical difficulty, learner proficiency, and post-hoc group discovery so future rulegen routing and SRS onboarding can reuse the same vocabulary without collapsing distinct ideas into one score.
Last updated: 2026-03-29
Last verified: 2026-03-29
Source-of-truth: planning doc only; executable truth still lives in benchmark artifacts, SRS planner code, and future placement/profile work.

## Why This Exists

LexiShift has two future needs that look similar but are not the same:

1. choose better rulegen behavior for different kinds of words
2. let users start the SRS journey at an appropriate point in the vocabulary continuum for their language proficiency and preferences

Both involve ideas like:

- easy vs hard words
- beginner vs advanced users
- common vs technical vocabulary

But those are different axes.

If we do not separate them now, later systems will end up reusing one overloaded `difficulty` number for:

- lexical ambiguity
- pedagogical difficulty
- SRS scheduling state
- user proficiency

That would be a mistake.

## Core Separation

There are at least four distinct concepts.

### 1. Intrinsic lexical difficulty

This is difficulty caused by the word itself under a given pair/resource setup.

Examples:

- high polysemy
- phrase-sensitive behavior
- slang/register leakage
- many competing candidate senses
- broad-vs-technical competition
- weak reverse-check specificity

This is the main difficulty that matters for rulegen profile selection.

It is not about the learner.

### 2. Learner-facing vocabulary difficulty

This is how difficult a word is likely to be for a human learner at a given stage.

Examples:

- very common concrete nouns are often easy for a beginner
- highly abstract high-frequency function-like words may be hard for a beginner
- narrow technical nouns may be easy for an advanced learner but poor onboarding material

This depends on the user.

The same word can be:

- too hard for a beginner
- appropriate for an intermediate learner
- trivial for an advanced learner

### 3. User proficiency

This is a property of the user or profile, not of the word.

Examples:

- self-reported level
- placement result
- known-lemma coverage
- reading/listening experience
- prior SRS history

This should be modeled as external context.

It must not be inferred only from the word.

### 4. Observed SRS difficulty

This is the learner's demonstrated difficulty with a specific item over time.

Examples:

- low retention
- repeated `again` / `hard`
- low stability
- high FSRS difficulty

This is not lexical difficulty and not proficiency.

It is item-specific observed learning difficulty after exposure.

## Important Consequence

The system should **not** try to collapse everything into one number.

Instead, keep at least these separate:

- lexical / rulegen difficulty
- learner proficiency
- observed SRS difficulty
- chosen curriculum target region or band label

That separation keeps future systems explainable.

## Why Beginner Vocabulary Often Feels Harder For Rulegen

The intuition that beginner-level vocabulary can be harder for rulegen is directionally correct.

The reason is usually not “beginner” itself.

It is that many very common words are also:

- highly polysemous
- idiomatic
- register-sensitive
- broad everyday words with many overlapping senses
- short lexical items with many noisy candidates

Examples from current `en-es` pressure regions:

- `cuenta`
- `red`
- `señal`
- `móvil`
- `hasta`
- `según`
- `acabar`
- `coger`
- `sacar`

By contrast, many medium or advanced words are narrower and therefore easier for rulegen:

- `nodo`
- `servidor`
- `aplicación`
- `tráfico`

So the practical rule is:

- beginner vocabulary and lexical difficulty correlate often
- but they are not identical

This matters because future routing should look at lexical ambiguity directly, not only at frequency rank or a beginner tag.

## Continuous Internal Model

The internal system should be modeled as a continuous feature space, not as a small set of rigid vocabulary buckets.

That means:

- words/items live in a multi-dimensional feature space
- user/profile state also lives in a feature space
- admission is a continuous fit/scoring problem

This is the right underlying model for:

- proficiency matching
- explicit topic preferences
- implicit interest signals
- later observed learning behavior

The system may still expose labels like:

- beginner
- intermediate
- advanced

but those should be treated as:

- soft summaries
- reporting labels
- optional UI abstractions

not as the true underlying storage primitive.

### Why this matters

A learner just above some UI boundary should not suddenly lose access to all words “below” that boundary.

The planner should still be able to admit:

- easier core words
- center-fit words
- slightly stretching words

at the same time, with different continuous scores.

## Shared Feature Model

The future system should carry a structured feature model, not a single scalar difficulty score.

### A. Lexical / rulegen-side features

Examples:

- frequency rank / percentile
- candidate row count
- surviving definition bucket count
- top1 vs top2 score gap
- reverse-hit count and spread
- exact-hit specificity / ambiguity
- phrase pressure
- variant pressure
- marker-family pressure
- register/slang pressure
- gloss-structure signals

These are the main inputs for rulegen profile selection.

### B. User / profile-side features

Examples:

- self-reported proficiency
- placement-estimated proficiency
- known-lemma coverage estimate
- explicit topic preferences
- implicit topic/interest weights
- target content mode
- pair objective

These are external context features.

They should be editable and explainable.

### C. Observed learning features

Examples:

- SRS stability
- SRS difficulty
- feedback rates
- exposure counts
- retention trend

These belong to the SRS layer and should inform future item serving and onboarding, not be confused with lexical ambiguity.

## Admission Should Be A Continuous Utility Function

The planner should not ask:

- "which rigid level band does this word belong to?"

It should ask:

- "how well does this word fit this user right now?"

At a high level, future admission should behave like:

`score(user, item) = proficiency_fit + challenge_fit + preference_affinity + coverage_gain - lexical_risk - redundancy + exploration_bonus`

The exact formula can evolve, but the shape should stay:

- continuous
- decomposed
- explainable

### Preference signals are first-class

Admission should depend heavily on:

- explicit preferences:
  - animals
  - games
  - news
- implicit interests:
  - browsing/reading habits
  - content interactions
  - later other behavioral signals

Important rule:

- the admission layer should consume derived topic/interest weights
- it should not depend directly on raw browsing history

### Guardrails still matter

Preferences should strongly bias the admitted set, but should not fully collapse it into a narrow bubble.

The selector should preserve room for:

- core/general vocabulary
- breadth/diversity
- moderate exploration

## How To Discover Good Groups After The Sweep

The goal is not to hand-label everything up front as:

- beginner-safe
- technical
- phrase-heavy

Those labels are useful for human discussion, but they should not be the source of truth.

The right framing is:

- every word gets a trait vector
- every frozen profile gets an outcome on that word
- we want to learn a policy from traits to best profile

### Preferred early method: shallow policy learning

Best current candidate:

- freeze a small profile bank
- compute per-word trait vectors
- compute per-profile reward for each word
- fit a shallow decision tree or policy tree

Why this is the best early method:

- interpretable
- naturally discovers groups after the fact
- chooses the number of groups by tree size / validation rather than by hand
- directly optimizes profile choice, not just word similarity

This is the clearest answer to “how do we find the best K groups?”

`K` is effectively the number of leaves.

### Good secondary method: outcome-space clustering

Alternative:

- cluster words by their per-profile performance fingerprints
- then fit a simple explainer (tree or rule list) over the trait vectors

This is useful when you want to discover latent groups before naming them.

### Good complementary method: subgroup discovery

This means searching for compact interpretable slices like:

- high-frequency + high reverse ambiguity + phrase-heavy
- computing-marked + adjective-vs-noun competition

This is useful for human understanding and later rule design.

### Later method: contextual bandit or mixture-of-experts

These are more powerful but later-stage techniques.

They are only appropriate after:

- the benchmark is broader
- the profile bank is stable
- simpler interpretable methods stop being enough

### Methods to avoid first

- plain clustering on words alone
- opaque neural routing
- hand-maintained per-word tags as the routing source of truth
- a giant manually defined taxonomy before enough evidence exists

## Choosing The Number Of Groups

We do not need to decide a rigid number up front.

The right choice should be driven by:

- validation performance
- stability across reruns / later-added cases
- minimum support per group
- interpretability
- whether groups generalize to held-out cases

Practical constraints for the first routing model:

- keep the router shallow
- require minimum case counts per leaf
- penalize tiny leaves
- reject groupings that only improve a handful of benchmark cases

## What This Means For Rulegen

For rulegen, the intended long-term flow is:

1. freeze a small profile bank
2. expand the benchmark suite
3. emit runtime-computable trait vectors
4. measure profile outcomes per case
5. learn an interpretable router from traits to profile
6. only then consider live runtime routing

Near-term implication:

- keep expanding the benchmark in hard pressure regions
- keep the frozen profile bank stable long enough to compare outcomes cleanly
- use the benchmark to discover whether profile-sensitive top1 splits grow beyond one-off cases like `móvil`

## What This Means For SRS Onboarding

The same conceptual model also matters for onboarding and progression.

Desired product behavior:

- a user with real prior proficiency should not be forced to start from absolute beginner vocabulary
- an intermediate learner should be able to start around the appropriate region of the vocabulary continuum
- an advanced learner should be able to bias toward advanced/core-technical vocabulary

This is **not** a rulegen problem by itself.

It is an SRS/profile-planning problem.

### Recommended SRS framing

Keep these separate:

- user proficiency estimate
- target challenge region
- optional user-facing band label
- observed SRS difficulty after admission

Then the onboarding/planning layer can choose:

- where in the vocabulary continuum the user should begin
- how broad or technical the initial admitted set should be
- how aggressively to grow from that point

### Recommended sources for proficiency

Examples:

- self-report
- placement test
- known-lemma quick check
- early SRS performance trend

### Recommended output

Do not output only one scalar like `difficulty=0.63`.

Prefer a small profile/context payload such as:

- proficiency estimate
- target challenge center
- target challenge spread / tolerance
- optional derived label for explanation
- confidence in that estimate
- optional pair-specific bias

That is more useful for both UI and planning.

## Shared Principle Across Rulegen And SRS

Use:

- explicit observable features
- interpretable grouping/routing
- external user-context inputs when appropriate

Do not use:

- hidden hand tags as the main source of truth
- one overloaded difficulty number for all decisions

## Explicit User-Facing Difficulty Concept

User-facing difficulty should be treated as its own product concept.

This is the idea the UI will eventually expose when a user says something like:

- "I am roughly intermediate"
- "Start me around intermediate vocabulary"
- "Do not make me start from absolute beginner material"

This concept overlaps with lexical frequency and lexical ambiguity, but it is not reducible to either one.

### What it is

User-facing difficulty should mean:

- how appropriate a word or item is for a learner at a given point in their journey
- how suitable a region of the vocabulary continuum is as a starting point or growth target
- how aggressively onboarding should bias toward broad/core vs narrower/advanced vocabulary

### What it is not

It should **not** mean:

- the intrinsic ambiguity of a word for rulegen
- the learner's observed SRS struggle on that specific item
- a hidden synonym for user proficiency

### Why this matters

An intermediate learner may want:

- mostly intermediate/core vocabulary
- not absolute beginner vocabulary from rank 1 upward
- not highly specialized technical vocabulary either

That requires the planner to choose an initial target region that matches the learner, even if:

- the learner has never used SRS in LexiShift before
- the learner has zero local item history

So the future SRS system needs a target-region decision that can operate before observed SRS difficulty exists.

### Recommended framing

Keep these as separate fields in future planning and product design:

- `user_proficiency_estimate`
- `target_challenge_center`
- `target_challenge_spread`
- `target_vocabulary_band_label` (optional, derived)
- `lexical_rulegen_difficulty`
- `observed_srs_difficulty`

The onboarding/planner layer can then decide:

- where the learner should start
- how wide the initial band should be
- how quickly to widen it

without confusing that decision with rulegen routing.

## Recommended User-Facing Control Surface

The recommended first UI is:

- a scalar difficulty/challenge control
- user preference controls
- a "generate sample words" preview button

This is better than forcing the user into a small rigid set of named levels.

### Why the preview matters

The preview solves the main UX problem directly:

- instead of trusting a label like `intermediate`
- the user can inspect a few representative candidate words

That lets the user judge:

- whether the difficulty feels right
- whether the topical flavor feels right
- whether the set is too broad, too niche, too easy, or too hard

### Preview design principle

The sample words should come from the same continuous admission logic that would actually admit words later.

That means the preview should be:

- representative
- diversity-aware
- lightly sampled, not a hard-coded canned list

### Recommended first interaction model

1. user moves a scalar challenge slider
2. user sets explicit preferences
3. system includes any available implicit interest weights
4. user clicks `generate sample words`
5. planner returns a small sample plus compact reasons

Example compact reasons:

- good fit for your current level
- matches your animal interest
- slightly stretching but still high-value
- core/common vocabulary

## Recommended Near-Term Repository Plan

### 1. Rulegen side

- continue suite expansion in the hard pressure regions
- keep rerunning the frozen profile bank
- keep the routing work offline and analytical for now

### 2. Difficulty/proficiency modeling

- treat difficulty as a cross-cutting design axis
- keep lexical difficulty, learner proficiency, and observed SRS difficulty separate in docs and schemas

### 3. SRS side

- later add a richer proficiency / difficulty-band model to onboarding and profile planning
- do not make that depend on rulegen routing being finished first

### 4. Shared analysis path

- use the same structured vocabulary around difficulty in:
  - rulegen routing analysis
  - SRS onboarding/profile planning
  - future placement/proficiency UX
- prefer post-hoc group discovery from observed outcomes over rigid hand-tag systems
- when a compact group model is needed, start with:
  - shallow policy trees
  - outcome-space clustering plus a simple explainer

## Related Docs

- `docs/rulegen/trait_conditioned_rulegen_profiles.md`
- `docs/developer/rulegen_workstream_execution_order.md`
- `docs/srs/srs_profile_schema.md`
- `docs/srs/srs_onboarding_and_placement_schema.md`
- `docs/srs/srs_selector_technical.md`
- `docs/reference/glossary.md`
