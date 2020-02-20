#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from collections.abc import Mapping
import re
import sys
from json import JSONEncoder
from pathlib import Path
from typing import Union, Dict, Optional, List, Callable, Any

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import jsonschema  # type: ignore
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


class EncodeTaxonomies(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (Taxonomy, Predicate, Entry)):
            return obj.to_dict()
        return JSONEncoder.default(self, obj)


class Entry():

    def __init__(self, entry: Optional[Dict[str, str]]=None):
        if not entry:
            # We're creating a new one
            self.expanded = None
            self.colour = None
            self.description = None
            self.numerical_value = None
            return
        self.value = entry['value']
        self.expanded = entry.get('expanded')
        self.colour = entry.get('colour')
        self.description = entry.get('description')
        self.numerical_value = entry.get('numerical_value')

    def to_dict(self) -> Dict[str, str]:
        to_return = {'value': self.value}
        if self.expanded:
            to_return['expanded'] = self.expanded
        if self.colour:
            to_return['colour'] = self.colour
        if self.description:
            to_return['description'] = self.description
        if self.numerical_value is not None:
            to_return['numerical_value'] = self.numerical_value
        return to_return

    def to_json(self) -> str:
        return json.dumps(self, cls=EncodeTaxonomies)

    def __str__(self):
        return self.value


class Predicate(Mapping):

    def __init__(self, predicate: Optional[Dict[str, str]]=None,
                 entries: Optional[List[Dict[str, str]]]=None):
        if not predicate and not entries:
            # We're creating a new one
            self.expanded = None
            self.description = None
            self.colour = None
            self.exclusive = None
            self.numerical_value = None
            self.entries: Dict[str, Entry] = {}
            return
        self.predicate = predicate['value']
        self.expanded = predicate.get('expanded')
        self.description = predicate.get('description')
        self.colour = predicate.get('colour')
        self.exclusive = predicate.get('exclusive')
        self.numerical_value = predicate.get('numerical_value')
        self.__init_entries(entries)

    def __init_entries(self, entries: Optional[List[Dict[str, str]]]=None):
        self.entries = {}
        if entries:
            for e in entries:
                self.entries[e['value']] = Entry(e)

    def to_dict(self):
        to_return = {'value': self.predicate}
        if self.expanded:
            to_return['expanded'] = self.expanded
        if self.description:
            to_return['description'] = self.description
        if self.colour:
            to_return['colour'] = self.colour
        if self.exclusive:
            to_return['exclusive'] = self.exclusive
        if self.numerical_value is not None:
            to_return['numerical_value'] = self.numerical_value
        if self.entries:
            to_return['entries'] = self.values()
        return to_return

    def to_json(self) -> str:
        return json.dumps(self, cls=EncodeTaxonomies)

    def __str__(self):
        return self.predicate

    def __getitem__(self, entry):
        return self.entries[entry]

    def __iter__(self):
        return iter(self.entries)

    def __len__(self):
        return len(self.entries)


class Taxonomy(Mapping):

    def __init__(self, taxonomy=None):
        if not taxonomy:
            # We're creating a new one
            self.expanded = None
            self.refs = None
            self.type = None
            self.exclusive = None
            self.predicates: Dict[str, Predicate] = {}
            return
        self.taxonomy = taxonomy
        self.name = self.taxonomy['namespace']
        self.description = self.taxonomy['description']
        self.version = self.taxonomy['version']
        self.expanded = self.taxonomy.get('expanded')
        self.refs = self.taxonomy.get('refs')
        self.type = self.taxonomy.get('type')
        self.exclusive = self.taxonomy.get('exclusive')
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
            self.predicates[p['value']] = Predicate(p, entries.get(p['value']))

    def to_json(self):
        return json.dumps(self, cls=EncodeTaxonomies)

    def to_dict(self):
        to_return = {'namespace': self.name, 'description': self.description,
                     'version': self.version}
        if self.expanded:
            to_return['expanded'] = self.expanded
        if self.refs:
            to_return['refs'] = self.refs
        if self.type:
            to_return['type'] = self.type
        if self.exclusive:
            to_return['exclusive'] = self.exclusive
        predicates = [p.to_dict() for p in self.values()]
        entries = []
        for p in predicates:
            if p.get('entries') is None:
                continue
            entries.append({'predicate': p['value'], 'entry': [e.to_dict() for e in p.pop('entries')]})
        to_return['predicates'] = predicates
        if entries:
            to_return['values'] = entries
        return to_return

    def has_entries(self):
        if self.values():
            for p in self.values():
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
        for p, content in self.items():
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
            return sum([len(e) for e in self.values()])
        else:
            return len(self.keys())

    def machinetags_expanded(self):
        to_return = []
        for p, content in self.items():
            if content:
                for k, entry in content.items():
                    to_return.append('{}:{}="{}"'.format(self.name, p, entry.expanded))
            else:
                to_return.append('{}:{}'.format(self.name, p))
        return to_return


class Taxonomies(Mapping):

    def __init__(self, manifest_url: str='https://raw.githubusercontent.com/MISP/misp-taxonomies/master/MANIFEST.json',
                 manifest_path: Union[Path, str]=Path(os.path.abspath(os.path.dirname(sys.modules['pytaxonomies'].__file__))) / 'data' / 'misp-taxonomies' / 'MANIFEST.json'):
        if manifest_path:
            self.loader: Callable[..., Dict[Any, Any]] = self.__load_path
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

    def validate_with_schema(self):
        if not HAS_JSONSCHEMA:
            raise ImportError('jsonschema is required: pip install jsonschema')
        schema = os.path.join(os.path.abspath(os.path.dirname(sys.modules['pytaxonomies'].__file__)), 'data', 'misp-taxonomies', 'schema.json')
        with open(schema, 'r') as f:
            loaded_schema = json.load(f)
        for t in self.values():
            jsonschema.validate(t.taxonomy, loaded_schema)

    def __load_path(self, path: Union[Path, str]) -> Dict:
        if isinstance(path, str):
            path = Path(path)
        with path.open('r') as f:
            return json.load(f)

    def __load_url(self, url: str) -> Dict:
        if not HAS_REQUESTS:
            raise Exception("Python module 'requests' isn't installed, unable to fetch the taxonomies.")
        return requests.get(url).json()

    def __make_uri(self, taxonomy_name) -> str:
        return f'{self.url}/{taxonomy_name}/{self.manifest["path"]}'

    def __init_taxonomies(self):
        self.taxonomies = {}
        for t in self.manifest['taxonomies']:
            uri = self.__make_uri(t['name'])
            tax = self.loader(uri)
            self.taxonomies[t['name']] = Taxonomy(tax)
            if t['name'] != self.taxonomies[t['name']].name:
                raise Exception("The name of the taxonomy in the manifest ({}) doesn't match with the name in the taxonomy ({})".format(t['name'], self.taxonomies[t['name']].name))

    def __getitem__(self, name: str):
        return self.taxonomies[name]

    def __iter__(self):
        return iter(self.taxonomies)

    def __len__(self):
        return len(self.taxonomies)

    def __str__(self):
        to_print = ''
        for taxonomy in self.values():
            to_print += "{}\n\n".format(str(taxonomy))
        return to_print

    def search(self, query: str, expanded: bool=False) -> List:
        query = query.lower()
        to_return = []
        for taxonomy in self.values():
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

    def revert_machinetag(self, machinetag: str):
        if '=' in machinetag:
            name, predicat, entry = re.findall('^([^:]*):([^=]*)="([^"]*)"$', machinetag)[0]
        else:
            name, predicat = re.findall('^([^:]*):([^=]*)$', machinetag)[0]
            entry = None
        if entry:
            return self.taxonomies[name], self.taxonomies[name][predicat], self.taxonomies[name][predicat][entry]
        else:
            return self.taxonomies[name], self.taxonomies[name][predicat]

    def all_machinetags(self, expanded: bool=False):
        if expanded:
            return [taxonomy.machinetags_expanded() for taxonomy in self.values()]
        return [taxonomy.machinetags() for taxonomy in self.values()]
