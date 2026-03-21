class QueueStats:
    """
    Tracks time-weighted average length, maximum length, and average
    waiting time for a ``simpy.Store`` inter-stage queue.

    Call ``record_put`` when an item is added to the queue, and
    ``record_get`` when an item is removed.  Items must carry a
    ``queue_entry_time`` attribute that is set before ``record_put``
    is called.

    Attributes
    ----------
    current_length : int
        Current number of items in the queue.
    max_length : int
        Maximum observed queue length during the simulation.
    total_wait_time : float
        Cumulative time items have spent waiting in the queue.
    wait_count : int
        Total number of items that have been retrieved from the queue.
    """

    def __init__(self):
        """
        Initialize all statistics accumulators to zero.
        """
        # Time-weighted average queue length (area-under-the-curve)
        self.current_length: int = 0
        self._last_change_time: float = 0.0
        self._length_area: float = 0.0
        self.max_length: int = 0

        # Queue waiting times
        self.total_wait_time: float = 0.0
        self.wait_count: int = 0

    def record_put(self, now: float) -> None:
        """
        Record that an item has been added to the queue.

        The item's ``queue_entry_time`` attribute must be set to
        ``now`` **before** calling this method.

        Parameters
        ----------
        now : float
            Current simulation time.
        """
        self._length_area += self.current_length * (now - self._last_change_time)
        self.current_length += 1
        self._last_change_time = now
        if self.current_length > self.max_length:
            self.max_length = self.current_length

    def record_get(self, now: float, entry_time: float) -> None:
        """
        Record that an item has been removed from the queue.

        Parameters
        ----------
        now : float
            Current simulation time.
        entry_time : float
            The simulation time at which the item entered the queue
            (i.e., the item's ``queue_entry_time`` attribute).
        """
        # Update queue length area
        self._length_area += self.current_length * (now - self._last_change_time)
        self.current_length -= 1
        self._last_change_time = now

        # Update waiting time
        self.total_wait_time += now - entry_time
        self.wait_count += 1

    def avg_length(self, sim_time: float) -> float:
        """
        Compute the time-weighted average queue length.

        Parameters
        ----------
        sim_time : float
            Total simulation time.

        Returns
        -------
        float
            Average number of items in the queue.
        """
        if sim_time <= 0:
            return 0.0
        total_area = (self._length_area
                      + self.current_length * (sim_time - self._last_change_time))
        return total_area / sim_time

    def avg_wait_time(self) -> float:
        """
        Compute the average time items waited in the queue.

        Returns
        -------
        float
            Average wait time in minutes.  Returns 0.0 if no items
            have been retrieved yet.
        """
        if self.wait_count == 0:
            return 0.0
        return self.total_wait_time / self.wait_count

