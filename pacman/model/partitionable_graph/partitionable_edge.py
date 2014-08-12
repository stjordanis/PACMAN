from pacman.model.partitioned_graph.partitioned_edge import PartitionedEdge
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.exceptions import PacmanInvalidParameterException


class PartitionableEdge(object):
    """ Represents a directional edge in a partitionable_graph between two vertices
    """

    def __init__(self, pre_vertex, post_vertex, label=None):
        """

        :param pre_vertex: the vertex at the start of the edge
        :type pre_vertex: :py:class:`pacman.model.graph.vertex.Vertex`
        :param post_vertex: the vertex at the end of the edge
        :type post_vertex: :py:class:`pacman.model.graph.vertex.Vertex`
        :param label: The name of the edge
        :type label: str
        :raise None: Raises no known exceptions
        """
        self._label = label
        self._pre_vertex = pre_vertex
        self._post_vertex = post_vertex
        
    def create_subedge(self, pre_subvertex, post_subvertex, label=None):
        """ Create a subedge between the pre_subvertex and the post_subvertex
        
        :param pre_subvertex: The subvertex at the start of the subedge
        :type pre_subvertex:\
                    :py:class:`pacman.model.partitioned_graph.subvertex.PartitionedVertex`
        :param post_subvertex: The subvertex at the end of the subedge
        :type post_subvertex:\
                    :py:class:`pacman.model.partitioned_graph.subvertex.PartitionedVertex`
        :param label: The label to give the edge.  If not specified, and the\
                    edge has no label, the subedge will have no label.  If not\
                    specified and the edge has a label, a label will be provided
        :type label: str
        :return: The created subedge
        :rtype: :py:class:`pacman.model.subgraph.subedge.PartitionedEdge`
        :raise None: does not raise any known exceptions
        """
        if not isinstance(pre_subvertex, PartitionedVertex):
            raise PacmanInvalidParameterException(
                "pre_subvertex", str(pre_subvertex),
                "Must be a pacman.model"
                ".partitioned_graph.subvertex.PartitionedVertex")
        if not isinstance(post_subvertex, PartitionedVertex):
            raise PacmanInvalidParameterException(
                "post_subvertex",
                str(post_subvertex),
                "Must be a pacman.model.partitioned_graph.subvertex.PartitionedVertex")

        if label is None and self.label is not None:
            label = self.label

        return PartitionedEdge(pre_subvertex, post_subvertex, label)

    @property
    def pre_vertex(self):
        """ The vertex at the start of the edge

        :return: A vertex
        :rtype: :py:class:`pacman.model.graph.vertex.Vertex`
        :raise None: Raises no known exceptions
        """
        return self._pre_vertex

    @property
    def post_vertex(self):
        """ The vertex at the end of the edge

        :return: A vertex
        :rtype: :py:class:`pacman.model.graph.vertex.Vertex`
        :raise None: Raises no known exceptions
        """
        return self._post_vertex

    @property
    def label(self):
        """ The label of the edge

        :return: The label, or None if there is no label
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label