import sys
import logging
import pathlib
import argparse

from .app import app


def argument_parser():
    parser = argparse.ArgumentParser(description="An A/B test server")

    parser.add_argument(
        "dir",
        type=pathlib.Path,
        default=pathlib.Path.cwd(),
        nargs='?',
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
        "-b",
        "--bind",
        default="::",
        help="host to which to bind",
    )

    parser.add_argument(
        "-D",
        "--debug",
        action='store_true',
        help="run in Flask debug mode",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action='store_true',
        help="be particularly noisy",
    )

    return parser


def main(args=sys.argv[1:]):
    options = argument_parser().parse_args(args)

    verbose_output = options.debug or options.verbose

    logging.basicConfig(
        level=logging.DEBUG if verbose_output else logging.INFO,
    )

    app.config['ROOT'] = options.dir

    app.run(
        host=options.bind,
        port=options.port,
        debug=options.debug,
    )
