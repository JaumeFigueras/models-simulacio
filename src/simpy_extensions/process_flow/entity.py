#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Dict, Optional


class Entity:
    """
    Represents a system element that flows through a discrete-event
    simulation following a create → process → dispose life-cycle.

    An ``Entity`` is a passive token: it does not own a SimPy process
    itself but is moved from block to block (``Arrival`` → ``Process``
    → ``Delete``) by the process-flow infrastructure.

    Each entity carries a unique identifier, a type label, creation
    timestamp, and a free-form dictionary for user-defined attributes
    (e.g. part dimensions, priority, colour).

    The ``entity_type`` attribute allows downstream blocks such as
    ``Process`` to apply different service-time distributions depending
    on the kind of entity they receive.

    Parameters
    ----------
    entity_id : int
        Unique numeric identifier assigned by the ``Arrival`` block that
        creates the entity.
    creation_time : float
        Simulation time at which the entity was created.
    entity_type : str, optional
        Label that identifies the category of this entity (e.g.
        ``'TypeA'``, ``'Rush'``).  Defaults to ``'default'``.
    name : str, optional
        Human-readable name.  Defaults to ``'Entity-<entity_id>'``.
    attributes : dict, optional
        Initial user-defined attributes to attach to the entity.

    Attributes
    ----------
    entity_id : int
        Unique numeric identifier.
    entity_type : str
        Category label used by ``Process`` blocks to select the
        appropriate service-time distribution.
    name : str
        Human-readable label.
    creation_time : float
        Simulation time at which the entity entered the system.
    deletion_time : float or None
        Simulation time at which the entity left the system.  ``None``
        until the entity reaches a ``Delete`` block.
    attributes : dict
        Free-form dictionary for custom data.

    Examples
    --------
    Entities are normally created by an ``Arrival`` block, but can also
    be instantiated manually for testing::

        entity = Entity(entity_id=1, creation_time=0.0,
                        entity_type='TypeA')
        entity.attributes['priority'] = 'high'
    """

    #: Class-level counter that guarantees unique IDs across all
    #: ``Arrival`` blocks in the same Python process.
    _next_id: int = 0

    @classmethod
    def generate_id(cls) -> int:
        """
        Return the next globally unique entity identifier.

        Returns
        -------
        int
            A positive integer that has not been used before.
        """
        cls._next_id += 1
        return cls._next_id

    @classmethod
    def reset_id_counter(cls) -> None:
        """
        Reset the global entity-ID counter to zero.

        Call this between independent simulation runs so that entity
        identifiers start from 1 again.
        """
        cls._next_id = 0

    def __init__(self, entity_id: int, creation_time: float, entity_type: str = "default", name: Optional[str] = None,
                 attributes: Optional[Dict[str, Any]] = None) -> None:
        self.entity_id: int = entity_id
        self.entity_type: str = entity_type
        self.name: str = name if name is not None else f"Entity-{entity_id}"
        self.creation_time: float = creation_time
        self.deletion_time: Optional[float] = None
        self.attributes: Dict[str, Any] = (
            attributes if attributes is not None else {}
        )

    # -----------------------------------------------------------------
    # Convenience helpers
    # -----------------------------------------------------------------

    def system_time(self) -> Optional[float]:
        """
        Compute the total time the entity spent in the system.

        Returns
        -------
        float or None
            ``deletion_time - creation_time`` if the entity has already
            been deleted; ``None`` otherwise.
        """
        if self.deletion_time is None:
            return None
        return self.deletion_time - self.creation_time

    # -----------------------------------------------------------------
    # Dunder methods
    # -----------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Entity(entity_id={self.entity_id}, "
            f"entity_type='{self.entity_type}', "
            f"name='{self.name}', "
            f"creation_time={self.creation_time})"
        )