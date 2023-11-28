from __future__ import annotations

import json
import logging
from functools import wraps
from typing import Tuple

from lsprotocol import types as lsp_types
from pygls.server import LanguageServer
from pygls.workspace import TextDocument

from hydra_lsp.parser import HydraContext
from hydra_lsp.utils import (
    to_markdown_content,
    yaml_get_identifier,
    yaml_get_variable_name,
)

logger = logging.getLogger(__name__)


def intel(feature: str, context_required: bool = True):
    def wrapper(method):
        @wraps(method)
        def _impl(self, *args, **kwargs):
            assert len(args) > 1, "Params or context is not loaded"
            logger.info(f"{feature} requested: {args[0]}")

            if context_required and args[1] is None:
                logger.warning("Context is not loaded")
                return None

            return method(self, *args, **kwargs)

        return _impl

    return wrapper


class HydraIntel:
    def __init__(self, ls: LanguageServer) -> None:
        self.ls = ls

    def _get_location(
        self,
        params: lsp_types.TextDocumentPositionParams
        | lsp_types.HoverParams
        | lsp_types.ReferenceParams,
    ) -> Tuple[str, TextDocument, lsp_types.Position]:
        document_path = params.text_document.uri
        document = self.ls.workspace.get_document(document_path)
        position = params.position

        return document_path, document, position

    @intel("Hover")
    def get_hover(
        self, params: lsp_types.HoverParams, context: HydraContext | None
    ) -> lsp_types.Hover | None:
        """
        Get hover information:

        - if the cursor is on the variable (after ':' and between '${' and '}'),
            it will return the value of the variable.
        - if the cursor is on the key (before ':'),
            it will return the computed value of the key.
        """

        document_path, document, position = self._get_location(params)
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

    @intel("Definition")
    def get_definition(
        self,
        params: lsp_types.TextDocumentPositionParams,
        context: HydraContext | None,
    ):
        """Get definition of the variable."""
        document_path, document, position = self._get_location(params)
        current_line = document.lines[position.line]

        key = yaml_get_variable_name(current_line, position.character)
        if key is None:
            return None

        logger.info(f"Definition of {key} is {context.definitions.get(key)}")
        return context.definitions.get(key)

    @intel("References")
    def get_references(
        self, params: lsp_types.ReferenceParams, context: HydraContext | None
    ):
        """Get references of the variable."""
        document_path, document, position = self._get_location(params)
        current_line = document.lines[position.line]
        key = yaml_get_identifier(current_line, position.character)

        if key is None:
            return None

        logger.info(f"References of {key} are {context.references.get(key)}")
        return context.references.get(key)

    def get_diagnostics(self, context: HydraContext | None, doc_uri: str | None):
        """Get diagnostics for the current context."""

        logger.info(f"Diagnostics requested for: {doc_uri}")
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
