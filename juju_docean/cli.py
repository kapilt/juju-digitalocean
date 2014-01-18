import argparse


def setup_parser():
    parser = argparse.ArgumentParser()
    return parser


def main():
    parser = setup_parser()
    options = parser.parse_args()
    options.command(options)
