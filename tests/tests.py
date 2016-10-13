#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import unittest
from pytaxonomies import Taxonomies, EncodeTaxonomies
import pytaxonomies.api


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
        for t in self.taxonomies.values():
            if not t.has_entries():
                continue
            tax = list(t.values())[0]
            print(tax)
            pred = list(tax.values())[0]
            print(pred)

    def test_amountEntries(self):
        list(self.taxonomies.values())[0].amount_entries()

    def test_missingDependency(self):
        pytaxonomies.api.HAS_REQUESTS = False
        with self.assertRaises(Exception):
            Taxonomies()
        Taxonomies(manifest_path="./misp-taxonomies/MANIFEST.json")
        pytaxonomies.api.HAS_REQUESTS = True

    def test_machinetags(self):
        tax = list(self.taxonomies.values())[0]
        for p in tax.values():
            mt = tax.make_machinetag(p)
            self.taxonomies.revert_machinetag(mt)

    def test_json(self):
        for t in self.taxonomies:
            json.dumps(t, cls=EncodeTaxonomies)


if __name__ == "__main__":
    unittest.main()
