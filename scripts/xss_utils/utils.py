"""
Utility classes/functions for the XSS Linter.
"""
import re


SKIP_DIRS = (
    '.git',
    '.pycharm_helpers',
    'common/static/xmodule/modules',
    'common/static/bundles',
    'perf_tests',
    'node_modules',
    'reports/diff_quality',
    'scripts/tests/templates',
    'spec',
    'test_root',
    'vendor',
)


def is_skip_dir(skip_dirs, directory):
    """
    Determines whether a directory should be skipped or linted.

    Arguments:
        skip_dirs: The configured directories to be skipped.
        directory: The current directory to be tested.

    Returns:
         True if the directory should be skipped, and False otherwise.

    """
    for skip_dir in skip_dirs:
        skip_dir_regex = re.compile(
            "(.*/)*{}(/.*)*".format(re.escape(skip_dir)))
        if skip_dir_regex.match(directory) is not None:
            return True
    return False


class StringLines(object):
    """
    StringLines provides utility methods to work with a string in terms of
    lines.  As an example, it can convert an index into a line number or column
    number (i.e. index into the line).
    """

    def __init__(self, string):
        """
        Init method.

        Arguments:
            string: The string to work with.

        """
        self._string = string
        self._line_start_indexes = self._process_line_breaks(string)
        # this is an exclusive index used in the case that the template doesn't
        # end with a new line
        self.eof_index = len(string)

    def _process_line_breaks(self, string):
        """
        Creates a list, where each entry represents the index into the string
        where the next line break was found.

        Arguments:
            string: The string in which to find line breaks.

        Returns:
             A list of indices into the string at which each line begins.

        """
        line_start_indexes = [0]
        index = 0
        while True:
            index = string.find('\n', index)
            if index < 0:
                break
            index += 1
            line_start_indexes.append(index)
        return line_start_indexes

    def get_string(self):
        """
        Get the original string.
        """
        return self._string

    def index_to_line_number(self, index):
        """
        Given an index, determines the line of the index.

        Arguments:
            index: The index into the original string for which we want to know
                the line number

        Returns:
            The line number of the provided index.

        """
        current_line_number = 0
        for line_break_index in self._line_start_indexes:
            if line_break_index <= index:
                current_line_number += 1
            else:
                break
        return current_line_number

    def index_to_column_number(self, index):
        """
        Gets the column (i.e. index into the line) for the given index into the
        original string.

        Arguments:
            index: The index into the original string.

        Returns:
            The column (i.e. index into the line) for the given index into the
            original string.

        """
        start_index = self.index_to_line_start_index(index)
        column = index - start_index + 1
        return column

    def index_to_line_start_index(self, index):
        """
        Gets the index of the start of the line of the given index.

        Arguments:
            index: The index into the original string.

        Returns:
            The index of the start of the line of the given index.

        """
        line_number = self.index_to_line_number(index)
        return self.line_number_to_start_index(line_number)

    def index_to_line_end_index(self, index):
        """
        Gets the index of the end of the line of the given index.

        Arguments:
            index: The index into the original string.

        Returns:
            The index of the end of the line of the given index.

        """
        line_number = self.index_to_line_number(index)
        return self.line_number_to_end_index(line_number)

    def line_number_to_start_index(self, line_number):
        """
        Gets the starting index for the provided line number.

        Arguments:
            line_number: The line number of the line for which we want to find
                the start index.

        Returns:
            The starting index for the provided line number.

        """
        return self._line_start_indexes[line_number - 1]

    def line_number_to_end_index(self, line_number):
        """
        Gets the ending index for the provided line number.

        Arguments:
            line_number: The line number of the line for which we want to find
                the end index.

        Returns:
            The ending index for the provided line number.

        """
        if line_number < len(self._line_start_indexes):
            return self._line_start_indexes[line_number]
        else:
            # an exclusive index in the case that the file didn't end with a
            # newline.
            return self.eof_index

    def line_number_to_line(self, line_number):
        """
        Gets the line of text designated by the provided line number.

        Arguments:
            line_number: The line number of the line we want to find.

        Returns:
            The line of text designated by the provided line number.

        """
        start_index = self._line_start_indexes[line_number - 1]
        if len(self._line_start_indexes) == line_number:
            line = self._string[start_index:]
        else:
            end_index = self._line_start_indexes[line_number]
            line = self._string[start_index:end_index - 1]
        return line

    def line_count(self):
        """
        Gets the number of lines in the string.
        """
        return len(self._line_start_indexes)
