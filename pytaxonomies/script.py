#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from pytaxonomies import Taxonomies


def main() -> None:
    argParser = argparse.ArgumentParser(description='Use MISP taxonomies')
    argParser.add_argument('-a', '--all', action='store_true', help='Print all taxonomies as machine tags')
    argParser.add_argument('-l', '--local', default=None, help='Use local manifest file.')
    args = argParser.parse_args()
    if args.local:
        t = Taxonomies(manifest_path=args.local)
    else:
        t = Taxonomies()
    if args.all:
        print(t)
