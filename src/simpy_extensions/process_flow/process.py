#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, Optional, Union

import simpy

from simpy_extensions.process_flow.entity import Entity
from simpy_extensions.process_flow.resource import Resource

if TYPE_CHECKING:
    from simpy_extensions.process_flow.delete import Delete


class Process:
    """
    Models a station where an entity seizes a resource, undergoes
    service for a given duration, and then releases the resource before
    being forwarded to the next block.

    ``Process`` is analogous to an *Arena Process* module (seize-delay-
    release) or an *AnyLogic Service* block.

    Service-time selection
    ----------------------
    The ``service_time`` parameter accepts **two forms**:

    * **Single callable** ``Callable[[Entity], float]`` — receives the
      entity and returns the service duration.  The callable can
      inspect ``entity.entity_type`` (or any other attribute) to
      decide the duration.
    * **Dictionary** ``Dict[str, Callable[[], float]]`` — maps each
      ``entity_type`` string to a zero-argument callable that returns
      the service duration.  A special key ``'default'`` is used as
      fall-back when the entity type is not found in the dictionary.

    Parameters
    ----------
    env : simpy.Environment
        The SimPy simulation environment.
    name : str
        Human-readable name for this processing station.
    resource : Resource
        The :class:`Resource` that entities must seize before being
        served.
    service_time : callable or dict
        Either a single callable ``(Entity) -> float``, or a dictionary
        ``{entity_type: () -> float, ...}``.  See *Service-time
        selection* above.
    next_block : Process or Delete or None, optional
        The downstream block that receives entities after service.  Can
        be set after construction via the :attr:`next_block` attribute.

    Attributes
    ----------
    env : simpy.Environment
        Reference to the simulation environment.
    name : str
        Human-readable label.
    resource : Resource
        Shared resource used by this station.
    service_time : callable or dict
        Service-time specification.
    next_block : Process or Delete or None
        Downstream block.
    entities_processed : int
        Counter of entities that have completed service.

    Raises
    ------
    ValueError
        If the service-time dictionary does not contain a matching
        ``entity_type`` key **and** no ``'default'`` key is present.

    Examples
    --------
    Using a single callable that inspects the entity::

        def drilling_time(entity):
            if entity.entity_type == 'TypeA':
                return random.uniform(3.0, 7.0)
            return random.uniform(5.0, 10.0)

        station = Process(env, 'Drilling', drill, drilling_time)

    Using a dictionary of per-type distributions::

        station = Process(env, 'Drilling', drill, service_time={
            'TypeA': lambda: random.uniform(3.0, 7.0),
            'TypeB': lambda: random.uniform(5.0, 10.0),
        })
    """

    def __init__(
        self,
        env: simpy.Environment,
        name: str,
        resource: Resource,
        service_time: Union[
            Callable[[Entity], float],
            Dict[str, Callable[[], float]],
        ],
        next_block: Optional[Union["Process", "Delete"]] = None,
    ) -> None:
        self.env: simpy.Environment = env
        self.name: str = name
        self.resource: Resource = resource
        self.service_time: Union[
            Callable[[Entity], float],
            Dict[str, Callable[[], float]],
        ] = service_time
        self.next_block: Optional[Union["Process", "Delete"]] = next_block
        self.entities_processed: int = 0

    # -----------------------------------------------------------------
    # Service-time resolution
    # -----------------------------------------------------------------

    def _resolve_service_time(self, entity: Entity) -> float:
        """
        Determine the service duration for a given entity.

        Parameters
        ----------
        entity : Entity
            The entity about to be served.

        Returns
        -------
        float
            Service duration.

        Raises
        ------
        ValueError
            If ``service_time`` is a dictionary and neither the
            entity's type nor a ``'default'`` key is present.
        """
        if callable(self.service_time):
            return self.service_time(entity)

        # Dictionary look-up
        st_dict: Dict[str, Callable[[], float]] = self.service_time
        if entity.entity_type in st_dict:
            return st_dict[entity.entity_type]()
        if "default" in st_dict:
            return st_dict["default"]()
        raise ValueError(
            f"Process '{self.name}': no service-time entry for "
            f"entity_type='{entity.entity_type}' and no 'default' key."
        )

    # -----------------------------------------------------------------
    # Public interface called by upstream blocks
    # -----------------------------------------------------------------

    def handle(self, entity: Entity):
        """
        Seize the resource, serve the entity, release the resource, and
        forward the entity to the next block.

        This method is a SimPy generator and must be started with
        ``env.process(process_block.handle(entity))``.

        Parameters
        ----------
        entity : Entity
            The entity entering the processing station.

        Yields
        ------
        simpy.events.Event
            SimPy resource-request and timeout events.
        """
        resource_stats = self.resource.stats

        # --- Seize ---
        request = self.resource.simpy_resource.request()
        resource_stats.record_queue_entry(self.env.now)
        yield request
        resource_stats.record_service_start(self.env.now)

        # --- Delay (service) ---
        duration = self._resolve_service_time(entity)
        yield self.env.timeout(duration)

        # --- Release ---
        self.resource.simpy_resource.release(request)
        resource_stats.record_service_end(self.env.now)
        self.entities_processed += 1

        # --- Forward ---
        if self.next_block is not None:
            self.env.process(self.next_block.handle(entity))

    def __repr__(self) -> str:
        return (
            f"Process(name='{self.name}', "
            f"resource='{self.resource.name}', "
            f"entities_processed={self.entities_processed})"
        )