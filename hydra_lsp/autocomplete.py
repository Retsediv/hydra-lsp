import json
import logging

import pygtrie
from lsprotocol.types import (
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    CompletionParams,
    MarkupContent,
)
from pygls.server import LanguageServer

from hydra_lsp.context import HydraContext
from hydra_lsp.utils import to_markdown_content, yaml_get_var_prefix

logger = logging.getLogger(__name__)


class Completer:
    def __init__(self):
        self.context = None
        self.trie = pygtrie.CharTrie()

    def update(self, context: HydraContext):
        self.context = context
        self.trie.update(context.definitions)

    def get_completions(self, ls: LanguageServer, params: CompletionParams):
        uri = params.text_document.uri
        logger.info(f"Completion requested: {uri} at {params.position}")

        document = ls.workspace.get_document(uri)
        position = params.position
        current_line = document.lines[position.line]

        prefix = yaml_get_var_prefix(current_line, position.character)
        return self.complete(prefix)

    def complete(self, prefix: str | None) -> CompletionList:
        if prefix is None:
            return CompletionList(is_incomplete=False, items=[])

        try:
            keys = self.trie.keys(prefix)
        except KeyError:
            keys = []

        items = [
            CompletionItem(
                label=k,
                kind=CompletionItemKind.Variable,
                documentation=self._get_docstring(k),
            )
            for k in keys
        ]

        return CompletionList(is_incomplete=False, items=items)

    def _get_docstring(self, key: str) -> MarkupContent:
        value = str(self.context.get(key))

        s = json.dumps({key: value}, indent=2)[1:-1]
        result = to_markdown_content(s)

        return result
