#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from collections import abc
import re
import sys
from pathlib import Path
from typing import Union, Dict, Optional, List, Callable, Any, ValuesView, Iterator, Tuple

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


def taxonomies_json_default(obj: Union['Taxonomy', 'Predicate', 'Entry']) -> Dict[str, Any]:
    if isinstance(obj, (Taxonomy, Predicate, Entry)):
        return obj.to_dict()


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
        return json.dumps(self, default=taxonomies_json_default)

    def __str__(self) -> str:
        return self.value


class Predicate(abc.Mapping):  # type: ignore

    def __init__(self, predicate: Optional[Dict[str, str]]=None,
                 entries: Optional[List[Dict[str, str]]]=None):
        if not predicate:
            if entries:
                raise Exception('Need predicates if entries.')
            else:
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

    def __init_entries(self, entries: Optional[List[Dict[str, str]]]=None) -> None:
        self.entries = {}
        if entries:
            for e in entries:
                self.entries[e['value']] = Entry(e)

    def to_dict(self) -> Dict[str, Union[str, ValuesView[Entry]]]:
        to_return: Dict[str, Union[str, ValuesView[Entry]]] = {'value': self.predicate}
        if self.expanded:
            to_return['expanded'] = self.expanded
        if self.description:
            to_return['description'] = self.description
        if self.colour:
            to_return['colour'] = self.colour
        if self.exclusive is not None:
            to_return['exclusive'] = self.exclusive
        if self.numerical_value is not None:
            to_return['numerical_value'] = self.numerical_value
        if self.entries:
            to_return['entries'] = self.values()
        return to_return

    def to_json(self) -> str:
        return json.dumps(self, default=taxonomies_json_default)

    def __str__(self) -> str:
        return self.predicate

    def __getitem__(self, entry: str) -> Entry:
        return self.entries[entry]

    def __iter__(self) -> Iterator[Any]:
        return iter(self.entries)

    def __len__(self) -> int:
        return len(self.entries)


class Taxonomy(abc.Mapping):  # type: ignore

    def __init__(self, taxonomy: Optional[Dict[str, Union[str, List[Dict[str, Any]]]]]=None):
        self.predicates: Dict[str, Predicate] = {}
        if not taxonomy:
            # We're creating a new one
            self.expanded = None
            self.refs = None
            self.type = None
            self.exclusive = None
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

    def __init_predicates(self) -> None:
        entries: Dict[str, List[Dict[str, str]]] = {}
        if self.taxonomy.get('values') and isinstance(self.taxonomy['values'], list):
            for v in self.taxonomy['values']:
                if not entries.get(v['predicate']):
                    entries[v['predicate']] = []
                entries[v['predicate']] += v['entry']
        for p in self.taxonomy['predicates']:
            if isinstance(p, str):
                continue
            self.predicates[p['value']] = Predicate(p, entries.get(p['value']))

    def to_json(self) -> str:
        return json.dumps(self, default=taxonomies_json_default)

    def to_dict(self) -> Dict[str, Union[str, List[Dict[str, Any]]]]:
        to_return = {'namespace': self.name, 'description': self.description,
                     'version': self.version}
        if self.expanded:
            to_return['expanded'] = self.expanded
        if self.refs:
            to_return['refs'] = self.refs
        if self.type:
            to_return['type'] = self.type
        if self.exclusive is not None:
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

    def has_entries(self) -> bool:
        if self.values():
            for p in self.values():
                if p.entries:
                    return True
        return False

    def __str__(self) -> str:
        return '\n'.join(self.machinetags())

    def make_machinetag(self, predicate: str, entry: Optional[Entry]=None) -> str:
        if entry:
            return f'{self.name}:{predicate}="{entry}"'
        else:
            return f'{self.name}:{predicate}'

    def machinetags(self) -> List[str]:
        to_return = []
        for p, content in self.items():
            if content:
                for k in content.keys():
                    to_return.append(f'{self.name}:{p}="{k}"')
            else:
                to_return.append(f'{self.name}:{p}')
        return to_return

    def __getitem__(self, predicate: str) -> Predicate:
        return self.predicates[predicate]

    def __iter__(self) -> Iterator[Any]:
        return iter(self.predicates)

    def __len__(self) -> int:
        return len(self.predicates)

    def amount_entries(self) -> int:
        if self.has_entries():
            return sum([len(e) for e in self.values()])
        else:
            return len(self.keys())

    def machinetags_expanded(self) -> List[str]:
        to_return = []
        for p, content in self.items():
            if content:
                for k, entry in content.items():
                    to_return.append('{}:{}="{}"'.format(self.name, p, entry.expanded))
            else:
                to_return.append('{}:{}'.format(self.name, p))
        return to_return


class Taxonomies(abc.Mapping):  # type: ignore

    def __init__(self, manifest_url: Optional[str]=None,
                 manifest_path: Optional[Union[Path, str]]=None):
        self.loader: Callable[..., Dict[Any, Any]]
        if not manifest_url and not manifest_path:
            # try path:
            if sys.modules['pytaxonomies'].__file__:
                root_path = Path(os.path.abspath(os.path.dirname(sys.modules['pytaxonomies'].__file__))) / 'data' / 'misp-taxonomies' / 'MANIFEST.json'
                if root_path.exists():
                    manifest_path = root_path
            if not manifest_path:
                manifest_url = 'https://raw.githubusercontent.com/MISP/misp-taxonomies/main/MANIFEST.json'

        if manifest_url:
            self.loader = self.__load_url
            self.manifest = self.loader(manifest_url)

        elif manifest_path:
            self.loader = self.__load_path
            self.manifest = self.loader(manifest_path)

        if manifest_path:
            self.url = os.path.dirname(os.path.realpath(manifest_path))
        else:
            self.url = self.manifest['url']
        self.version = self.manifest['version']
        self.license = self.manifest['license']
        self.description = self.manifest['description']
        self.__init_taxonomies()

    def validate_with_schema(self) -> None:
        if not HAS_JSONSCHEMA:
            raise ImportError('jsonschema is required: pip install jsonschema')
        if sys.modules['pytaxonomies'].__file__:
            schema = os.path.join(os.path.abspath(os.path.dirname(sys.modules['pytaxonomies'].__file__)), 'data', 'misp-taxonomies', 'schema.json')
            with open(schema, 'r', encoding="utf-8") as f:
                loaded_schema = json.load(f)
            for t in self.values():
                jsonschema.validate(t.taxonomy, loaded_schema)

    def __load_path(self, path: Union[Path, str]) -> Dict[str, Any]:
        if isinstance(path, str):
            path = Path(path)
        with path.open('r', encoding="utf-8") as f:
            return json.load(f)

    def __load_url(self, url: str) -> Dict[str, Any]:
        if not HAS_REQUESTS:
            raise Exception("Python module 'requests' isn't installed, unable to fetch the taxonomies.")
        return requests.get(url).json()

    def __make_uri(self, taxonomy_name: str) -> str:
        return f'{self.url}/{taxonomy_name}/{self.manifest["path"]}'

    def __init_taxonomies(self) -> None:
        self.taxonomies = {}
        for t in self.manifest['taxonomies']:
            uri = self.__make_uri(t['name'])
            tax = self.loader(uri)
            self.taxonomies[t['name']] = Taxonomy(tax)
            if t['name'] != self.taxonomies[t['name']].name:
                raise Exception("The name of the taxonomy in the manifest ({}) doesn't match with the name in the taxonomy ({})".format(t['name'], self.taxonomies[t['name']].name))

    def __getitem__(self, name: str) -> Taxonomy:
        return self.taxonomies[name]

    def __iter__(self) -> Iterator[Any]:
        return iter(self.taxonomies)

    def __len__(self) -> int:
        return len(self.taxonomies)

    def __str__(self) -> str:
        to_print = ''
        for taxonomy in self.values():
            to_print += "{}\n\n".format(str(taxonomy))
        return to_print

    def search(self, query: str, expanded: bool=False) -> List[str]:
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

    def revert_machinetag(self, machinetag: str) -> Union[Tuple[Taxonomy, Predicate, Entry], Tuple[Taxonomy, Predicate]]:
        if '=' in machinetag:
            name, predicat, entry = re.findall('^([^:]*):([^=]*)="([^"]*)"$', machinetag)[0]
        else:
            name, predicat = re.findall('^([^:]*):([^=]*)$', machinetag)[0]
            entry = None
        if entry:
            return self.taxonomies[name], self.taxonomies[name][predicat], self.taxonomies[name][predicat][entry]
        else:
            return self.taxonomies[name], self.taxonomies[name][predicat]

    def all_machinetags(self, expanded: bool=False) -> List[str]:
        if expanded:
            return [taxonomy.machinetags_expanded() for taxonomy in self.values()]
        return [taxonomy.machinetags() for taxonomy in self.values()]
