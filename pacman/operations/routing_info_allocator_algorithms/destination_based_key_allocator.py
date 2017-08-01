from pacman.model.constraints.key_allocator_constraints\
    import AbstractKeyAllocatorConstraint
from pacman.model.routing_info \
    import BaseKeyAndMask, RoutingInfo, PartitionRoutingInfo
from pacman.model.routing_tables import MulticastRoutingTables
from pacman.utilities.utility_calls \
    import check_algorithm_can_support_constraints
from pacman.exceptions import PacmanConfigurationException

from spinn_utilities.progress_bar import ProgressBar

MAX_KEYS_SUPPORTED = 2048
MASK = 0xFFFFF800


class DestinationBasedRoutingInfoAllocator(object):
    """ A routing key allocator that operates for people who wish to have a\
    separate key for each destination (making a mc into a point-to-point cast.
    """

    __slots__ = []

    def __call__(self, machine_graph, placements, n_keys_map):
        """

        :param machine_graph: The graph to allocate the routing info for
        :type machine_graph:\
            :py:class:`pacman.model.graph.machine.machine_graph.MachineGraph`
        :param placements: The placements of the vertices
        :type placements:\
            :py:class:`pacman.model.placements.placements.Placements`
        :param n_keys_map: A map between the edges and the number of keys\
            required by the edges
        :type n_keys_map:\
            :py:class:`pacman.model.routing_info.abstract_machine_partition_n_keys_map.AbstractMachinePartitionNKeysMap`
        :return: The routing information
        :rtype: :py:class:`pacman.model.routing_info.routing_info.RoutingInfo`,
            :py:class:`pacman.model.routing_tables.multicast_routing_table.MulticastRoutingTable
        :raise pacman.exceptions.PacmanRouteInfoAllocationException: If\
            something goes wrong with the allocation.
        """

        # check that this algorithm supports the constraints put onto the
        # partitions
        supported_constraints = []
        check_algorithm_can_support_constraints(
            constrained_vertices=machine_graph.partitions,
            supported_constraints=supported_constraints,
            abstract_constraint_type=AbstractKeyAllocatorConstraint)

        # take each edge and create keys from its placement
        progress = ProgressBar(machine_graph.n_outgoing_edge_partitions,
                               "Allocating routing keys")
        routing_infos = RoutingInfo()
        routing_tables = MulticastRoutingTables()

        for partition in progress.over(machine_graph.outgoing_edge_partitions):
            for edge in partition.edges:
                routing_infos.add_partition_info(self._create_routing_info(
                    machine_graph, edge, placements, n_keys_map))

        return routing_infos, routing_tables

    def _create_routing_info(self, graph, edge, placements, n_keys_map):
        """
        :type graph: \
            :py:class:`pacman.model.graph.machine.machine_graph.MachineGraph`
        :type edge: \
            :py:class:`pacman.model.graph.machine.machine_edge.MachineEdge`
        :type placements: \
            :py:class:`pacman.model.placements.placements.Placements`
        :type n_keys_map: \
            :py:class:`pacman.model.routing_info.abstract_machine_partition_n_keys_map.AbstractMachinePartitionNKeysMap`
        """
        destination = edge.post_vertex
        placement = placements.get_placement_of_vertex(destination)
        key = self._get_key_from_placement(placement)
        keys_and_masks = list([BaseKeyAndMask(base_key=key, mask=MASK)])
        partition = graph.get_outgoing_edge_partition_starting_at_vertex(
            edge.pre_vertex)

        n_keys = n_keys_map.n_keys_for_partition(partition)
        if n_keys > MAX_KEYS_SUPPORTED:
            raise PacmanConfigurationException(
                "Only edges which require less than {} keys are supported"
                .format(MAX_KEYS_SUPPORTED))

        return PartitionRoutingInfo(keys_and_masks, edge)

    @staticmethod
    def _get_key_from_placement(placement):
        """ Return a key given a placement

        :param placement: the associated placement
        :type placement:\
            :py:class:`pacman.model.placements.placement.Placement`
        :return: The key
        :rtype: int
        """
        return placement.x << 24 | placement.y << 16 | placement.p << 11
