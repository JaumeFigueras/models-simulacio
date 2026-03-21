class ResourceStats:
    """
    Tracks resource utilization, queue waiting times, and time-weighted
    average queue length for a single station (SimPy Resource).

    This class must be instrumented manually within SimPy process
    methods by calling its ``record_*`` methods at the appropriate
    points in the process flow.

    Attributes
    ----------
    total_busy_time : float
        Cumulative time the resource has been busy serving entities.
    total_wait_time : float
        Cumulative time entities have spent waiting in the queue.
    wait_count : int
        Total number of entities that have waited in the queue.
    current_queue_length : int
        Current number of entities waiting in the queue.
    max_queue_length : int
        Maximum observed queue length during the simulation.

    Examples
    --------
    Typical usage within a SimPy process::

        stats.record_queue_entry(env.now)     # before yield req
        yield req                             # wait for resource
        stats.record_service_start(env.now)   # service begins
        yield env.timeout(service_time)       # service
        stats.record_service_end(env.now)     # service ends
    """

    def __init__(self):
        """
        Initialize all statistics accumulators to zero.
        """
        # Resource utilization
        self.total_busy_time: float = 0.0
        self._busy_start: float = 0.0

        # Queue waiting times
        self.total_wait_time: float = 0.0
        self.wait_count: int = 0
        self._current_wait_start: float = 0.0

        # Time-weighted average queue length (area-under-the-curve)
        self.current_queue_length: int = 0
        self._last_queue_change_time: float = 0.0
        self._queue_length_area: float = 0.0
        self.max_queue_length: int = 0

    def record_queue_entry(self, now: float) -> None:
        """
        Record that an entity has joined the queue.

        Must be called **before** ``yield req``.

        Parameters
        ----------
        now : float
            Current simulation time.
        """
        self._current_wait_start = now
        self._queue_length_area += self.current_queue_length * (now - self._last_queue_change_time)
        self.current_queue_length += 1
        self._last_queue_change_time = now
        if self.current_queue_length > self.max_queue_length:
            self.max_queue_length = self.current_queue_length

    def record_service_start(self, now: float) -> None:
        """
        Record that an entity has started being served.

        Must be called **after** ``yield req`` (when the resource is granted).

        Parameters
        ----------
        now : float
            Current simulation time.
        """
        wait = now - self._current_wait_start
        self.total_wait_time += wait
        self.wait_count += 1

        self._queue_length_area += self.current_queue_length * (now - self._last_queue_change_time)
        self.current_queue_length -= 1
        self._last_queue_change_time = now

        self._busy_start = now

    def record_service_end(self, now: float) -> None:
        """
        Record that an entity has finished being served.

        Must be called after the service timeout completes.

        Parameters
        ----------
        now : float
            Current simulation time.
        """
        self.total_busy_time += now - self._busy_start

    def utilization(self, sim_time: float) -> float:
        """
        Compute resource utilization as a fraction.

        Parameters
        ----------
        sim_time : float
            Total simulation time.

        Returns
        -------
        float
            Utilization ratio in [0, 1].
        """
        if sim_time <= 0:
            return 0.0
        return self.total_busy_time / sim_time

    def avg_wait_time(self) -> float:
        """
        Compute the average time entities waited in the queue.

        Returns
        -------
        float
            Average wait time in minutes.  Returns 0.0 if no entities
            have been served yet.
        """
        if self.wait_count == 0:
            return 0.0
        return self.total_wait_time / self.wait_count

    def avg_queue_length(self, sim_time: float) -> float:
        """
        Compute the time-weighted average queue length.

        Uses the area-under-the-curve method, including the last
        interval up to ``sim_time``.

        Parameters
        ----------
        sim_time : float
            Total simulation time.

        Returns
        -------
        float
            Average number of entities in the queue.
        """
        if sim_time <= 0:
            return 0.0
        total_area = (self._queue_length_area
                      + self.current_queue_length * (sim_time - self._last_queue_change_time))
        return total_area / sim_time
