#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import collections
import re

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class Entry():

    def __init__(self, value, expanded, colour, description):
        self.value = value
        self.expanded = expanded
        self.colour = colour
        self.description = None
        if description:
            self.description = description

    def __str__(self):
        return self.value


class Predicate(collections.Mapping):

    def __init__(self, predicate, description, colour, entries):
        self.predicate = predicate
        self.description = None
        self.colour = colour
        if description:
            self.description = description
        self.entries = {}
        if entries:
            self.__init_entries(entries)

    def __init_entries(self, entries):
        for e in entries:
            self.entries[e['value']] = Entry(e['value'], e['expanded'],
                                             e.get('colour'), e.get('description'))

    def __str__(self):
        return self.predicate

    def __getitem__(self, entry):
        return self.entries[entry]

    def __iter__(self):
        return iter(self.entries)

    def __len__(self):
        return len(self.entries.keys())


class Taxonomy(collections.Mapping):

    def __init__(self, taxonomy):
        self.taxonomy = taxonomy
        self.name = self.taxonomy['namespace']
        self.description = self.taxonomy['description']
        self.version = self.taxonomy['version']
        self.expanded = self.taxonomy.get('expanded')
        self.refs = self.taxonomy.get('refs')
        self.__init_predicates()

    def __init_predicates(self):
        self.predicates = {}
        entries = {}
        if self.taxonomy.get('values'):
            for v in self.taxonomy['values']:
                if not entries.get(v['predicate']):
                    entries[v['predicate']] = []
                entries[v['predicate']] += v['entry']
        for p in self.taxonomy['predicates']:
            self.predicates[p['value']] = Predicate(p['value'], p.get('expanded'),
                                                    p.get('colour'), entries.get(p['value']))

    def has_entries(self):
        if self.predicates.values() and list(self.predicates.values())[0].entries:
            return True
        return False

    def __str__(self):
        return '\n'.join(self.machinetags())

    def make_machinetag(self, predicate, entry=None):
        if entry:
            return '{}:{}="{}"'.format(self.name, predicate, entry)
        else:
            return '{}:{}'.format(self.name, predicate)

    def machinetags(self):
        to_return = []
        for p, content in self.predicates.items():
            if content:
                for k in content.keys():
                    to_return.append('{}:{}="{}"'.format(self.name, p, k))
            else:
                to_return.append('{}:{}'.format(self.name, p))
        return to_return

    def __getitem__(self, predicate):
        return self.predicates[predicate]

    def __iter__(self):
        return iter(self.predicates)

    def __len__(self):
        return len(self.predicates)

    def amount_entries(self):
        if self.has_entries():
            return sum([len(e) for e in self.predicates.values()])
        else:
            return len(self.predicates.keys())

    def machinetags_expanded(self):
        to_return = []
        for p, content in self.predicates.items():
            if content:
                for k, entry in content.items():
                    to_return.append('{}:{}="{}"'.format(self.name, p, entry.expanded.decode()))
            else:
                to_return.append('{}:{}'.format(self.name, p))
        return to_return


class Taxonomies(collections.Mapping):

    def __init__(self, manifest_url='https://raw.githubusercontent.com/MISP/misp-taxonomies/master/MANIFEST.json',
                 manifest_path=None):
        if manifest_path:
            self.loader = self.__load_path
            self.manifest = self.loader(manifest_path)
        else:
            self.loader = self.__load_url
            self.manifest = self.loader(manifest_url)

        if manifest_path:
            self.url = os.path.dirname(os.path.realpath(manifest_path))
        else:
            self.url = self.manifest['url']
        self.version = self.manifest['version']
        self.license = self.manifest['license']
        self.description = self.manifest['description']
        self.__init_taxonomies()

    def __load_path(self, path):
        with open(path, 'r') as f:
            return json.load(f)

    def __load_url(self, url):
        if not HAS_REQUESTS:
            raise Exception("Python module 'requests' isn't installed, unable to fetch the taxonomies.")
        return requests.get(url).json()

    def __make_uri(self, taxonomy_name):
        return '{}/{}/{}'.format(self.url, taxonomy_name, self.manifest['path'])

    def __init_taxonomies(self):
        self.taxonomies = {}
        for t in self.manifest['taxonomies']:
            uri = self.__make_uri(t['name'])
            tax = self.loader(uri)
            self.taxonomies[t['name']] = Taxonomy(tax)
            if t['name'] != self.taxonomies[t['name']].name:
                raise Exception("The name of the taxonomy in the manifest ({}) doesn't match with the name in the taxonomy ({})".format(t['name'], self.taxonomies[t['name']].name))

    def __getitem__(self, name):
        return self.taxonomies[name]

    def __iter__(self):
        return iter(self.taxonomies)

    def __len__(self):
        return len(self.taxonomies)

    def __str__(self):
        to_print = ''
        for taxonomy in self.taxonomies.values():
            to_print += "{}\n\n".format(str(taxonomy))
        return to_print

    def search(self, query, expanded=False):
        query = query.lower()
        to_return = []
        for taxonomy in self.taxonomies.values():
            if expanded:
                machinetags = taxonomy.machinetags_expanded()
            else:
                machinetags = taxonomy.machinetags()
            for mt in machinetags:
                entries = [e.lower() for e in re.findall('[^:="]*', mt) if e]
                for e in entries:
                    if e.startswith(query) or e.endswith(query):
                        to_return.append(mt)
        return to_return

    def revert_machinetag(self, machinetag):
        if '=' in machinetag:
            name, predicat, entry = re.findall('^([^:]*):([^=]*)="([^"]*)"$', machinetag)[0]
        else:
            name, predicat = re.findall('^([^:]*):([^=]*)$', machinetag)[0]
            entry = None
        if entry:
            return self.taxonomies[name], self.taxonomies[name][predicat], self.taxonomies[name][predicat][entry]
        else:
            return self.taxonomies[name], self.taxonomies[name][predicat]

    def all_machinetags(self, expanded=False):
        if expanded:
            return [taxonomy.machinetags_expanded() for taxonomy in self.taxonomies.values()]
        return [taxonomy.machinetags() for taxonomy in self.taxonomies.values()]
