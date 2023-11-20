from __future__ import annotations

import logging
import os
import re
from collections import defaultdict
from typing import Dict, Generator, List

import ruamel.yaml
from lsprotocol import types as lsp_types
from pygls.server import LanguageServer
from ruamel.yaml.main import (
    BlockEndToken,
    BlockEntryToken,
    BlockMappingStartToken,
    BlockSequenceStartToken,
    DocumentStartToken,
    FlowEntryToken,
    FlowMappingEndToken,
    FlowMappingStartToken,
    FlowSequenceEndToken,
    FlowSequenceStartToken,
    KeyToken,
    ScalarToken,
    StreamStartToken,
    ValueToken,
)
from ruamel.yaml.tokens import Token

from hydra_lsp.context import Definitions, HydraContext, References
from hydra_lsp.utils import deep_update

logger = logging.getLogger(__name__)


def assert_type_is_any_of(t, types, msg: str = "Invalid type"):
    assert any([t is _t for _t in types]), msg


def append_to_base_key(base_key: str, key: str):
    return f"{base_key}.{key}" if base_key else key


def remove_from_base_key(base_key: str):
    if "." not in base_key:
        return ""

    return base_key.rsplit(".", 1)[0] if base_key else ""


def get_file(ls: LanguageServer | None, uri: str) -> List[str]:
    if ls is not None:
        doc = ls.workspace.get_document(uri)
        return doc.lines

    uri = uri[len("file://") :] if uri.startswith("file://") else uri
    with open(uri) as f:
        f.seek(0)
        data = f.readlines()

    return data


class ConfigParser:
    """Load a Hydra YAML config file, looks for _defaults and loads respective files"""

    def __init__(self, ls: LanguageServer | None = None):
        self.ls = ls
        self.definitions: Definitions = {}
        self.references: References = defaultdict(list)

    def _get_raw_file(self, uri: str) -> List[str]:
        return get_file(self.ls, uri)

    def _get_yaml_file(self, uri: str) -> Dict:
        data = "".join(get_file(self.ls, uri))

        try:
            return ruamel.yaml.safe_load(data)
        except ruamel.yaml.YAMLError as e:
            logger.error(f"Error while parsing {uri}: {e}")
            return {}

    def _get_yaml_tokens(self, uri: str) -> Generator:
        data = "".join(get_file(self.ls, uri))

        try:
            return ruamel.yaml.scan(data)
        except ruamel.yaml.YAMLError as e:
            logger.error(f"Error while parsing {uri}: {e}")
            raise GeneratorExit

    def _get_location(self, node: Token, filename: str) -> lsp_types.Location:
        return lsp_types.Location(
            uri=filename,
            range=lsp_types.Range(
                start=lsp_types.Position(
                    line=node.start_mark.line, character=node.start_mark.column
                ),
                end=lsp_types.Position(
                    line=node.end_mark.line, character=node.end_mark.column
                ),
            ),
        )

    def _get_variables(self, token: ScalarToken) -> List[str]:
        return re.findall(r"\${(.*?)}", token.value)

    def _process_tokens(self, tokens: Generator, filename: str):
        tokens = self._get_yaml_tokens(filename)
        base_key: str = ""
        prev_key: str = ""

        # NOTE: may rewrite into match expression
        for token in tokens:
            t = type(token)

            if (
                t is StreamStartToken
                or t is DocumentStartToken
                or t is BlockMappingStartToken
                or t is FlowEntryToken
                or t is FlowSequenceEndToken
                or t is FlowMappingEndToken
            ):
                continue

            if t is BlockEndToken:
                base_key = remove_from_base_key(base_key)

            elif t is KeyToken:
                token = next(tokens)  # now it's ScalarToken
                assert type(token) is ScalarToken

                k = append_to_base_key(base_key, token.value)
                self.definitions[k] = self._get_location(token, filename)
                prev_key = token.value

            elif t is ValueToken:
                token = next(tokens)  # now it's ScalarToken or BlockMappingStartToken
                t = type(token)

                assert_type_is_any_of(
                    t,
                    [
                        ScalarToken,  # value
                        BlockMappingStartToken,  # inner block started
                        BlockSequenceStartToken,  # inner block ended
                        BlockEntryToken,  # - (in case of list of strings)
                        FlowSequenceStartToken,  # [
                        FlowSequenceEndToken,  # ]
                        FlowMappingStartToken,  # {
                        FlowMappingEndToken,  # }
                    ],
                    f"token is {token}",
                )

                if t is BlockMappingStartToken:  # Inner block started
                    base_key += f".{prev_key}" if base_key else prev_key
                    continue

                if t is BlockSequenceStartToken:  # Inner block ended
                    continue

                if t is FlowSequenceStartToken:  # [
                    continue

                if t is FlowMappingStartToken:  # {
                    continue

                if t is BlockEntryToken:  # - (in case of list of strings)
                    continue

                #  ScalarToken
                for var in self._get_variables(token):
                    self.references[var].append(self._get_location(token, filename))

            elif t is ScalarToken:
                for var in self._get_variables(token):
                    self.references[var].append(self._get_location(token, filename))

    def _update_context(self, filename: str):
        tokens = self._get_yaml_tokens(filename)
        self._process_tokens(tokens, filename)

    def load_yaml_config(self, config_path: str) -> Dict:
        logger.info("Loading config from: {}".format(config_path))
        data = self._get_yaml_file(config_path)

        # Recursively load default file (config inheritance)
        result: Dict = {}
        if "defaults" in data:
            base_folder = "/".join(config_path.split("/")[:-1])

            for default_file_path in data["defaults"]:
                if default_file_path == "_self_":
                    continue

                default_file_path = os.path.join(
                    base_folder, f"{default_file_path}.yaml"
                )
                default_data = self.load_yaml_config(default_file_path)
                result = deep_update(result, default_data)

        data = deep_update(result, data)
        self._update_context(config_path)

        return data

    def load(self, config_path: str) -> HydraContext:
        """
        Load the config from the file
        """
        self.definitions.clear()
        self.references.clear()

        logger.info(f"Loaded config from: {config_path}")
        config = self.load_yaml_config(config_path)

        return HydraContext(config, self.references, self.definitions)
