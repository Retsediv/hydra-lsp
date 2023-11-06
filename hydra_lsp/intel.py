import json
import logging

from lsprotocol import types as lsp_types
from pygls.server import LanguageServer

from hydra_lsp.parser import HydraContext
from hydra_lsp.utils import to_markdown_content, yaml_get_key, yaml_get_variable_name

logger = logging.getLogger(__name__)


# TODO: this class has a lot of duplicated code
class HydraIntel:
    def __init__(self, ls: LanguageServer) -> None:
        self.ls = ls

    def get_hover(
        self,
        params: lsp_types.HoverParams,
        context: HydraContext | None,
        debug_hover: bool = False,
    ) -> lsp_types.Hover | None:
        """
        Get hover information:

        - if the cursor is on the variable (after ':' and between '${' and '}'),
            it will return the value of the variable.
        - if the cursor is on the key (before ':'),
            it will return the computed value of the key.
        """

        document_path = params.text_document.uri
        document = self.ls.workspace.get_document(document_path)
        position = params.position

        if debug_hover:
            logger.info(f"Hover requested: {document_path} at {position}")

        if context is None:
            logger.warning("Context is not loaded")
            return None

        current_line = document.lines[position.line]

        # check if the cursor is before or after the ':'
        if position.character > current_line.find(":"):
            key = yaml_get_variable_name(current_line, position.character)
        else:
            key = context.loc_to_definition.find_key_by_position(
                position, document_path
            )
            logger.info(f"Key from position: {key}")

        value = context.get(key) if key is not None else None

        if key is None or value is None:
            return None

        s = json.dumps({key: value}, indent=2)[1:-1]
        return lsp_types.Hover(contents=to_markdown_content(s))

    # TODO: get_definition and get_references are very similar, we should merge them somehow
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
        key = yaml_get_variable_name(current_line, position.character)

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
        key = yaml_get_variable_name(current_line, position.character)

        if context is None:
            logger.warning("Context is not loaded")
            return None

        if key is None:
            key = yaml_get_key(current_line, position.character)

        if key is None:
            return None

        logger.info(f"References of {key} are {context.references.get(key)}")
        return context.references.get(key)

    def get_diagnostics(self, context: HydraContext | None, doc_uri: str | None):
        """Get diagnostics for the current context."""

        if context is None:
            logger.warning("Context is not loaded")
            return None

        diagnostics = []

        for reference, locations in context.references.items():
            if reference in context.definitions:
                continue

            for loc in locations:
                if doc_uri is not None and loc.uri != doc_uri:
                    continue

                diagnostics.append(
                    lsp_types.Diagnostic(
                        range=loc.range,
                        message=f"`{reference}` is not defined",
                        source="hydra-lsp",
                    )
                )

        logger.debug(f"Diagnostics: {diagnostics}")
        return diagnostics
