#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from pyprometheus.registry import BaseRegistry
from pyprometheus.metrics import BaseMetric, Gauge, Counter, Histogram, Summary
from pyprometheus.storage import LocalMemoryStorage
from pyprometheus.contrib.uwsgi_features import UWSGIStorage
from pyprometheus.utils.exposition import registry_to_text, write_to_textfile


CONTROL_EXPORT = """
# HELP metric_counter_name doc_counter
# TYPE metric_counter_name counter
metric_counter_name{label1="value1", label2="value2"} 7.0 1487933466491
metric_counter_name{label1="value3", label2="value4"} 7.0 1487933466491
# HELP metric_summary_name doc_summary
# TYPE metric_summary_name summary
metric_summary_name_sum{label1="value1", label2="value2"} 4.0 1487933466491
metric_summary_name_count{label1="value1", label2="value2"} 1.0 1487933466491
metric_summary_name_sum{label1="value3", label2="value4"} 4.0 1487933466491
metric_summary_name_count{label1="value3", label2="value4"} 1.0 1487933466492
# HELP metric_untyped_name doc_untyped
# TYPE metric_untyped_name untyped
# HELP metric_histogram_name doc_histogram
# TYPE metric_histogram_name histogram
metric_histogram_name_sum{label1="value1", label2="value2"} 6.0 1487933466492
metric_histogram_name_count{label1="value1", label2="value2"} 1.0 1487933466492
metric_histogram_name_bucket{le="0.005", label1="value1", label2="value2"} 0.0 1487933466492
metric_histogram_name_bucket{le="0.01", label1="value1", label2="value2"} 0.0 1487933466493
metric_histogram_name_bucket{le="7.5", label1="value1", label2="value2"} 1.0 1487933466494
metric_histogram_name_bucket{le="+Inf", label1="value1", label2="value2"} 1.0 1487933466494
metric_histogram_name_sum{label1="value3", label2="value4"} 6.0 1487933466494
metric_histogram_name_count{label1="value3", label2="value4"} 1.0 1487933466494
metric_histogram_name_bucket{le="0.005", label1="value3", label2="value4"} 0.0 1487933466494
metric_histogram_name_bucket{le="0.01", label1="value3", label2="value4"} 0.0 1487933466495
metric_histogram_name_bucket{le="+Inf", label1="value3", label2="value4"} 1.0 1487933466496
metric_histogram_name_bucket{le="7.5", label1="value3", label2="value4"} 1.0 1487933466496
# HELP metric_gauge_name doc_gauge
# TYPE metric_gauge_name gauge
metric_gauge_name{label1="value1", label2="value2"} 5.0 1487933466497
metric_gauge_name{label1="value3", label2="value4"} 5.0 1487933466497"""


@pytest.mark.parametrize("storage_cls", [LocalMemoryStorage, UWSGIStorage])
def test_base_registry(storage_cls, measure_time):
    storage = storage_cls()
    registry = BaseRegistry(storage=storage)

    assert registry.storage == storage

    name_template = "metric_{0}_name"
    doc_template = "doc_{0}"
    metrics = {}
    labels = ("label1", "label2")
    labelnames = ("value1", "value2")

    for metric_class in [
            BaseMetric,
            Counter,
            Gauge,
            Summary]:
        metrics[metric_class.TYPE] = metric_class(
            name_template.format(metric_class.TYPE),
            doc_template.format(metric_class.TYPE),
            labels, registry=registry)

    metrics[Histogram.TYPE] = Histogram(
        name_template.format(Histogram.TYPE),
        doc_template.format(Histogram.TYPE),
        labels,
        buckets=(0.005, 0.01, 7.5, float("inf")),
        registry=registry
    )

    for k, v in metrics.items():
        assert registry.is_registered(v)

        registry.unregister(v)

        assert not registry.is_registered(v)

    for k, v in metrics.items():
        assert not registry.is_registered(v)

        registry.register(v)

        assert registry.is_registered(v)

    assert len(registry) == 5
    assert len(registry.collectors()) == 5

    labels_dict = dict(zip(labels, labelnames))

    metrics["gauge"].labels(**labels_dict).inc(5)
    metrics["counter"].labels(**labels_dict).inc(7)
    metrics["summary"].labels(**labels_dict).observe(4)
    metrics["histogram"].labels(**labels_dict).observe(6)

    labelnames2 = ("value3", "value4")
    labels_dict2 = dict(zip(labels, labelnames2))

    metrics["gauge"].labels(**labels_dict2).inc(5)
    metrics["counter"].labels(**labels_dict2).inc(7)
    metrics["summary"].labels(**labels_dict2).observe(4)
    metrics["histogram"].labels(**labels_dict2).observe(6)

    assert len(list(registry.get_samples())) == 5

    write_to_textfile(registry, "/tmp/metrics.prom")

    lines = []

    with open("/tmp/metrics.prom") as f:
        for x in f:
            if x:
                lines.append(x.strip())

    with measure_time("registry to text"):

        for test1, test2 in zip(registry_to_text(registry).split("\n")[4:], lines[4:]):
            if test1.startswith("#"):
                assert test1 == test2
            else:
                assert test1.split()[:-1] == test2.split()[:-1]

    metrics_count = map(lambda x: x.split(" ")[2],
                        filter(lambda x: x.startswith("# HELP"), [x for x in registry_to_text(registry).split("\n")]))

    assert len(metrics_count) == len(set(metrics_count))
