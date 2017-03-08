#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pyprometheus.metrics
~~~~~~~~~~~~~~~~~~~~

Prometheus instrumentation library for Python applications

:copyright: (c) 2017 by Alexandr Lispython.
:license: , see LICENSE for more details.
:github: http://github.com/Lispython/pyprometheus
"""

from pyprometheus.const import TYPES
from pyprometheus.values import (MetricValue, GaugeValue,
                                 CounterValue, SummaryValue,
                                 HistogramValue)
class BaseMetric(object):

    value_class = MetricValue

    NOT_ALLOWED_LABELS = set()

    TYPE = "untyped"

    PARENT_METHODS = set()

    def __init__(self, name, doc, labels=[], registry=None):
        self._name = name
        self._doc = doc
        self._labelnames = tuple(sorted(labels))
        self.validate_labelnames(labels)
        self._storage = None

        if registry is not None:
            self.add_to_registry(registry)

        self._samples = {}

        self._labels_cache = {}

    def __repr__(self):
        return u"<{0}[{1}]: {2} samples>".format(self.__class__.__name__, self._name, len(self._samples))

    def get_proxy(self):
        if self._labelnames:
            raise RuntimeError("You need to use labels")
        return self.value_class(self, label_values={})

    def validate_labelnames(self, names):
        for name in names:
            if name in self.NOT_ALLOWED_LABELS:
                raise RuntimeError("Label name {0} not allowed for {1}".format(name, self.__class__.__name__))
        return True

    @property
    def name(self):
        return self._name

    @property
    def doc(self):
        return self._doc

    @property
    def label_names(self):
        return self._labelnames

    @property
    def uid(self):
        return "{0}-{1}".format(self._name, str(self._labelnames))

    def add_to_registry(self, registry):
        """Add metric to registry
        """
        registry.register(self)
        self._storage = registry.storage
        return self

    def labels(self, *args, **kwargs):
        if args and isinstance(args[0], dict):
            label_values = self.value_class.prepare_labels(args[0])[0]
        else:
            label_values = self.value_class.prepare_labels(kwargs)[0]
        return self._labels_cache.setdefault((label_values, self.value_class.TYPE),
                                             self.value_class(self, label_values=label_values))

    @property
    def text_export_header(self):
        """
        Format description lines for collector
        # HELP go_gc_duration_seconds A summary of the GC invocation durations.
        # TYPE go_gc_duration_seconds summary
        """
        return "\n".join(["# HELP {name} {doc}",
                          "# TYPE {name} {metric_type}"]).format(
                          name=self.name,
                          doc=self.doc,
                          metric_type=self.TYPE)

    def build_samples(self, items):
        """Build samples from objects

        [((2, "metric_gauge_name", "", (("label1", "value3"), ("label2", "value4"))), 5.0)]
        """
        for label_values, data in items:
            self.add_sample(label_values, self.build_sample(label_values, data))
        return self

    def build_sample(self, label_values, item):
        """Build value object from given data
        """
        return self.value_class(self, label_values=label_values, value=item[0][-1])


    def add_sample(self, label_values, value):
        self._samples[tuple(sorted(label_values, key=lambda x: x[0]))] = value

    def get_samples(self):
        """Get samples from storage
        """
        return self._samples.values()


    def __getattr__(self, name):
        if name in self.PARENT_METHODS:
            return getattr(self.get_proxy(), name)

        raise AttributeError
        # return super(BaseMetric, self).__getattr__(name)


class Gauge(BaseMetric):

    TYPE = "gauge"

    value_class = GaugeValue

    PARENT_METHODS = set(("inc", "dec", "set", "get", "track_inprogress",
                        "set_to_current_time", "time", "value"))


class Counter(BaseMetric):
    TYPE = "counter"

    value_class = CounterValue

    PARENT_METHODS = set(("inc", "get", "value"))


class Summary(BaseMetric):

    TYPE = "summary"
    DEFAULT_QUANTILES = (0, 0.25, 0.5, 0.75, 1)

    value_class = SummaryValue

    NOT_ALLOWED_LABELS = set("quantile")

    PARENT_METHODS = set(("observe", "value", "time"))

    def __init__(self, name, doc, labels=[], quantiles=False, registry=None):
        self._quantiles = list(sorted(quantiles)) if quantiles else []
        super(Summary, self).__init__(name, doc, labels, registry)

    @property
    def quantiles(self):
        return self._quantiles

    def build_sample(self, label_values, data):
        subtypes = {
            "sum": None,
            "count": None,
            "quantiles": [] if isinstance(self._quantiles, (list, tuple)) else None
        }

        for meta, value in data:
            value_class = self.value_class.SUBTYPES[meta[2]]

            if meta[0] == TYPES.SUMMARY_SUM:
                subtypes["sum"] = value_class(self, label_values=label_values, value=value)
            elif meta[0] == TYPES.SUMMARY_COUNTER:
                subtypes["count"] = value_class(self, label_values=label_values, value=value)
            elif meta[0] == TYPES.SUMMARY_QUANTILE:
                quantile = dict(meta[3])["quantile"]
                subtypes["quantiles"].append(
                    value_class(self, label_values=label_values, quantile=quantile, value=value))

        return self.value_class(self, label_values=label_values, value=subtypes)


class Histogram(BaseMetric):
    TYPE = "histogram"

    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5,
                       0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float("inf"))

    NOT_ALLOWED_LABELS = set("le")

    value_class = HistogramValue

    PARENT_METHODS = set(("observe", "value", "time"))

    def __init__(self, name, doc, labels=[], buckets=DEFAULT_BUCKETS, registry=None):
        self._buckets = list(sorted(buckets)) if buckets else []
        super(Histogram, self).__init__(name, doc, labels, registry)

    @property
    def buckets(self):
        return self._buckets


    def build_sample(self, label_values, data):
        subtypes = {
            "sum": None,
            "count": None,
            "buckets": [] if isinstance(self._buckets, (list, tuple)) else None
        }

        for meta, value in data:
            value_class = self.value_class.SUBTYPES[meta[2]]

            if meta[0] == TYPES.HISTOGRAM_SUM:
                subtypes["sum"] = value_class(self, label_values=label_values, value=value)
            elif meta[0] == TYPES.HISTOGRAM_COUNTER:
                subtypes["count"] = value_class(self, label_values=label_values, value=value)
            elif meta[0] == TYPES.HISTOGRAM_BUCKET:
                bucket = dict(meta[3])["bucket"]
                subtypes["buckets"].append(
                    value_class(self, label_values=label_values, bucket=bucket, value=value))

        return self.value_class(self, label_values=label_values, value=subtypes)
