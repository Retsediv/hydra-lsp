from __future__ import annotations

import logging
from collections import defaultdict
from typing import DefaultDict, Dict, List, Tuple

from intervaltree import Interval, IntervalTree
from lsprotocol import types as lsp_types

logger = logging.getLogger(__name__)


# References = DefaultDict[str, List[lsp_types.Location]]

# Tuple of (location, parent_key)
References = DefaultDict[str, List[Tuple[lsp_types.Location, str]]]
Definitions = Dict[str, lsp_types.Location]
LocationToDefinition = Dict[lsp_types.Location, str]


class LocationKeyMap:
    """
    Build an interval tree to map a location to a key.
    Also allows to find a key by non-exact location
    """

    __slots__ = ["file_to_tree"]

    def __init__(self):
        self.file_to_tree = defaultdict(IntervalTree)

    def add_location_key(self, position: lsp_types.Location, value: str) -> None:
        interval = Interval(
            (position.range.start.line, position.range.start.character),
            (position.range.end.line, position.range.end.character),
            value,
        )
        self.file_to_tree[position.uri].add(interval)

    def find_key_by_position(
        self, position: lsp_types.Position, doc_id: str
    ) -> str | None:
        logger.debug(
            f"Finding key for {position.line}-{position.character} in {doc_id}"
        )
        overlapping_intervals = self.file_to_tree[doc_id].at(
            (position.line, position.character)
        )

        for interval in overlapping_intervals:
            return interval.data

        return None

    def find_key_by_location(self, position: lsp_types.Location) -> str | None:
        return self.find_key_by_position(position.range.start, position.uri)


class HydraContext:
    """
    Stores: YAML keys and values pairs
    """

    __slots__ = ["config", "references", "definitions", "loc_to_definition"]

    def __init__(
        self,
        config: Dict,
        references: References = defaultdict(list),
        definitions: Definitions = {},
    ):
        self.config = config
        self.references = references
        self.definitions = definitions
        self.loc_to_definition = LocationKeyMap()
        for k, v in definitions.items():
            self.loc_to_definition.add_location_key(v, k)

    def set(self, key: str, value: str):
        raise NotImplementedError

    def get(self, key: str, parent_key: str = "") -> str | None:
        """
        Get a value from the config:
            1. Using a standard dict notation (e.g. config["data"])
            2. Using a dot notation (e.g. config["data.loader"])
            3. Using a relative dot notation (e.g. key = ".loader" or key = "..tag")

        Will return None if the key is not found
        """

        logger.debug(f"Getting {key} with parent {parent_key}")

        # This is to handle the case when the key is relative to the parent
        # e.g. key = ".loader", parent_key = "data" -> key = "data.loader"
        # or key = "..tag", parent_key = "data.loader" -> key = "data.tag"
        if parent_key and key.startswith("."):
            j = 1  # skip the first dot
            # key = key[1:]  # skip the first dot

            parts = parent_key.split(".")
            for j in range(1, len(key)):
                c = key[j]
                if c == "." and parts:
                    parts.pop()
                else:
                    break

            parts.append(key[j:])
            key = ".".join(parts)
            return self.get(key)

        if "." not in key:
            return self.config.get(key)

        # nested case
        value = self.config
        for k in key.split("."):
            value = value.get(k)

            if value is None:
                return None

        return value
