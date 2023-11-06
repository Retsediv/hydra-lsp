import logging
from importlib import metadata

from lsprotocol import types as lsp_types
from lsprotocol.types import CompletionList, WorkDoneProgressBegin, WorkDoneProgressEnd
from pygls.server import LanguageServer

from hydra_lsp.autocomplete import Completer
from hydra_lsp.context import HydraContext
from hydra_lsp.intel import HydraIntel
from hydra_lsp.parser import ConfigParser

logger = logging.getLogger(__name__)


class HydraLSP(LanguageServer):
    CONFIGURATION_SECTION: str = "hydralsp"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.init_params: lsp_types.InitializeParams | None = None

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
    ls.init_params = params


@server.feature(lsp_types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: HydraLSP, params: lsp_types.DidOpenTextDocumentParams) -> None:
    """Document opened."""
    logger.info(f"Document opened: {params.text_document.uri}")

    ls.progress.begin("context", WorkDoneProgressBegin(title="Indexing"))
    ls.reload_config(params.text_document.uri)

    diagnostics = ls.intel.get_diagnostics(ls.context, params.text_document.uri)
    ls.publish_diagnostics(params.text_document.uri, diagnostics)
    ls.progress.end("context", WorkDoneProgressEnd())


@server.feature(lsp_types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: HydraLSP, params: lsp_types.DidChangeTextDocumentParams) -> None:
    """Document changed."""
    logger.info(f"Document changed: {params.text_document.uri}")

    # NOTE: perform diagnostics and reload config? (should it be done on every change?)
    # self.reload_config(params.text_document.uri)


@server.feature(lsp_types.TEXT_DOCUMENT_DID_SAVE)
def did_save(ls: HydraLSP, params: lsp_types.DidSaveTextDocumentParams) -> None:
    """Document saved."""
    logger.info(f"Document saved: {params.text_document.uri}")

    ls.progress.begin("context", WorkDoneProgressBegin(title="Indexing"))
    ls.reload_config(params.text_document.uri)

    diagnostics = ls.intel.get_diagnostics(ls.context, params.text_document.uri)
    ls.publish_diagnostics(params.text_document.uri, diagnostics)
    ls.progress.end("context", WorkDoneProgressEnd())


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


@server.feature(lsp_types.TEXT_DOCUMENT_COMPLETION)
def completions(params: lsp_types.CompletionParams) -> CompletionList:
    logger.info("Completions feature is called")
    return server.completer.get_completions(server, params)
