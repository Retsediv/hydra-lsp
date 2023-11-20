from __future__ import annotations

import logging
from collections import defaultdict
from typing import DefaultDict, Dict, List

from intervaltree import Interval, IntervalTree
from lsprotocol import types as lsp_types

logger = logging.getLogger(__name__)


References = DefaultDict[str, List[lsp_types.Location]]
Definitions = Dict[str, lsp_types.Location]
LocationToDefinition = Dict[lsp_types.Location, str]


class LocationKeyMap:
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

    def get(self, key: str):
        """
        Get a value from the config:
            1. Using a standard dict notation (e.g. config["data"])
            2. Using a dot notation (e.g. config["data.loader"])

        Will return None if the key is not found
        """
        if "." not in key:
            return self.config.get(key)

        # nested case
        value = self.config
        for k in key.split("."):
            value = value.get(k)

            if value is None:
                return None

        return value
