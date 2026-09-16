#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import unittest
import uuid

from pytaxonomies import Taxonomies, Taxonomy, Predicate, Entry
import pytaxonomies.api


class TestPyTaxonomies(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.taxonomies_offline = Taxonomies()
        self.loaded_tax = {}
        for t in self.taxonomies_offline.manifest['taxonomies']:
            with open('{}/{}/{}'.format(self.taxonomies_offline.url, t['name'], 'machinetag.json'), 'r') as f:
                self.loaded_tax[t['name']] = json.load(f)

    def machinetags_from_raw_json(self, name):
        """Machine tags derived straight from the bundled machinetag.json.

        Deliberately does not go through the API, so the assertions below compare
        the API against the data rather than against itself.
        """
        raw = self.loaded_tax[name]
        entries = {}
        for v in raw.get('values') or []:
            entries.setdefault(v['predicate'], []).extend(e['value'] for e in v['entry'])
        to_return = []
        for p in raw['predicates']:
            if isinstance(p, str):
                continue
            if entries.get(p['value']):
                to_return.extend(f'{raw["namespace"]}:{p["value"]}="{e}"'
                                 for e in entries[p['value']])
            else:
                to_return.append(f'{raw["namespace"]}:{p["value"]}')
        return to_return

    def test_compareOnlineOffilne(self):
        taxonomies_online = Taxonomies(manifest_url='https://raw.githubusercontent.com/MISP/misp-taxonomies/main/MANIFEST.json')
        for t_online, t_offline in zip(taxonomies_online.values(), self.taxonomies_offline.values()):
            self.assertEqual(str(t_online), str(t_offline))
        self.assertEqual(str(taxonomies_online), str(self.taxonomies_offline))

    def test_expanded_machinetags(self):
        all_expanded = self.taxonomies_offline.all_machinetags(expanded=True)
        self.assertEqual(len(all_expanded), len(self.taxonomies_offline))
        for taxonomy, expanded in zip(self.taxonomies_offline.values(), all_expanded):
            self.assertIsInstance(expanded, list)
            self.assertTrue(expanded, taxonomy.name)
            # one expanded machine tag per machine tag, and both start with the namespace
            self.assertEqual(len(expanded), len(taxonomy.machinetags()))
            for mt in expanded:
                self.assertIsInstance(mt, str)
                self.assertTrue(mt.startswith(f'{taxonomy.name}:'), mt)

    def test_machinetags(self):
        all_machinetags = self.taxonomies_offline.all_machinetags()
        self.assertEqual(len(all_machinetags), len(self.taxonomies_offline))
        for taxonomy, machinetags in zip(self.taxonomies_offline.values(), all_machinetags):
            self.assertIsInstance(machinetags, list)
            self.assertTrue(machinetags, taxonomy.name)
            self.assertEqual(machinetags, self.machinetags_from_raw_json(taxonomy.name))
            for mt in machinetags:
                self.assertIsInstance(mt, str)
                self.assertTrue(mt.startswith(f'{taxonomy.name}:'), mt)
        flat = [mt for machinetags in all_machinetags for mt in machinetags]
        # a well known tag every consumer relies on
        self.assertIn('tlp:red', flat)

    def test_dict(self):
        self.assertEqual(len(self.taxonomies_offline),
                         len(self.taxonomies_offline.manifest['taxonomies']))
        for n, t in self.taxonomies_offline.items():
            self.assertIsInstance(t, Taxonomy)
            self.assertEqual(n, t.name)
            self.assertEqual(len(t), len([p for p in self.loaded_tax[n]['predicates']
                                          if not isinstance(p, str)]))
            self.assertTrue(len(t), n)
            for p, value in t.items():
                self.assertIsInstance(value, Predicate)
                self.assertEqual(p, value.predicate)
                for k, entry in value.items():
                    self.assertIsInstance(entry, Entry)
                    self.assertEqual(k, entry.value)

    def test_search(self):
        results = self.taxonomies_offline.search('phish')
        self.assertTrue(results)
        all_machinetags = {mt for machinetags in self.taxonomies_offline.all_machinetags()
                           for mt in machinetags}
        for mt in results:
            self.assertIsInstance(mt, str)
            self.assertIn('phish', mt.lower())
            self.assertIn(mt, all_machinetags)
        self.assertIn('CERT-XLM:fraud="phishing"', results)
        self.assertEqual(self.taxonomies_offline.search('nosuchthinginanytaxonomy'), [])

    def test_search_expanded(self):
        results = self.taxonomies_offline.search('phish', expanded=True)
        self.assertTrue(results)
        all_expanded = {mt for machinetags in self.taxonomies_offline.all_machinetags(expanded=True)
                        for mt in machinetags}
        for mt in results:
            self.assertIsInstance(mt, str)
            self.assertIn('phish', mt.lower())
            self.assertIn(mt, all_expanded)
        self.assertIn('CERT-XLM:fraud="Phishing"', results)
        self.assertEqual(self.taxonomies_offline.search('nosuchthinginanytaxonomy',
                                                        expanded=True), [])

    def test_print_classes(self):
        self.assertTrue(str(self.taxonomies_offline))
        for taxonomy in self.taxonomies_offline.values():
            raw = self.loaded_tax[taxonomy.name]
            self.assertEqual(str(taxonomy).split('\n'),
                             self.machinetags_from_raw_json(taxonomy.name))
            raw_predicates = {p['value'] for p in raw['predicates'] if not isinstance(p, str)}
            raw_entries = {e['value'] for v in raw.get('values') or [] for e in v['entry']}
            for predicate in taxonomy.values():
                self.assertIn(str(predicate), raw_predicates)
                for entry in predicate.values():
                    self.assertIn(str(entry), raw_entries)

    def test_amountEntries(self):
        for tax in self.taxonomies_offline.values():
            amount = tax.amount_entries()
            self.assertIsInstance(amount, int)
            self.assertGreater(amount, 0, tax.name)
            # every counted entry has a machine tag, but predicates without entries
            # are only counted when the taxonomy has no entries at all
            self.assertLessEqual(amount, len(tax.machinetags()), tax.name)
            if not tax.has_entries():
                self.assertEqual(amount, len(tax.keys()), tax.name)

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
            invalid_uuids = []
            try:
                self.assertTrue(uuid.UUID(taxonomy.uuid).version in [4, 5, 1], taxonomy.uuid)
            except ValueError:
                invalid_uuids.append(('Taxonomy', taxonomy.uuid))
            for predicate in taxonomy.predicates.values():
                try:
                    self.assertTrue(uuid.UUID(predicate.uuid).version in [4, 5, 1], predicate.uuid)
                except ValueError:
                    invalid_uuids.append((f'Predicate "{predicate.predicate}"', predicate.uuid))
                for entry in predicate.entries.values():
                    try:
                        self.assertTrue(uuid.UUID(entry.uuid).version in [4, 5, 1], entry.uuid)
                    except ValueError:
                        invalid_uuids.append((f'Entry "{entry.value}"', entry.uuid))
            if invalid_uuids:
                print(invalid_uuids)
                raise Exception(f'Invalid UUIDs in {taxonomy.name}')


if __name__ == "__main__":
    unittest.main()
