from __future__ import annotations

import ast
import base64
import json
import zlib
from pprint import pformat

from lexishift_core.settings import settings_from_dict, settings_to_dict
from lexishift_core.storage import VocabDataset, dataset_from_dict, dataset_to_dict


def export_dataset_json(dataset: VocabDataset, *, indent: int = 2, sort_keys: bool = True) -> str:
    data = dataset_to_dict(dataset)
    return json.dumps(data, indent=indent, sort_keys=sort_keys)


def import_dataset_json(payload: str) -> VocabDataset:
    data = json.loads(payload)
    return dataset_from_dict(data)


def export_dataset_python(dataset: VocabDataset, *, var_name: str = "VOCAB_DATASET") -> str:
    data = dataset_to_dict(dataset)
    body = pformat(data, width=100, sort_dicts=True)
    return f"{var_name} = {body}\n"


def import_dataset_python(payload: str, *, var_name: str = "VOCAB_DATASET") -> VocabDataset:
    tree = ast.parse(payload)
    value = _extract_literal_value(tree, var_name=var_name)
    data = ast.literal_eval(value)
    if not isinstance(data, dict):
        raise ValueError("Expected a dict literal for dataset import.")
    return dataset_from_dict(data)


def export_dataset_code(dataset: VocabDataset) -> str:
    data = dataset_to_dict(dataset)
    payload = json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")
    compressed = zlib.compress(payload, level=9)
    return _encode_code(compressed)


def import_dataset_code(code: str) -> VocabDataset:
    compressed = _decode_code(code)
    payload = zlib.decompress(compressed)
    data = json.loads(payload)
    return dataset_from_dict(data)


def export_app_settings_json(settings, *, indent: int = 2, sort_keys: bool = True) -> str:
    data = settings_to_dict(settings)
    return json.dumps(data, indent=indent, sort_keys=sort_keys)


def import_app_settings_json(payload: str):
    data = json.loads(payload)
    return settings_from_dict(data)


def export_app_settings_python(settings, *, var_name: str = "APP_SETTINGS") -> str:
    data = settings_to_dict(settings)
    body = pformat(data, width=100, sort_dicts=True)
    return f"{var_name} = {body}\n"


def import_app_settings_python(payload: str, *, var_name: str = "APP_SETTINGS"):
    tree = ast.parse(payload)
    value = _extract_literal_value(tree, var_name=var_name)
    data = ast.literal_eval(value)
    if not isinstance(data, dict):
        raise ValueError("Expected a dict literal for app settings import.")
    return settings_from_dict(data)


def export_app_settings_code(settings) -> str:
    data = settings_to_dict(settings)
    payload = json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")
    compressed = zlib.compress(payload, level=9)
    return _encode_code(compressed)


def import_app_settings_code(code: str):
    compressed = _decode_code(code)
    payload = zlib.decompress(compressed)
    data = json.loads(payload)
    return settings_from_dict(data)


def _extract_literal_value(tree: ast.AST, *, var_name: str) -> ast.AST:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == var_name:
                    return node.value
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Dict):
            return node.value
    raise ValueError(f"Expected a dict literal or assignment to {var_name}.")


def _encode_code(payload: bytes) -> str:
    encoded = base64.urlsafe_b64encode(payload).decode("ascii")
    return encoded.rstrip("=")


def _decode_code(code: str) -> bytes:
    trimmed = "".join(code.split())
    padding = "=" * (-len(trimmed) % 4)
    return base64.urlsafe_b64decode(trimmed + padding)
