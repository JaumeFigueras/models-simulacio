#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Process-flow building blocks for discrete-event simulation with SimPy.

This sub-package provides an object-oriented, Arena / AnyLogic-style
API on top of SimPy.  A model is assembled by instantiating blocks and
chaining them together.

.. code-block:: python

    import simpy, random
    from simpy_extensions.process_flow import (
        Arrival, Process, Delete, Resource,
    )

    env = simpy.Environment()
    drill = Resource(env, 'Drill', capacity=1)

    source_a = Arrival(env, 'Type-A', lambda: random.expovariate(1/5),
                       entity_type='TypeA')
    source_b = Arrival(env, 'Type-B', lambda: random.expovariate(1/8),
                       entity_type='TypeB')

    station = Process(env, 'Drilling', drill, service_time={
        'TypeA': lambda: random.uniform(3, 7),
        'TypeB': lambda: random.uniform(5, 10),
    })
    sink = Delete(env, 'Exit')

    source_a.next_block = station
    source_b.next_block = station
    station.next_block = sink

    env.run(until=480)
"""

from simpy_extensions.process_flow.entity import Entity
from simpy_extensions.process_flow.resource import Resource
from simpy_extensions.process_flow.arrival import Arrival
from simpy_extensions.process_flow.process import Process
from simpy_extensions.process_flow.delete import Delete

__all__ = [
    "Entity",
    "Resource",
    "Arrival",
    "Process",
    "Delete",
]