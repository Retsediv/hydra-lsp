import json
import logging
import os
import re
from collections import defaultdict
from typing import DefaultDict, Dict, Generator, List

import ruamel.yaml
import yaml
from lsprotocol import types as lsp_types
from pygls.server import LanguageServer
from ruamel.yaml.main import (
    BlockEndToken,
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

from hydra_lsp.context import HydraContext

logger = logging.getLogger(__name__)


def assert_type_is_any_of(t, types, msg: str = "Invalid type"):
    assert any([t is _t for _t in types]), msg


def append_to_base_key(base_key: str, key: str):
    return f"{base_key}.{key}" if base_key else key


def remove_from_base_key(base_key: str):
    return base_key.rsplit(".", 1)[0] if base_key else ""


# TODO: config has to be reloaded on file change
# TODO: context has to be global (in respect to the folder)
class ConfigParser:
    """Load a Hydra YAML config file, looks for _defaults and loads respective files"""

    def __init__(self, ls: LanguageServer | None = None):
        self.ls = ls
        self.definitions: Dict[str, lsp_types.Location] = {}
        self.references: DefaultDict[str, List[lsp_types.Location]] = defaultdict(list)

    def _get_raw_file(self, uri: str) -> List[str]:
        if self.ls is None:
            uri = uri[len("file://") :] if uri.startswith("file://") else uri
            with open(uri) as f:
                f.seek(0)
                return f.readlines()

        return self.ls.workspace.get_document(uri).lines

    # TODO: replace pyyaml with ruamel.yaml
    def _get_yaml_file(self, uri: str) -> Dict:
        if self.ls is None:
            uri = uri[len("file://") :] if uri.startswith("file://") else uri
            with open(uri) as f:
                f.seek(0)
                data = "\n".join(f.readlines())
            return yaml.safe_load(data)

        return yaml.safe_load(self.ls.workspace.get_document(uri).source)

    def _get_yaml_tokens(self, uri: str) -> Generator:
        if self.ls is None:
            uri = uri[len("file://") :] if uri.startswith("file://") else uri
            with open(uri) as f:
                f.seek(0)
                data = "\n".join(f.readlines())
            return ruamel.yaml.scan(data)

        return ruamel.yaml.scan(self.ls.workspace.get_document(uri).source)

    def _get_location(
        self, node: KeyToken | ValueToken | ScalarToken, filename: str
    ) -> lsp_types.Location:
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
                        FlowSequenceStartToken,  # [
                        FlowSequenceEndToken,  # ]
                        # FlowEntryToken,  # divider between items in [] or {}
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
        self._update_context(config_path)

        # Recursively load default file (config inheritance)
        result = {}
        if "defaults" in data:
            base_folder = "/".join(config_path.split("/")[:-1])

            for default_file_path in data["defaults"]:
                # TODO: Account for _self_ position in defaults list
                if default_file_path == "_self_":
                    continue

                default_file_path = os.path.join(
                    base_folder, f"{default_file_path}.yaml"
                )
                default_data = self.load_yaml_config(default_file_path)
                result.update(default_data)

        data.update(result)
        return data

    def load(self, config_path: str) -> HydraContext:
        """
        Load the config from the file
        """
        # Clear previous definitions and references
        self.definitions = {}
        self.references = defaultdict(list)

        logger.info(f"Loaded config: {config_path}")
        config = self.load_yaml_config(config_path)

        return HydraContext(config, self.references, self.definitions)


if __name__ == "__main__":
    config_loader = ConfigParser()
    config = config_loader.load("examples/config_ldm_precompute_dataset.yaml")
    print(json.dumps(config.config, indent=2))

    print("data: ", config.get("data"))
    print("data.loader: ", config.get("data.loader"))
    print("data.loader.batch_size: ", config.get("data.loader.batch_size"))
