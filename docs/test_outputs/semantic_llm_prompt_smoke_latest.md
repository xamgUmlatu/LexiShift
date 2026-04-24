# en-es Semantic LLM Prompt Smoke

- Status: `ok`
- Generated: `2026-04-24T02:41:17Z`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Prompt spec: `semantic_prompt_spec_en_es_v10`
- Prompt version: `semantic_prompt_bakeoff_v3`
- Stage: `proxy`
- Selected model: `gpt-5.4-mini`
- Temperature: `0.2`

## Summary

- Active slots: `4`
- Prompt requests: `12`
- Target families covered: `6`
- Negative controls held out of prompting: `2`

## Slot Matrix

| Slot | Status | Target Families | Requests | Notes |
| --- | --- | ---: | ---: | --- |
| `cue_contrastive_general_v1` | `active` | 2 | 2 | Incumbent general cue slot from semantic_prompt_bakeoff_v2.<br>Use same-POS or ordinary competition families only. |
| `cue_contrastive_overlap_v1` | `active` | 2 | 2 | Challenger general cue slot for overlap-bearing discriminators.<br>Test whether shorter collocate fragments beat smoother semantic prose downstream. |
| `cue_cross_pos_frame_v1` | `active` | 4 | 4 | Incumbent cross-POS cue slot from semantic_prompt_bakeoff_v2.<br>Favor frame-sensitive noun-active vs verb-shadow cue generation. |
| `cue_cross_pos_overlap_v1` | `active` | 4 | 4 | Challenger cross-POS slot aimed at overlap-bearing frame fragments.<br>Test literal collocates and frame snippets against the incumbent meta-frame phrasing. |

## Sample Requests

### `en-es:proxy:cue-contrastive-general-v1:plant:fabrica`

- Slot: `cue_contrastive_general_v1`
- Family: `en-es:sentence-veto:plant:planta`
- Trigger: `plant`
- Active -> Candidate: `planta` -> `fábrica`
- Model: `gpt-5.4-mini` @ temperature `0.2`

System prompt:

```text
You generate one LexiShift semantic cue. Return compact JSON only. The cue must help choose the active Spanish target over one named competitor for one English trigger. Write short discriminative evidence text in English. Prefer concrete semantic or lexical discriminators over dictionary paraphrase. Do not generate phrase or idiom guidance, examples, explanations, markdown, or extra keys.
```

User prompt:

```text
Return a JSON object with exactly one key `items`. `items` must be an array with exactly one object.

That object may contain only:
- required `evidence_text`
- optional `confidence`

Do not repeat ids, targets, trigger text, or metadata; those are already fixed outside the model output.

Active sense:
- trigger: `plant`
- active target: `planta`
- sense label: `living plant`
- gloss: `living organism that grows in soil or water`

Competing candidate:
- candidate target: `fábrica`
- candidate POS: `noun`
- sense label: `industrial plant`
- gloss: `factory where goods are manufactured`

Family notes:
- `Useful same-POS cue calibration family. | Current hard row still misses plant:002, but the accepted overlay already rescues it. | The hard runtime row still misses plant:002.`

Task:
Write `evidence_text` in English, between 6 and 18 words, as one compact cue for the active sense only.

Rules:
- make it contrastive and specific
- do not merely restate the active label
- do not mention the candidate target by name
- do not write multiple cues or bullets
- do not mention phrases, idioms, or lexicalized expressions
- keep the cue useful for ordinary single-word sense discrimination

Optional:
- include `confidence` as a number from 0 to 1

Return JSON only.
```

Expected row preview:

```json
{
  "row_id": "en-es:proxy:cue-contrastive-general-v1:plant:fabrica:row",
  "relation_type": "anchor_cue",
  "trigger": "plant",
  "active_target": "planta",
  "candidate_target": "fábrica",
  "candidate_pos": "noun",
  "evidence_text": "<model-written cue text>",
  "prompt_slot": "cue_contrastive_general_v1",
  "input_ref": "en-es:proxy:cue-contrastive-general-v1:plant:fabrica",
  "metadata": {
    "family_id": "en-es:sentence-veto:plant:planta",
    "active_sense_id": "en-es:sentence-veto:plant:planta:active",
    "candidate_sense_id": "en-es:sentence-veto:plant:fabrica:shadow",
    "stage": "proxy",
    "family_archetype": "ordinary_weak_active_support"
  }
}
```

### `en-es:proxy:cue-contrastive-overlap-v1:plant:fabrica`

- Slot: `cue_contrastive_overlap_v1`
- Family: `en-es:sentence-veto:plant:planta`
- Trigger: `plant`
- Active -> Candidate: `planta` -> `fábrica`
- Model: `gpt-5.4-mini` @ temperature `0.2`

System prompt:

```text
You generate one LexiShift semantic cue optimized for downstream lexical overlap. Return compact JSON only. The cue must help choose the active Spanish target over one named competitor for one English trigger. Write a short overlap-bearing cue fragment in English. Prefer concrete collocates, nearby object words, modifiers, or anchor nouns likely to appear literally in real context. Avoid polished sentence summaries, dictionary phrasing, examples, markdown, or extra keys.
```

User prompt:

```text
Return a JSON object with exactly one key `items`. `items` must be an array with exactly one object.

That object may contain only:
- required `evidence_text`
- optional `confidence`

Do not repeat ids, targets, trigger text, or metadata; those are already fixed outside the model output.

Active sense:
- trigger: `plant`
- active target: `planta`
- sense label: `living plant`
- gloss: `living organism that grows in soil or water`

Competing candidate:
- candidate target: `fábrica`
- candidate POS: `noun`
- sense label: `industrial plant`
- gloss: `factory where goods are manufactured`

Family notes:
- `Useful same-POS cue calibration family. | Current hard row still misses plant:002, but the accepted overlay already rescues it. | The hard runtime row still misses plant:002.`

Task:
Write `evidence_text` in English, between 4 and 12 words, as one compact cue fragment for the active sense only.

Rules:
- prefer 1 to 3 strong anchor words or one short collocate phrase
- favor words likely to appear near the trigger in real sentences
- fragments are better than explanatory sentences
- avoid generic wrappers like `refers to`, `used for`, `something that`, or `kind of`
- do not mention the candidate target by name
- do not write multiple cues or bullets
- do not mention phrases, idioms, or lexicalized expressions
- prefer concrete noun, modifier, or object overlap over abstract category prose

Optional:
- include `confidence` as a number from 0 to 1

Return JSON only.
```

Expected row preview:

```json
{
  "row_id": "en-es:proxy:cue-contrastive-overlap-v1:plant:fabrica:row",
  "relation_type": "anchor_cue",
  "trigger": "plant",
  "active_target": "planta",
  "candidate_target": "fábrica",
  "candidate_pos": "noun",
  "evidence_text": "<model-written cue text>",
  "prompt_slot": "cue_contrastive_overlap_v1",
  "input_ref": "en-es:proxy:cue-contrastive-overlap-v1:plant:fabrica",
  "metadata": {
    "family_id": "en-es:sentence-veto:plant:planta",
    "active_sense_id": "en-es:sentence-veto:plant:planta:active",
    "candidate_sense_id": "en-es:sentence-veto:plant:fabrica:shadow",
    "stage": "proxy",
    "family_archetype": "ordinary_weak_active_support"
  }
}
```

### `en-es:proxy:cue-cross-pos-frame-v1:check:revisar`

- Slot: `cue_cross_pos_frame_v1`
- Family: `en-es:sentence-veto:check:cheque`
- Trigger: `check`
- Active -> Candidate: `cheque` -> `revisar`
- Model: `gpt-5.4-mini` @ temperature `0.2`

System prompt:

```text
You generate one LexiShift semantic cue for cross-POS ambiguity. Return compact JSON only. The cue must help choose the active Spanish target over one named competitor for one English trigger. Favor short frame-sensitive evidence in English: noun-vs-verb usage, nearby function words, determiner patterns, object or modifier cues, or document-like vs action-like framing. Do not generate phrase or idiom guidance, examples, explanations, markdown, or extra keys.
```

User prompt:

```text
Return a JSON object with exactly one key `items`. `items` must be an array with exactly one object.

That object may contain only:
- required `evidence_text`
- optional `confidence`

Do not repeat ids, targets, trigger text, or metadata; those are already fixed outside the model output.

Active sense:
- trigger: `check`
- active target: `cheque`
- canonical POS: `noun`
- sense label: `check as a bank payment slip`
- gloss: `written order directing a bank to pay money`

Competing candidate:
- candidate target: `revisar`
- candidate POS: `verb`
- sense label: `check or inspect carefully`
- gloss: `examine, verify, or inspect something carefully`

Family notes:
- `Held-out noun-active / verb-shadow residue remains unresolved after the accepted overlay. | The fixed-shadow competition set is already plausible, but check:002 still abstains on the strong row and on the accepted overlay. | The phrase probe keeps check:005 safely abstained, so the remaining gap is not a new phrase leak.`

Task:
Write `evidence_text` in English, between 6 and 18 words, as one compact cue for the active sense only.

Rules:
- prefer syntactic-frame or collocate signals that favor the active POS
- make the cue specific enough to separate noun-active from verb-shadow competition
- do not mention the candidate target by name
- do not write multiple cues or bullets
- do not mention phrases, idioms, or lexicalized expressions
- avoid generic dictionary prose that ignores POS framing

Optional:
- include `confidence` as a number from 0 to 1

Return JSON only.
```

Expected row preview:

```json
{
  "row_id": "en-es:proxy:cue-cross-pos-frame-v1:check:revisar:row",
  "relation_type": "anchor_cue",
  "trigger": "check",
  "active_target": "cheque",
  "candidate_target": "revisar",
  "candidate_pos": "verb",
  "evidence_text": "<model-written cue text>",
  "prompt_slot": "cue_cross_pos_frame_v1",
  "input_ref": "en-es:proxy:cue-cross-pos-frame-v1:check:revisar",
  "metadata": {
    "family_id": "en-es:sentence-veto:check:cheque",
    "active_sense_id": "en-es:sentence-veto:check:cheque:active",
    "candidate_sense_id": "en-es:sentence-veto:check:revisar:shadow",
    "stage": "proxy",
    "family_archetype": "cross_pos_weak_active_support"
  }
}
```

### `en-es:proxy:cue-cross-pos-overlap-v1:check:revisar`

- Slot: `cue_cross_pos_overlap_v1`
- Family: `en-es:sentence-veto:check:cheque`
- Trigger: `check`
- Active -> Candidate: `cheque` -> `revisar`
- Model: `gpt-5.4-mini` @ temperature `0.2`

System prompt:

```text
You generate one LexiShift semantic cue for cross-POS ambiguity, optimized for downstream lexical overlap. Return compact JSON only. The cue must help choose the active Spanish target over one named competitor for one English trigger. Write a short frame-like cue fragment in English. Prefer determiners, prepositions, nearby verbs or adjectives, object words, or document and action collocates that could literally appear near the trigger. Avoid grammar metalanguage, polished summaries, examples, markdown, or extra keys.
```

User prompt:

```text
Return a JSON object with exactly one key `items`. `items` must be an array with exactly one object.

That object may contain only:
- required `evidence_text`
- optional `confidence`

Do not repeat ids, targets, trigger text, or metadata; those are already fixed outside the model output.

Active sense:
- trigger: `check`
- active target: `cheque`
- canonical POS: `noun`
- sense label: `check as a bank payment slip`
- gloss: `written order directing a bank to pay money`

Competing candidate:
- candidate target: `revisar`
- candidate POS: `verb`
- sense label: `check or inspect carefully`
- gloss: `examine, verify, or inspect something carefully`

Family notes:
- `Held-out noun-active / verb-shadow residue remains unresolved after the accepted overlay. | The fixed-shadow competition set is already plausible, but check:002 still abstains on the strong row and on the accepted overlay. | The phrase probe keeps check:005 safely abstained, so the remaining gap is not a new phrase leak.`

Task:
Write `evidence_text` in English, between 4 and 12 words, as one compact frame fragment for the active sense only.

Rules:
- prefer literal frame snippets over explanations about grammar
- use overlap-bearing collocates such as nouns, adjectives, verbs, or prepositions that could appear in context
- short fragments beat full sentences
- avoid metalanguage like `preceded by a determiner`, `used as a noun`, or `signals a`
- avoid generic dictionary prose
- do not mention the candidate target by name
- do not write multiple cues or bullets
- do not mention phrases, idioms, or lexicalized expressions

Optional:
- include `confidence` as a number from 0 to 1

Return JSON only.
```

Expected row preview:

```json
{
  "row_id": "en-es:proxy:cue-cross-pos-overlap-v1:check:revisar:row",
  "relation_type": "anchor_cue",
  "trigger": "check",
  "active_target": "cheque",
  "candidate_target": "revisar",
  "candidate_pos": "verb",
  "evidence_text": "<model-written cue text>",
  "prompt_slot": "cue_cross_pos_overlap_v1",
  "input_ref": "en-es:proxy:cue-cross-pos-overlap-v1:check:revisar",
  "metadata": {
    "family_id": "en-es:sentence-veto:check:cheque",
    "active_sense_id": "en-es:sentence-veto:check:cheque:active",
    "candidate_sense_id": "en-es:sentence-veto:check:revisar:shadow",
    "stage": "proxy",
    "family_archetype": "cross_pos_weak_active_support"
  }
}
```
