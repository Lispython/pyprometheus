#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pyprometheus.storage
~~~~~~~~~~~~~~~~~~~~

Prometheus instrumentation library for Python applications

:copyright: (c) 2017 by Alexandr Lispython.
:license: , see LICENSE for more details.
:github: http://github.com/Lispython/pyprometheus
"""


from collections import defaultdict
from itertools import groupby
from threading import Lock

from pyprometheus.const import TYPES


class BaseStorage(object):

    def inc_value(self, key, amount):
        raise NotImplementedError("inc_value")

    def write_value(self, key, value):
        raise NotImplementedError("write_value")

    def get_value(self, key):
        raise NotImplementedError("get_value")

    def get_items(self):
        raise NotImplementedError("get_items")

    def __len__(self):
        raise NotImplementedError("len")

    def __repr__(self):
        return u"<{0}: {1} items>".format(self.__class__.__name__, len(self))

    def items(self):
        """Read all keys from storage and yield grouped by name metrics and their samples

        ((name1, ((labels1, data1), (labels2 data1)))
         (name2, ((labels1, data2), (labels2 data2))))

        """
        for name, items in groupby(sorted(self.get_items(), key=self.sorter),
                                   key=self.name_group):

            yield name, self.group_by_labels(items)

    def group_by_labels(self, items):
        """Group metric by labels
        """
        return [(k, list(v)) for k, v in groupby(items, key=self.label_group)]

    def name_group(self, value):
        """Group keys by metric name
        :param value: (type, name, subtype, labels dict, value)
        """
        return value[0][1]

    def sorter(self, value):
        """Sort keys by (name, labels, type)

        :param value: (type, name, subtype, labels dict, value)
        """
        if TYPES.HISTOGRAM_BUCKET == value[0][0]:
            return value[0][1], value[0][3][1:], value[0][0]
        return value[0][1], value[0][3], value[0][0]

    def label_group(self, value):
        """Group by labels
        :param value: (type, name, subtype, lebels dict, value)
        """
        if TYPES.HISTOGRAM_BUCKET == value[0][0]:
            return value[0][3][1:]
        return value[0][3]


class LocalMemoryStorage(BaseStorage):

    def __init__(self):
        self._storage = defaultdict(float)
        self._lock = Lock()

    def inc_value(self, key, value):
        with self._lock:
            self._storage[key] += value

    def write_value(self, key, value):
        with self._lock:
            self._storage[key] = value

    def get_value(self, key):
        with self._lock:
            return self._storage[key]

    def get_items(self):
        return self._storage.items()

    def __len__(self):
        return len(self._storage)

    def __repr__(self):
        return u"<{0}: {1} items>".format(self.__class__.__name__, len(self))

    def clear(self):
        """Remove all items from storage
        """
        self._storage.clear()
