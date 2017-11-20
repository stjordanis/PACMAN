import subprocess

from pacman.exceptions import PacmanExternalAlgorithmFailedToCompleteException
from .abstract_algorithm import AbstractAlgorithm
from pacman.model.decorators import overrides
from spinn_utilities.progress_bar import ProgressBar


class ExternalAlgorithm(AbstractAlgorithm):
    """
    the container for a algorithm which is external to the SpiNNaker software
    """

    __slots__ = [
        # The command line to call
        "_command_line_arguments"
    ]

    def __init__(
            self, algorithm_id, required_inputs, optional_inputs, outputs,
            required_input_tokens, optional_input_tokens,
            generated_output_tokens, command_line_arguments):
        # pylint: disable=too-many-arguments
        AbstractAlgorithm.__init__(
            self, algorithm_id, required_inputs, optional_inputs, outputs,
            required_input_tokens, optional_input_tokens,
            generated_output_tokens)
        self._command_line_arguments = command_line_arguments

    def _run_to_completion(self, args):
        progress = ProgressBar(
            1, "Running external algorithm {}".format(self._algorithm_id))
        try:
            # Run the external command
            child = subprocess.Popen(
                list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                stdin=subprocess.PIPE)
            child.wait()
            return child
        finally:
            progress.update()
            progress.end()


    @overrides(AbstractAlgorithm.call)
    def call(self, inputs):
        # Get the inputs to pass as the arguments
        arg_inputs = self._get_inputs(inputs)

        # Run the child with arguments appropriately converted
        child = self._run_to_completion(
            arg.format(**arg_inputs) for arg in self._command_line_arguments)

        # Detect any errors
        if child.returncode != 0:
            stdout, stderr = child.communicate()
            raise PacmanExternalAlgorithmFailedToCompleteException(
                    "Algorithm {} returned a non-zero error code {}\n"
                    "    Inputs: {}\n"
                    "    Output: {}\n"
                    "    Error: {}\n".format(
                        self._algorithm_id, child.returncode,
                        inputs, stdout, stderr))

        # Return the results processed into a dict
        # Use None here as the results don't actually exist, and are expected
        # to be obtained from a file, whose name is in inputs
        return self._get_outputs(inputs, [None] * len(self._outputs))

    def __repr__(self):
        return (
            "ExternalAlgorithm(algorithm_id={},"
            " required_inputs={}, optional_inputs={}, outputs={}"
            " command_line_arguments={})".format(
                self._algorithm_id, self._required_inputs,
                self._optional_inputs, self._outputs,
                self._command_line_arguments))

    @overrides(AbstractAlgorithm.write_provenance_header)
    def write_provenance_header(self, provenance_file):
        provenance_file.write("{}\n".format(self._algorithm_id))
        provenance_file.write("\t{}\n".format(self._command_line_arguments))
