class WipStats:
    """
    Tracks time-weighted average Work in Progress (WIP) for a
    category of entities.

    WIP represents the number of entities currently in the system
    (from arrival to departure).  An entity enters WIP when it
    arrives and leaves WIP when it is consumed (assembled) or
    discarded (scrapped).

    Uses the area-under-the-curve method for time-weighted averaging.

    Attributes
    ----------
    current_wip : int
        Current number of entities in progress.
    max_wip : int
        Maximum observed WIP during the simulation.

    Examples
    --------
    Typical usage::

        wip.record_entry(env.now)   # entity arrives / enters the system
        # ... entity flows through stations ...
        wip.record_exit(env.now)    # entity is consumed or scrapped
    """

    def __init__(self):
        """
        Initialize all WIP accumulators to zero.
        """
        self.current_wip: int = 0
        self._last_change_time: float = 0.0
        self._wip_area: float = 0.0
        self.max_wip: int = 0

    def record_entry(self, now: float) -> None:
        """
        Record that an entity has entered the system (WIP increases).

        Parameters
        ----------
        now : float
            Current simulation time.
        """
        self._wip_area += self.current_wip * (now - self._last_change_time)
        self.current_wip += 1
        self._last_change_time = now
        if self.current_wip > self.max_wip:
            self.max_wip = self.current_wip

    def record_exit(self, now: float) -> None:
        """
        Record that an entity has left the system (WIP decreases).

        Called when an entity is consumed by assembly or discarded
        as scrap.

        Parameters
        ----------
        now : float
            Current simulation time.
        """
        self._wip_area += self.current_wip * (now - self._last_change_time)
        self.current_wip -= 1
        self._last_change_time = now

    def avg_wip(self, sim_time: float) -> float:
        """
        Compute the time-weighted average WIP.

        Parameters
        ----------
        sim_time : float
            Total simulation time.

        Returns
        -------
        float
            Average number of entities in progress.
        """
        if sim_time <= 0:
            return 0.0
        total_area = (self._wip_area
                      + self.current_wip * (sim_time - self._last_change_time))
        return total_area / sim_time
