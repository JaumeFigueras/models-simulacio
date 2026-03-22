#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import simpy

from simpy_extensions.statistics.resource import ResourceStats


class Resource:
    """
    Represents a system element needed by entities to perform a process.

    A ``Resource`` wraps a :class:`simpy.Resource` and exposes an
    associated :class:`~simpy_extensions.statistics.resource.ResourceStats`
    instance for automatic utilization and queue-length tracking.

    This class is analogous to an *Arena Resource* or an *AnyLogic
    ResourcePool*.

    Parameters
    ----------
    env : simpy.Environment
        The SimPy simulation environment.
    name : str
        Human-readable name for the resource (e.g. ``'Drill'``).
    capacity : int, optional
        Number of identical units available.  Defaults to ``1``.

    Attributes
    ----------
    env : simpy.Environment
        Reference to the simulation environment.
    name : str
        Human-readable label.
    capacity : int
        Number of resource units.
    simpy_resource : simpy.Resource
        The underlying SimPy resource used for seize / release.
    stats : ResourceStats
        Statistics collector (utilization, wait time, queue length).

    Examples
    --------
    ::

        env = simpy.Environment()
        drill = Resource(env, name='Drill', capacity=2)
    """

    def __init__(self, env: simpy.Environment, name: str, capacity: int = 1) -> None:
        self.env: simpy.Environment = env
        self.name: str = name
        self.capacity: int = capacity
        self.simpy_resource: simpy.Resource = simpy.Resource(env, capacity=capacity)
        self.stats: ResourceStats = ResourceStats()

    def __repr__(self) -> str:
        return f"Resource(name='{self.name}', capacity={self.capacity})"