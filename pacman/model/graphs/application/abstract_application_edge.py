from abc import abstractmethod

from pacman.model.graphs.abstract_edge import AbstractEdge


class AbstractApplicationEdge(AbstractEdge):
    """ a application edge between two application vertices

    """

    __slots__ = ()

    @abstractmethod
    def create_machine_edge(
            self, pre_vertex, pre_vertex_slice, post_vertex,
            post_vertex_slice, label):
        """ Create a machine edge between two machine vertices

        :param pre_vertex: The machine vertex at the start of the edge
        :type pre_vertex:\
            :py:class:`pacman.model.graph.machine.abstract_machine_vertex.AbstractMachineVertex`
        :param pre_vertex_slice:\
            The slice of the application vertex that is in the pre_vertex, or\
            None if the pre_vertex was a machine vertex to begin with
        :type pre_vertex_slice:\
            :py:class:`~pacman.model.graph.common.slice.Slice` or None
        :param post_vertex: The machine vertex at the end of the edge
        :type post_vertex:\
            :py:class:`pacman.model.graph.machine.abstract_machine_vertex.AbstractMachineVertex`
        :param post_vertex_slice:\
            The slice of the application vertex that is in the post_vertex, or\
            None if the post_vertex was a machine vertex to being with
        :param label: label of the edge
        :type label: str
        :return: The created machine edge
        :rtype:\
            :py:class:`pacman.model.graph.machine.abstract_machine_edge.AbstractMachineEdge`
        """
