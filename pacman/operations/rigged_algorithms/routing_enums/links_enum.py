from enum import Enum
from six import iteritems


class Links(Enum):
    """Enumeration of links from a SpiNNaker chip."""

    east = 0
    north_east = 1
    north = 2
    west = 3
    south_west = 4
    south = 5

    def to_vector(self):
        """Given a link direction, return the equivalent vector."""
        return _direction_link_lookup[self]

    @property
    def opposite(self):
        """Get the opposite link to the one given."""
        return Links((self + 3) % 6)

_link_direction_lookup = {
    (+1, +0): Links.east,
    (-1, +0): Links.west,
    (+0, +1): Links.north,
    (+0, -1): Links.south,
    (+1, +1): Links.north_east,
    (-1, -1): Links.south_west,
}
_direction_link_lookup = {l: v for (v, l) in iteritems(_link_direction_lookup)}

# Special case: Lets assume we've got a 2xN or Nx2 system (N >= 2) where we can
# "spiral" around the Z axis to reach places which normally wouldn't be
# accessible.
#
# (x+1, 0) <-> (x+0, 1)        (1, y+0) <-> (0, y+1)
#           /                        |   |   |
#     --+--/+---+--                  +---+---+
#       | . |   |                    | . |   |/
#     --+---+---+--                  /---+---/
#       |   | . |                   /|   | . |
#     --+---+/--+--                  +---+---+
#           /                        |   |   |
_link_direction_lookup[(+1, -1)] = Links.south_west
_link_direction_lookup[(-1, +1)] = Links.north_east
