import argparse
import inspect
import logging
from importlib import metadata

from hydra_lsp.server import server

logging.basicConfig(level=logging.INFO)
logging.getLogger('pygls.protocol').setLevel(logging.DEBUG)

def main():
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

    if args.tcp:
        server.start_tcp(args.host, args.port)
    else:
        server.start_io()

if __name__ == '__main__':
    main()
