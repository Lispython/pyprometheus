#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pyprometheus.storage import BaseStorage, LocalMemoryStorage
import random
import threading

try:
    xrange = xrange
except Exception:
    xrange = range

DATA = (
    ((2, "metric_gauge_name", "", (("label1", "value1"), ("label2", "value2"))), 5),
    ((3, "metric_counter_name", "", (("label1", "value1"), ("label2", "value2"))), 7),
    ((5, "metric_summary_name", "_sum", (("label1", "value1"), ("label2", "value2"))), 4),
    ((7, "metric_summary_name", "_count", (("label1", "value1"), ("label2", "value2"))), 1),
    ((11, "metric_histogram_name", "_sum", (("label1", "value1"), ("label2", "value2"))), 6),
    ((12, "metric_histogram_name", "_count", (("label1", "value1"), ("label2", "value2"))), 1),
    ((13, "metric_histogram_name", "_bucket", (("bucket", 0.005), ("label1", "value1"), ("label2", "value2"))), 0),
    ((13, "metric_histogram_name", "_bucket", (("bucket", 0.01), ("label1", "value1"), ("label2", "value2"))), 0),
    ((13, "metric_histogram_name", "_bucket", (("bucket", 7.5), ("label1", "value1"), ("label2", "value2"))), 1),
    ((13, "metric_histogram_name", "_bucket", (("bucket", float("inf")), ("label1", "value1"), ("label2", "value2"))), 1),
    ((2, "metric_gauge_name", "", (("label1", "value3"), ("label2", "value4"))), 5),
    ((3, "metric_counter_name", "", (("label1", "value3"), ("label2", "value4"))), 7),
    ((5, "metric_summary_name", "_sum", (("label1", "value3"), ("label2", "value4"))), 4),
    ((7, "metric_summary_name", "_count", (("label1", "value3"), ("label2", "value4"))), 1),
    ((11, "metric_histogram_name", "_sum", (("label1", "value3"), ("label2", "value4"))), 6),
    ((12, "metric_histogram_name", "_count", (("label1", "value3"), ("label2", "value4"))), 1),
    ((13, "metric_histogram_name", "_bucket", (("bucket", 0.005), ("label1", "value3"), ("label2", "value4"))), 0),
    ((13, "metric_histogram_name", "_bucket", (("bucket", 0.01), ("label1", "value3"), ("label2", "value4"))), 0),
    ((13, "metric_histogram_name", "_bucket", (("bucket", 7.5), ("label1", "value3"), ("label2", "value4"))), 1),
    ((13, "metric_histogram_name", "_bucket", (("bucket", float("inf")), ("label1", "value3"), ("label2", "value4"))), 1))


def test_base_storage():
    storage = BaseStorage()

    assert isinstance(storage, BaseStorage)


def test_local_memory_storage():
    storage = LocalMemoryStorage()

    assert len(storage) == 0

    key1 = (1,
            "metric_name1",
            "",
            (("key1", "value1"),
             ("key2", "value2")))

    key2 = (1,
            "metric_name2",
            "",
            (("key1", "value1"),
             ("key2", "value2")))

    storage.inc_value(key1, 1)
    assert storage.get_value(key1) == 1.0

    storage.inc_value(key2, 4)
    assert storage.get_value(key2) == 4.0

    storage.write_value(key1, 40)

    assert storage.get_value(key1) == 40.0

    storage.clear()
    assert len(storage) == 0

    storage = LocalMemoryStorage()

    for k, v in DATA:
        storage.write_value(k, v)

    assert len(storage) == len(DATA)

    items = list(storage.items())
    assert len(items) == 4

    for name, labels in items:

        if name == "metric_counter_name":
            for label, label_data in labels:
                assert len(label_data) == 1
        if name == "metric_gauge_name":
            for label, label_data in labels:
                assert len(label_data) == 1

        if name == "metric_histogram_name":
            for label, label_data in labels:
                assert len(label_data) == 6

        if name == "metric_summary_name":
            for label, label_data in labels:
                assert len(label_data) == 2

        assert len(labels) == 2

    assert len(items) == 4


def test_local_storage_threading(measure_time, iterations, num_workers):
    storage = LocalMemoryStorage()

    ITERATIONS = iterations

    with measure_time("threading writes") as mt:
        def f1():
            for _ in xrange(ITERATIONS):
                for x in DATA:
                    storage.inc_value(x[0], x[1])

        def f2():
            for _ in xrange(ITERATIONS):
                for x in DATA:
                    storage.inc_value(x[0], x[1])

        def f3():
            for _ in xrange(ITERATIONS):
                for x in DATA:
                    storage.inc_value(x[0], x[1])

        workers = []
        for _ in xrange(num_workers):
            func = random.choice([f1, f2, f3])
            t = threading.Thread(target=func)

            t.start()
            workers.append(t)

        for x in workers:
            x.join()

        mt.set_num_ops(ITERATIONS * len(workers) * len(DATA))

    with measure_time("threading reads") as mt:
        mt.set_num_ops(len(DATA))

        for x in DATA:
            assert storage.get_value(x[0]) == x[1] * ITERATIONS * len(workers)
