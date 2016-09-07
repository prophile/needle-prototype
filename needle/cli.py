import sys
import pathlib
import argparse

def argument_parser():
    parser = argparse.ArgumentParser(description="An A/B test server")

    parser.add_argument(
        'dir',
        type=pathlib.Path,
        default=pathlib.Path.cwd(),
        help="main directory, defining tests and metrics",
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=1212,
        help="port on which to run the HTTP server",
    )

    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help="be particularly noisy",
    )

    return parser

def main(args=sys.argv[1:]):
    options = argument_parser().parse_args(args)
    print(options)
