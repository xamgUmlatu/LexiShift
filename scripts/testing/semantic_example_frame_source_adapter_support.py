from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Mapping, Sequence

WORD_RE = re.compile(r"[a-z]+")
SLUG_RE = re.compile(r"[^a-z0-9]+")
STOPWORDS = frozenset(
    """
    a about above after again against all am an and any are as at be because been before being
    below between both but by can could did do does doing down during each few for from further
    had has have having he her here hers herself him himself his how i if in into is it its itself
    just me more most my myself no nor not of off on once only or other our ours ourselves out over
    own same she should so some such than that the their theirs them themselves then there these
    they this those through to too under until up very was we were what when where which while who
    whom why will with you your yours yourself yourselves something someone somebody anything any
    someth someon anyth
    """.split()
)


def all_family_dataset(
    dataset_payload: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, str]]:
    family_roles = {
        str(family.get("family_id") or "").strip(): "target"
        for family in dataset_payload.get("families", ())
        if isinstance(family, Mapping) and str(family.get("family_id") or "").strip()
    }
    payload = dict(dataset_payload)
    payload["families"] = [
        dict(family)
        for family in dataset_payload.get("families", ())
        if isinstance(family, Mapping)
    ]
    return payload, family_roles


def family_key_dataset(
    dataset_payload: Mapping[str, object],
    *,
    family_keys: Sequence[str],
    default_family_keys: Sequence[str] = (),
) -> tuple[dict[str, object], dict[str, str]]:
    keys = {str(key or "").strip() for key in family_keys if str(key or "").strip()}
    if not keys:
        keys = {str(key or "").strip() for key in default_family_keys if str(key or "").strip()}
    payload = dict(dataset_payload)
    payload["families"] = [
        dict(family)
        for family in dataset_payload.get("families", ())
        if isinstance(family, Mapping) and str(family.get("family_id") or "").strip() in keys
    ]
    return payload, {
        str(family.get("family_id") or "").strip(): "target"
        for family in payload["families"]
        if isinstance(family, Mapping)
    }


def sense_hint(
    sense: Mapping[str, object],
    *,
    note: str,
    metadata: Mapping[str, object] | None = None,
) -> dict[str, object]:
    hint: dict[str, object] = {
        "provider": "sentence_veto_dataset",
        "locator_kind": "sense_id",
        "target_key": sense_id(sense),
        "canonical_pos": str(sense.get("canonical_pos") or "").strip(),
        "note": note,
    }
    if metadata:
        hint["metadata"] = dict(metadata)
    return hint


def sense_target_tokens(sense: Mapping[str, object], *, trigger: str) -> set[str]:
    evidence_views = sense.get("evidence_views")
    parts = [
        str(sense.get("target_lemma") or ""),
        str(sense.get("canonical_pos") or ""),
    ]
    if isinstance(evidence_views, Mapping):
        parts.extend(
            str(evidence_views.get(key) or "")
            for key in (
                "sense_label",
                "gloss_text",
                "sense_gloss_bundle",
                "all_evidence_text",
            )
        )
    return content_tokens(" | ".join(parts), trigger=trigger)


def content_tokens(text: str, *, trigger: str) -> set[str]:
    trigger_token = stem(str(trigger or "").lower())
    tokens = {stem(token) for token in WORD_RE.findall(str(text or "").lower())}
    return {
        token
        for token in tokens
        if token and len(token) > 2 and token not in STOPWORDS and token != trigger_token
    }


def stem(token: str) -> str:
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 4 and token.endswith("es"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def text_list(value: object) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item).strip() for item in value if str(item or "").strip()]
    text = str(value or "").strip()
    return [text] if text else []


def bucket_for_relation(relation_type: str) -> str:
    return "active" if relation_type == "anchor_cue" else "shadow"


def sense_id(sense: Mapping[str, object]) -> str:
    return str(sense.get("sense_id") or "").strip()


def slug(value: object) -> str:
    text = str(value or "").strip().lower()
    return SLUG_RE.sub("-", text).strip("-") or "row"


def read_json_object(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
