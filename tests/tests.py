#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import unittest
from pytaxonomies import Taxonomies, EncodeTaxonomies
import pytaxonomies.api
import os


class TestPyTaxonomies(unittest.TestCase):

    def setUp(self):
        self.taxonomies = Taxonomies()
        self.manifest_path = "./misp-taxonomies/MANIFEST.json"
        self.taxonomies_offline = Taxonomies(manifest_path=self.manifest_path)
        self.json_load_taxonomies()

    def __load_path(self, path):
        with open(path, 'r') as f:
            return json.load(f)

    def json_load_taxonomies(self):
        self.manifest = self.__load_path(self.manifest_path)
        self.loaded_tax = {}
        for t in self.manifest['taxonomies']:
            path = '{}/{}/{}'.format(os.path.dirname(os.path.realpath(self.manifest_path)), t['name'], self.manifest['path'])
            self.loaded_tax[t['name']] = self.__load_path(path)

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
        for taxonomy in self.taxonomies.values():
            print(taxonomy)
            for predicate in taxonomy.values():
                print(predicate)
                for entry in predicate.values():
                    print(entry)

    def test_amountEntries(self):
        for tax in self.taxonomies.values():
            tax.amount_entries()

    def test_missingDependency(self):
        pytaxonomies.api.HAS_REQUESTS = False
        with self.assertRaises(Exception):
            Taxonomies()
        Taxonomies(manifest_path="./misp-taxonomies/MANIFEST.json")
        pytaxonomies.api.HAS_REQUESTS = True

    def test_revert_machinetags(self):
        for tax in self.taxonomies.values():
            for p in tax.values():
                if tax.has_entries():
                    for e in p.values():
                        mt = tax.make_machinetag(p, e)
                        self.taxonomies.revert_machinetag(mt)
                else:
                    mt = tax.make_machinetag(p)
                    self.taxonomies.revert_machinetag(mt)

    def test_json(self):
        for key, t in self.taxonomies.items():
            json.dumps(t, cls=EncodeTaxonomies)

    def test_recreate_dump(self):
        self.maxDiff = None
        for key, t in self.taxonomies.items():
            out = t._json()
            print(t.name)
            self.assertCountEqual(out, self.loaded_tax[t.name])


if __name__ == "__main__":
    unittest.main()
