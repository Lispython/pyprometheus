#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pyprometheus
~~~~~~~~~~~~

Prometheus instrumentation library for Python applications

:copyright: (c) 2017 by Alexandr Lispython.
:license: , see LICENSE for more details.
:github: http://github.com/Lispython/pyprometheus
"""



class BaseRegistry(object):
    """Link with metrics collectors
    """
    def __init__(self, storage={}):
        self._collectors = {}
        self._storage = storage

    @property
    def storage(self):
        return self._storage

    def register(self, collector):
        """Add collector to registry
        """
        if collector.uid in self._collectors:
            raise RuntimeError(u"Collector {0} already registered".format(collector.uid))
        self._collectors[collector.uid] = collector

    def unregister(self, collector):
        """Remove collector from registry
        """
        self._collectors.pop(collector.uid, None)

    def collect(self):
        """Get all metrics from all registered collectos
        """
        data = dict(self._storage.items())

        for uid, collector in self.collectors():
            # Collectors with collect method already have stats
            if hasattr(collector, 'collect'):
                for item in collector.collect():
                    yield item
            else:
                yield collector.build_samples(data.get(collector.name, []))

    def collectors(self):
        return self._collectors.items()

    def is_registered(self, collector):
        """Check that collector already exists
        """
        return collector.uid in self._collectors

    def __len__(self):
        return len(self._collectors)

    def get_samples(self):
        """
        Yield collector object and its samples
        """
        for collector in self.collect():
            yield collector, collector.get_samples()
