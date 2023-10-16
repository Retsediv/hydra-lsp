import logging

from lsprotocol import types as lsp_types
from pygls.server import LanguageServer

from hydra_lsp.loader import HydraConfig

logger = logging.getLogger(__name__)


class Hover:
    def __init__(self, ls: LanguageServer) -> None:
        self.ls = ls

    def get_hover(
        self,
        params: lsp_types.HoverParams,
        context: HydraConfig | None,
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
