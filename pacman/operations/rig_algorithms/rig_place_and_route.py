from pacman.utilities import rig_converters
from rig.place_and_route.place.sa import place
from rig.place_and_route.allocate.greedy import allocate
from rig.place_and_route.route.ner import route
from spinn_utilities.progress_bar import ProgressBar
from six import iteritems


class RigPlaceAndRoute(object):
    """ Performs placement and routing using rig algorithms; both are done\
        to save conversion time
    """

    __slots__ = ["_graph", "_machine"]

    def __call__(self, machine_graph, machine):
        self._graph = machine_graph
        self._machine = machine
        progress = ProgressBar(9, "Placing and Routing")
        try:
            return self._place_and_route(progress)
        finally:
            progress.end()

    def _place_and_route(self, p):
        vertex_resources, nets, net_names = self._rig_graph()
        p.update()

        rig_machine = self._rig_machine()
        p.update()

        constraints = self._rig_machine_constraints()
        p.update()

        self._add_graph_constraits(constraints, rig_machine)
        p.update()

        rig_placements = place(
            vertex_resources, nets, rig_machine, constraints)
        p.update()

        allocations = allocate(
            vertex_resources, nets, rig_machine, constraints, rig_placements)
        p.update()

        rig_routes = route(
            vertex_resources, nets, rig_machine, constraints, rig_placements,
            allocations, "cores")
        # Invert the map
        rig_routes = {
            name: rig_routes[net] for net, name in iteritems(net_names)}
        p.update()

        placements = self._from_rig_placements(rig_placements, allocations)
        p.update()

        routes = self._from_rig_routes(rig_routes)
        p.update()
        return placements, routes

    def _rig_graph(self):
        return rig_converters.convert_to_rig_graph(self._graph)

    def _rig_machine(self):
        return rig_converters.convert_to_rig_machine(self._machine)

    def _rig_machine_constraints(self):
        return rig_converters.create_rig_machine_constraints(self._machine)

    def _add_graph_constraits(self, constraints, rig_machine):
        constraints.extend(
            rig_converters.create_rig_graph_constraints(
                self._graph, rig_machine))

    def _from_rig_placements(self, rig_placements, rig_allocations):
        return rig_converters.convert_from_rig_placements(
            rig_placements, rig_allocations, self._graph)

    def _from_rig_routes(self, rig_routes):
        return rig_converters.convert_from_rig_routes(rig_routes, self._graph)
