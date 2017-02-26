#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pyprometheus.utils
~~~~~~~~~~~~~~~~~~

Prometheus instrumentation library for Python applications

:copyright: (c) 2017 by Alexandr Lispython.
:license: , see LICENSE for more details.
:github: http://github.com/Lispython/pyprometheus
"""
import sys
import time


def import_storage(path):
    try:
        __import__(path)
    except ImportError:
        raise
    else:
        return sys.modules[path]


def format_binary(value):
    return ':'.join("{0}>{1}".format(i, x.encode('hex')) for i, x in enumerate(value))


def format_char_positions(value):
    return ":".join("{0}>{1}".format(i, x) for i, x in enumerate(value))


def print_binary(value):
    print(value)
    print(format_char_positions(value))
    print(format_binary(value))


class measure_time(object):
    def __init__(self,name):
        self.name = name
        self._num_ops = 0

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self,ty,val,tb):
        end = time.time()
        print("{0} : {1:.4f} seconds for {2} ops [{3:.4f} / s]".format(
            self.name, end-self.start,
            self._num_ops, self._num_ops / (end-self.start)))
        return False

    def set_num_ops(self, value):
        self._num_ops = value
