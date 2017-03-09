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


__all__ = ("__version__", "__version_info__", "__maintainer__",
           "Counter", "Gauge", "Summary", "Histogram", "BaseStorage",
           "LocalMemoryStorage")

__license__ = "BSD, see LICENSE for more details"

__version__ = "0.0.6"

__version_info__ = list(map(int, __version__.split(".")))

__maintainer__ = "Alexandr Lispython"

from pyprometheus.metrics import Counter, Gauge, Summary, Histogram # noqa
from pyprometheus.storage import BaseStorage, LocalMemoryStorage # noqa
