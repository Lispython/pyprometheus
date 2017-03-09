#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pyprometheus.contrib.uwsgi_features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

UWSGI server process collector and storage

:copyright: (c) 2017 by Alexandr Lispython.
:license: , see LICENSE for more details.
:github: http://github.com/Lispython/pyprometheus
"""

import marshal
import os
import struct
import uuid
import copy
from contextlib import contextmanager
from logging import getLogger
from pyprometheus.const import TYPES
from pyprometheus.metrics import Gauge, Counter
from pyprometheus.storage import BaseStorage, LocalMemoryStorage


try:
    import uwsgi
except ImportError:
    uwsgi = None

try:
    xrange = xrange
except Exception:
    xrange = range


class InvalidUWSGISharedareaPagesize(Exception):
    pass

logger = getLogger("pyprometheus.uwsgi_features")


class UWSGICollector(object):
    """Grap UWSGI stats and export to prometheus
    """
    def __init__(self, namespace, labels={}):
        self._namespace = namespace
        self._labels = tuple(sorted(labels.items(), key=lambda x: x[0]))
        self._collectors = self.declare_metrics()

    @property
    def uid(self):
        return "uwsgi-collector:{0}".format(self._namespace)

    def get_samples(self):
        """Get uwsgi stats
        """
        for collector in self.collect():
            yield collector, collector.get_samples()

    @property
    def text_export_header(self):
        return "# UWSGI stats metrics"

    def metric_name(self, name):
        """Make metric name with namespace

        :param name:
        """
        return ":".join([self._namespace, name])

    def declare_metrics(self):
        return {
            "memory": Gauge(self.metric_name("uwsgi_memory_bytes"), "UWSGI memory usage in bytes", ("type",) + self._labels),
            "processes": Gauge(self.metric_name("processes_total"), "Number of UWSGI processes", self._labels),
            "worker_status": Gauge(self.metric_name("worker_status_totla"), "Current workers status", self._labels),
            "total_requests": Gauge(self.metric_name("requests_total"), "Total processed request", self._labels),
            "buffer_size": Gauge(self.metric_name("buffer_size_bytes"), "UWSGI buffer size in bytes", self._labels),
            "started_on": Gauge(self.metric_name("started_on"), "UWSGI started on timestamp", self._labels),
            "cores": Gauge(self.metric_name("cores"), "system cores", self._labels),


            "process:respawn_count": Gauge(self.metric_name("process:respawn_count"), "Process respawn count", ("id", ) + self._labels),
            "process:last_spawn": Gauge(self.metric_name("process:last_spawn"), "Process last spawn", ("id", ) + self._labels),
            "process:signals": Gauge(self.metric_name("process:signals"), "Process signals total", ("id", ) + self._labels),
            "process:avg_rt": Gauge(self.metric_name("process:avg_rt"), "Process average response time", ("id", ) + self._labels),
            "process:tx": Gauge(self.metric_name("process:tx"), "Process transmitted data", ("id",) + self._labels),

            "process:status": Gauge(self.metric_name("process:status"), "Process status", ("id", "status") + self._labels),
            "process:running_time": Gauge(self.metric_name("process:running_time"), "Process running time", ("id", ) + self._labels),
            "process:exceptions": Gauge(self.metric_name("process:exceptions"), "Process exceptions", ("id", ) + self._labels),
            "process:requests": Gauge(self.metric_name("process:requests"), "Process requests", ("id", ) + self._labels),
            "process:delta_requests": Gauge(self.metric_name("process:delta_requests"), "Process delta_requests", ("id", ) + self._labels),
            "process:rss": Gauge(self.metric_name("process:rss"), "Process rss memory", ("id", ) + self._labels),
            "process:vsz": Gauge(self.metric_name("process:vzs"), "Process vsz address space", ("id", ) + self._labels),
        }

    def collect(self):
        for name, value in [("processes", uwsgi.numproc),
                            ("total_requests", uwsgi.total_requests()),
                            ("buffer_size", uwsgi.buffer_size),
                            ("started_on", uwsgi.started_on),
                            ("cores", uwsgi.cores)]:
            yield self.get_sample(name, value)

        yield self.get_memory_samples()

        for x in self.get_workers_samples(uwsgi.workers()):
            yield x


    def get_workers_samples(self, workers):
        """Read worker stats and create samples

        :param worker: worker stats
        """
        for name in ["requests", "respawn_count", "running_time",
                     "exceptions", "delta_requests",
                     "rss", "vsz", "last_spawn", "tx", "avg_rt", "signals"]:
            metric = self._collectors["process:" + name]

            for worker in workers:
                labels = self._labels + (("id", worker["id"]),)
                metric.add_sample(labels, metric.build_sample(labels,
                                  (  (TYPES.GAUGE, metric.name, "", labels, worker[name]),  )))

            yield metric

        metric = self._collectors["process:status"]
        for worker in workers:
            labels = self._labels + (("id", worker["id"]), ("status", worker["status"]))
            metric.add_sample(labels, metric.build_sample(labels,
                                (  (TYPES.GAUGE, metric.name, "", self._labels + (("id", worker["id"]), ("status", worker["status"])), 1),  )))

        yield metric

    def get_sample(self, name, value):
        """Create sample for given name and value

        :param name:
        :param value:
        """
        metric = self._collectors[name]
        return metric.build_samples([(self._labels, (  (TYPES.GAUGE, metric.name, "", self._labels, float(value)),  ))])

    def get_memory_samples(self):
        """Get memory usage samples
        """
        metric = self._collectors["memory"]
        return metric.build_samples(
            [(self._labels + (("type", "rss"),), (  (TYPES.GAUGE, metric.name, "", self._labels + (("type", "rss"),), uwsgi.mem()[0]),  )),
             (self._labels + (("type", "vsz"),), (  (TYPES.GAUGE, metric.name, "", self._labels + (("type", "vsz"),), uwsgi.mem()[1]),  ))])


class UWSGIStorage(BaseStorage):
    """A dict of doubles, backend by uwsgi sharedarea"""

    SHAREDAREA_ID = int(os.environ.get("PROMETHEUS_UWSGI_SHAREDAREA", 0))
    KEY_SIZE_SIZE = 4
    KEY_VALUE_SIZE = 8
    SIGN_SIZE = 10
    AREA_SIZE_SIZE = 4
    SIGN_POSITION = 4
    AREA_SIZE_POSITION = 0

    def __init__(self, sharedarea_id=SHAREDAREA_ID, namespace="", stats=False, labels={}):
        self._sharedarea_id = sharedarea_id
        self._used = None
        # Changed every time then keys added
        self._sign = None
        self._positions = {}
        self._rlocked = False
        self._wlocked = False
        self._keys_cache = {}
        self._namespace = namespace
        self._stats = stats
        self._labels = tuple(sorted(labels.items(), key=lambda x: x[0]))

        self._m = uwsgi.sharedarea_memoryview(self._sharedarea_id)

        self.init_memory()

        self._collectors = self.declare_metrics()

    @property
    def uid(self):
        return "uwsgi-storage:{0}".format(self._namespace)

    @property
    def text_export_header(self):
        return "# {0} stats metrics".format(self.__class__.__name__)

    def metric_name(self, name):
        """Make metric name with namespace

        :param name:
        """
        return ":".join([self._namespace, name])

    def declare_metrics(self):
        return {
            "memory_sync": Counter(self.metric_name("memory_read"), "UWSGI shared memory syncs", ("sharedarea", ) + self._labels),
            "memory_size": Gauge(self.metric_name("memory_size"), "UWSGI shared memory size", ("sharedarea", ) + self._labels),
            "num_keys": Gauge(self.metric_name("num_keys"), "UWSGI num_keys", ("sharedarea", ) + self._labels)
        }

    def collect(self):
        labels = self._labels + (("sharedarea", self._sharedarea_id), )
        # metric = self._collectors["memory_sync"]
        # metric.add_sample(labels, metric.build_sample(labels, (   (TYPES.GAUGE, metric.name, "", labels, ) ))

        # yield metric
        metric = self._collectors["memory_size"]

        metric.add_sample(labels, metric.build_sample(labels, (   (TYPES.GAUGE, metric.name, "", labels, self.get_area_size()), )))

        yield metric

        metric = self._collectors["num_keys"]
        metric.add_sample(labels, metric.build_sample(labels, (   (TYPES.GAUGE, metric.name, "", labels, len(self._positions)), )))

        yield metric


    @property
    def m(self):
        return self._m

    @property
    def wlocked(self):
        return self._wlocked

    @wlocked.setter
    def wlocked(self, value):
        self._wlocked = value
        return self._wlocked

    @property
    def rlocked(self):
        return self._rlocked

    @rlocked.setter
    def rlocked(self, value):
        self._rlocked = value
        return self._rlocked

    def serialize_key(self, key):
        try:
            return self._keys_cache[key]
        except KeyError:
            self._keys_cache[key] = val = marshal.dumps(key)
            return val

    def unserialize_key(self, serialized_key):
        return marshal.loads(serialized_key)

    def get_area_size_with_lock(self):
        with self.lock():
            return self.get_area_size()

    def get_slice(self, start, size):
        return slice(start, start+size)

    def get_area_size(self):
        """Read area size from uwsgi
        """
        return struct.unpack(b"i", self.m[self.get_slice(self.AREA_SIZE_POSITION, self.AREA_SIZE_SIZE)])[0]

    def init_area_size(self):
        return self.update_area_size(self.AREA_SIZE_SIZE)

    def update_area_size(self, size):
        self._used = size
        self.m[self.get_slice(self.AREA_SIZE_POSITION, self.AREA_SIZE_SIZE)] = struct.pack(b"i", size)
        return True

    def update_area_sign(self):
        self._sign = os.urandom(self.SIGN_SIZE)
        self.m[self.get_slice(self.SIGN_POSITION, self.SIGN_SIZE)] = self._sign


    def get_area_sign(self):
        """Get current area sign from memory
        """
        return self.m[self.get_slice(self.SIGN_POSITION, self.SIGN_SIZE)].tobytes()

    def init_memory(self, validation=True):
        """Initialize default memory addresses
        """
        with self.lock():
            if self._used is None:
                self._used = self.get_area_size()

            if self._used == 0:
                self.update_area_sign()
                self.update_area_size(self.SIGN_SIZE + self.AREA_SIZE_SIZE)

            if validation:
                self.validate_actuality()


    def read_memory(self):
        """Read all keys from sharedared
        """
        if self.get_area_size() == 0:
            self.init_memory(False)

        pos = self.AREA_SIZE_POSITION + self.AREA_SIZE_SIZE + self.SIGN_SIZE
        self._used = self.get_area_size()
        self._sign = self.get_area_sign()
        self._positions.clear()

        while pos < self._used + self.AREA_SIZE_POSITION:

            key_size, (key, key_value), positions = self.read_item(pos)
            yield key_size, (key, key_value), positions
            pos = positions[3]

    def load_exists_positions(self):
        """Load all keys from memory
        """

        self._used = self.get_area_size()
        self._sign = self.get_area_sign()

        for _, (key, _), positions in self.read_memory():
            self._positions[key] = positions
            #self._keys_cache[marshal.loads(key)] = key

    def get_string_padding(self, key):
        """Calculate string padding

        http://stackoverflow.com/questions/11642210/computing-padding-required-for-n-byte-alignment
        :param key: encoded string
        """
        #return (4 - (len(key) % 4)) % 4

        return (8 - (len(key) + 4) % 8)

    def get_key_size(self, key):
        """Calculate how many memory need key
        :param key: key string
        """
        return len(self.serialize_key(key)) + self.KEY_SIZE_SIZE + self.KEY_VALUE_SIZE


    def get_binary_string(self, key, value):
        item_template = "=i{0}sd".format(len(key)).encode()

        return struct.pack(item_template, len(key), key, value)

    def init_key(self, key, init_value=0.0):
        """Initialize memory for key

        :param key: key string
        """

        value = self.get_binary_string(key, init_value)

        key_string_position = self._used + self.AREA_SIZE_POSITION

        self.m[self.get_slice(key_string_position, len(value))] = value

        self.update_area_size(self._used + len(value))
        self._positions[key] = [key_string_position, key_string_position + self.KEY_SIZE_SIZE,
                                self._used - self.KEY_VALUE_SIZE, self._used]
        self.update_area_sign()
        return self._positions[key]

    def read_key_string(self, position, size):
        """Read key value from position by given size

        :param position: int offset for key string
        :param size:  int key size in bytes to read
        """
        key_string_bytes = self.m[self.get_slice(position, size)]
        return struct.unpack(b"{0}s".format(size), key_string_bytes)[0]

    def read_key_value(self, position):
        """Read float value of position

        :param position: int offset for key value float
        """
        key_value_bytes = self.m[self.get_slice(position, self.KEY_VALUE_SIZE)]
        return struct.unpack(b"d", key_value_bytes)[0]

    def read_key_size(self, position):
        """Read key size from position

        :param position: int offset for 4-byte key size
        """
        key_size_bytes = self.m[self.get_slice(position, self.KEY_SIZE_SIZE)]
        return struct.unpack(b"i", key_size_bytes)[0]

    def write_key_value(self, position, value):
        """Write float value to position

        :param position: int offset for 8-byte float value
        """
        self.m[self.get_slice(position, self.KEY_VALUE_SIZE)] = struct.pack(b"d", value)
        return value

    def read_item(self, position):
        """Read key info from given position

        4 bytes int key size
        n bytes key value of utf-8 encoded string key padding to a 8 byte
        8 bytes float counter value
        """

        key_size = self.read_key_size(position)

        key_string_position = position + self.KEY_SIZE_SIZE

        key = self.read_key_string(key_string_position, key_size)

        key_value_position = key_string_position + key_size  # + self.get_string_padding(key)

        key_value = self.read_key_value(key_value_position)
        return (key_size,
                (key, key_value),
                (position, key_string_position,
                 key_value_position, key_value_position + self.KEY_VALUE_SIZE))

    def get_key_position(self, key, init_value=0.0):
        try:
            return self._positions[key], False
        except Exception:
            return (self.init_key(key, init_value=init_value), True)

    def inc_value(self, key, value):
        """Increase/decrease key value

        :param key: key string
        :param value: key value
        """
        with self.lock():
            try:
                self.validate_actuality()
                positions, created = self.get_key_position(self.serialize_key(key), value)
                if created:
                    return value
                return self.write_key_value(positions[2], self.read_key_value(positions[2]) + value)
            except InvalidUWSGISharedareaPagesize as e:
                logger.error("Invalid sharedarea pagesize {0} bytes".format(len(self._m)))
                return 0

    def write_value(self, key, value):
        """Write value to shared memory

        :param key: key string
        :param value: key value
        """
        with self.lock():
            try:
                self.validate_actuality()
                positions, created = self.get_key_position(self.serialize_key(key), value)
                if created:
                    return value
                return self.write_key_value(positions[2], value)
            except InvalidUWSGISharedareaPagesize as e:
                logger.error("Invalid sharedarea pagesize {0} bytes".format(len(self._m)))
                return None

    def get_value(self, key):
        """Read value from shared memory

        :param key: key string
        """
        with self.lock():
            try:
                self.validate_actuality()
                return self.read_key_value(self.get_key_position(self.serialize_key(key))[0][2])
            except InvalidUWSGISharedareaPagesize:
                logger.error("Invalid sharedarea pagesize {0} bytes".format(len(self._m)))
                return 0

    @property
    def is_actual(self):
        return self._sign == self.get_area_sign()

    def validate_actuality(self):
        """For prevent data corruption

        Reload data from sharedmemory into process if sign changed
        """
        if not self.is_actual:
            self.load_exists_positions()

        return True

    @contextmanager
    def lock(self):
        lock_id = uuid.uuid4().hex
        if not self.wlocked and not self.rlocked:
            self.wlocked, self.rlocked = lock_id, lock_id
            uwsgi.sharedarea_wlock(self._sharedarea_id)
            yield
            uwsgi.sharedarea_unlock(self._sharedarea_id)
            self.wlocked, self.rlocked = False, False
        else:
            yield

    @contextmanager
    def rlock(self):
        lock_id = uuid.uuid4().hex
        if not self.rlocked:
            self.rlocked = lock_id
            uwsgi.sharedarea_rlock(self._sharedarea_id)
            yield
            uwsgi.sharedarea_unlock(self._sharedarea_id)
            self.rlocked = False
        else:
            yield

    def unlock(self):
        self._wlocked, self._rlocked = False, False
        uwsgi.sharedarea_unlock(self._sharedarea_id)

    def __len__(self):
        return len(self._positions)

    def clear(self):
        for x in xrange(self.AREA_SIZE_SIZE + self.AREA_SIZE_SIZE):
            self.m[x] = "\x00"

        self._positions.clear()

    def get_items(self):
        self.validate_actuality()

        for key, position in self._positions.items():
            yield self.unserialize_key(key), self.read_key_value(position[2])

    def inc_items(self, items):
        self.validate_actuality()
        with self.lock():
            for key, value in items:
                try:
                    positions, created = self.get_key_position(self.serialize_key(key), value)
                    if created:
                        continue
                    self.write_key_value(positions[2], self.read_key_value(positions[2]) + value)
                except InvalidUWSGISharedareaPagesize:
                    logger.error("Invalid sharedarea pagesize {0} bytes".format(len(self._m)))

    def write_items(self, items):
        self.validate_actuality()
        with self.lock():
            for key, value in items:
                try:
                    positions, created = self.get_key_position(self.serialize_key(key), value)
                    if created:
                        continue
                    self.write_key_value(positions[2], value)
                except InvalidUWSGISharedareaPagesize:
                    logger.error("Invalid sharedarea pagesize {0} bytes".format(len(self._m)))


class UWSGIFlushStorage(LocalMemoryStorage):
    """Storage wrapper for UWSGI storage that update couters inmemory and flush into uwsgi sharedarea
    """
    SHAREDAREA_ID = int(os.environ.get("PROMETHEUS_UWSGI_SHAREDAREA", 0))

    def __init__(self, sharedarea_id=UWSGIStorage.SHAREDAREA_ID, namespace="", stats=False, labels={}):
        self._uwsgi_storage = UWSGIStorage(sharedarea_id, namespace=namespace, stats=stats, labels=labels)
        self._flush = 0
        self._get_items = 0
        self._clear = 0
        super(UWSGIFlushStorage, self).__init__()

    @property
    def persistent_storage(self):
        return self._uwsgi_storage

    def flush(self):
        items = list(super(UWSGIFlushStorage, self).get_items())
        self._uwsgi_storage.inc_items(items)
        super(UWSGIFlushStorage, self).clear()

    def get_items(self):
        return self._uwsgi_storage.get_items()

    def __len__(self):
        return super(UWSGIFlushStorage, self).__len__()

    def clear(self):
        self._uwsgi_storage.clear()
        super(UWSGIFlushStorage, self).clear()
