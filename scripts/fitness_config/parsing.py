"""Strict reading of config text: UTF-8 only, valid JSON, no key set twice.

Pure: never raises. Every document the resolver reads -- a proposal on
stdin, a config file, a file in the chain -- goes through parse_document.
"""

from __future__ import annotations

import json

# (parsed value, None), or (None, reason). The reason completes a sentence
# whose subject is the document: f"Proposal {reason}", f"{path} {reason}".
Parsed = tuple[object, str | None]

NOT_UTF8 = "is not valid UTF-8 text"


class _RepeatedKey(Exception):
    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key


def _object_with_unique_keys(pairs: list[tuple[str, object]]) -> dict:
    """object_pairs_hook: build the object, refusing a key it has already seen."""
    unique: dict = {}
    for key, value in pairs:
        if key in unique:
            raise _RepeatedKey(key)
        unique[key] = value
    return unique


def _as_text(document: bytes | str) -> str | None:
    if isinstance(document, str):
        return document
    try:
        return document.decode("utf-8")
    except UnicodeDecodeError:
        return None


def parse_document(document: bytes | str) -> Parsed:
    """Parse JSON text (bytes must be UTF-8); a key set twice at any depth is an error."""
    text = _as_text(document)
    if text is None:
        return None, NOT_UTF8
    try:
        return json.loads(text, object_pairs_hook=_object_with_unique_keys), None
    except _RepeatedKey as repeated:
        return None, f'sets the key "{repeated.key}" more than once'
    except ValueError as exc:
        return None, f"is not valid JSON: {exc}"
