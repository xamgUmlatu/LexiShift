# SRS Curriculum Growth Notes

## Core idea
Grow the SRS set `S` based on what the user actually reads or writes. This lets the curriculum adapt to the user’s day‑to‑day interests and lifestyle, ensuring relevance and better retention.

## Why this matters
- **Personal relevance:** words the user encounters frequently are inherently meaningful.
- **Adaptive over time:** as a user’s topics change, the curriculum shifts naturally.
- **Lower friction:** less manual curation, better learning ROI.

## Baseline coverage (base rate)
Use a high‑frequency lexicon as the starting core. This provides strong early coverage and ensures that the initial SRS set is broadly useful even before personalization.

## Growth strategy (planned)
1) **User‑context growth**  
   - Add words observed in the user’s real text streams (reading/writing).  
   - Prioritize words that recur but are not mastered.
2) **Gradual coverage expansion**  
   - Expand beyond the core lexicon in controlled steps.  
   - Keep growth slow and steady to avoid overload.
3) **Personalized pacing**  
   - Add new items only when the user’s workload is manageable.  
   - Reduce new additions when due items are high.

## Open questions (to flesh out)
- Best method for “observed word” capture in extension + plugin contexts.
- Privacy and on‑device processing constraints.
- How to handle multi‑language text streams cleanly.
- How to define “recurring” vs “one‑off” exposures.
- The exact rules for when a word becomes eligible for S.

## Settings UX outline (early)
- **Configurable + portable:** learning settings should be editable in the GUI app, extension, and plugin, with export/import for portability across devices.
- **Coverage scalar:** represent S‑coverage as a single large scalar value with a slider UI (low → high coverage). This scalar drives how far beyond the base lexicon the system expands.
- **History log:** persist historical progress reports so users never lose their learning timeline (even if settings change).
- **Room for growth:** additional fine‑grained controls can be layered later without breaking the core model.
