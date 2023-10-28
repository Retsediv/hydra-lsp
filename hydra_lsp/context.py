import logging
from collections import defaultdict
from typing import DefaultDict, Dict, List

from lsprotocol import types as lsp_types

logger = logging.getLogger(__name__)

References = DefaultDict[str, List[lsp_types.Location]]
Definitions = Dict[str, lsp_types.Location]


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