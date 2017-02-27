Prometheus instrumentation library for Python applications
============================================================

The unofficial Python 2 and 3 client for `Prometheus`_.

.. image:: https://travis-ci.org/Lispython/pyprometheus.svg?branch=master
    :target: https://travis-ci.org/Lispython/pyprometheus



Features
--------

- Four types of metric are supported: Counter, Gauge, Summary(without quantiles) and Histogram.
- InMemoryStorage (do not use it for multiprocessing apps)
- UWSGI storage - share metrics between processes
- time decorator
- time context manager



INSTALLATION
------------

To use pyprometheus use pip or easy_install:

:code:`pip install pyprometheus`

or

:code:`easy_install pyprometheus`


HOW TO INSTRUMENTING CODE
-------------------------

Gauge
~~~~~

A gauge is a metric that represents a single numerical value that can arbitrarily go up and down.::

   from pyprometheus import Gauge
   from pyprometheus import BaseRegistry, LocalMemoryStorage

   storage = LocalMemoryStorage()
   registry = CollectorRegistry(storage=storage)
   gauge = Gauge("job_in_progress", "Description", registry=registry)

   gauge.inc(10)
   gauge.dec(5)
   gauge.set(21.1)


utilities::

  gauge.set_to_current_time()   # Set to current unixtime

  # Increment when entered, decrement when exited.
  @gauge.track_in_progress()
  def f():
      pass

  with gauge.track_in_progress():
      pass


  with gauge.time():
      time.sleep(10)



Counter
~~~~~~~

A counter is a cumulative metric that represents a single numerical value that only ever goes up.::

   from pyprometheus import Counter
   from pyprometheus import BaseRegistry, LocalMemoryStorage

   storage = LocalMemoryStorage()
   registry = CollectorRegistry(storage=storage)
   counter = Counter("requests_total", "Description", registry=registry)

   counter.inc(10)





Summary
~~~~~~~

Similar to a histogram, a summary samples observations (usually things like request durations and response sizes).::

   from pyprometheus import Summary
   from pyprometheus import BaseRegistry, LocalMemoryStorage

   storage = LocalMemoryStorage()
   registry = CollectorRegistry(storage=storage)
   s = Summary("requests_duration_seconds", "Description", registry=registry)

   s.observe(0.100)


utilities for timing code::

   @gauge.time()
   def func():
      time.sleep(10)

   with gauge.time():
      time.sleep(10)



Histogram
~~~~~~~~~

A histogram samples observations (usually things like request durations or response sizes) and counts them in configurable buckets. It also provides a sum of all observed values.::

  from pyprometheus import Summary
   from pyprometheus import BaseRegistry, LocalMemoryStorage

   storage = LocalMemoryStorage()
   registry = CollectorRegistry(storage=storage)
   histogram = Histogram("requests_duration_seconds", "Description", registry=registry)

   histogram.observe(1.1)

utilities for timing code::

   @histogram.time()
   def func():
      time.sleep(10)

   with histogram.time():
      time.sleep(10)



Labels
~~~~~~

All metrics can have labels, allowing grouping of related time series.


Example::

    from pyprometheus import Counter
    c = Counter('my_requests_total', 'HTTP Failures', ['method', 'endpoint'])
    c.labels('get', '/').inc()
    c.labels('post', '/submit').inc()

or labels as keyword arguments::

    from pyprometheus import Counter
    c = Counter('my_requests_total', 'HTTP Failures', ['method', 'endpoint'])
    c.labels(method='get', endpoint='/').inc()
    c.labels(method='post', endpoint='/submit').inc()



STORAGES
--------

Currently library support 2 storages: LocalMemoryStorage and UWSGIStorage

Every registry MUST have link to storage::

  from pyprometheus import BaseRegistry, LocalMemoryStorage

  storage = LocalMemoryStorage()
  registry = CollectorRegistry(storage=storage)


Use LocalMemoryStorage
~~~~~~~~~~~~~~~~~~~~~~

Simple storage that store samples to application memory. It can be used with threads.::

  from pyprometheus import BaseRegistry, LocalMemoryStorage

  storage = LocalMemoryStorag()


Use UWSGIStorage
~~~~~~~~~~~~~~~~

UWSGIStorage allow to use `uwsgi sharedarea`_ to sync metrics between processes.::

  from pyprometheus.contrib.uwsgi_features import UWSGICollector, UWSGIStorage

  SHAREDAREA_ID = 0
  storage = UWSGIStorage(SHAREDAREA_ID)



also need to configure UWSGI sharedaread pages.




EXPORTING
---------

Library have some helpers to export metrics

To text format
~~~~~~~~~~~~~~

You can convert registry to text format::


  from pyprometheus import BaseRegistry, LocalMemoryStorage
  from pyprometheus.utils.exposition import registry_to_text
  from pyprometheus import Gauge

  storage = LocalMemoryStorage()
  registry = CollectorRegistry(storage=storage)
  g = Gauge('raid_status', '1 if raid array is okay', registry=registry)
  g.set(1)
  print(registry_to_text(registry))



Text file export
~~~~~~~~~~~~~~~~

This is useful for monitoring cronjobs, or for writing cronjobs to expose metrics about a machine system.::

  from pyprometheus import BaseRegistry, LocalMemoryStorage
  from pyprometheus.utils.exposition import registry_to_text, write_to_textfile
  from pyprometheus import Gauge

  storage = LocalMemoryStorage()
  registry = CollectorRegistry(storage=storage)
  g = Gauge('raid_status', '1 if raid array is okay', registry=registry)
  g.set(1)
  write_to_textfile(registry, "/path/to/file/metrics.prom")


You can configure `text file collector`_ to use generated file.


TODO
----

Some features that we plan to do:

- [ ] Add mmap storage
- [ ] Add features for async frameworks
- [ ] Optimize UWSGI storage byte pad
- [ ] Add quantiles



EXAMPLE PROJECT
---------------

We create `example project`_ to show hot to use pyprometheus in real project.


CONTRIBUTE
----------

Fork https://github.com/Lispython/pyprometheus/ , create commit and pull request to ``develop``.



.. _`example project`: http://github.com/Lispython/pyprometheus_demo
.. _`text file collector`: https://github.com/prometheus/node_exporter#textfile-collector
.. _`uwsgi sharedarea`: http://uwsgi-docs.readthedocs.io/en/latest/SharedArea.html
.. _`Prometheus`: http://prometheus.io
