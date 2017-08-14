

class NerRoute(object):
    """Neighbour Exploring Routing (NER) algorithm from J. Navaridas et al.

    Algorithm refrence: J. Navaridas et al. SpiNNaker: Enhanced multicast routing,
    Parallel Computing (2014).

    `http://dx.doi.org/10.1016/j.parco.2015.01.002`
    """

    # determine if the system has wrap-around links
    def has_wrap_around_links(self, machine):
        (cores, links) = machine.get_cores_and_link_count
        if cores
