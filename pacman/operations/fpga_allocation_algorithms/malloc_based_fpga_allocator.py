
# pacman imports
from pacman.model.abstract_classes.abstract_virtual_vertex \
    import AbstractVirtualVertex
from pacman.utilities.algorithm_utilities.element_allocator_algorithm \
    import ElementAllocatorAlgorithm
from spinn_machine.FPGA import FPGA
from spinn_machine.chip import Chip
from spinn_machine.link import Link
from spinn_machine.router import Router
from spinn_machine.sdram import SDRAM
from spinn_machine.utilities.progress_bar import ProgressBar
from pacman.utilities.algorithm_utilities import machine_algorithm_utilities
from pacman.model.abstract_classes.virtual_partitioned_vertex \
    import VirtualPartitionedVertex
from pacman import exceptions

# general imports
import logging
import math
import sys
logger = logging.getLogger(__name__)


class MallocBasedFPGAAllocator(ElementAllocatorAlgorithm):
    """ A Chip id Allocation Allocator algorithm that keeps track of
        chip ids and attempts to allocate them as requested
    """

    DIRECTION_TO_EDGE_ID = {
        'left': [3, 4], 'left_north': [2, 3], 'north': [2, 1], 'right': [1, 0],
        'right_south': [0, 5], 'south': [5, 4]}

    FPGA_SIDES_TO_FPGA = {
        'left': 1, 'left_north': 1, 'north': 2, 'right': 2, 'right_south': 0,
        'south': 0}
    
    FPGA_ROUTER_SIZE = 1024

    def __init__(self):
        ElementAllocatorAlgorithm.__init__(self, 0, math.pow(2, 32))

        # we only want one virtual chip per 'link'
        self._virtual_chips = dict()

    def __call__(self, machine, link_interal_fpga_links, link_fpgas_links):
        """
        :param machine: the spinnaker machine
        :param link_interal_fpga_links: boolean flag, to see if we need to tie
        fpga chips with
        :return:
        """
        progress_bar = ProgressBar(
            len(machine.ethernet_connected_chips) * 48,
            "Allocating FPGA objects")

        # allocate standard ids for real chips
        for real_chip in machine.chips:
            expected_chip_id = (real_chip.x << 8) + real_chip.y
            self._allocate_elements(expected_chip_id, 1)

        for ethernet_chip in machine.ethernet_connected_chips:

            # get chips that should be connected to a fpga
            chips = self._find_chips(ethernet_chip, machine)

            # add the phyiscal fphga's for assocation later
            self._build_physical_fpgas(machine, ethernet_chip)

            for direction in chips.keys():
                for chip in chips[direction]:

                    # chips start moving in diagnoal at 4 up and 5 accross.
                    router = chip.router

                    # start at diagonal link and work around going up first
                    for link_id in self.DIRECTION_TO_EDGE_ID[direction]:
                        link = router.get_link(link_id)

                        fpga_chip = self._add_fpga_chip(
                            machine, self.FPGA_SIDES_TO_FPGA[direction],
                            ethernet_chip)

                        if link is None:
                            self._add_basic_fpga(chip, link_id, fpga_chip)
                        else:
                            self._add_linked_fpga(
                                link, chip, machine, fpga_chip)

                    progress_bar.update()
        progress_bar.end()

        # handle the initial linking of internal comms via fpga's.
        if link_interal_fpga_links:
            self._handle_internal_fpga_links(machine)

        # handle the linking of the 3 fpga on each board.
        if link_fpgas_links:
            self._handle_external_fpga_links(machine)

        return {"machine": machine}
    
    def _handle_external_fpga_links(self, machine):
        progress_bar = ProgressBar(
            len(machine.ethernet_connected_chips) * 3,
            "linking external FPGA objects together")
        for ethernet_chip in self._ethernet_connected_chips:
            
            fpga_0 = machine.get_fpga(ethernet_chip, 0)
            fpga_1 = machine.get_fpga(ethernet_chip, 1)
            fpga_2 = machine.get_fpga(ethernet_chip, 2)
            
            self._wire_fpga_faking_chips(fpga_0.chips[0], fpga_1.chips[-1])
            progress_bar.update()
            self._wire_fpga_faking_chips(fpga_1.chips[0], fpga_2.chips[-1])
            progress_bar.update()
            self._wire_fpga_faking_chips(fpga_2.chips[0], fpga_0.chips[-1])
            progress_bar.update()
        progress_bar.end()

    def _handle_internal_fpga_links(self, machine):
        progress_bar = ProgressBar(
            len(machine.ethernet_connected_chips) * 3,
            "linking internal FPGA objects together")
        for ethernet_chip in self._ethernet_connected_chips:
            for fpga_id in range(0, 3):
                fpga = machine.get_fpga(ethernet_chip, fpga_id)
                chips = list()
                for chip in fpga.chips:
                    chips.append(chip)
                    if len(chips) == 2:
                        
                        # wire the two chips by whatever two links are avilable
                        self._wire_fpga_faking_chips(chips[0], chips[1])
                        
                        # remove first chip
                        chips.pop(0)
            progress_bar.update()
        progress_bar.end()
        
    def _wire_fpga_faking_chips(self, chip_1, chip_2):
        source_id = self._locate_empty_link_id(chip_1)
        destination_id = self._locate_empty_link_id(chip_2)
        
        # check we have a valid linkage
        if source_id is None or destination_id is None:
            raise exceptions. PacmanAlgorithmFailedToCompleteException(
                "chips {} and {} dont have a free link".format(
                    chip_1, chip_2), "failed to link", None)
        
        # wire links
        chip_1.router.add_link(Link(
            source_x=chip_1.x, source_y=chip_1.y, source_link_id=source_id,
            destination_x=chip_2.x, destination_y=chip_2.y,
            multicast_default_from=source_id,
            multicast_default_to=destination_id))
        chip_2.router.add_link(Link(
            source_x=chip_2.x, source_y=chip_2.y, 
            source_link_id=destination_id,
            destination_x=chip_1.x, destination_y=chip_1.y,
            multicast_default_from=destination_id,
            multicast_default_to=source_id))

    @staticmethod
    def _locate_empty_link_id(chip):
        for link_id in range(0, 5):
            if chip.router.get_link(link_id) is None:
                return link_id
        return None

    @staticmethod
    def _build_physical_fpgas(machine, ethernet_chip):
        for id in range(0, 3):
            machine.add_fpga(FPGA(id), ethernet_chip)

    @staticmethod
    def _find_chips(ethernet_chip, machine):
        """

        :param ethernet_chip:
        :param machine:
        :return:
        """
        chips = {'left': [], 'left_north': [], 'north': [], 'right': [],
                 'right_south': [], 'south': []}

        # handle main chip
        chips['left'].append(ethernet_chip)

        chip = ethernet_chip

        # handle left chips (goes up 4)
        for _ in range(0, 4):
            x = chip.router.get_link(2).destination_x
            y = chip.router.get_link(2).destination_x
            chip = machine.get_chip_at(x, y)
            chips['left'].append(chip)

        # handle left north (goes accross 4 but add this chip)
        chips['left_north'].append(chip)
        for _ in range(0, 4):
            x = chip.router.get_link(1).destination_x
            y = chip.router.get_link(1).destination_x
            chip = machine.get_chip_at(x, y)
            chips['left_north'].append(chip)

        # handle north (goes left 3 but add this chip)
        chips['north'].append(chip)
        for _ in range(0, 3):
            x = chip.router.get_link(0).destination_x
            y = chip.router.get_link(0).destination_x
            chip = machine.get_chip_at(x, y)
            chips['north'].append(chip)

        # handle east (goes down 4 but add this chip)
        chips['right'].append(chip)
        for _ in range(0, 4):
            x = chip.router.get_link(5).destination_x
            y = chip.router.get_link(5).destination_x
            chip = machine.get_chip_at(x, y)
            chips['right'].append(chip)

        # handle east south (goes down accross 3 but add this chip)
        chips['right_south'].append(chip)
        for _ in range(0, 3):
            x = chip.router.get_link(4).destination_x
            y = chip.router.get_link(4).destination_x
            chip = machine.get_chip_at(x, y)
            chips['right_south'].append(chip)

        # handle south (goes accross 3 but add this chip)
        chips['south'].append(chip)
        for _ in range(0, 4):
            x = chip.router.get_link(3).destination_x
            y = chip.router.get_link(3).destination_x
            chip = machine.get_chip_at(x, y)
            chips['south'].append(chip)

        return chips

    @staticmethod
    def _add_basic_fpga(chip, link_id, fpga_chip):
        """

        :param chip:
        :param link_id:
        :param fpga_chip:
        :return:
        """
        virtual_link_id = (link_id + 3) % 6
        chip.router.add_link(Link(
            source_x=chip.x, source_y=chip.y, source_link_id=link_id,
            destination_x=fpga_chip.x, destination_y=fpga_chip.y,
            multicast_default_from=virtual_link_id,
            multicast_default_to=virtual_link_id))
        fpga_chip.router.add_link(Link(
            source_x=fpga_chip.x, source_y=fpga_chip.y,
            source_link_id=virtual_link_id, destination_x=chip.x,
            destination_y=chip.y, multicast_default_from=link_id,
            multicast_default_to=link_id))

    @staticmethod
    def _add_linked_fpga(link, chip, machine, fpga_chip):
        """

        :param link:
        :param chip:
        :param machine:
        :param fpga_chip:
        :return:
        """

        link_id = link.source_link_id
        virtual_link_id = (link_id + 3) % 6

        extra_chip = machine.get_chip_at(link.destination_x, link.destination_y)

        # forward
        chip.router.remove_link(link_id)
        chip.router.add_link(Link(
            source_x=chip.x, source_y=chip.y,
            source_link_id=link.source_link_id,
            destination_x=fpga_chip.x, destination_y=fpga_chip.y,
            multicast_default_from=virtual_link_id,
            multicast_default_to=virtual_link_id))
        # backwards
        fpga_chip.router.add_link(Link(
            source_x=fpga_chip.x, source_y=fpga_chip.y,
            source_link_id=virtual_link_id, destination_x=chip.x,
            destination_y=chip.y, multicast_default_from=link_id,
            multicast_default_to=link_id))

        # extra chip forwards
        extra_chip.router.remove_link(virtual_link_id)
        extra_chip.router.add_link(Link(
            source_x=extra_chip.x, source_y=extra_chip.y,
            source_link_id=virtual_link_id,
            destination_x=fpga_chip.x, destination_y=fpga_chip.y,
            multicast_default_from=virtual_link_id,
            multicast_default_to=virtual_link_id))
        # backwards
        fpga_chip.router.add_link(Link(
            source_x=fpga_chip.x, source_y=fpga_chip.y,
            source_link_id=link_id, destination_x=extra_chip.x,
            destination_y=extra_chip.y, multicast_default_from=link_id,
            multicast_default_to=link_id))

    def _add_fpga_chip(self, machine, fpga_id, ethernet_connected_chip):
        """ Create a virtual chip as a real chip in the machine

        :param machine: the machine which will be adjusted
        :param fpga_id:
        :param ethernet_connected_chip:
        :return: The fpga chip thats been created
        """

        # create the router
        links = []
        router_object = Router(
            links=links, emergency_routing_enabled=False,
            clock_speed=Router.ROUTER_DEFAULT_CLOCK_SPEED,
            n_available_multicast_entries=sys.maxint)

        # create the processors
        processors = list()

        # get id
        x, y = self._allocate_id()

        chip = Chip(
            processors=processors, router=router_object, sdram=SDRAM(size=0),
            x=x, y=y, fpga=True, virtual=True, nearest_ethernet_x=None,
            nearest_ethernet_y=None)

        machine.add_chip(chip)
        fpga = machine.get_fpga(ethernet_connected_chip, fpga_id)
        fpga.add_chip(chip)

        return chip

    def _allocate_id(self):
        """ Allocate a chip id from the free space
        """

        # can always assume there's at least one element in the free space,
        # otherwise it will have already been deleted already.
        free_space_chunk = self._free_space_tracker[0]
        chip_id = free_space_chunk.start_address
        self._allocate_elements(chip_id, 1)
        return (chip_id >> 8), (chip_id & 0xFFFF)
