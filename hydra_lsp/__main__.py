import argparse
import inspect
import logging
from importlib import metadata

from hydra_lsp.server import server

logging.basicConfig(
    filename='/tmp/mylsp.log',
    filemode='w',     
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%d/%b/%Y %H:%M:%S",
    level=logging.DEBUG
)
logging.getLogger('pygls.protocol').setLevel(logging.WARN)

def main() -> None:
    """Hydra-lsp entry point."""

    parser = argparse.ArgumentParser()
    parser.description = 'Hydra Language Server Protocol implementation'

    parser.add_argument(
        '--tcp', action='store_true',
        help='Use TCP server instead of stdio'
    )

    parser.add_argument(
        '--host', default='127.0.0.1',
        help='Bind to this address'
    )

    parser.add_argument(
        '--port', type=int, default=3099,
        help='Bind to this port'
    )

    parser.add_argument(
        '--version', action='store_true',
        help='Print version and exit'
    )

    parser.add_argument(
        '-v', action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    if args.version:
        version = metadata.version('hydra-lsp')
        print(inspect.cleandoc(f'''HydraLSP v{version} '''))
        return

    if args.v:
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger('pygls.protocol').setLevel(logging.DEBUG)

    logging.info("Starting hydra-lsp server")
    if args.tcp:
        logging.info(f"Starting TCP server on {args.host}:{args.port}")
        server.start_tcp(args.host, args.port)
    else:
        logging.info("Starting stdio server")
        server.start_io()

if __name__ == '__main__':
    main()
