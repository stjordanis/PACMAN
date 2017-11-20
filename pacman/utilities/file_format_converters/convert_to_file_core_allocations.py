from pacman.utilities.file_format_schemas.validator \
    import validate_core_allocations

from spinn_utilities.progress_bar import ProgressBar

import json


class ConvertToFileCoreAllocations(object):
    """ Converts placements to core allocations
    """

    __slots__ = []

    def __call__(self, placements, file_path):
        """
        :param placements:
        :param file_path:
        """

        progress = ProgressBar(len(placements) + 1,
                               "Converting to JSON core allocations")

        # write basic stuff
        json_dict = dict()
        json_dict['type'] = "cores"
        vertex_by_id = dict()

        # process placements
        for placement in progress.over(placements, False):
            self._convert_placement(placement, vertex_by_id, json_dict)

        # dump dict into json file
        with open(file_path, "w") as f:
            json.dump(json_dict, f)
        progress.update()

        # validate the schema
        validate_core_allocations(json_dict)

        # complete progress bar
        progress.end()

        # return the file format
        return file_path, vertex_by_id

    def _convert_placement(self, placement, vertex_map, allocations_dict):
        vertex_id = str(id(placement.vertex))
        vertex_map[vertex_id] = placement.vertex
        allocations_dict[vertex_id] = [placement.p, placement.p + 1]
