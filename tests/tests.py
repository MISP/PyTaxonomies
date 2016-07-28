#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from pytaxonomies import Taxonomies


class TestPyTaxonomies(unittest.TestCase):

    def setUp(self):
        self.taxonomies = Taxonomies()
        self.taxonomies_offline = Taxonomies(manifest_path="./misp-taxonomies/MANIFEST.json")

    def test_compareOnlineOffilne(self):
        self.assertEqual(str(self.taxonomies), str(self.taxonomies_offline))

    def test_expanded_machinetags(self):
        self.taxonomies.all_machinetags(expanded=True)

    def test_machinetags(self):
        self.taxonomies.all_machinetags()

    def test_dict(self):
        len(self.taxonomies)
        for n, t in self.taxonomies.items():
            len(t)
            for p, value in t.items():
                continue

    def test_search(self):
        self.taxonomies.search('phish')

    def test_search_expanded(self):
        self.taxonomies.search('phish', expanded=True)

    def test_print_classes(self):
        tax = list(self.taxonomies.values())[0]
        print(tax)
        pred = list(tax.values())[0]
        print(pred)
        entry = list(pred.values())[0]
        print(entry)


if __name__ == "__main__":
    unittest.main()
