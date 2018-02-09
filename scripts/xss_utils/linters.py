"""
Linter classes containing logic for checking various filetypes.
"""
import re
import os

from scripts.xss_utils.reporting import ExpressionRuleViolation, FileResults
from scripts.xss_utils.rules import Rules
from scripts.xss_utils.utils import Expression, ParseString, StringLines, is_skip_dir, SKIP_DIRS


class BaseLinter(object):
    """
    BaseLinter provides some helper functions that are used by multiple linters.

    """

    LINE_COMMENT_DELIM = None

    def _is_valid_directory(self, skip_dirs, directory):
        """
        Determines if the provided directory is a directory that could contain
        a file that needs to be linted.

        Arguments:
            skip_dirs: The directories to be skipped.
            directory: The directory to be linted.

        Returns:
            True if this directory should be linted for violations and False
            otherwise.
        """
        if is_skip_dir(skip_dirs, directory):
            return False

        return True

    def _load_file(self, file_full_path):
        """
        Loads a file into a string.

        Arguments:
            file_full_path: The full path of the file to be loaded.

        Returns:
            A string containing the files contents.

        """
        with open(file_full_path, 'r') as input_file:
            file_contents = input_file.read()
            return file_contents.decode(encoding='utf-8')

    def _load_and_check_file_is_safe(self, file_full_path, lint_function, results):
        """
        Loads the Python file and checks if it is in violation.

        Arguments:
            file_full_path: The file to be loaded and linted.
            lint_function: A function that will lint for violations. It must
                take two arguments:
                1) string contents of the file
                2) results object
            results: A FileResults to be used for this file

        Returns:
            The file results containing any violations.

        """
        file_contents = self._load_file(file_full_path)
        lint_function(file_contents, results)
        return results

    def _find_closing_char_index(
            self, start_delim, open_char, close_char, template, start_index, num_open_chars=0, strings=None
    ):
        """
        Finds the index of the closing char that matches the opening char.

        For example, this could be used to find the end of a Mako expression,
        where the open and close characters would be '{' and '}'.

        Arguments:
            start_delim: If provided (e.g. '${' for Mako expressions), the
                closing character must be found before the next start_delim.
            open_char: The opening character to be matched (e.g '{')
            close_char: The closing character to be matched (e.g '}')
            template: The template to be searched.
            start_index: The start index of the last open char.
            num_open_chars: The current number of open chars.
            strings: A list of ParseStrings already parsed

        Returns:
            A dict containing the following, or None if unparseable:
                close_char_index: The index of the closing character
                strings: a list of ParseStrings

        """
        strings = [] if strings is None else strings

        # Find start index of an uncommented line.
        start_index = self._uncommented_start_index(template, start_index)
        # loop until we found something useful on an uncommented out line
        while start_index is not None:
            close_char_index = template.find(close_char, start_index)
            if close_char_index < 0:
                # If we can't find a close char, let's just quit.
                return None
            open_char_index = template.find(open_char, start_index, close_char_index)
            parse_string = ParseString(template, start_index, close_char_index)

            valid_index_list = [close_char_index]
            if 0 <= open_char_index:
                valid_index_list.append(open_char_index)
            if parse_string.start_index is not None:
                valid_index_list.append(parse_string.start_index)
            min_valid_index = min(valid_index_list)

            start_index = self._uncommented_start_index(template, min_valid_index)
            if start_index == min_valid_index:
                break

        if start_index is None:
            # No uncommented code to search.
            return None

        if parse_string.start_index == min_valid_index:
            strings.append(parse_string)
            if parse_string.end_index is None:
                return None
            else:
                return self._find_closing_char_index(
                    start_delim, open_char, close_char, template, start_index=parse_string.end_index,
                    num_open_chars=num_open_chars, strings=strings
                )

        if open_char_index == min_valid_index:
            if start_delim is not None:
                # if we find another starting delim, consider this unparseable
                start_delim_index = template.find(start_delim, start_index, close_char_index)
                if 0 <= start_delim_index < open_char_index:
                    return None
            return self._find_closing_char_index(
                start_delim, open_char, close_char, template, start_index=open_char_index + 1,
                num_open_chars=num_open_chars + 1, strings=strings
            )

        if num_open_chars == 0:
            return {
                'close_char_index': close_char_index,
                'strings': strings,
            }
        else:
            return self._find_closing_char_index(
                start_delim, open_char, close_char, template, start_index=close_char_index + 1,
                num_open_chars=num_open_chars - 1, strings=strings
            )

    def _uncommented_start_index(self, template, start_index):
        """
        Finds the first start_index that is on an uncommented line.

        Arguments:
            template: The template to be searched.
            start_index: The start index of the last open char.

        Returns:
            If start_index is on an uncommented out line, returns start_index.
            Otherwise, returns the start_index of the first line that is
            uncommented, if there is one. Otherwise, returns None.
        """
        if self.LINE_COMMENT_DELIM is not None:
            line_start_index = StringLines(template).index_to_line_start_index(start_index)
            uncommented_line_start_index_regex = re.compile("^(?!\s*{})".format(self.LINE_COMMENT_DELIM), re.MULTILINE)
            # Finds the line start index of the first uncommented line, including the current line.
            match = uncommented_line_start_index_regex.search(template, line_start_index)
            if match is None:
                # No uncommented lines.
                return None
            elif match.start() < start_index:
                # Current line is uncommented, so return original start_index.
                return start_index
            else:
                # Return start of first uncommented line.
                return match.start()
        else:
            # No line comment delimeter, so this acts as a no-op.
            return start_index


class UnderscoreTemplateLinter(BaseLinter):
    """
    The linter for Underscore.js template files.
    """
    def __init__(self):
        """
        Init method.
        """
        super(UnderscoreTemplateLinter, self).__init__()
        self._skip_underscore_dirs = SKIP_DIRS + ('test',)

    def process_file(self, directory, file_name):
        """
        Process file to determine if it is an Underscore template file and
        if it is safe.

        Arguments:
            directory (string): The directory of the file to be checked
            file_name (string): A filename for a potential underscore file

        Returns:
            The file results containing any violations.

        """
        full_path = os.path.normpath(directory + '/' + file_name)
        results = FileResults(full_path)

        if not self._is_valid_directory(self._skip_underscore_dirs, directory):
            return results

        if not file_name.lower().endswith('.underscore'):
            return results

        return self._load_and_check_file_is_safe(full_path, self.check_underscore_file_is_safe, results)

    def check_underscore_file_is_safe(self, underscore_template, results):
        """
        Checks for violations in an Underscore.js template.

        Arguments:
            underscore_template: The contents of the Underscore.js template.
            results: A file results objects to which violations will be added.

        """
        self._check_underscore_expressions(underscore_template, results)
        results.prepare_results(underscore_template)

    def _check_underscore_expressions(self, underscore_template, results):
        """
        Searches for Underscore.js expressions that contain violations.

        Arguments:
            underscore_template: The contents of the Underscore.js template.
            results: A list of results into which violations will be added.

        """
        expressions = self._find_unescaped_expressions(underscore_template)
        for expression in expressions:
            if not self._is_safe_unescaped_expression(expression):
                results.violations.append(ExpressionRuleViolation(
                    Rules.underscore_not_escaped, expression
                ))

    def _is_safe_unescaped_expression(self, expression):
        """
        Determines whether an expression is safely escaped, even though it is
        using the expression syntax that doesn't itself escape (i.e. <%= ).

        In some cases it is ok to not use the Underscore.js template escape
        (i.e. <%- ) because the escaping is happening inside the expression.

        Safe examples::

            <%= HtmlUtils.ensureHtml(message) %>
            <%= _.escape(message) %>

        Arguments:
            expression: The Expression being checked.

        Returns:
            True if the Expression has been safely escaped, and False otherwise.

        """
        if expression.expression_inner.startswith('HtmlUtils.'):
            return True
        if expression.expression_inner.startswith('_.escape('):
            return True
        return False

    def _find_unescaped_expressions(self, underscore_template):
        """
        Returns a list of unsafe expressions.

        At this time all expressions that are unescaped are considered unsafe.

        Arguments:
            underscore_template: The contents of the Underscore.js template.

        Returns:
            A list of Expressions.
        """
        unescaped_expression_regex = re.compile("<%=.*?%>", re.DOTALL)

        expressions = []
        for match in unescaped_expression_regex.finditer(underscore_template):
            expression = Expression(
                match.start(), match.end(), template=underscore_template, start_delim="<%=", end_delim="%>"
            )
            expressions.append(expression)
        return expressions
