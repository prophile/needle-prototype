import sys
import argparse

def argument_parser():
    parser = argparse.ArgumentParser(description="An A/B test server")

    return parser

def main(args=sys.argv[1:]):
    options = argument_parser().parse_args(args)
    print(options)
