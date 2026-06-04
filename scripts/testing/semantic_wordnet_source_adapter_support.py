from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from semantic_example_frame_source_adapter_support import (
    content_tokens,
    read_json_object,
    sense_target_tokens,
    text_list,
)

_POS_BY_CANONICAL = {
    "noun": "n",
    "verb": "v",
    "adjective": "a",
    "adj": "a",
    "adverb": "r",
    "adv": "r",
}


@dataclass(frozen=True)
class WordNetCandidate:
    sense_id: str
    synset_id: str
    pos: str
    sense_rank: int
    definition_texts: tuple[str, ...]
    example_texts: tuple[str, ...]
    members: tuple[str, ...]
    entry_sentences: tuple[str, ...]
    score: float
    overlap_tokens: tuple[str, ...]
    source_relation: str = "direct"
    relation_path: tuple[str, ...] = ()


@dataclass(frozen=True)
class WordNetIndex:
    entries_by_word: Mapping[str, Mapping[str, object]]
    synsets_by_id: Mapping[str, Mapping[str, object]]
    hyponyms_by_synset: Mapping[str, tuple[str, ...]]
    source_file_count: int

    @classmethod
    def load(cls, wordnet_dir: Path) -> "WordNetIndex":
        entries_by_word: dict[str, Mapping[str, object]] = {}
        synsets_by_id: dict[str, Mapping[str, object]] = {}
        hyponyms_by_synset: dict[str, list[str]] = {}
        source_file_count = 0
        if not wordnet_dir.exists():
            return cls(entries_by_word, synsets_by_id, {}, source_file_count)
        for path in sorted(wordnet_dir.glob("entries-*.json")):
            data = read_json_object(path)
            if not isinstance(data, Mapping):
                continue
            source_file_count += 1
            for word, entry in data.items():
                if isinstance(entry, Mapping):
                    entries_by_word[str(word).strip().lower()] = entry
        for path in sorted(wordnet_dir.glob("*.json")):
            if path.name.startswith("entries-") or path.name == "frames.json":
                continue
            data = read_json_object(path)
            if not isinstance(data, Mapping):
                continue
            source_file_count += 1
            for synset_id, synset in data.items():
                if isinstance(synset, Mapping):
                    synsets_by_id[str(synset_id).strip()] = synset
        for synset_id, synset in synsets_by_id.items():
            for hypernym_id in text_list(synset.get("hypernym")):
                hyponyms_by_synset.setdefault(hypernym_id, []).append(synset_id)
        return cls(
            entries_by_word,
            synsets_by_id,
            {
                synset_id: tuple(sorted(hyponym_ids))
                for synset_id, hyponym_ids in hyponyms_by_synset.items()
            },
            source_file_count,
        )

    def candidates_for_sense(
        self,
        *,
        trigger: str,
        sense: Mapping[str, object],
        min_link_score: float,
        include_related_hyponyms: bool = False,
        max_related_candidates: int = 0,
        related_hyponym_depth: int = 1,
    ) -> list[WordNetCandidate]:
        word_entry = self.entries_by_word.get(str(trigger or "").strip().lower())
        if not isinstance(word_entry, Mapping):
            return []
        pos_key = wordnet_pos(str(sense.get("canonical_pos") or ""))
        sections = [word_entry.get(pos_key)] if pos_key else []
        if not sections:
            sections = [value for value in word_entry.values() if isinstance(value, Mapping)]
        target_tokens = sense_target_tokens(sense, trigger=trigger)
        candidates: list[WordNetCandidate] = []
        for section in sections:
            if not isinstance(section, Mapping):
                continue
            senses = section.get("sense")
            if not isinstance(senses, Sequence) or isinstance(senses, (str, bytes)):
                continue
            for sense_rank, raw_sense in enumerate(senses, start=1):
                if not isinstance(raw_sense, Mapping):
                    continue
                synset_id = str(raw_sense.get("synset") or "").strip()
                synset = self.synsets_by_id.get(synset_id)
                if not isinstance(synset, Mapping):
                    continue
                candidate_tokens = candidate_tokens_for_wordnet_sense(
                    wordnet_sense=raw_sense,
                    synset=synset,
                    trigger=trigger,
                )
                overlap = tuple(sorted(target_tokens & candidate_tokens))
                score = len(overlap) / max(len(target_tokens), 1)
                if score < min_link_score:
                    continue
                candidates.append(
                    WordNetCandidate(
                        sense_id=str(raw_sense.get("id") or "").strip(),
                        synset_id=synset_id,
                        pos=pos_key,
                        sense_rank=sense_rank,
                        definition_texts=tuple(text_list(synset.get("definition"))),
                        example_texts=tuple(text_list(synset.get("example"))),
                        members=tuple(text_list(synset.get("members"))),
                        entry_sentences=tuple(text_list(raw_sense.get("sent"))),
                        score=round(score, 4),
                        overlap_tokens=overlap,
                    )
                )
        direct_candidates = sorted(
            candidates,
            key=_candidate_sort_key,
            reverse=True,
        )
        if not include_related_hyponyms or max_related_candidates <= 0:
            return direct_candidates
        return _with_related_hyponym_candidates(
            direct_candidates,
            synsets_by_id=self.synsets_by_id,
            hyponyms_by_synset=self.hyponyms_by_synset,
            trigger=trigger,
            max_related_candidates=max_related_candidates,
            max_depth=related_hyponym_depth,
        )


def candidate_tokens_for_wordnet_sense(
    *,
    wordnet_sense: Mapping[str, object],
    synset: Mapping[str, object],
    trigger: str,
) -> set[str]:
    parts = []
    for key in ("definition", "example", "members"):
        parts.extend(text_list(synset.get(key)))
    for key in ("sent", "subcat"):
        parts.extend(text_list(wordnet_sense.get(key)))
    return content_tokens(" | ".join(parts), trigger=trigger)


def _with_related_hyponym_candidates(
    direct_candidates: Sequence[WordNetCandidate],
    *,
    synsets_by_id: Mapping[str, Mapping[str, object]],
    hyponyms_by_synset: Mapping[str, tuple[str, ...]],
    trigger: str,
    max_related_candidates: int,
    max_depth: int = 1,
) -> list[WordNetCandidate]:
    related: list[WordNetCandidate] = []
    seen_synset_ids = {candidate.synset_id for candidate in direct_candidates}
    for parent in direct_candidates:
        queued = [
            (synset_id, 1, (parent.synset_id, synset_id))
            for synset_id in hyponyms_by_synset.get(parent.synset_id, ())
        ]
        related_for_parent = 0
        while queued and related_for_parent < max(0, int(max_related_candidates)):
            synset_id, depth, relation_path = queued.pop(0)
            if synset_id in seen_synset_ids:
                continue
            synset = synsets_by_id.get(synset_id)
            if not isinstance(synset, Mapping):
                continue
            seen_synset_ids.add(synset_id)
            related_for_parent += 1
            related.append(
                WordNetCandidate(
                    sense_id=f"{parent.sense_id}:hyponym:{synset_id}",
                    synset_id=synset_id,
                    pos=parent.pos,
                    sense_rank=parent.sense_rank,
                    definition_texts=tuple(text_list(synset.get("definition"))),
                    example_texts=tuple(text_list(synset.get("example"))),
                    members=tuple(text_list(synset.get("members"))),
                    entry_sentences=(),
                    score=round(float(parent.score) * 0.75, 4),
                    overlap_tokens=parent.overlap_tokens,
                    source_relation="direct_hyponym" if depth == 1 else "related_hyponym",
                    relation_path=relation_path,
                )
            )
            if depth < max(1, int(max_depth)):
                queued.extend(
                    (child_id, depth + 1, (*relation_path, child_id))
                    for child_id in hyponyms_by_synset.get(synset_id, ())
                    if child_id not in seen_synset_ids
                )
    return [*direct_candidates, *related]


def _candidate_sort_key(item: WordNetCandidate) -> tuple[object, ...]:
    strong_link = len(item.overlap_tokens) >= 2 or float(item.score) >= 0.25
    if strong_link:
        return (
            1,
            item.score,
            bool(item.example_texts),
            len(item.overlap_tokens),
            -item.sense_rank,
            item.synset_id,
        )
    return (
        0,
        -item.sense_rank,
        item.score,
        bool(item.example_texts),
        len(item.overlap_tokens),
        item.synset_id,
    )


def wordnet_pos(canonical_pos: str) -> str:
    return _POS_BY_CANONICAL.get(str(canonical_pos or "").strip().lower(), "")
