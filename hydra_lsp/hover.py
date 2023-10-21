import logging

from lsprotocol import types as lsp_types
from pygls.server import LanguageServer

from hydra_lsp.parser import HydraContext

logger = logging.getLogger(__name__)


# TODO: this class has a lot of duplicated code
# TODO: maybe we should divide this class or move everything to the server
class Hover:
    def __init__(self, ls: LanguageServer) -> None:
        self.ls = ls

    def get_hover(
        self,
        params: lsp_types.HoverParams,
        context: HydraContext | None,
        debug_hover: bool = False,
    ) -> lsp_types.Hover | None:
        """Get hover information."""

        document_path = params.text_document.uri
        document = self.ls.workspace.get_document(document_path)
        position = params.position

        if debug_hover:
            logger.info(f"Hover requested: {document_path} at {position}")

        if context is None:
            logger.warning("Context is not loaded")
            return None

        current_line = document.lines[position.line]
        key = self._get_variable_name(current_line, position.character)
        value = context.get(key) if key is not None else None

        if key is None or value is None:
            return None

        return lsp_types.Hover(contents=f"""{value}""")

    def get_definition(
        self,
        params: lsp_types.TextDocumentPositionParams,
        context: HydraContext | None,
    ):
        """Get definition of the variable."""

        logger.info(
            f"Definition requested: {params.text_document.uri} at {params.position}"
        )
        document_path = params.text_document.uri
        document = self.ls.workspace.get_document(document_path)
        position = params.position

        current_line = document.lines[position.line]
        key = self._get_variable_name(current_line, position.character)

        if context is None:
            logger.warning("Context is not loaded")
            return None

        if key is None:
            return None

        logger.info(f"Definition of {key} is {context.definitions.get(key)}")
        return context.definitions.get(key)

    def get_references(
        self, params: lsp_types.ReferenceParams, context: HydraContext | None
    ):
        """Get references of the variable."""

        logger.info(
            f"References requested: {params.text_document.uri} at {params.position}"
        )
        document_path = params.text_document.uri
        document = self.ls.workspace.get_document(document_path)
        position = params.position

        current_line = document.lines[position.line]
        key = self._get_variable_name(current_line, position.character)
        if key is None:
            key = self._get_key(current_line, position.character)

        if context is None:
            logger.warning("Context is not loaded")
            return None

        if key is None:
            return None

        logger.info(f"References of {key} are {context.references.get(key)}")
        return context.references.get(key)

    def _get_key(self, line: str, position: int) -> str | None:
        """
        Get key from the yaml value (if exists).
        convert the line like this:
            "foo: foo ${bar}/something else" -> "foo"
        given the position of the cursor (in this case, it's on the "b", "a" or "r" letter)
        """
        start = line.find(":")
        if start == -1:
            return None

        if position > start:
            return None

        return line[:start].strip()

    def _get_variable_name(self, line: str, position: int) -> str | None:
        """
        Get variable name from the yaml value (if exists).
        convert the line like this:
            "foo: foo ${bar}/something else" -> "bar"
        given the position of the cursor (in this case, it's on the "b", "a" or "r" letter)
        """
        start = line.find(":")
        if start == -1:
            # TODO: Double check if there is case when it does not hold
            return None

        first_part_index = line.rfind("${", start, position)
        if first_part_index == -1:
            return None

        second_part_index = line.find("}", position + 1)
        if second_part_index == -1:
            return None

        return line[first_part_index + 2 : second_part_index]
