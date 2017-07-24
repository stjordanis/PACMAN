import unittest

from spinn_machine import VirtualMachine

from pacman.utilities.utility_objs import ResourceTracker
from pacman.model.resources import PreAllocatedResourceContainer
from pacman.model.resources import CoreResource
from pacman.model.resources import SpecificCoreResource
from spinn_machine.machine import Machine
from spinn_machine.chip import Chip
from spinn_machine.router import Router
from spinn_machine.sdram import SDRAM
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.resources.sdram_resource import SDRAMResource
from pacman.exceptions import PacmanValueError


class TestResourceTracker(unittest.TestCase):

    def test_n_cores_available(self):
        machine = VirtualMachine(
            width=2, height=2, n_cpus_per_chip=18, with_monitors=True)
        chip = machine.get_chip_at(0, 0)
        preallocated_resources = PreAllocatedResourceContainer(
            specific_core_resources=[
                SpecificCoreResource(chip=chip, cores=[1])],
            core_resources=[
                CoreResource(chip=chip, n_cores=2)])
        tracker = ResourceTracker(
            machine, preallocated_resources=preallocated_resources)

        # Should be 14 cores = 18 - 1 monitor - 1 specific core - 2 other cores
        self.assertEqual(tracker._n_cores_available(chip, (0, 0), None), 14)

        # Should be 0 since the core is already pre allocated
        self.assertEqual(tracker._n_cores_available(chip, (0, 0), 1), 0)

        # Should be 1 since the core is not pre allocated
        self.assertEqual(tracker._n_cores_available(chip, (0, 0), 2), 1)

        # Should be 0 since the core is monitor
        self.assertEqual(tracker._n_cores_available(chip, (0, 0), 0), 0)

        # Allocate a core
        tracker._allocate_core(chip, (0, 0), 2)

        # Should be 13 cores as one now allocated
        self.assertEqual(tracker._n_cores_available(chip, (0, 0), None), 13)

    def test_allocate_resources_when_chip_used(self):
        router = Router([])
        sdram = SDRAM()
        empty_chip = Chip(
            0, 0, [], router, sdram, 0, 0, "127.0.0.1",
            virtual=False, tag_ids=[1])
        machine = Machine([empty_chip], 0, 0)
        resource_tracker = ResourceTracker(machine)
        with self.assertRaises(PacmanValueError):
            resource_tracker.allocate_resources(
                ResourceContainer(sdram=SDRAMResource(1024)))


if __name__ == '__main__':
    unittest.main()
