import logging
from importlib import metadata
from typing import Any, List

from lsprotocol import types as lsp_types
from lsprotocol.types import (
    CompletionList,
    CompletionOptions,
    WorkDoneProgressReport,
)
from pygls.server import LanguageServer

from hydra_lsp.autocomplete import Completer
from hydra_lsp.context import HydraContext
from hydra_lsp.hover import HydraIntel
from hydra_lsp.parser import ConfigParser

logger = logging.getLogger(__name__)


class HydraLSP(LanguageServer):
    CONFIGURATION_SECTION: str = "hydralsp"

    COMMAND_EVALUATE_LINE: str = "hydralsp.evaluate_line"
    COMMAND_EVALUATE_SELECTION: str = "hydralsp.evaluate_selection"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config_loaded: ConfigParser = ConfigParser(self)
        self.context: HydraContext | None = None

        self.intel: HydraIntel = HydraIntel(self)
        self.completer: Completer = Completer()

    def reload_config(self, file_path: str) -> None:
        """Load configuration."""
        self.context = self.config_loaded.load(file_path)
        self.completer.update(self.context)
        logger.info(f"Context loaded from {file_path}")


version = metadata.version("hydra-lsp")
server = HydraLSP("hydralsp", f"v{version}")


@server.feature(lsp_types.INITIALIZED)
def initialize(ls: HydraLSP, params: lsp_types.InitializeParams) -> None:
    """Connection is initialized."""
    logger.info("Server is initialized")

    ls.progress.report("init", WorkDoneProgressReport(message="HydraLSP: up"))


@server.feature(lsp_types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: HydraLSP, params: lsp_types.DidOpenTextDocumentParams) -> None:
    """Document opened."""
    logger.info(f"Document opened: {params.text_document.uri}")

    ls.reload_config(params.text_document.uri)
    ls.progress.report(
        "context", WorkDoneProgressReport(message="HydraLSP: loaded context")
    )
    # TODO: perform diagnostics


@server.feature(lsp_types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: HydraLSP, params: lsp_types.DidChangeTextDocumentParams) -> None:
    """Document changed."""
    logger.info(f"Document changed: {params.text_document.uri}")

    # self.reload_config(params.text_document.uri)
    # TODO: perform diagnostics (should it be done on every change?)


@server.feature(lsp_types.TEXT_DOCUMENT_DID_SAVE)
def did_save(ls: HydraLSP, params: lsp_types.DidSaveTextDocumentParams) -> None:
    """Document saved."""
    logger.info(f"Document saved: {params.text_document.uri}")

    ls.reload_config(params.text_document.uri)
    ls.progress.report(
        "context", WorkDoneProgressReport(message="HydraLSP: reloaded context")
    )
    # TODO: decide if diagnostics should be performed on save


@server.feature(lsp_types.TEXT_DOCUMENT_DEFINITION)
def definition(
    ls: HydraLSP, params: lsp_types.TextDocumentPositionParams
) -> lsp_types.Location | None:
    """Definition of a symbol."""
    logger.info(f"Definition feature is called with params: {params}")

    return ls.intel.get_definition(params, ls.context)


@server.feature(lsp_types.TEXT_DOCUMENT_REFERENCES)
def references(
    ls: HydraLSP, params: lsp_types.ReferenceParams
) -> list[lsp_types.Location] | None:
    """Provide a list of references for the symbol at the current cursor position."""
    logger.info(f"References feature is called with params: {params}")

    return ls.intel.get_references(params, ls.context)


@server.feature(lsp_types.TEXT_DOCUMENT_HOVER)
def hover(ls: HydraLSP, params: lsp_types.HoverParams) -> lsp_types.Hover | None:
    """Cursor over a symbol."""
    logger.info(f"Hover feature is called with params: {params}")

    return ls.intel.get_hover(params, ls.context)


@server.feature(
    lsp_types.TEXT_DOCUMENT_COMPLETION, CompletionOptions(trigger_characters=[","])
)
def completions(params: lsp_types.CompletionParams) -> CompletionList:
    logger.info("Completions feature is called")
    return server.completer.get_completions(server, params)


@server.command(HydraLSP.COMMAND_EVALUATE_LINE)
def evaluate_line(ls: HydraLSP, params: List[Any]) -> None:
    """Evaluate line under the cursor."""
    logger.info(f"Evaluate line command is called with params: {params}")

    # TODO: implement


@server.command(HydraLSP.COMMAND_EVALUATE_SELECTION)
def evaluate_selection(ls: HydraLSP, params: List[Any]) -> None:
    """Evaluate selected text."""
    logger.info(f"Evaluate selection command is called with params: {params}")

    # TODO: implement
