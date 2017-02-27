#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pyprometheus.utils.exposition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Helpers to export registry to another formats

:copyright: (c) 2017 by Alexandr Lispython.
:license: , see LICENSE for more details.
:github: http://github.com/Lispython/pyprometheus
"""
import os
from datetime import datetime

from pyprometheus.const import CREDITS


def registry_to_text(registry):
    """Get all registry metrics and convert to text format
    """
    output = [CREDITS.format(dt=datetime.utcnow().isoformat())]
    for collector, samples in registry.get_samples():
        output.append(collector.text_export_header)
        for sample in samples:
            output.append(sample.export_str)
    output.append('')
    return '\n'.join(output)


def write_to_textfile(registry, path):
    """Write metrics to text file
    """

    tmp_filename = "{0}.{1}.tmp".format(path, os.getpid())

    with open(tmp_filename, 'wb') as f:
        f.write(registry_to_text(registry))

    os.rename(tmp_filename, path)
