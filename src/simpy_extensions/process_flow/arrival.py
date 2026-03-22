#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Optional

import simpy

from simpy_extensions.process_flow.entity import Entity

if TYPE_CHECKING:
    from simpy_extensions.process_flow.process import Process
    from simpy_extensions.process_flow.delete import Delete


class Arrival:
    """
    Creates entities of a given type and sends them into the model.

    ``Arrival`` is analogous to an *Arena Create* module or an *AnyLogic
    Source* block.  It owns a SimPy process that loops indefinitely (or
    up to ``max_entities``), sleeping for an inter-arrival time and then
    injecting a new :class:`Entity` into the next downstream block.

    Every entity produced by this block receives the
    :attr:`entity_type` label, which downstream ``Process`` blocks can
    use to choose the correct service-time distribution.  This makes it
    possible to connect **several** ``Arrival`` blocks — each producing
    a different entity type — to a **single** ``Process`` block.

    Parameters
    ----------
    env : simpy.Environment
        The SimPy simulation environment.
    name : str
        Human-readable name for this arrival block.
    inter_arrival_time : callable
        A zero-argument callable that returns the time until the next
        entity arrives.  Use a lambda or ``functools.partial`` to wrap
        any random distribution, e.g.
        ``lambda: random.expovariate(1 / 5.0)``.
    entity_type : str, optional
        Type label stamped on every entity created by this block.
        Defaults to ``'default'``.
    next_block : Process or Delete or None, optional
        The downstream block that will receive each new entity.  Can be
        set after construction via the :attr:`next_block` attribute.
    max_entities : int or None, optional
        Maximum number of entities to create.  ``None`` (default) means
        unlimited — the process runs until the simulation ends.
    entity_name_prefix : str, optional
        Prefix for auto-generated entity names.  Defaults to
        ``'Entity'``.

    Attributes
    ----------
    env : simpy.Environment
        Reference to the simulation environment.
    name : str
        Human-readable label.
    inter_arrival_time : callable
        Inter-arrival-time generator.
    entity_type : str
        Type label for created entities.
    next_block : Process or Delete or None
        Downstream block.
    max_entities : int or None
        Creation limit.
    entities_created : int
        Counter of entities produced so far.

    Examples
    --------
    Two sources feeding the same process with different entity types::

        source_a = Arrival(env, 'Type-A Arrivals',
                           inter_arrival_time=lambda: random.expovariate(1/5),
                           entity_type='TypeA')
        source_b = Arrival(env, 'Type-B Arrivals',
                           inter_arrival_time=lambda: random.expovariate(1/8),
                           entity_type='TypeB')
        source_a.next_block = shared_process
        source_b.next_block = shared_process
    """

    def __init__(self, env: simpy.Environment, name: str, inter_arrival_time: Callable[[], float],
                 entity_type: str = "default", next_block: Optional["Process | Delete"] = None,
                 max_entities: Optional[int] = None, entity_name_prefix: str = "Entity") -> None:
        self.env: simpy.Environment = env
        self.name: str = name
        self.inter_arrival_time: Callable[[], float] = inter_arrival_time
        self.entity_type: str = entity_type
        self.next_block: Optional["Process | Delete"] = next_block
        self.max_entities: Optional[int] = max_entities
        self.entity_name_prefix: str = entity_name_prefix
        self.entities_created: int = 0

        # Auto-start the arrival process
        self._process: simpy.events.Process = self.env.process(self._run())

    # -----------------------------------------------------------------
    # Internal SimPy process
    # -----------------------------------------------------------------

    def _run(self):
        """
        Main generator loop that creates entities at each inter-arrival
        interval and forwards them to :attr:`next_block`.

        Yields
        ------
        simpy.events.Event
            SimPy timeout events for inter-arrival delays.
        """
        while True:
            # Respect the creation limit
            if self.max_entities is not None and self.entities_created >= self.max_entities:
                return

            # Wait for the next arrival
            iat = self.inter_arrival_time()
            yield self.env.timeout(iat)

            # Create a new entity with a globally unique ID
            eid = Entity.generate_id()
            self.entities_created += 1
            entity = Entity(entity_id=eid, creation_time=self.env.now, entity_type=self.entity_type,
                            name=f"{self.entity_name_prefix}-{eid}")

            # Forward to the next block
            if self.next_block is not None:
                self.env.process(self.next_block.handle(entity))

    def __repr__(self) -> str:
        return (
            f"Arrival(name='{self.name}', "
            f"entity_type='{self.entity_type}', "
            f"entities_created={self.entities_created})"
        )