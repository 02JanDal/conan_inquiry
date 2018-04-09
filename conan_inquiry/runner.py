#!/usr/bin/env python

import argparse
import logging
import os
from http.server import HTTPServer

from conan_inquiry.deployment import deploy
from conan_inquiry.finder import BintrayFinder, GithubFinder
from conan_inquiry.generator import Generator
from conan_inquiry.util.github import get_github_client
from conan_inquiry.web.server import DevelopmentHTTPRequestHandler
from conan_inquiry.util.cache import Cache
from conan_inquiry.validator import validate_packages


def main():
    logging.basicConfig(level=logging.WARN)

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help', dest='subparser_name')

    gen = subparsers.add_parser('generate', help='generates final json file from yaml files')
    gen.add_argument('--development', action='store_true', help='turns on various options useful for development')
    subparsers.add_parser('find', help='finds conan recipies')
    subparsers.add_parser('validate', help='validates the generated json file')
    subparsers.add_parser('deploy', help='deploys files to GitHub pages')
    subparsers.add_parser('server', help='starts a development server')

    args = parser.parse_args()

    dir = os.path.join(os.path.dirname(__file__), 'data/packages')
    if args.subparser_name == 'generate':
        if args.development:
            print('Running with development options enabled.')
        Generator(dir).transform_packages(args.development)
    elif args.subparser_name == 'find':
        # GithubFinder(get_github_client(3)).print()
        with Cache():
            btfinder = BintrayFinder()
            btfinder.run()
            btfinder.print()
            btfinder.generate_stubs()
    elif args.subparser_name == 'validate':
        validate_packages(os.getcwd())
    elif args.subparser_name == 'deploy':
        deploy()
    elif args.subparser_name == 'server':
        httpd = HTTPServer(('', 8000), DevelopmentHTTPRequestHandler)
        print('Server ready on port {}'.format(httpd.server_port))
        httpd.serve_forever()


if __name__ == '__main__':
    main()
