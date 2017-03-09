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

from pyprometheus.const import TYPES
from pyprometheus.managers import TimerManager, InprogressTrackerManager, GaugeTimerManager


class MetricValue(object):
    """Base metric collector"""

    TYPE = TYPES.BASE
    POSTFIX = ""

    def __init__(self, metric, label_values={}, value=None):
        self._metric = metric
        self.validate_labels(metric.label_names, label_values)

        self._labels, self._label_values = self.prepare_labels(label_values)
        self._value = value

    @staticmethod
    def prepare_labels(label_values):
        if isinstance(label_values, (list, tuple)):
            labels = tuple(sorted(label_values, key=lambda x: x[0]))
        elif isinstance(label_values, dict):
            labels = tuple(sorted(label_values.items(), key=lambda x: x[0]))
        return labels, dict(label_values)

    @property
    def metric(self):
        return self._metric

    def set_value(self, value):
        self._value = value

    def __repr__(self):
        return u"<{0}[{1}]: {2} -> {3}>".format(
            self.__class__.__name__, self._metric.name,
            str(self._labels).replace("'", "\""), self.__repr_value__())

    def validate_labels(self, label_names, labels):
        if len(labels) != len(label_names):
            raise RuntimeError(u"Invalid label values size: {0} != {1}".format(
                len(label_names), len(labels)))

    def __repr_value__(self):
        return self.get()

    # def __str__(self):
    #     return u"{0}{1}".format(self.__class__.__name__, self._labels)

    @property
    def key(self):
        return (self.TYPE, self._metric.name, self.POSTFIX, self._labels)

    def inc(self, amount=1):
        return self._metric._storage.inc_value(self.key, amount)

    def get(self):
        # Do not lookup storage if value 0
        if self._value is not None:
            return self._value
        return self._metric._storage.get_value(self.key)

    @property
    def value(self):
        raise RuntimeError("Metric value")

    @property
    def export_str(self):
        return "{name}{postfix}{{{labels}}} {value} {timestamp}".format(
            name=self._metric.name, postfix=self.POSTFIX,
            labels=self.export_labels, timestamp=int(time.time() * 1000), value=float(self.value))

    @property
    def export_labels(self):
        return ", ".join(["{0}=\"{1}\"".format(self.format_export_label(name), self.format_export_value(value))
                          for name, value in self._labels])

    def format_export_label(self, label):
        if label == "bucket":
            return "le"
        return label

    def format_export_value(self, value):
        if value == float("inf"):
            return "+Inf"
        elif value == float("-inf"):
            return "-Inf"
        # elif math.isnan(value):
        #     return "NaN"
        return value


class GaugeValue(MetricValue):

    TYPE = TYPES.GAUGE

    def dec(self, amount=1):
        self.inc(-amount)

    def set(self, value):
        self._metric._storage.write_value(self.key, value)
        return value

    @property
    def value(self):
        return self.get()

    def track_in_progress(self):
        return InprogressTrackerManager(self)

    def set_to_current_time(self):
        return self.set(time.time())

    def time(self):
        return GaugeTimerManager(self)


class CounterValue(MetricValue):

    TYPE = TYPES.COUNTER

    @property
    def value(self):
        return self.get()


class SummarySumValue(CounterValue):
    TYPE = TYPES.SUMMARY_SUM
    POSTFIX = "_sum"


class SummaryCountValue(CounterValue):
    TYPE = TYPES.SUMMARY_COUNTER
    POSTFIX = "_count"


class SummaryQuantilyValue(GaugeValue):
    TYPE = TYPES.SUMMARY_QUANTILE

    POSTFIX = "_quantile"

    def __init__(self, metric, label_values={}, quantile=0, value=None):
        label_values = dict(label_values).copy()
        label_values["quantile"] = quantile
        self._quantile = quantile
        super(SummaryQuantilyValue, self).__init__(metric, label_values, value)

    def validate_labels(self, label_names, labels):
        if len(labels) != len(label_names) + 1:
            raise RuntimeError(u"Invalid label values size: {0} != {1}".format(
                len(label_names), len(labels) + 1))

    def __repr_value__(self):
        return u"{0} -> {1}".format(self._quantile, self._value)

    @property
    def key(self):
        return (self.TYPE, self._metric.name, self.POSTFIX, self._labels)
        # return (self.TYPE, self._metric.name, self._metric.name, self._labels)


class SummaryValue(MetricValue):
    u"""
    summary with a base metric name of <basename> exposes multiple time series during a scrape:

     streaming φ-quantiles (0 ≤ φ ≤ 1) of observed events, exposed as <basename>{quantile="<φ>"}
     the total sum of all observed values, exposed as <basename>_sum
     the count of events that have been observed, exposed as <basename>_count
    """

    TYPE = TYPES.SUMMARY

    SUBTYPES = {
        "_sum": SummarySumValue,
        "_count": SummaryCountValue,
        "_quantile": SummaryQuantilyValue
    }

    def __init__(self, metric, label_values={}, value={}):

        super(SummaryValue, self).__init__(metric, label_values=label_values)
        self._sum = value.pop("sum", None) or SummarySumValue(self._metric, label_values=self._label_values)
        self._count = value.pop("count", None) or SummaryCountValue(self._metric, label_values=self._label_values)
        if isinstance(self._metric.quantiles, (list, tuple)):

            self._quantiles = value.pop("quantiles", []) or [SummaryQuantilyValue(self._metric, label_values=self._label_values, quantile=quantile)
                                                             for quantile in self._metric.quantiles]
        else:
            self._quantiles = []

    def __repr_value__(self):
        return u"sum={sum} / count={count} = {value} [{quantiles}]".format(
            **{
                "sum": self._sum.value,
                "count": self._count.value,
                "value": (self._sum.value / self._count.value) if self._count.value != 0 else "-",
                "quantiles": ", ".join([x.__repr_value__() for x in self._quantiles]) if self._quantiles else "empty"
            }
        )

    def observe(self, amount):
        self._sum.inc(amount)
        self._count.inc()

        # TODO: calculate quantiles
        # for quantile, value in self._quantiles:
        #     pass

    @property
    def value(self):
        return {
            "sum": self._sum,
            "count": self._count,
            "quantiles": self._quantiles}

    @property
    def export_str(self):
        return "\n".join([self._sum.export_str, self._count.export_str] + [quantile.export_str for quantile in self._quantiles])

    def time(self):
        return TimerManager(self)


class HistogramCountValue(SummaryCountValue):
    TYPE = TYPES.HISTOGRAM_COUNTER
    POSTFIX = "_count"


class HistogramSumValue(SummarySumValue):
    TYPE = TYPES.HISTOGRAM_SUM
    POSTFIX = "_sum"


class HistogramBucketValue(SummaryCountValue):
    """
    """    """
    <basename>_bucket{le="<upper inclusive bound>"}
    """
    POSTFIX = "_bucket"
    TYPE = TYPES.HISTOGRAM_BUCKET

    def __init__(self, metric, label_values={}, bucket=None, value=None):
        label_values = dict(label_values).copy()
        label_values["bucket"] = bucket
        self._bucket_threshold = bucket
        super(HistogramBucketValue, self).__init__(metric, label_values, value)

    def __repr_value__(self):
        return u"{0} -> {1}".format(self._bucket_threshold, self._value)

    @property
    def bucket_threshold(self):
        return self._bucket_threshold

    def validate_labels(self, label_names, labels):
        if len(labels) != len(label_names) + 1:
            raise RuntimeError(u"Invalid label values size: {0} != {1}".format(
                len(label_names), len(labels) + 1))


class HistogramValue(MetricValue):
    TYPE = TYPES.HISTOGRAM

    SUBTYPES = {
        "_sum": HistogramSumValue,
        "_count": HistogramCountValue,
        "_bucket": HistogramBucketValue
    }

    def __init__(self, metric, label_values={}, value={}):
        self._buckets = []
        super(HistogramValue, self).__init__(metric, label_values=label_values)

        self._sum = value.pop("sum", None) or HistogramSumValue(self._metric, label_values=self._label_values)
        self._count = value.pop("count", None) or HistogramCountValue(self._metric, label_values=self._label_values)

        self._buckets = (value.pop("buckets", []) or [HistogramBucketValue(self._metric, label_values=self._label_values, bucket=bucket)
                                                      for bucket in sorted(self._metric.buckets)])

    def __repr_value__(self):
        return u"sum={sum} / count={count} = {value} [{buckets}]".format(
            **{
                "sum": self._sum.__repr_value__(),
                "count": self._count.__repr_value__(),
                "value": (self._sum.value / self._count.value) if self._count.value != 0 else "-",
                # "buckets": ""
                "buckets": ", ".join([x.__repr_value__() for x in self._buckets]) if self._buckets else "empty"
            }
        )

    def observe(self, amount):
        self._sum.inc(amount)
        self._count.inc()

        for bucket in self._buckets:
            bucket.inc(int(amount < bucket.bucket_threshold))

    @property
    def value(self):
        return {
            "sum": self._sum,
            "count": self._count,
            "buckets": self._buckets
        }

    @property
    def export_str(self):
        return "\n".join([self._sum.export_str, self._count.export_str] + [bucket.export_str for bucket in self._buckets])

    def time(self):
        return TimerManager(self)
