"""
TestTagsModel
"""
from __future__ import absolute_import
# pacman imports
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.tags import Tags

# spinnmachine imports
from spinn_machine.tags import IPTag, ReverseIPTag

# general imports
import unittest
from pacman.exceptions import PacmanInvalidParameterException


class TestTagsModel(unittest.TestCase):
    """
    test that the tags object works as expected
    """

    def test_new_tag_info(self):
        """
        test that creating a empty tag object works
        """
        Tags()

    def test_adding_a_iptag_to_tag_info(self):
        """
        check that adding a tag after initialisation works
        """
        tag_info = Tags()
        iptag = IPTag("", 0, 0, 1, "122.2.2.2", 1, False)
        machine_vertex = SimpleMachineVertex(None, "")
        tag_info.add_ip_tag(iptag, machine_vertex)

    def test_adding_a_reverse_iptag(self):
        """
        check that adding a reverse iptag works correctly
        """
        tag_info = Tags()
        reverse_iptag = ReverseIPTag("", 1, 23, 0, 0, 1, 1)
        machine_vertex = SimpleMachineVertex(None, "")
        tag_info.add_reverse_ip_tag(reverse_iptag, machine_vertex)

    def test_add_iptag_then_locate_tag(self):
        """
        check that locating a iptag via get_ip_tags_for_vertex function
        """
        tag_info = Tags()
        iptag = IPTag("", 0, 0, 1, "122.2.2.2", 1, False)
        machine_vertex = SimpleMachineVertex(None, "")
        tag_info.add_ip_tag(iptag, machine_vertex)

        gotton_tag = tag_info.get_ip_tags_for_vertex(machine_vertex)
        self.assertEqual(gotton_tag[0], iptag)

    def test_add_iptag_then_fail_to_locate(self):
        """
        test that asking for a invalid iptag returns a None value
        """
        tag_info = Tags()
        iptag = IPTag("", 0, 0, 1, "122.2.2.2", 1, False)
        machine_vertex = SimpleMachineVertex(None, "")
        machine_vertex_2 = SimpleMachineVertex(None, "")
        tag_info.add_ip_tag(iptag, machine_vertex)

        gotton_tag = tag_info.get_ip_tags_for_vertex(machine_vertex_2)
        self.assertEqual(gotton_tag, None)

    def test_add_reverse_iptag_then_locate_tag(self):
        """
        check that asking for a reverse iptag for a specific machine vertex
        works
        """
        tag_info = Tags()
        reverse_iptag = ReverseIPTag("", 1, 23, 0, 0, 1, 1)
        machine_vertex = SimpleMachineVertex(None, "")
        tag_info.add_reverse_ip_tag(reverse_iptag, machine_vertex)
        gotton_tag = tag_info.get_reverse_ip_tags_for_vertex(
            machine_vertex)
        self.assertEqual(gotton_tag[0], reverse_iptag)

    def test_add_reverse_iptag_then_not_locate_tag(self):
        """
        check that asking for a reverse iptag with a incorrect machine vertex
        will cause a none returned
        """
        tag_info = Tags()
        reverse_iptag = ReverseIPTag("", 1, 23, 0, 0, 1, 1)
        machine_vertex = SimpleMachineVertex(None, "")
        machine_vertex2 = SimpleMachineVertex(None, "")
        tag_info.add_reverse_ip_tag(reverse_iptag, machine_vertex2)
        gotton_tag = tag_info.get_reverse_ip_tags_for_vertex(
            machine_vertex)
        self.assertEqual(gotton_tag, None)

    def test_add_conflicting_ip_tag(self):
        tags = Tags()
        tag1 = IPTag("", 0, 0, 1, "122.2.2.2", 1, False)
        tag2 = IPTag("", 0, 7, 1, "122.2.2.3", 1, False)
        tag3 = ReverseIPTag("", 1, 23, 0, 0, 1, 1)
        machine_vertex = SimpleMachineVertex(None, "")
        tags.add_ip_tag(tag1, machine_vertex)
        with self.assertRaises(PacmanInvalidParameterException) as e:
            tags.add_ip_tag(tag2, machine_vertex)
        self.assertIn("The tag specified has already been assigned with "
                      "different properties", str(e.exception))
        with self.assertRaises(PacmanInvalidParameterException) as e:
            tags.add_reverse_ip_tag(tag3, machine_vertex)
        self.assertIn("The tag has already been assigned on the given board",
                      str(e.exception))
        with self.assertRaises(PacmanInvalidParameterException) as e:
            tags.add_ip_tag(tag3, machine_vertex)
        self.assertIn("Only add IP tags with this method.",
                      str(e.exception))

    def test_add_conflicting_reverse_ip_tag(self):
        tags = Tags()
        tag1 = ReverseIPTag("", 1, 23, 0, 0, 1, 1)
        tag2 = ReverseIPTag("", 1, 23, 0, 0, 1, 1)
        tag3 = IPTag("", 0, 7, 1, "122.2.2.3", 1, False)
        machine_vertex = SimpleMachineVertex(None, "")
        tags.add_reverse_ip_tag(tag1, machine_vertex)
        with self.assertRaises(PacmanInvalidParameterException) as e:
            tags.add_reverse_ip_tag(tag2, machine_vertex)
        self.assertIn("The tag has already been assigned on the given board",
                      str(e.exception))
        with self.assertRaises(PacmanInvalidParameterException) as e:
            tags.add_ip_tag(tag3, machine_vertex)
        self.assertIn("The tag has already been assigned to a reverse IP tag"
                      " on the given board", str(e.exception))
        with self.assertRaises(PacmanInvalidParameterException) as e:
            tags.add_reverse_ip_tag(tag3, machine_vertex)
        self.assertIn("Only add reverse IP tags with this method.",
                      str(e.exception))


if __name__ == '__main__':
    unittest.main()
