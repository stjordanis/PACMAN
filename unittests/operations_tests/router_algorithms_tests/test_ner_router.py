import unittest

from pacman.model.graphs.application \
    import ApplicationVertex, ApplicationGraph, ApplicationEdge
from pacman.model.graphs.machine \
    import MachineEdge, MachineGraph, SimpleMachineVertex

from pacman.model.placements import Placement, Placements
from pacman.model.routing_info import PartitionRoutingInfo, RoutingInfo
from pacman.operations.rigged_algorithms.ner_route import NerRoute
from pacman.utilities.constants import DEFAULT_MASK
from spinn_machine import VirtualMachine


class Vertex(ApplicationVertex):
    def __init__(self, n_atoms, label):
        ApplicationVertex.__init__(self, label=label, max_atoms_per_core=256)
        # Ignoring n_atoms

    def get_cpu_usage_for_atoms(self, lo_atom, hi_atom):
        return 10 * (hi_atom - lo_atom)

    def get_dtcm_usage_for_atoms(self, lo_atom, hi_atom):
        return 200 * (hi_atom - lo_atom)

    def get_sdram_usage_for_atoms(self, lo_atom, hi_atom, vertex_in_edges):
        return 4000 + (50 * (hi_atom - lo_atom))

    def get_resources_used_by_atoms(self, vertex_slice):
        # raise NotImplementedError("get_resources_used_by_atoms")
        pass

    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        # raise NotImplementedError("create_machine_vertex")
        pass

    def n_atoms(self):
        # raise NotImplementedError("n_atoms")
        pass


class TestRouter(unittest.TestCase):

    def setUp(self):
        # sort out graph
        self.vert1 = Vertex(10, "New AbstractConstrainedVertex 1")
        self.vert2 = Vertex(5, "New AbstractConstrainedVertex 2")
        self.edge1 = ApplicationEdge(self.vert1, self.vert2, "First edge")
        self.verts = [self.vert1, self.vert2]
        self.edges = [self.edge1]
        self.graph = ApplicationGraph("ApplicationGraph")
        # sort out graph
        self.graph = MachineGraph("MachineGraph")
        self.vertex1 = SimpleMachineVertex(
            0, 10, self.vert1.get_resources_used_by_atoms(0))
        self.vertex2 = SimpleMachineVertex(
            0, 5, self.vert2.get_resources_used_by_atoms(0))
        self.edge = MachineEdge(self.vertex1, self.vertex2)
        self.graph.add_vertex(self.vertex1)
        self.graph.add_vertex(self.vertex2)
        self.graph.add_edge(self.edge, "TEST")

    # @unittest.skip("demonstrating skipping")
    def test_router_with_multi_hop_route_across_board(self):
        # sort out placements
        self.placements = Placements()
        self.placement1 = Placement(x=0, y=0, p=2, vertex=self.vertex1)
        self.placement2 = Placement(x=7, y=11, p=2, vertex=self.vertex2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        # sort out routing infos
        self.routing_info = RoutingInfo()
        self.edge_routing_info1 = PartitionRoutingInfo(
            keys_and_masks=DEFAULT_MASK, partition=self.edge)
        #     # key=2 << 11, mask=DEFAULT_MASK, edge=self.edge)
        # self.routing_info.add_partition_info(self.edge_routing_info1)
        # create machine
        self.machine = VirtualMachine(28, 16, False)
        self.routing = NerRoute()
        self.routing(
            machine=self.machine, placements=self.placements,
            machine_graph=self.graph)
        print self.routing_info


if __name__ == '__main__':
    unittest.main()
