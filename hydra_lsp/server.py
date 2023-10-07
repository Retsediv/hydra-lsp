from pygls.server import LanguageServer
from lsprotocol.types import (
    TEXT_DOCUMENT_COMPLETION,
    CompletionItem,
    CompletionList,
    CompletionOptions,
    CompletionParams,
)

import logging

logging.basicConfig(filename='/tmp/mylsp.log', filemode='w', level=logging.DEBUG,
                    format='{time:HH:mm:ss.SSS} ({name}:{function}:{line}) - {message}')
server = LanguageServer("hydralsp", "v0.1")

@server.feature(TEXT_DOCUMENT_COMPLETION, CompletionOptions(trigger_characters=[","]))
def completions(params: CompletionParams) -> CompletionList:
    logging.debug("\n\nCompletions feature is called")

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

def main() -> None:
    logging.debug("Starting hydra-lsp server")
    server.start_io()  # good for production
    # server.start_tcp('127.0.0.1', 8080)  # good for debugging

if __name__ == "__main__":
    main()
