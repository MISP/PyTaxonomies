#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import unittest
import uuid

from unittest import mock

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

    @unittest.skipUnless(pytaxonomies.api.HAS_REQUESTS, 'requires the optional remote extra')
    def test_manifest_url_and_path_are_mutually_exclusive(self):
        def no_network(url):
            raise AssertionError(f'no HTTP request expected, got {url}')

        # requests.exceptions.MissingSchema is itself a ValueError, so make sure
        # the error comes from the argument check and not from a failed request.
        with mock.patch.object(pytaxonomies.api.requests, 'get', side_effect=no_network):
            with self.assertRaisesRegex(ValueError, 'mutually exclusive'):
                Taxonomies(
                    manifest_url='https://raw.githubusercontent.com/MISP/misp-taxonomies/main/MANIFEST.json',
                    manifest_path=os.path.join(self.taxonomies_offline.url, 'MANIFEST.json'))

    def test_url_and_loader_consistent_with_manifest_path(self):
        manifest_path = os.path.join(self.taxonomies_offline.url, 'MANIFEST.json')
        taxonomies = Taxonomies(manifest_path=manifest_path)
        self.assertEqual(taxonomies.loader.__func__,
                         pytaxonomies.api.Taxonomies._Taxonomies__load_path)
        self.assertEqual(taxonomies.url, os.path.dirname(os.path.realpath(manifest_path)))

    @unittest.skipUnless(pytaxonomies.api.HAS_REQUESTS, 'requires the optional remote extra')
    def test_url_and_loader_consistent_with_manifest_url(self):
        root = self.taxonomies_offline.url
        requested = []

        def fake_get(url):
            requested.append(url)
            if url.endswith('/MANIFEST.json'):
                local = os.path.join(root, 'MANIFEST.json')
            else:
                local = os.path.join(root, url.rsplit('/', 2)[-2], url.rsplit('/', 1)[-1])
            with open(local, 'r') as f:
                content = json.load(f)
            response = mock.Mock()
            response.json.return_value = content
            return response

        manifest_url = 'https://example.org/misp-taxonomies/MANIFEST.json'
        with mock.patch.object(pytaxonomies.api.requests, 'get', side_effect=fake_get):
            taxonomies = Taxonomies(manifest_url=manifest_url)
        self.assertEqual(taxonomies.loader.__func__,
                         pytaxonomies.api.Taxonomies._Taxonomies__load_url)
        self.assertEqual(taxonomies.url, taxonomies.manifest['url'])
        # every taxonomy is fetched as a URL, never as a filesystem path - this is
        # what broke: self.url was overwritten with a directory while the URL loader
        # was still selected, and requests.get raised MissingSchema on the result.
        self.assertEqual(requested[0], manifest_url)
        self.assertGreater(len(requested), 1)
        for url in requested[1:]:
            self.assertRegex(url, r'^https?://', url)
            self.assertFalse(os.path.isabs(url), url)


if __name__ == "__main__":
    unittest.main()
