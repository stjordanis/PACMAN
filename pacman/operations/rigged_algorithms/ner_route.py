from pacman.model.graphs import AbstractFPGAVertex, AbstractVirtualVertex, \
    AbstractSpiNNakerLinkVertex
from pacman.operations.rigged_algorithms.ner_routing_tree import RoutingTree
from pacman.operations.rigged_algorithms.geometry import \
    shortest_mesh_path_length, shortest_torus_path_length, \
    shortest_mesh_path, shortest_torus_path, to_xyz, longest_dimension_first,\
    concentric_hexagons, Routes

import heapq


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



    def disconnect_external_devices(self, placements, chip, machine):
        external_device_chip = object

        # placement find fpga vertex
        # chip find router find link that is active
        # real chip is destination of link
        # make a distinction between ingoing and outgoing connections
        #   -perhaps not as this may be out of my scope
        for vertex in placements:
            if isinstance (vertex, AbstractVirtualVertex):
                virtual_chip_placement = None
                if isinstance (vertex, AbstractFPGAVertex):
                    virtual_chip_placement = \
                        placements.get_placement_of_vertex()
                elif isinstance (vertex, AbstractSpiNNakerLinkVertex):
                    virtual_chip_placement = \
                        placements.get_placement_of_vertex()

                # does something need to be done here to verify that
                # there is only one link?
                chip_links = chip.router.links(virtual_chip_placement.x,
                                              virtual_chip_placement.y)

                machine.get_chip_over_link(virtual_chip_placement.x,
                                           virtual_chip_placement.y,
                                           chip_links)

        # force the routing tree to route to the nearest connected chip

    def generate_routing_tree(self, source, destinations, machine, width,
                              height, radius=10):
        """Produce a shortest path tree for a given partition using NER.
        A RoutingTree is produced rooted at the source and visiting all
        destinations but which does not contain any vertices etc.

        Benchmarks and comments taken from Rig. (place_and_route.route.ner)

        :param source:
        :param destinations:
        :param machine:
        :param width:
        :param height:
        :param radius:
        :return:
        """

        # called for each partition
        route = {source: RoutingTree(source)}

        # Handle each destination, sorted by distance from the source,
        # closest first.
        for destination in sorted(destinations,
                                  key=(lambda destination_distance:
                                       shortest_mesh_path_length(
                                           to_xyz(source),
                                           to_xyz(
                                               destination_distance)
                                       )
                                       if not machine.has_wrap_arounds else
                                       shortest_torus_path_length(
                                           to_xyz(source),
                                           to_xyz(
                                               destination_distance),
                                           width, height
                                       ))):
            # Attempt to find the nearest neighboring placed node.
            neighbor = None

            # Try to find a nearby (within radius hops) node in the routing
            # tree that we can route to (falling back on just routing to
            # the source).
            #
            # In an implementation according to the algorithm's original
            # specification looks for nodes at each point in a growing set
            # of rings of concentric hexagons. If it doesn't find any
            # destinations this means an awful lot of checks: 1261 for the
            # default radius of 20.
            #
            # An alternative (but behaviourally identical) implementation
            # scans the list of all route nodes created so far and finds the
            # closest node which is < radius hops (falling back on the origin
            # if no node is closer than radius hops).  This implementation
            # requires one check per existing route node. In most routes this
            # is probably a lot less than 1261 since most routes will probably
            # have at most a few hundred route nodes by the time the last
            # destination is being routed.
            #
            # Which implementation is best is a difficult question to answer:
            # * In principle partitions with quite localised connections (e.g.
            #   nearest-neighbour or centroids traffic) may route slightly
            #   more quickly with the original algorithm since it may very
            #   quickly find a neighbour.
            # * In partitions which connect very spaced-out destinations the
            #   second implementation may be quicker since in such a scenario
            #   it is unlikely that a neighbour will be found.
            # * In extremely high-fan-out nets (e.g. broadcasts), the original
            #   method is very likely to perform *far* better than the
            #   alternative method since most iterations will complete
            #   immediately while the alternative method must scan *all* the
            #   route vertices.
            # As such, it should be clear that neither method alone is 'best'
            # and both have degenerate performance in certain completely
            # reasonable styles of net. As a result, a simple heuristic is
            # used to decide which technique to use.
            #
            # The following micro-benchmarks are crude estimate of the
            # runtime-per-iteration of each approach (at least in the case of
            # a torus topology)::
            #
            #     $ # Original approach
            #     $ python -m timeit --setup 'x, y, w, h, r = 1, 2, 5, 10, \
            #                                   {x:None for x in range(10)}' \
            #                    'x += 1; y += 1; x %= w; y %= h; (x, y) in r'
            #     1000000 loops, best of 3: 0.207 usec per loop
            #     $ # Alternative approach
            #     $ python -m timeit --setup 'from rig.geometry import \
            #                                 shortest_torus_path_length' \
            #                        'shortest_torus_path_length( \
            #                             (0, 1, 2), (3, 2, 1), 10, 10)'
            #     1000000 loops, best of 3: 0.666 usec per loop
            #
            # From this we can approximately suggest that the alternative
            # approach is 3x more expensive per iteration. A very crude
            # heuristic is to use the original approach when the number of
            # route nodes is more than 1/3rd of the number of routes checked
            # by the original method.

            hexagons = concentric_hexagons(radius)
            if len(hexagons) < len(route) / 3:
                # Original approach: Start looking for route nodes in a
                # concentric spiral pattern out from the destination node.
                for x, y in hexagons:
                    x += destination[0]
                    y += destination[1]
                    if machine.has_wrap_arounds:
                        x %= width
                        y %= height
                    if (x, y) in route:
                        neighbor = (x, y)
                        break
            else:
                # Alternative approach: Scan over every route node and check
                # to see if any are < radius, picking the closest one if so.
                neighbor = None
                neighbor_distance = None
                for candidate_neighbor in route:
                    if machine.has_wrap_arounds:
                        distance = shortest_torus_path_length(
                            to_xyz(candidate_neighbor),
                            to_xyz(destination), width, height
                        )
                    else:
                        distance = shortest_mesh_path_length(
                            to_xyz(candidate_neighbor),
                            to_xyz(destination)
                        )
                    if distance <= radius and (neighbor is None or
                                               distance < neighbor_distance):
                        neighbor = candidate_neighbor
                        neighbor_distance = distance

            # Route directly from the source if no nodes within radius hops of
            # the destination were found.
            if neighbor is None:
                neighbor = source

            # Find the shortest vector from the neighbor to the destination
            if machine.has_wrap_arounds:
                vector = shortest_torus_path(
                    to_xyz(neighbor), to_xyz(destination),
                    width, height)
            else:
                vector = shortest_mesh_path(
                    to_xyz(neighbor), to_xyz(destination))

            # The longest-dimension-first route may inadvertently pass through
            # an already connected node. If the route is allowed to pass
            # through that node it would create a cycle in the route which
            # would be VeryBad(TM). As a result, we work backward through the
            # route and truncate it at the first point where the route
            # intersects with a connected node.
            ldf = longest_dimension_first(vector, neighbor, width,
                                                   height)
            i = len(ldf)
            for direction, (x, y) in reversed(ldf):
                i -= 1
                if (x, y) in route:
                    # We've just bumped into a node which is already part of
                    # the route, this becomes our new neighbor and we truncate
                    # the LDF route. (Note ldf list is truncated just after
                    # the current position since it gives (direction,
                    # destination) pairs).
                    neighbor = (x, y)
                    ldf = ldf[i + 1:]
                    break

            # Take the longest dimension first route (i.e. traverse first
            # in the direction (x, y, w) with the greatest change in respect
            # to the source).
            last_node = route[neighbor]
            for direction, (x, y) in ldf:
                this_node = RoutingTree((x, y))
                route[(x, y)] = this_node

            # Add the route just generated to the list of children
                last_node.children.append((Routes(direction),
                                           this_node))
                last_node = this_node

        return route[source], route

    def a_star(self, machine, heuristic_source, sink, sources, chip, link):
        if machine.has_wrap_arounds:
            heuristic = (lambda node:
                         shortest_torus_path_length(to_xyz(node),
                                                    to_xyz(heuristic_source),
                                                    machine.max_chip_x,
                                                    machine.max_chip_y))
        else:
            heuristic = (lambda node:
                         shortest_mesh_path_length(to_xyz(node),
                                                   to_xyz(heuristic_source)))

        # A dictionary {node: (direction, previous_node)}. An entry indicates
        # that 1) the node has been visited and 2) which node we hopped from
        # (and the direction used) to reach previous_node.  This may be None
        # if the node is the sink.
        visited = {sink: None}

        # The node to which the tree will be reconnected
        selected_source = None

        # A heap (accessed vis heapq) of (distance, (x, y)) where distance is
        # the distance between (x, y) and heuristic_source and (x, y) is a
        # node to explore.
        to_visit = [(heuristic(sink), sink)]
        while to_visit:
            _, node = heapq.heappop(to_visit)

            # Terminate if we've found the destination
            if node in sources:
                selected_source = node
                break

            # Try all neighboring locations. Note: link identifiers are
            # from the perspective of the neighbor, not the current node!
            for neighbor_link in chip.router.links:
                # this is a link id (int)
                vector = link.multicast_default_to(neighbor_link)
