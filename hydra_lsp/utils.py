from __future__ import annotations

import collections
import logging

from lsprotocol.types import MarkupContent, MarkupKind

logger = logging.getLogger(__name__)


def to_markdown_content(value: str, lang: str = "json") -> MarkupContent:
    """Return the MarkupContent with Markdown kind."""
    return MarkupContent(kind=MarkupKind.Markdown, value=f"```{lang}\n{value}\n```")


def yaml_get_var_prefix(line: str, pos: int = 0) -> str | None:
    """
    Assume that the line should be in the following format:
        var: something ${va<cursor>xx} bbb
    it will return "va"
    """
    start = line.rfind("${", 0, pos)
    if start == -1:
        return None

    return line[start + len("${") : pos]


def yaml_get_key(line: str, position: int) -> str | None:
    """
    Get key from the yaml value (if exists).
    convert the line like this:
        "foo: foo ${bar}/something else" -> "bar"
    given the position of the cursor (in this case, it's on the "b", "a" or "r" letter)
    """
    start = line.find(":")
    if start == -1:
        return None

    if position > start:
        return None

    return line[:start].strip()


def yaml_get_variable_name(line: str, position: int) -> str | None:
    """
    Get variable name from the yaml value (if exists).
    convert the line like this:
        "foo: foo ${bar}/something else" -> "bar"
    given the position of the cursor (in this case, it's on the "b", "a" or "r" letter)
    """
    start = line.find(":")
    if start == -1:
        return None

    first_part_index = line.rfind("${", start, position)
    if first_part_index == -1:
        return None

    second_part_index = line.find("}", position + 1)
    if second_part_index == -1:
        return None

    return line[first_part_index + 2 : second_part_index]


def deep_update(source, overrides):
    """
    Update a nested dictionary or similar mapping.
    Modify ``source`` in place.
    """
    for key, value in overrides.items():
        if isinstance(value, collections.abc.Mapping) and value:
            source[key] = deep_update(source.get(key, {}), value)
        else:
            source[key] = value
    return source
