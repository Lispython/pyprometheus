#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pyprometheus.compat
~~~~~~~~~~~~~~~~~~~

Prometheus instrumentation library for Python applications

:copyright: (c) 2017 by Alexandr Lispython.
:license: , see LICENSE for more details.
:github: http://github.com/Lispython/pyprometheus
"""

import sys

# Useful for very coarse version differentiation.
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
PY34 = sys.version_info[0:2] >= (3, 4)


if PY3:
    PAD_SYMBOL = 0
else:
    PAD_SYMBOL = "\x00"


try:
    xrange = xrange
except Exception:
    xrange = range


if PY3:
    def b(s):
        if isinstance(s, bytes):
            return s
        return s.encode("latin-1")

    def u(s):
        return s

else:
    def b(s):
        return s

    def u(s):
        return s
        # if isinstance(s, unicode):
        #     return s
        # return unicode(s.replace(r"\\", r"\\\\"), "unicode_escape")
