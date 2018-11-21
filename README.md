# PyTaxonomies

[![Build Status](https://travis-ci.org/MISP/PyTaxonomies.svg?branch=master)](https://travis-ci.org/MISP/PyTaxonomies)
[![Coverage Status](https://coveralls.io/repos/github/MISP/PyTaxonomies/badge.svg?branch=master)](https://coveralls.io/github/MISP/PyTaxonomies?branch=master)
[![codecov.io](https://codecov.io/github/MISP/PyTaxonomies/coverage.svg?branch=master)](https://codecov.io/github/MISP/PyTaxonomies?branch=master)

Pythonic way to work with the taxonomies defined there: https://github.com/MISP/misp-taxonomies

# Usage

Taxonomies and predicates are represented as immutable Python dictionaries.

# Installation
```
pip3 install git+https://github.com/MISP/PyTaxonomies
```
or
```
git clone https://github.com/MISP/PyTaxonomies
cd PyTaxonomies
git submodule init && git submodule update
python3 setup.py install
```

## Basics

```
In [1]: from pytaxonomies import Taxonomies

In [2]: taxonomies = Taxonomies()

In [3]: taxonomies.version
Out[3]: '20160725'

In [4]: taxonomies.license
Out[4]: 'CC-BY'

In [5]: taxonomies.description
Out[5]: 'Manifest file of MISP taxonomies available.'

# How many taxonomies have been imported
In [6]: len(taxonomies)
Out[6]: 27

# Names of the taxonomies
In [7]: list(taxonomies.keys())
Out[7]:
['tlp',
 'eu-critical-sectors',
 'dni-ism',
 'de-vs',
 'osint',
 'ms-caro-malware',
 'open-threat',
 'circl',
 'iep',
 'euci',
 'kill-chain',
 'europol-events',
 'veris',
 'information-security-indicators',
 'estimative-language',
 'adversary',
 'europol-incident',
 'malware_classification',
 'ecsirt',
 'dhs-ciip-sectors',
 'csirt_case_classification',
 'nato',
 'fr-classif',
 'enisa',
 'misp',
 'admiralty-scale',
 'ms-caro-malware-full']

In [8]: taxonomies.get('enisa').description
Out[8]: 'The present threat taxonomy is an initial version that has been developed on the basis of available ENISA material. This material has been used as an ENISA-internal structuring aid for information collection and threat consolidation purposes. It emerged in the time period 2012-2015.'

In [9]: taxonomies.get('enisa').version
Out[9]: 201601

In [10]: taxonomies.get('enisa').name
Out[10]: 'enisa'

In [11]: list(taxonomies.get('enisa').keys())
Out[11]:
['legal',
 'outages',
 'eavesdropping-interception-hijacking',
 'nefarious-activity-abuse',
 'physical-attack',
 'failures-malfunction',
 'disaster',
 'unintentional-damage']

In [12]: list(taxonomies.get('enisa').get('physical-attack'))
Out[12]:
['fraud-by-employees',
 'theft',
 'unauthorised-physical-access-or-unauthorised-entry-to-premises',
 'theft-of-documents',
 'information-leak-or-unauthorised-sharing',
 'vandalism',
 'damage-from-the-wafare',
 'sabotage',
 'coercion-or-extortion-or-corruption',
 'theft-of-mobile-devices',
 'theft-of-fixed-hardware',
 'terrorist-attack',
 'theft-of-backups',
 'fraud']

In [13]: taxonomies.get('enisa').get('physical-attack').get('vandalism').value
Out[13]: 'vandalism'

In [14]: taxonomies.get('enisa').get('physical-attack').get('vandalism').expanded
Out[14]: 'Vandalism'

In [15]: taxonomies.get('enisa').get('physical-attack').get('vandalism').description
Out[15]: 'Act of physically damaging IT assets.'

```

## Get machine tags

```
In [1]: print(taxonomies)  # or taxonomies.all_machinetags()

<display the machine tags for all the taxonomies>

In [2]: print(taxonomies.get('circl'))  # or taxonomies.get('circl').machinetags()
circl:incident-classification="vulnerability"
circl:incident-classification="malware"
circl:incident-classification="fastflux"
circl:incident-classification="system-compromise"
circl:incident-classification="sql-injection"
circl:incident-classification="scan"
circl:incident-classification="XSS"
circl:incident-classification="information-leak"
circl:incident-classification="scam"
circl:incident-classification="copyright-issue"
circl:incident-classification="denial-of-service"
circl:incident-classification="phishing"
circl:incident-classification="spam"
circl:topic="undefined"
circl:topic="industry"
circl:topic="ict"
circl:topic="finance"
circl:topic="services"
circl:topic="individual"
circl:topic="medical"

# All entries
In [3]: taxonomies.get('circl').amount_entries()
Out[3]: 28

# Amount predicates
In [3]: len(taxonomies.get('circl'))
Out[3]: 2

```

## Expanded machine tag

```
In [10]: print(taxonomies.get('circl').machinetags_expanded())
circl:topic="Individual"
circl:topic="Services"
circl:topic="Finance"
circl:topic="Medical"
circl:topic="Industry"
circl:topic="Undefined"
circl:topic="ICT"
circl:incident-classification="Phishing"
circl:incident-classification="Malware"
circl:incident-classification="XSS"
circl:incident-classification="Copyright issue"
circl:incident-classification="Spam"
circl:incident-classification="SQL Injection"
circl:incident-classification="Scan"
circl:incident-classification="Scam"
circl:incident-classification="Vulnerability"
circl:incident-classification="Denial of Service"
circl:incident-classification="Information leak"
circl:incident-classification="Fastflux"
circl:incident-classification="System compromise"
```
