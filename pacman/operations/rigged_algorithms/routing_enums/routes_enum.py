from enum import IntEnum


class Routes(IntEnum):
    """Enumeration of routes which a SpiNNaker packet can take after arriving
    at a router.

    Note that the integer values assigned are chosen to match the numbers used
    to identify routes in the low-level software API and hardware registers.
    """

    @classmethod
    def core(cls, num):
        """Get the :py:class:`.Routes` for the numbered core.

        Raises
        ------
        ValueError
            If the core number isn't in the range 0-17 inclusive.
        """
        if not (0 <= num <= 17):
            raise ValueError("Cores are numbered from 0 to 17")
        return cls(6 + num)

    east = 0
    north_east = 1
    north = 2
    west = 3
    south_west = 4
    south = 5

    core_monitor = 6
    core_1 = 7
    core_2 = 8
    core_3 = 9
    core_4 = 10
    core_5 = 11
    core_6 = 12
    core_7 = 13
    core_8 = 14
    core_9 = 15
    core_10 = 16
    core_11 = 17
    core_12 = 18
    core_13 = 19
    core_14 = 20
    core_15 = 21
    core_16 = 22
    core_17 = 23

    @property
    def is_link(self):
        """True iff a Routes object represents a chip to chip link."""
        return self < 6

    @property
    def is_core(self):
        """True iff a Routes object represents a route to a core."""
        return not self.is_link

    @property
    def core_num(self):
        """Get the core number being routed to.

        Raises
        ------
        ValueError
            If the route is not to a core.
        """
        if self.is_core:
            return self - 6
        else:
            raise ValueError("{} is not a core".format(repr(self)))
