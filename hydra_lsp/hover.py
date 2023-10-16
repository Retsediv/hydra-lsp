import logging

from lsprotocol import types as lsp_types
from pygls.server import LanguageServer

logger = logging.getLogger(__name__)


class Hover:
    def __init__(self, ls: LanguageServer) -> None:
        self.ls = ls

    def get_hover(
        self, params: lsp_types.TextDocumentPositionParams
    ) -> lsp_types.Hover | None:
        """Get hover information."""
        document = self.ls.workspace.get_document(params.text_document.uri)
        position = params.position

        if self.ls.debug_hover:
            logger.info(f"Hover requested: {params.text_document.uri}")

        # TODO: implement
        return lsp_types.Hover(
            contents=f"Hello world from hydra-lsp | Position: {params.position}",
        )
