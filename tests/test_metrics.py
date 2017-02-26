#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from pyprometheus.metrics import BaseMetric, Gauge, Counter, Histogram, Summary
from pyprometheus.registry import BaseRegistry
from pyprometheus.values import MetricValue
from pyprometheus.storage import LocalMemoryStorage
from pyprometheus.contrib.uwsgi_features import UWSGIStorage


@pytest.mark.parametrize("storage_cls", [LocalMemoryStorage, UWSGIStorage])
def test_base_metric(storage_cls):
    storage = storage_cls()
    registry = BaseRegistry(storage=storage)
    metric_name = "test_base_metric"
    metric = BaseMetric(metric_name, "test_base_metric doc", ('label1', 'label2'), registry=registry)

    assert registry.is_registered(metric)
    assert repr(metric) == "<BaseMetric[test_base_metric]: 0 samples>"

    with pytest.raises(RuntimeError) as exc_info:
        registry.register(metric)

        assert str(exc_info.value) == u"Collector {0} already registered.".format(metric.uid)

    with pytest.raises(RuntimeError) as exc_info:
        metric.add_to_registry(registry)

        assert str(exc_info.value) == u"Collector {0} already registered.".format(metric.uid)

    labels = metric.labels({'label1': 'label1_value', 'label2': 'label2_value'})

    assert isinstance(labels, MetricValue)

    labels.inc(1)

    assert labels.get() == 1

    assert metric.text_export_header == '\n'.join(["# HELP test_base_metric test_base_metric doc",
                                                   "# TYPE test_base_metric untyped"])


@pytest.mark.parametrize("storage_cls", [LocalMemoryStorage, UWSGIStorage])
def test_counter_metric(storage_cls):
    storage = storage_cls()

    registry = BaseRegistry(storage=storage)
    metric_name = "counter_metric_name"
    metric = Counter(metric_name, "counter_metric_name doc", ('label1', 'label2'), registry=registry)

    assert registry.is_registered(metric)

    assert repr(metric) == u"<Counter[counter_metric_name]: 0 samples>"

    with pytest.raises(RuntimeError) as exc_info:
        registry.register(metric)

        assert str(exc_info.value) == u"Collector {0} already registered.".format(metric.uid)

    with pytest.raises(RuntimeError) as exc_info:
        metric.add_to_registry(registry)

        assert str(exc_info.value) == u"Collector {0} already registered.".format(metric.uid)

    labels = metric.labels({'label1': 'label1_value', 'label2': 'label2_value'})

    assert labels.get() == 0

    labels.inc(10)

    assert labels.get() == 10

    assert repr(labels) == str(labels)

    assert str(labels) == "<CounterValue[counter_metric_name]: (('label1', 'label1_value'), ('label2', 'label2_value')) -> 10.0>"

    assert labels.key == (labels.TYPE, metric_name, labels.POSTFIX,
                          (('label1', 'label1_value'), ('label2', 'label2_value')))

    assert metric.text_export_header == '\n'.join(["# HELP counter_metric_name counter_metric_name doc",
                                                   "# TYPE counter_metric_name counter"])


def test_gauge_metric():
    storage = LocalMemoryStorage()

    registry = BaseRegistry(storage=storage)
    metric_name = "gauge_metric_name"
    metric = Gauge(metric_name, metric_name + " doc", ('label1', 'label2'), registry=registry)
    assert registry.is_registered(metric)

    assert repr(metric) == "<Gauge[gauge_metric_name]: 0 samples>"

    with pytest.raises(RuntimeError) as exc_info:
        registry.register(metric)

        assert str(exc_info.value) == u"Collector {0} already registered.".format(metric.uid)

    with pytest.raises(RuntimeError) as exc_info:
        metric.add_to_registry(registry)

        assert str(exc_info.value) == u"Collector {0} already registered.".format(metric.uid)

    labels = metric.labels({'label1': 'label1_value', 'label2': 'label2_value'})

    assert labels.get() == 0

    labels.inc(10)

    assert labels.get() == 10

    assert repr(labels) == str(labels)
    assert str(labels) == "<GaugeValue[gauge_metric_name]: (('label1', 'label1_value'), ('label2', 'label2_value')) -> 10.0>"

    assert labels.key == (labels.TYPE, metric_name, labels.POSTFIX,
                          (('label1', 'label1_value'), ('label2', 'label2_value')))

    assert metric.text_export_header == '\n'.join(["# HELP gauge_metric_name gauge_metric_name doc",
                                                   "# TYPE gauge_metric_name gauge"])


@pytest.mark.parametrize("storage_cls", [LocalMemoryStorage, UWSGIStorage])
def test_summary(storage_cls):
    storage = storage_cls()

    registry = BaseRegistry(storage=storage)
    metric_name = "summary_metric_name"
    metric = Summary(metric_name, "summary_metric_name doc", ('label1', 'label2'), registry=registry)

    assert registry.is_registered(metric)

    assert repr(metric) == u"<Summary[summary_metric_name]: 0 samples>"

    with pytest.raises(RuntimeError) as exc_info:
        registry.register(metric)

        assert str(exc_info.value) == u"Collector {0} already registered.".format(metric.uid)

    with pytest.raises(RuntimeError) as exc_info:
        metric.add_to_registry(registry)

        assert str(exc_info.value) == u"Collector {0} already registered.".format(metric.uid)

    labels = metric.labels({'label1': 'label1_value', 'label2': 'label2_value'})

    labels.observe(10)

    value = labels.value

    assert value['sum'].value == 10
    assert value['count'].value == 1

    labels.observe(14)

    assert value['sum'].value == 24
    assert value['count'].value == 2

    assert value['quantiles'] == []

    assert str(value['sum']) == "<SummarySumValue[summary_metric_name]: (('label1', 'label1_value'), ('label2', 'label2_value')) -> 24.0>"
    assert str(value['count']) == "<SummaryCountValue[summary_metric_name]: (('label1', 'label1_value'), ('label2', 'label2_value')) -> 2.0>"

    assert value['sum'].key == (value['sum'].TYPE, 'summary_metric_name', value['sum'].POSTFIX, (('label1', 'label1_value'), ('label2', 'label2_value')))
    assert value['count'].key == (value['count'].TYPE, 'summary_metric_name', value['count'].POSTFIX, (('label1', 'label1_value'), ('label2', 'label2_value')))

    assert metric.text_export_header == '\n'.join(["# HELP summary_metric_name summary_metric_name doc",
                                                   "# TYPE summary_metric_name summary"])


@pytest.mark.parametrize("storage_cls", [LocalMemoryStorage, UWSGIStorage])
def test_histogram(storage_cls):
    storage = storage_cls()

    registry = BaseRegistry(storage=storage)
    metric_name = "histogram_metric_name"
    metric = Histogram(metric_name, "histogram_metric_name doc", ('label1', 'label2'), registry=registry)

    assert repr(metric) == u"<Histogram[histogram_metric_name]: 0 samples>"

    with pytest.raises(RuntimeError) as exc_info:
        registry.register(metric)

        assert str(exc_info.value) == u"Collector {0} already registered.".format(metric.uid)

    with pytest.raises(RuntimeError) as exc_info:
        metric.add_to_registry(registry)

        assert str(exc_info.value) == u"Collector {0} already registered.".format(metric.uid)

    labels = metric.labels({'label1': 'label1_value', 'label2': 'label2_value'})
    labels.observe(2.4)

    value = labels.value

    assert value['sum'].value == 2.4
    assert value['count'].value == 1

    assert str(value['sum']) == "<HistogramSumValue[histogram_metric_name]: (('label1', 'label1_value'), ('label2', 'label2_value')) -> 2.4>"
    assert str(value['count']) == "<HistogramCountValue[histogram_metric_name]: (('label1', 'label1_value'), ('label2', 'label2_value')) -> 1.0>"

    labels.observe(0.06)

    assert str(value['sum']) == "<HistogramSumValue[histogram_metric_name]: (('label1', 'label1_value'), ('label2', 'label2_value')) -> 2.46>"
    assert str(value['count']) == "<HistogramCountValue[histogram_metric_name]: (('label1', 'label1_value'), ('label2', 'label2_value')) -> 2.0>"

    buckets = dict([(x.bucket_threshold, x) for x in value['buckets']])
    assert buckets[0.025].value == 0
    assert buckets[0.075].value == 1
    assert buckets[2.5].value == 2
    assert buckets[float('inf')].value == 2

    assert value['sum'].key == (value['sum'].TYPE, 'histogram_metric_name', value['sum'].POSTFIX, (('label1', 'label1_value'), ('label2', 'label2_value')))
    assert value['count'].key == (value['count'].TYPE, 'histogram_metric_name', value['count'].POSTFIX, (('label1', 'label1_value'), ('label2', 'label2_value')))

    assert metric.text_export_header == '\n'.join(["# HELP histogram_metric_name histogram_metric_name doc",
                                                   "# TYPE histogram_metric_name histogram"])
