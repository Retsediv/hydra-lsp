import logging

import pygtrie
from lsprotocol.types import (
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    CompletionParams,
    MarkupContent,
    MarkupKind,
)
from pygls.server import LanguageServer

from hydra_lsp.context import HydraContext

logger = logging.getLogger(__name__)


def _markdown_content(value: str) -> MarkupContent:
    """Return the MarkupContent with Markdown kind."""
    return MarkupContent(kind=MarkupKind.Markdown, value=value)


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

        prefix = self._get_var_prefix(current_line, position.character)
        return self.complete(prefix)

    def _get_var_prefix(self, line: str, pos: int = 0) -> str | None:
        """
        Assume that the line should be in the following format:
            var: something ${va<cursor>xx} bbb
        it will return "va"
        """
        start = line.rfind("${", 0, pos)
        if start == -1:
            return None

        return line[start + len("${") : pos]

    def complete(self, prefix: str | None) -> CompletionList:
        if prefix is None:
            return CompletionList(is_incomplete=False, items=[])

        try:
            kk = self.trie.keys(prefix)
        except KeyError:
            kk = []

        items = [
            CompletionItem(
                label=k,
                kind=CompletionItemKind.Variable,
                documentation=self._get_docstring(k),
            )
            for k in kk
        ]

        return CompletionList(is_incomplete=False, items=items)

    def _get_docstring(self, key: str) -> MarkupContent:
        value = str(self.context.get(key))

        result = _markdown_content(
            f"""
            *Var*: `{key}`
     ```
     {value}
     ```

            """
        )

        return result
