#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

import pytest
import uwsgi
import time
from pyprometheus.storage import BaseStorage
from pyprometheus.utils import measure_time as measure_time_manager
from pyprometheus.compat import PAD_SYMBOL, xrange


@pytest.fixture
def project_root():
    return os.path.dirname(os.path.abspath(__file__))


@pytest.yield_fixture(autouse=True)
def run_around_tests():
    m = uwsgi.sharedarea_memoryview(0)
    for x in xrange(len(m)):
        m[x] = PAD_SYMBOL

    yield


@pytest.fixture
def measure_time():
    return measure_time_manager


@pytest.fixture()
def iterations():
    return 500


@pytest.fixture()
def num_workers():
    return 10
