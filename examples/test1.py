#!/usr/bin/env python
# -*- coding: utf-8 -*-


from pyprometheus.registry import BaseRegistry

registry = BaseRegistry()



total_requests = registry.gauge("app:total_requests",
                                "Documentation string", ["env_name"]).add_to_registry(register)


total_request.labels(env_name="test").inc()


response_time = registry.Histogram('name', 'Doc', ['label1'], buckets=(.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0, float('inf')))
