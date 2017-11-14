#!/usr/bin/env python

import argparse
import logging
import os

from conan_inquiry.deployment import deploy
from conan_inquiry.finder import BintrayFinder
from conan_inquiry.generator import Generator
from conan_inquiry.validator import validate_packages


def main():
    logging.basicConfig(level=logging.WARN)

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help', dest='subparser_name')

    subparsers.add_parser('generate', help='generates final json file from yaml files')
    subparsers.add_parser('find', help='finds conan recipies')
    subparsers.add_parser('validate', help='validates the generated json file')
    subparsers.add_parser('deploy', help='deploys files to GitHub pages')

    args = parser.parse_args()

    dir = os.path.join(os.path.dirname(__file__), 'data/packages')
    if args.subparser_name == 'generate':
        Generator(dir).transform_packages()
    elif args.subparser_name == 'find':
        # Finder(create_github()).generate_stubs(dir)
        BintrayFinder().print()
    elif args.subparser_name == 'validate':
        validate_packages(os.getcwd())
    elif args.subparser_name == 'deploy':
        deploy()


if __name__ == '__main__':
    main()
