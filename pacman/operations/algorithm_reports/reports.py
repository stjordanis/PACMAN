import logging
import os
import time

from pacman.exceptions import PacmanRoutingException
from pacman.model.graphs import AbstractSpiNNakerLinkVertex, AbstractFPGAVertex
from pacman.model.graphs.common import EdgeTrafficType

from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.log import FormatAdapter

logger = FormatAdapter(logging.getLogger(__name__))


class _Report(object):
    def __init__(self, activity, folder, name, *args):
        self.activity = activity
        if not os.path.exists(folder):
            os.mkdir(folder)
        if len(args):
            name = name.format(*args)
        self.filename = os.path.join(folder, name)

    def __enter__(self):
        try:
            self._f = open(self.filename, "w")
            return self._f
        except IOError:
            logger.error("%s: Can't open file %s for writing.",
                         self.activity, self.filename, exc_info=True)
        return None
            
    def __exit__(self, exty, exval, traceback):  # @UnusedVariable
        self._f.close()
        return False


class _PlacementReport(_Report):
    def __init__(self, folder, name, *args):
        name += ".rpt"
        _Report.__init__(
            self, "Generate_placement_reports", folder, name, *args)


def tag_allocator_report(report_folder, tag_infos):
    """ Reports the tags that are being used by the tool chain for this\
        simulation

    :param report_folder: the folder to which the reports are being written
    :param tag_infos: the tags container generated by the tools.
    :rtype: None
    """
    with _Report("Generate_tag_report", report_folder, "tags.rpt") as f:
        progress = ProgressBar(
            len(list(tag_infos.ip_tags)) +
            len(list(tag_infos.reverse_ip_tags)),
            "Reporting Tags")
        for ip_tag in progress.over(tag_infos.ip_tags, False):
            f.write(str(ip_tag) + "\n")
        for reverse_ip_tag in progress.over(tag_infos.reverse_ip_tags):
            f.write(str(reverse_ip_tag) + "\n")


def placer_reports_with_application_graph(
        report_folder, hostname, graph, graph_mapper, placements, machine):
    """ Reports that can be produced from placement given a application\
        graph's existence

    :param report_folder: the folder to which the reports are being written
    :param hostname: the machine's hostname to which the placer worked on
    :param graph: the application graph to which placements were built
    :param graph_mapper: the mapping between application and machine \
                graphs
    :param placements: the placements objects built by the placer.
    :param machine: the python machine object
    :rtype: None
    """
    placement_report_with_application_graph_by_vertex(
        report_folder, hostname, graph, graph_mapper, placements)
    placement_report_with_application_graph_by_core(
        report_folder, hostname, placements, machine, graph_mapper)
    sdram_usage_report_per_chip(
        report_folder, hostname, placements, machine)


def placer_reports_without_application_graph(
        report_folder, hostname, machine_graph, placements, machine):
    """

    :param report_folder: the folder to which the reports are being written
    :param hostname: the machine's hostname to which the placer worked on
    :param placements: the placements objects built by the placer.
    :param machine: the python machine object
    :param machine_graph: the machine graph to which the reports are to\
             operate on
    :rtype: None
    """
    placement_report_without_application_graph_by_vertex(
        report_folder, hostname, placements, machine_graph)
    placement_report_without_application_graph_by_core(
        report_folder, hostname, placements, machine)
    sdram_usage_report_per_chip(
        report_folder, hostname, placements, machine)


def router_report_from_paths(
        report_folder, routing_tables, routing_infos, hostname,
        machine_graph, placements, machine):
    """ Generates a text file of routing paths

    :param routing_tables:
    :param report_folder:
    :param hostname:
    :param routing_infos:
    :param machine_graph:
    :param placements:
    :param machine:
    :rtype: None
    """
    with _Report("Generate_routing_reports", report_folder,
                 "edge_routing_info.rpt") as f:
        progress = ProgressBar(machine_graph.n_outgoing_edge_partitions,
                               "Generating Routing path report")

        f.write("        Edge Routing Report\n")
        f.write("        ===================\n\n")
        time_date_string = time.strftime("%c")
        f.write("Generated: {}".format(time_date_string))
        f.write(" for target machine '{}'".format(hostname))
        f.write("\n\n")

        for partition in progress.over(
                machine_graph.outgoing_edge_partitions):
            if partition.traffic_type == EdgeTrafficType.MULTICAST:
                source_placement = placements.get_placement_of_vertex(
                    partition.pre_vertex)
                key_and_mask = routing_infos.get_routing_info_from_partition(
                    partition).first_key_and_mask
                for edge in partition.edges:
                    destination_placement = placements.get_placement_of_vertex(
                        edge.post_vertex)
                    path, number_of_entries = _search_route(
                        source_placement, destination_placement, key_and_mask,
                        routing_tables, machine)
                    text = ("**** Edge '{}', from vertex: '{}' to vertex: '{}'"
                            .format(edge.label, edge.pre_vertex.label,
                                    edge.post_vertex.label))
                    text += " Takes path \n {}\n".format(path)
                    f.write(text)
                    f.write("Route length: {}\n".format(number_of_entries))

                    # End one entry:
                    f.write("\n")


def partitioner_report(report_folder, hostname, graph, graph_mapper):
    """ Generate report on the placement of vertices onto cores.
    """

    # Cycle through all vertices, and for each cycle through its vertices.
    # For each vertex, describe its core mapping.
    with _PlacementReport(report_folder, "partitioned_by_vertex") as f:
        progress = ProgressBar(
            graph.n_vertices, "Generating partitioner report")

        f.write("        Placement Information by Vertex\n")
        f.write("        ===============================\n\n")
        time_date_string = time.strftime("%c")
        f.write("Generated: {}".format(time_date_string))
        f.write(" for target machine '{}'".format(hostname))
        f.write("\n\n")

        for v in progress.over(graph.vertices):
            vertex_name = v.label
            vertex_model = v.__class__.__name__
            num_atoms = v.n_atoms
            f.write("**** Vertex: '{}'\n".format(vertex_name))
            f.write("Model: {}\n".format(vertex_model))
            f.write("Pop size: {}\n".format(num_atoms))
            f.write("Machine Vertices: \n")

            machine_vertices = sorted(graph_mapper.get_machine_vertices(v),
                                      key=lambda x: x.label)
            machine_vertices = sorted(
                machine_vertices,
                key=lambda x: graph_mapper.get_slice(x).lo_atom)
            for sv in machine_vertices:
                lo_atom = graph_mapper.get_slice(sv).lo_atom
                hi_atom = graph_mapper.get_slice(sv).hi_atom
                f.write("  Slice {}:{} ({} atoms) \n".format(
                    lo_atom, hi_atom, hi_atom - lo_atom + 1))
            f.write("\n")


def placement_report_with_application_graph_by_vertex(
        report_folder, hostname, graph, graph_mapper, placements):
    """ Generate report on the placement of vertices onto cores by vertex.

    :param report_folder: the folder to which the reports are being written
    :param hostname: the machine's hostname to which the placer worked on
    :param graph: the graph to which placements were built
    :param graph_mapper: the mapping between graphs
    :param placements: the placements objects built by the placer.
    """

    # Cycle through all vertices, and for each cycle through its vertices.
    # For each vertex, describe its core mapping.
    with _PlacementReport(report_folder, "placement_by_vertex") as f:
        progress = ProgressBar(
            graph.n_vertices, "Generating placement report")

        f.write("        Placement Information by Vertex\n")
        f.write("        ===============================\n\n")
        time_date_string = time.strftime("%c")
        f.write("Generated: {}".format(time_date_string))
        f.write(" for target machine '{}'".format(hostname))
        f.write("\n\n")

        used_processors_by_chip = dict()
        used_sdram_by_chip = dict()
        vertex_by_processor = dict()

        for v in progress.over(graph.vertices):
            vertex_name = v.label
            vertex_model = v.__class__.__name__
            num_atoms = v.n_atoms
            f.write("**** Vertex: '{}'\n".format(vertex_name))
            f.write("Model: {}\n".format(vertex_model))
            f.write("Pop size: {}\n".format(num_atoms))
            f.write("Machine Vertices: \n")

            machine_vertices = sorted(graph_mapper.get_machine_vertices(v),
                                      key=lambda vert: vert.label)
            machine_vertices = sorted(
                machine_vertices,
                key=lambda vert: graph_mapper.get_slice(vert).lo_atom)
            for sv in machine_vertices:
                lo_atom = graph_mapper.get_slice(sv).lo_atom
                hi_atom = graph_mapper.get_slice(sv).hi_atom
                num_atoms = hi_atom - lo_atom + 1
                cur_placement = placements.get_placement_of_vertex(sv)
                x, y, p = cur_placement.x, cur_placement.y, cur_placement.p
                key = "{},{}".format(x, y)
                if key in used_processors_by_chip:
                    used_pros = used_processors_by_chip[key]
                else:
                    used_pros = list()
                    used_sdram_by_chip.update({key: 0})
                vertex_by_processor["{},{},{}".format(x, y, p)] = sv
                new_pro = [p, cur_placement]
                used_pros.append(new_pro)
                used_processors_by_chip.update({key: used_pros})
                f.write("  Slice {}:{} ({} atoms) on core ({}, {}, {}) \n"
                        .format(lo_atom, hi_atom, num_atoms, x, y, p))
            f.write("\n")


def placement_report_without_application_graph_by_vertex(
        report_folder, hostname, placements, machine_graph):
    """ Generate report on the placement of vertices onto cores by vertex.

    :param report_folder: the folder to which the reports are being written
    :param hostname: the machine's hostname to which the placer worked on
    :param placements: the placements objects built by the placer.
    :param machine_graph: the machine graph generated by the end user
    """

    # Cycle through all vertices, and for each cycle through its vertices.
    # For each vertex, describe its core mapping.
    with _PlacementReport(report_folder, "placement_by_vertex") as f:
        progress = ProgressBar(machine_graph.n_vertices,
                               "Generating placement report")

        f.write("        Placement Information by Vertex\n")
        f.write("        ===============================\n\n")
        time_date_string = time.strftime("%c")
        f.write("Generated: {}".format(time_date_string))
        f.write(" for target machine '{}'".format(hostname))
        f.write("\n\n")

        used_processors_by_chip = dict()
        used_sdram_by_chip = dict()
        vertex_by_processor = dict()

        for v in progress.over(machine_graph.vertices):
            vertex_name = v.label
            vertex_model = v.__class__.__name__
            f.write("**** Vertex: '{}'\n".format(vertex_name))
            f.write("Model: {}\n".format(vertex_model))

            cur_placement = placements.get_placement_of_vertex(v)
            x, y, p = cur_placement.x, cur_placement.y, cur_placement.p
            key = "{},{}".format(x, y)
            if key in used_processors_by_chip:
                used_pros = used_processors_by_chip[key]
            else:
                used_pros = list()
                used_sdram_by_chip.update({key: 0})
            vertex_by_processor["{},{},{}".format(x, y, p)] = v
            new_pro = [p, cur_placement]
            used_pros.append(new_pro)
            used_processors_by_chip.update({key: used_pros})
            f.write(" Placed on core ({}, {}, {})\n\n".format(x, y, p))


def placement_report_with_application_graph_by_core(
        report_folder, hostname, placements, machine, graph_mapper):
    """ Generate report on the placement of vertices onto cores by core.

    :param report_folder: the folder to which the reports are being written
    :param hostname: the machine's hostname to which the placer worked on
    :param graph_mapper: the mapping between application and machine\
            graphs
    :param machine: the spinnaker machine object
    :param placements: the placements objects built by the placer.
    """

    # File 2: Placement by core.
    # Cycle through all chips and by all cores within each chip.
    # For each core, display what is held on it.
    with _PlacementReport(report_folder, "placement_by_core") as f:
        progress = ProgressBar(
            machine.n_chips, "Generating placement by core report")

        f.write("        Placement Information by Core\n")
        f.write("        =============================\n\n")
        time_date_string = time.strftime("%c")
        f.write("Generated: {}".format(time_date_string))
        f.write(" for target machine '{}'".format(hostname))
        f.write("\n\n")

        for chip in progress.over(machine.chips):
            written_header = False
            for processor in chip.processors:
                if placements.is_processor_occupied(
                        chip.x, chip.y, processor.processor_id):
                    if not written_header:
                        f.write("**** Chip: ({}, {})\n".format(
                            chip.x, chip.y))
                        f.write("Application cores: {}\n".format(
                            len(list(chip.processors))))
                        written_header = True
                    pro_id = processor.processor_id
                    vertex = placements.get_vertex_on_processor(
                        chip.x, chip.y, processor.processor_id)
                    app_vertex = graph_mapper.get_application_vertex(vertex)
                    vertex_label = app_vertex.label
                    vertex_model = app_vertex.__class__.__name__
                    vertex_atoms = app_vertex.n_atoms
                    lo_atom = graph_mapper.get_slice(vertex).lo_atom
                    hi_atom = graph_mapper.get_slice(vertex).hi_atom
                    num_atoms = hi_atom - lo_atom + 1
                    f.write("  Processor {}: Vertex: '{}', pop size: {}\n"
                            .format(pro_id, vertex_label, vertex_atoms))
                    f.write("              "
                            "Slice on this core: {}:{} ({} atoms)\n".format(
                                lo_atom, hi_atom, num_atoms))
                    f.write("              Model: {}\n\n".format(vertex_model))


def placement_report_without_application_graph_by_core(
        report_folder, hostname, placements, machine):
    """ Generate report on the placement of vertices onto cores by core.

    :param report_folder: the folder to which the reports are being written
    :param hostname: the machine's hostname to which the placer worked on
    :param machine: the spinnaker machine object
    :param placements: the placements objects built by the placer.
    """

    # File 2: Placement by core.
    # Cycle through all chips and by all cores within each chip.
    # For each core, display what is held on it.
    with _PlacementReport(report_folder, "placement_by_core") as f:
        progress = ProgressBar(
            machine.chips, "Generating placement by core report")

        f.write("        Placement Information by Core\n")
        f.write("        =============================\n\n")
        time_date_string = time.strftime("%c")
        f.write("Generated: {}".format(time_date_string))
        f.write(" for target machine '{}'".format(hostname))
        f.write("\n\n")

        for chip in progress.over(machine.chips):
            written_header = False
            for processor in chip.processors:
                if placements.is_processor_occupied(
                        chip.x, chip.y, processor.processor_id):
                    if not written_header:
                        f.write("**** Chip: ({}, {})\n".format(chip.x, chip.y))
                        f.write("Application cores: {}\n".format(
                            len(list(chip.processors))))
                        written_header = True
                    pro_id = processor.processor_id
                    vertex = placements.get_vertex_on_processor(
                        chip.x, chip.y, processor.processor_id)
                    f.write("  Processor {}: Vertex: '{}' \n".format(
                        pro_id, vertex.label))
                    f.write("              Model: {}\n\n".format(
                        vertex.__class__.__name__))
                    f.write("\n")


def sdram_usage_report_per_chip(report_folder, hostname, placements, machine):
    """ Reports the SDRAM used per chip

    :param report_folder: the folder to which the reports are being written
    :param hostname: the machine's hostname to which the placer worked on
    :param placements: the placements objects built by the placer.
    :param machine: the python machine object
    :rtype: None
    """
    with _PlacementReport(report_folder, "chip_sdram_usage_by_core") as f:
        f.write("        Memory Usage by Core\n")
        f.write("        ====================\n\n")
        time_date_string = time.strftime("%c")
        f.write("Generated: %s" % time_date_string)
        f.write(" for target machine '{}'".format(hostname))
        f.write("\n\n")
        used_sdram_by_chip = dict()

        placements = sorted(placements.placements,
                            key=lambda x: x.vertex.label)
        progress = ProgressBar(len(placements) + machine.n_chips,
                               "Generating SDRAM usage report")

        for placement in progress.over(placements, False):
            reqs = placement.vertex.resources_required
            x, y, p = placement.x, placement.y, placement.p
            f.write("SDRAM reqs for core ({},{},{}) is {} KB\n".format(
                x, y, p, int(reqs.sdram.get_value() / 1024.0)))
            if (x, y) not in used_sdram_by_chip:
                used_sdram_by_chip[x, y] = reqs.sdram.get_value()
            else:
                used_sdram_by_chip[x, y] += reqs.sdram.get_value()

        for chip in progress.over(machine.chips):
            try:
                used_sdram = used_sdram_by_chip[chip.x, chip.y]
            except KeyError:
                continue
            if not used_sdram:
                continue
            f.write(
                "**** Chip: ({}, {}) has total memory usage of {} KB "
                "({} bytes) out of a max of {} KB ({} bytes)\n\n".format(
                    chip.x, chip.y,
                    int(used_sdram / 1024.0), used_sdram,
                    int(chip.sdram.size / 1024.0), chip.sdram.size))


def routing_info_report(report_folder, machine_graph, routing_infos):
    """ Generates a report which says which keys is being allocated to each\
        vertex

    :param report_folder: the report folder to store this value
    :param machine_graph:
    :param routing_infos:
    """
    with _Report(
            "generate virtual key space information report",
            report_folder, "virtual_key_space_information_report.rpt") as f:
        progress = ProgressBar(machine_graph.n_outgoing_edge_partitions,
                               "Generating Routing info report")

        for vertex in machine_graph.vertices:
            f.write("Vertex: {}\n".format(vertex))
            for partition in progress.over(
                    machine_graph.
                    get_outgoing_edge_partitions_starting_at_vertex(
                        vertex), False):
                if partition.traffic_type == EdgeTrafficType.MULTICAST:
                    rinfo = routing_infos.get_routing_info_from_partition(
                        partition)
                    f.write("    Partition: {}, Routing Info: {}\n".format(
                        partition.identifier, rinfo.keys_and_masks))
        progress.end()


def router_report_from_router_tables(report_folder, routing_tables):
    """

    :param report_folder:
    :param routing_tables:
    :rtype: None
    """

    folder = os.path.join(report_folder, "routing_tables_generated")
    if not os.path.exists(folder):
        os.mkdir(folder)
    progress = ProgressBar(routing_tables.routing_tables,
                           "Generating Router table report")
    for routing_table in progress.over(routing_tables.routing_tables):
        if routing_table.number_of_entries > 0:
            _generate_routing_table(routing_table, folder)


def router_report_from_compressed_router_tables(report_folder, routing_tables):
    """

    :param report_folder:
    :param routing_tables:
    :rtype: None
    """

    folder = os.path.join(report_folder, "compressed_routing_tables_generated")
    if not os.path.exists(folder):
        os.mkdir(folder)
    progress = ProgressBar(routing_tables.routing_tables,
                           "Generating compressed router table report")
    for routing_table in progress.over(routing_tables.routing_tables):
        if routing_table.number_of_entries:
            _generate_routing_table(routing_table, folder)


def format_route(entry):
    line_format = "0x{:08X} 0x{:08X} 0x{:08X} {: <7s} {}"

    key = entry.routing_entry_key
    mask = entry.mask
    route = _reduce_route_value(entry.processor_ids, entry.link_ids)
    route_txt = _expand_route_value(entry.processor_ids, entry.link_ids)
    return line_format.format(key, mask, route, str(entry.defaultable),
                              route_txt)


def _generate_routing_table(routing_table, top_level_folder):
    with _Report("Generate_placement_reports", top_level_folder,
                 "routing_table_%d_%d.rpt",
                 routing_table.x, routing_table.y) as f:
        f.write("Router contains {} entries\n".format(
            routing_table.number_of_entries))

        f.write("{: <5s} {: <10s} {: <10s} {: <10s} {: <7s} {}\n".format(
            "Index", "Key", "Mask", "Route", "Default", "[Cores][Links]"))
        f.write(
            "{:-<5s} {:-<10s} {:-<10s} {:-<10s} {:-<7s} {:-<14s}\n".format(
                "", "", "", "", "", ""))
        line_format = "{: >5d} {}\n"

        entry_count = 0
        n_defaultable = 0
        for entry in routing_table.multicast_routing_entries:
            index = entry_count & 0xFFFF
            entry_str = line_format.format(index, format_route(entry))
            entry_count += 1
            if entry.defaultable:
                n_defaultable += 1
            f.write(entry_str)
        f.write("{} Defaultable entries\n".format(n_defaultable))


def generate_comparison_router_report(
        report_folder, routing_tables, compressed_routing_tables):
    """ Make a report on comparison of the compressed and uncompressed \
        routing tables

    :param report_folder: the folder to store the resulting report
    :param routing_tables: the original routing tables
    :param compressed_routing_tables: the compressed routing tables
    :rtype: None
    """
    with _Report("Generate_router_comparison_reports", report_folder,
                 "comparison_of_compressed_uncompressed_routing_tables") as f:
        progress = ProgressBar(
            routing_tables.routing_tables,
            "Generating comparison of router table report")

        for table in progress.over(routing_tables.routing_tables):
            x = table.x
            y = table.y
            compressed_table = \
                compressed_routing_tables.get_routing_table_for_chip(x, y)

            n_entries_uncompressed = table.number_of_entries
            n_entries_compressed = compressed_table.number_of_entries
            ratio = ((n_entries_uncompressed - n_entries_compressed) /
                     float(n_entries_uncompressed))

            n_entries_uncompressed = table.number_of_entries
            n_entries_compressed = compressed_table.number_of_entries
            ratio = ((n_entries_uncompressed - n_entries_compressed) /
                     float(n_entries_uncompressed))

            f.write(
                "Uncompressed table at {}:{} has {} entries whereas "
                "compressed table has {} entries. This is a decrease "
                "of {} %\n".format(
                    x, y, n_entries_uncompressed, n_entries_compressed,
                    ratio * 100))


def _reduce_route_value(processors_ids, link_ids):
    value = 0
    for link in link_ids:
        value += 1 << link
    for processor in processors_ids:
        value += 1 << (processor + 6)
    return value


def _expand_route_value(processors_ids, link_ids):
    """ Convert a 32-bit route word into a string which lists the target cores\
        and links.
    """

    # Convert processor targets to readable values:
    route_string = "["
    separator = ""
    for processor in processors_ids:
        route_string += "{}{}".format(separator, processor)
        separator = ", "

    route_string += "] ["

    # Convert link targets to readable values:
    link_labels = {0: 'E', 1: 'NE', 2: 'N', 3: 'W', 4: 'SW', 5: 'S'}

    separator = ""
    for link in link_ids:
        route_string += "{}{}".format(separator, link_labels[link])
        separator = ", "
    route_string += "]"
    return route_string


def _search_route(
        source_placement, dest_placement, key_and_mask, routing_tables,
        machine):

    # Create text for starting point
    source_vertex = source_placement.vertex
    text = ""
    if isinstance(source_vertex, AbstractSpiNNakerLinkVertex):
        text += "Virtual SpiNNaker Link"
    if isinstance(source_vertex, AbstractFPGAVertex):
        text += "Virtual FPGA Link"
    text += "{}:{}:{} -> ".format(
        source_placement.x, source_placement.y, source_placement.p)

    # Start the search
    number_of_entries = 0

    # If the destination is virtual, replace with the real destination chip
    extra_text, total_number_of_entries = _recursive_trace_to_destinations(
        source_placement.x, source_placement.y, key_and_mask,
        dest_placement.x, dest_placement.y, dest_placement.p, machine,
        routing_tables, number_of_entries)
    text += extra_text
    return text, total_number_of_entries


# locates the next dest position to check
def _recursive_trace_to_destinations(
        chip_x, chip_y, key_and_mask,
        dest_chip_x, dest_chip_y, dest_p, machine, routing_tables,
        number_of_entries):
    """ recursively search though routing tables till no more entries are\
        registered with this key
    """

    chip = machine.get_chip_at(chip_x, chip_y)

    # If reached destination, return the core
    if (chip_x == dest_chip_x and chip_y == dest_chip_y):
        text = ""
        if chip.virtual:
            text += "Virtual "
        text += "{}:{}:{}".format(dest_chip_x, dest_chip_y, dest_p)
        return text, number_of_entries + 1

    link_id = None
    result = None
    new_n_entries = None
    if chip.virtual:
        # If the current chip is virtual, use link out
        link_id, link = next(iter(chip.router))
        result, new_n_entries = _recursive_trace_to_destinations(
            link.destination_x, link.destination_y, key_and_mask,
            dest_chip_x, dest_chip_y, dest_p, machine,
            routing_tables, number_of_entries)
    else:
        # If the current chip is real, find the link to the destination
        table = routing_tables.get_routing_table_for_chip(chip_x, chip_y)
        entry = _locate_routing_entry(table, key_and_mask.key)
        for link_id in entry.link_ids:
            link = chip.router.get_link(link_id)
            result, new_n_entries = _recursive_trace_to_destinations(
                link.destination_x, link.destination_y, key_and_mask,
                dest_chip_x, dest_chip_y, dest_p, machine,
                routing_tables, number_of_entries)
            if result is not None:
                break

    if result is None:
        return None, None

    direction_text = _add_direction(link_id)
    text = "{}:{}:{} -> {}".format(
        chip_x, chip_y, direction_text, result)
    return text, new_n_entries + 1


def _add_direction(link):
    # Convert link targets to readable values:
    link_labels = {0: 'E', 1: 'NE', 2: 'N', 3: 'W', 4: 'SW', 5: 'S'}
    return link_labels[link]


def _locate_routing_entry(current_router, key):
    """ locate the entry from the router based off the edge

    :param current_router: the current router being used in the trace
    :param key: the key being used by the source placement
    :return: the routing table entry
    :raise PacmanRoutingException: when there is no entry located on this\
            router.
    """
    for entry in current_router.multicast_routing_entries:
        if entry.mask & key == entry.routing_entry_key:
            return entry
    raise PacmanRoutingException("no entry located")
