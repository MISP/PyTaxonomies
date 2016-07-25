#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from pytaxonomies import Taxonomies


class TestPyTaxonomies(unittest.TestCase):

    def setUp(self):
        self.taxonomies = Taxonomies()

    def test_print(self):
        print(self.taxonomies)

if __name__ == "__main__":
    unittest.main()
