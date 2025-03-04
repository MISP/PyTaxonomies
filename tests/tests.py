#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import unittest
import uuid

from pytaxonomies import Taxonomies
import pytaxonomies.api


class TestPyTaxonomies(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.taxonomies_offline = Taxonomies()
        self.loaded_tax = {}
        for t in self.taxonomies_offline.manifest['taxonomies']:
            with open('{}/{}/{}'.format(self.taxonomies_offline.url, t['name'], 'machinetag.json'), 'r') as f:
                self.loaded_tax[t['name']] = json.load(f)

    def test_compareOnlineOffilne(self):
        taxonomies_online = Taxonomies(manifest_url='https://raw.githubusercontent.com/MISP/misp-taxonomies/main/MANIFEST.json')
        for t_online, t_offline in zip(taxonomies_online.values(), self.taxonomies_offline.values()):
            self.assertEqual(str(t_online), str(t_offline))
        self.assertEqual(str(taxonomies_online), str(self.taxonomies_offline))

    def test_expanded_machinetags(self):
        self.taxonomies_offline.all_machinetags(expanded=True)

    def test_machinetags(self):
        self.taxonomies_offline.all_machinetags()

    def test_dict(self):
        len(self.taxonomies_offline)
        for n, t in self.taxonomies_offline.items():
            len(t)
            for p, value in t.items():
                continue

    def test_search(self):
        self.taxonomies_offline.search('phish')

    def test_search_expanded(self):
        self.taxonomies_offline.search('phish', expanded=True)

    def test_print_classes(self):
        for taxonomy in self.taxonomies_offline.values():
            print(taxonomy)
            for predicate in taxonomy.values():
                print(predicate)
                for entry in predicate.values():
                    print(entry)

    def test_amountEntries(self):
        for tax in self.taxonomies_offline.values():
            tax.amount_entries()

    def test_missingDependency(self):
        pytaxonomies.api.HAS_REQUESTS = False
        with self.assertRaises(Exception):
            Taxonomies(manifest_url='foo')
        Taxonomies()
        pytaxonomies.api.HAS_REQUESTS = True

    def test_revert_machinetags(self):
        for tax in self.taxonomies_offline.values():
            for p in tax.values():
                if tax.has_entries():
                    for e in p.values():
                        mt = tax.make_machinetag(p, e)
                        self.taxonomies_offline.revert_machinetag(mt)
                else:
                    mt = tax.make_machinetag(p)
                    self.taxonomies_offline.revert_machinetag(mt)

    def test_json(self):
        for key, t in self.taxonomies_offline.items():
            t.to_json()

    def test_recreate_dump(self):
        self.maxDiff = None
        for key, t in self.taxonomies_offline.items():
            out = t.to_dict()
            self.assertDictEqual(out, self.loaded_tax[t.name])

    def test_validate_schema(self):
        self.taxonomies_offline.validate_with_schema()

    def test_validate_uuid(self):
        for taxonomy in self.taxonomies_offline.values():
            self.assertTrue(uuid.UUID(taxonomy.uuid).version in [4, 5])
            for predicate in taxonomy.predicates.values():
                self.assertTrue(uuid.UUID(predicate.uuid).version in [4, 5])
                for entry in predicate.entries.values():
                    self.assertTrue(uuid.UUID(entry.uuid).version in [4, 5])


if __name__ == "__main__":
    unittest.main()
