#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import random
from multiprocessing import Process

import uwsgi
from pyprometheus.contrib.uwsgi_features import UWSGICollector, UWSGIStorage
from pyprometheus.registry import BaseRegistry
from pyprometheus.utils.exposition import registry_to_text
try:
    xrange = xrange
except Exception:
    xrange = range


def test_uwsgi_collector():
    registry = BaseRegistry()
    uwsgi_collector = UWSGICollector(namespace="uwsgi_namespace", labels={"env_role": "test"})

    registry.register(uwsgi_collector)

    collectors = dict([(x.name, x) for x in registry.collect()])

    metrics_count = sorted(map(lambda x: x.split(' ')[2],
                           filter(lambda x: x.startswith('# HELP'), [x for x in registry_to_text(registry).split('\n')])))

    assert len(metrics_count) == len(set(metrics_count))

    assert len(registry_to_text(registry).split('\n')) == 60

    assert collectors['uwsgi_namespace:buffer_size_bytes'].get_samples()[0].value == uwsgi.buffer_size
    assert collectors['uwsgi_namespace:processes_total'].get_samples()[0].value == uwsgi.numproc
    assert collectors['uwsgi_namespace:requests_total'].get_samples()[0].value == uwsgi.total_requests()

    for name in ['requests', 'respawn_count', 'running_time', 'exceptions', 'delta_requests']:
        assert collectors['uwsgi_namespace:process:{0}'.format(name)].get_samples()[0].value == uwsgi.workers()[0][name]

    assert uwsgi_collector.metric_name("test") == "uwsgi_namespace:test"


DATA = (
    ((2, 'metric_gauge_name', '', (('label1', 'value1'), ('label2', 'value2'))), 5),
    ((3, 'metric_counter_name', '', (('label1', 'value1'), ('label2', 'value2'))), 7),
    ((5, 'metric_summary_name', '_sum', (('label1', 'value1'), ('label2', 'value2'))), 4),
    ((7, 'metric_summary_name', '_count', (('label1', 'value1'), ('label2', 'value2'))), 1),
    ((11, 'metric_histogram_name', '_sum', (('label1', 'value1'), ('label2', 'value2'))), 6),
    ((12, 'metric_histogram_name', '_count', (('label1', 'value1'), ('label2', 'value2'))), 1),
    ((13, 'metric_histogram_name', '_bucket', (('bucket', '0.005'), ('label1', 'value1'), ('label2', 'value2'))), 0),
    ((13, 'metric_histogram_name', '_bucket', (('bucket', '0.01'), ('label1', 'value1'), ('label2', 'value2'))), 0),
    ((13, 'metric_histogram_name', '_bucket', (('bucket', '7.5'), ('label1', 'value1'), ('label2', 'value2'))), 1),
    ((13, 'metric_histogram_name', '_bucket', (('bucket', '+Inf'), ('label1', 'value1'), ('label2', 'value2'))), 1),
    ((2, 'metric_gauge_name', '', (('label1', 'value3'), ('label2', 'value4'))), 5),
    ((3, 'metric_counter_name', '', (('label1', 'value3'), ('label2', 'value4'))), 7),
    ((5, 'metric_summary_name', '_sum', (('label1', 'value3'), ('label2', 'value4'))), 4),
    ((7, 'metric_summary_name', '_count', (('label1', 'value3'), ('label2', 'value4'))), 1),
    ((11, 'metric_histogram_name', '_sum', (('label1', 'value3'), ('label2', 'value4'))), 6),
    ((12, 'metric_histogram_name', '_count', (('label1', 'value3'), ('label2', 'value4'))), 1),
    ((13, 'metric_histogram_name', '_bucket', (('bucket', '0.005'), ('label1', 'value3'), ('label2', 'value4'))), 0),
    ((13, 'metric_histogram_name', '_bucket', (('bucket', 0.01), ('label1', 'value3'), ('label2', 'value4'))), 0),
    ((13, 'metric_histogram_name', '_bucket', (('bucket', 7.5), ('label1', 'value3'), ('label2', 'value4'))), 1),
    ((13, 'metric_histogram_name', '_bucket', (('bucket', float('inf')), ('label1', 'value3'), ('label2', 'value4'))), 1))


def test_uwsgi_storage():

    storage = UWSGIStorage(0)
    storage2 = UWSGIStorage(0)

    # 100 pages
    assert len(storage.m) == 409600 == 100 * 1024 * 4

    assert (storage.get_area_size()) == 14

    assert storage.m[15] == '\x00'

    with storage.lock():

        assert storage.wlocked
        assert storage.rlocked

    assert not storage.wlocked
    assert not storage.rlocked

    with storage.rlock():
        assert not storage.wlocked
        assert storage.rlocked

    assert not storage.wlocked
    assert not storage.rlocked

    assert storage.is_actual

    area_sign = storage.get_area_sign()

    assert area_sign == storage2.get_area_sign()

    storage.m[storage.SIGN_POSITION + 2] = os.urandom(1)

    assert not storage.is_actual

    s = 'keyname'
    assert storage.get_string_padding(s) == 5

    assert len(s.encode('utf-8')) + storage.get_string_padding(s) == 12

    assert storage.validate_actuality()

    assert storage.is_actual

    assert storage.get_key_position("keyname") == ([14, 18, 25, 33], True)

    assert (storage.get_area_size()) == 33

    assert storage.get_key_size("keyname") == 24

    storage.write_value('keyname', 10)

    assert storage.get_value('keyname') == 10.0

    storage.clear()

    assert storage.get_area_size() == 0 == storage2.get_area_size()

    storage.validate_actuality()

    assert storage.get_area_size() == 14 == storage2.get_area_size()

    storage.write_value(DATA[0][0], DATA[0][1])

    assert storage.get_key_size(DATA[0][0]) == 108

    assert storage.get_area_size() == 122 == storage2.get_area_size()

    assert storage2.get_value(DATA[0][0]) == DATA[0][1] == storage.get_value(DATA[0][0])

    for x in DATA:
        storage.write_value(x[0], x[1])
        assert storage.get_value(x[0]) == x[1]

    for x in DATA:
        assert storage.get_value(x[0]) == x[1]

    assert len(storage) == len(DATA) == 20

    assert storage.get_area_size() == 2531
    assert not storage2.is_actual

    assert storage.is_actual

    storage2.validate_actuality()

    for x in DATA:
        assert storage2.get_value(x[0]) == x[1]


def test_multiprocessing(measure_time):
    storage = UWSGIStorage(0)
    storage2 = UWSGIStorage(0)
    storage3 = UWSGIStorage(0)
    ITERATIONS = 500
    with measure_time("multiprocessing writes") as mt:
        def f1():
            for _ in xrange(ITERATIONS):
                for x in DATA:
                    storage.inc_value(x[0], x[1])

        def f2():
            for _ in xrange(ITERATIONS):
                for x in DATA:
                    storage2.inc_value(x[0], x[1])

        def f3():
            for _ in xrange(ITERATIONS):
                for x in DATA:
                    storage3.inc_value(x[0], x[1])

        workers = []
        for _ in xrange(10):
            func = random.choice([f1, f2, f3])
            p = Process(target=func)
            p.start()
            workers.append(p)

        for x in workers:
            x.join()

        mt.set_num_ops(ITERATIONS * len(workers) * len(DATA))

    with measure_time("multiprocessing reads") as mt:
        mt.set_num_ops(3 * len(DATA))

        for x in DATA:
            assert storage2.get_value(x[0]) == storage.get_value(x[0]) == storage3.get_value(x[0]) == x[1] * ITERATIONS * len(workers)
