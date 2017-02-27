#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
pyprometheus.values
~~~~~~~~~~~~~~~~~~~

Prometheus instrumentation library for Python applications

:copyright: (c) 2017 by Alexandr Lispython.
:license: , see LICENSE for more details.
:github: http://github.com/Lispython/pyprometheus
"""
import time
from functools import wraps

default_timer = time.time

class BaseManager(object):
    def __call__(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            with self:
                return f(*args, **kwargs)
        return wrapper


class TimerManager(BaseManager):
    def __init__(self, collector):
        self._collector = collector

    def __enter__(self):
        self._start_time = default_timer()

    def __exit__(self, exc_type, exc_value, traceback):
        self._collector.observe(default_timer() - self._start_time)


class InprogressTrackerManager(BaseManager):

    def __init__(self, gauge):
        self._gauge = gauge

    def __enter__(self):
        self._gauge.inc()

    def __exit__(self, exc_info, exc_value, traceback):
        self._gauge.dec()


class GaugeTimerManager(TimerManager):

    def __exit__(self, exc_type, exc_value, traceback):
        self._collector.set(default_timer() - self._start_time)
