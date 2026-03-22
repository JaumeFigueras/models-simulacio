#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import List, Optional

import simpy

from simpy_extensions.process_flow.entity import Entity


class Delete:
    """
    Removes an entity from the system and records its departure.

    ``Delete`` is analogous to an *Arena Dispose* module or an *AnyLogic
    Sink* block.  It is always the terminal block of a process-flow
    chain.

    Upon receiving an entity the block stamps its ``deletion_time``,
    appends it to an internal log, and updates the entity counter.
    Optionally it can keep the full list of departed entities for
    post-simulation analysis.

    Parameters
    ----------
    env : simpy.Environment
        The SimPy simulation environment.
    name : str
        Human-readable name for this disposal point.
    keep_entities : bool, optional
        If ``True`` (default), every deleted entity is appended to
        :attr:`deleted_entities` for later inspection.  Set to
        ``False`` to save memory in large runs.

    Attributes
    ----------
    env : simpy.Environment
        Reference to the simulation environment.
    name : str
        Human-readable label.
    entities_deleted : int
        Counter of entities that have been removed from the system.
    deleted_entities : list of Entity
        Log of all entities that passed through this block (empty when
        ``keep_entities`` is ``False``).
    total_system_time : float
        Cumulative system time of all deleted entities.

    Examples
    --------
    ::

        sink = Delete(env, name='Exit')
        # ... build model ...
        env.run(until=480)
        print(f"Entities out: {sink.entities_deleted}")
        print(f"Avg system time: {sink.avg_system_time():.2f}")
    """

    def __init__(
        self,
        env: simpy.Environment,
        name: str,
        keep_entities: bool = True,
    ) -> None:
        self.env: simpy.Environment = env
        self.name: str = name
        self.keep_entities: bool = keep_entities
        self.entities_deleted: int = 0
        self.deleted_entities: List[Entity] = []
        self.total_system_time: float = 0.0

    # -----------------------------------------------------------------
    # Public interface called by upstream blocks
    # -----------------------------------------------------------------

    def handle(self, entity: Entity):
        """
        Record entity departure and remove it from the system.

        This method is a SimPy generator (yields a zero-delay timeout)
        so that it can be called uniformly via
        ``env.process(block.handle(entity))``.

        Parameters
        ----------
        entity : Entity
            The entity leaving the system.

        Yields
        ------
        simpy.events.Event
            A zero-delay timeout to keep the generator protocol.
        """
        entity.deletion_time = self.env.now
        system_time = entity.system_time()
        if system_time is not None:
            self.total_system_time += system_time
        self.entities_deleted += 1

        if self.keep_entities:
            self.deleted_entities.append(entity)

        # Yield a zero-timeout so this remains a valid SimPy generator
        yield self.env.timeout(0)

    # -----------------------------------------------------------------
    # Statistics helpers
    # -----------------------------------------------------------------

    def avg_system_time(self) -> float:
        """
        Compute the average time entities spent in the system.

        Returns
        -------
        float
            Average system time.  Returns ``0.0`` if no entities have
            been deleted yet.
        """
        if self.entities_deleted == 0:
            return 0.0
        return self.total_system_time / self.entities_deleted

    def __repr__(self) -> str:
        return (
            f"Delete(name='{self.name}', "
            f"entities_deleted={self.entities_deleted})"
        )