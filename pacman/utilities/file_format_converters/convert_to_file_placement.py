from pacman.utilities.file_format_schemas.validator import validate_placements
from spinn_utilities.progress_bar import ProgressBar

import json


class ConvertToFilePlacement(object):
    """ Converts memory placements to file placements
    """

    __slots__ = []

    def __call__(self, placements, file_path):
        """
        :param placements: the memory placements object
        :param file_path: the file path for the placements.json
        :return: file path for the placements.json
        """

        # write basic stuff
        json_obj = dict()
        vertex_by_id = dict()

        progress = ProgressBar(placements.n_placements + 1,
                               "converting to JSON placements")

        # process placements
        for placement in progress.over(placements, False):
            vertex_id = str(id(placement.vertex))
            vertex_by_id[vertex_id] = placement.vertex
            json_obj[vertex_id] = [placement.x, placement.y]

        # dump dict into json file
        with open(file_path, "w") as f:
            json.dump(json_obj, f)

        # validate the schema
        progress.update()
        validate_placements(json_obj)

        progress.end()

        # return the file format
        return file_path, vertex_by_id
