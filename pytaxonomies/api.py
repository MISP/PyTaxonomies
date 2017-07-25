#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import collections
import re
import sys
from json import JSONEncoder

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class EncodeTaxonomies(JSONEncoder):
    def default(self, obj):
        try:
            return obj._json()
        except AttributeError:
            return JSONEncoder.default(self, obj)


class Entry():

    def __init__(self, value, expanded, colour, description, numerical_value):
        self.value = value
        self.expanded = expanded
        self.colour = colour
        self.description = description
        self.numerical_value = numerical_value

    def __str__(self):
        return self.value


class Predicate(collections.Mapping):

    def __init__(self, predicate, expanded, description, colour, entries):
        self.predicate = predicate
        self.expanded = expanded
        self.description = description
        self.colour = colour
        self.__init_entries(entries)

    def __init_entries(self, entries):
        self.entries = {}
        if entries:
            for e in entries:
                self.entries[e['value']] = Entry(e['value'], e['expanded'], e.get('colour'),
                                                 e.get('description'), e.get('numerical_value'))

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
        self.type = self.taxonomy.get('type')
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
            self.predicates[p['value']] = Predicate(p['value'], p.get('expanded'), p.get('description'),
                                                    p.get('colour'), entries.get(p['value']))

    def _json_predicates(self):
        predicates_to_return = []
        values_to_return = []
        for predicate in self.predicates.values():
            temp_predicate = {'value': predicate.predicate}
            if predicate.expanded:
                temp_predicate['expanded'] = predicate.expanded
            if predicate.description:
                temp_predicate['description'] = predicate.description
            if predicate.colour:
                temp_predicate['colour'] = predicate.colour
            predicates_to_return.append(temp_predicate)

            if predicate.entries:
                temp_entries = {'entry': [], 'predicate': predicate.predicate}
                for entry in predicate.entries.values():
                    temp_entry = {'value': entry.value}
                    if entry.expanded:
                        temp_entry['expanded'] = entry.expanded
                    if entry.numerical_value is not None:
                        temp_entry['numerical_value'] = entry.numerical_value
                    if entry.colour:
                        temp_entry['colour'] = entry.colour
                    if entry.description:
                        temp_entry['description'] = entry.description
                    temp_entries['entry'].append(temp_entry)
                values_to_return.append(temp_entries)

        return predicates_to_return, values_to_return

    def _json(self):
        to_return = {'namespace': self.name, 'description': self.description, 'version': self.version}
        if self.expanded:
            to_return['expanded'] = self.expanded
        if self.refs:
            to_return['refs'] = self.refs
        if self.type:
            to_return['type'] = self.type
        p, v = self._json_predicates()
        if p:
            to_return['predicates'] = p
        if v:
            to_return['values'] = v
        return to_return

    def has_entries(self):
        if self.predicates.values():
            for p in self.predicates.values():
                if p.entries:
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
                    to_return.append('{}:{}="{}"'.format(self.name, p, entry.expanded))
            else:
                to_return.append('{}:{}'.format(self.name, p))
        return to_return


class Taxonomies(collections.Mapping):

    def __init__(self, manifest_url='https://raw.githubusercontent.com/MISP/misp-taxonomies/master/MANIFEST.json',
                 manifest_path=os.path.join(os.path.abspath(os.path.dirname(sys.modules['pytaxonomies'].__file__)),
                                            'data', 'misp-taxonomies', 'MANIFEST.json')):
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
