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

    def disconnect_external_devices(self, machine, machine_graph):
        external_device_chip = object

        for vertex in machine_graph.vertices:
            if isinstance (vertex, AbstractVirtualVertex):
                link_data = None
                if isinstance (vertex, AbstractFPGAVertex):
                    link_data = machine.get_fpga_link_with_id(
                        vertex.board_address, vertex.fpga_id,
                        vertex.fpga_link_id
                    )
                elif isinstance (vertex, AbstractSpiNNakerLinkVertex):
                    link_data = machine.get_spinnaker_link_with_id(
                        vertex.spinnaker_link_id, vertex.board_address
                    )
                # force the routing tree to route to the nearest connected chip

