#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from pytaxonomies import Taxonomies


class TestPyTaxonomies(unittest.TestCase):

    def setUp(self):
        self.taxonomies = Taxonomies()

    def test_print(self):
        print(self.taxonomies)

    def test_expanded_print(self):
        for name in self.taxonomies.keys():
            tax = self.taxonomies.get(name)
            print(tax.print_expanded_entries())

    def test_len(self):
        len(self.taxonomies)

    def test_iter(self):
        for n, t in self.taxonomies.items():
            len(t)
            t.amount_entries()
            for p, value in t.items():
                continue

    def test_local(self):
        Taxonomies(manifest_path="./misp-taxonomies/MANIFEST.json")


if __name__ == "__main__":
    unittest.main()
