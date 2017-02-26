#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pyprometheus.contrib.graphite
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Bridge to push metrics over TCP in the Graphite plaintext format.

:copyright: (c) 2017 by Alexandr Lispython.
:license: , see LICENSE for more details.
:github: http://github.com/Lispython/pyprometheus
"""

class GraphitePusher(object):

    def __init__(self, address, registry, connection_timeout=30):
        self._connection_timeout = connection_timeout
        self._address = address
        self._registry = registry

    def format_sample(self, sample):
        """Format single sample to graphite format
        """
        raise NotImplementedError


    def push(self):
        """Push samples from registry to graphite
        """
        raise NotImplementedError
