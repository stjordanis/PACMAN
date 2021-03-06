class SpecificCoreResource(object):
    """ Represents specific cores that need to be allocated.
    """

    __slots__ = [

        # The number of cores that need to be allocated on a given chip
        "_cores",

        # the chip that has these cores allocated
        "_chip"
    ]

    def __init__(self, chip, cores):
        """
        :param cores:\
            The specific cores that need to be allocated\
            (list of processor IDs)
        :type cores: iterable(int)
        :param chip: chip of where these cores are to be allocated
        :type chip: :py:class:`spinn_machine.Chip`
        :raise None: No known exceptions are raised
        """
        self._cores = cores
        self._chip = chip

    @property
    def cores(self):
        return self._cores

    @property
    def chip(self):
        return self._chip

    def get_value(self):
        return self._chip, self._cores
