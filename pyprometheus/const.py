#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pyprometheus.const
~~~~~~~~~~~~~~~~~~

Prometheus instrumentation library for Python applications

:copyright: (c) 2017 by Alexandr Lispython.
:license: , see LICENSE for more details.
:github: http://github.com/Lispython/pyprometheus
"""


class Types(object):

    BASE = 1
    GAUGE = 2
    COUNTER = 3

    SUMMARY = 4
    SUMMARY_SUM = 5
    SUMMARY_COUNTER = 7
    SUMMARY_QUANTILE = 8

    HISTOGRAM = 10

    HISTOGRAM_SUM = 11
    HISTOGRAM_COUNTER = 12
    HISTOGRAM_BUCKET = 13


TYPES = Types()


CONTENT_TYPE = 'text/plain; version=0.0.4; charset=utf-8'


CREDITS = """# Python client for prometheus.io
# http://github.com/Lispython/pyprometheus
# Generated at {dt}
"""
