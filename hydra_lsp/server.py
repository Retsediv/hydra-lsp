import logging
from typing import Any, List

from lsprotocol import types as lsp_types
from lsprotocol.types import CompletionItem, CompletionList, CompletionOptions
from pygls.server import LanguageServer

logging.basicConfig(filename='/tmp/mylsp.log', filemode='w', level=logging.DEBUG)

class HydraLSP(LanguageServer):
    CONFIGURATION_SECTION = 'hydralsp'

    COMMAND_EVALUATE_LINE = 'hydralsp.evaluate_line'
    COMMAND_EVALUATE_SELECTION = 'hydralsp.evaluate_selection'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)



server = HydraLSP("hydralsp", "v0.1")


@server.feature(lsp_types.INITIALIZED)
def initialize(ls: HydraLSP, params: lsp_types.InitializeParams) -> None:
    """Connection is initialized."""
    logging.debug("Server is initialized")

@server.feature(lsp_types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: HydraLSP, params: lsp_types.DidOpenTextDocumentParams) -> None:
    """Document opened."""
    logging.debug(f"Document opened: {params.text_document.uri}")
    # TODO: perform diagnostics

@server.feature(lsp_types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: HydraLSP, params: lsp_types.DidChangeTextDocumentParams) -> None:
    """Document changed."""
    logging.debug(f"Document changed: {params.text_document.uri}")
    # TODO: perform diagnostics (should it be done on every change?)

@server.feature(lsp_types.TEXT_DOCUMENT_DID_SAVE)
def did_save(ls: HydraLSP, params: lsp_types.DidSaveTextDocumentParams) -> None:
    """Document saved."""
    logging.debug(f"Document saved: {params.text_document.uri}")
    # TODO: decide if diagnostics should be performed on save

@server.feature(lsp_types.TEXT_DOCUMENT_DEFINITION)
def definition(ls: HydraLSP, params: lsp_types.TextDocumentPositionParams) -> lsp_types.Location | None:
    """Definition of a symbol."""
    logging.debug(f"Definition feature is called with params: {params}")

    # TODO: implement
    return lsp_types.Location(
        uri=params.text_document.uri,
        range=lsp_types.Range(
            start=lsp_types.Position(line=1, character=1),
            end=lsp_types.Position(line=1, character=5),
        ),
    )

@server.feature(lsp_types.TEXT_DOCUMENT_REFERENCES)
def references(ls: HydraLSP, params: lsp_types.ReferenceParams) -> list[lsp_types.Location] | None:
    """Provide a list of references for the symbol at the current cursor position."""
    logging.debug(f"References feature is called with params: {params}")
    # TODO: implement

    return []

@server.feature(lsp_types.TEXT_DOCUMENT_HOVER)
def hover(ls: HydraLSP, params: lsp_types.HoverParams) -> lsp_types.Hover | None:
    """Cursor over a symbol."""
    logging.debug(f"Hover feature is called with params: {params}")

    # TODO: implement
    return lsp_types.Hover(
        contents="Hello world from hydra-lsp",
    )

@server.feature(TEXT_DOCUMENT_COMPLETION, CompletionOptions(trigger_characters=[","]))
def completions(params: lsp_types.CompletionParams) -> CompletionList:
    logging.debug("\n\nCompletions feature is called")
    # TODO: implement

    items = []
    document = server.workspace.get_document(params.text_document.uri)
    logging.debug(f"Document: {document}")

    current_line = document.lines[params.position.line].strip()
    logging.debug(f"Current line: {current_line}")

    if current_line.endswith("hello,"):
        items = [
            CompletionItem(label="world"),
            CompletionItem(label="friend111"),
        ]

    return CompletionList(
        is_incomplete=False,
        items=items,
    )

@server.command(HydraLSP.COMMAND_EVALUATE_LINE)
def evaluate_line(ls: HydraLSP, params: List[Any]) -> None:
    """Evaluate line under the cursor."""
    logging.debug(f"Evaluate line command is called with params: {params}")

    # TODO: implement

@server.command(HydraLSP.COMMAND_EVALUATE_SELECTION)
def evaluate_selection(ls: HydraLSP, params: List[Any]) -> None:
    """Evaluate selected text."""
    logging.debug(f"Evaluate selection command is called with params: {params}")

    # TODO: implement

def main() -> None:
    """Hydra-lsp entry point."""

    logging.debug("Starting hydra-lsp server")

    server.start_io()  # good for production
    # server.start_tcp('127.0.0.1', 8080)  # good for debugging

if __name__ == "__main__":
    main()
