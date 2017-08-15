from pacman.model.graphs import AbstractFPGAVertex, AbstractVirtualVertex, \
    AbstractSpiNNakerLinkVertex

class NerRoute(object):
    """Neighbour Exploring Routing (NER) algorithm from J. Navaridas et al.

    Algorithm refrence: J. Navaridas et al. SpiNNaker: Enhanced multicast routing,
    Parallel Computing (2014).

    `http://dx.doi.org/10.1016/j.parco.2015.01.002`
    """

    # determine if the system has wrap-around links
    def __call__(self, placements, machine, machine_graph):
        """

        :param placements:
        :param machine:
        :param machine_graph:
        :return:
        """

        wrap_around = machine.has_wrap_arounds()

    def disconnect_external_devices(self, placements, chip, machine):
        external_device_chip = object

        # placement find fpga vertex
        # chip find router find link that is active
        # real chip is destination of link
        # make a distinction between ingoing and outgoing connections
        for vertex in placements:
            if isinstance (vertex, AbstractVirtualVertex):
                virtual_chip_placement = None
                if isinstance (vertex, AbstractFPGAVertex):
                    virtual_chip_placement = \
                        placements.get_placement_of_vertex()
                elif isinstance (vertex, AbstractSpiNNakerLinkVertex):
                    virtual_chip_placement = \
                        placements.get_placement_of_vertex()

                # iterable
                chip_links = chip.router.links(virtual_chip_placement.x,
                                              virtual_chip_placement.y)

        # force the routing tree to route to the nearest connected chip

    def generate_routing_tree(self):
        # called for each partition

    def route_has_dead_links(self):

    def reroute_dead_links(self):

