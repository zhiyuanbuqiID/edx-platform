#!/usr/bin/env python
"""
A linting tool to check for xss vulnerabilities.
"""
from __future__ import print_function

import argparse
import ast
import os
import re
import sys
import textwrap

from scripts.xss_utils.linters import BaseLinter, JavaScriptLinter, UnderscoreTemplateLinter
from scripts.xss_utils.reporting import ExpressionRuleViolation, FileResults, RuleViolation, SummaryResults
from scripts.xss_utils.rules import Rules
from scripts.xss_utils.utils import Expression, ParseString, StringLines, is_skip_dir, SKIP_DIRS
from scripts.xss_utils.visitors import AllNodeVisitor, HtmlStringVisitor, OuterFormatVisitor


class PythonLinter(BaseLinter):
    """
    The linter for Python files.

    The current implementation of the linter does naive Python parsing. It does
    not use the parser. One known issue is that parsing errors found inside a
    docstring need to be disabled, rather than being automatically skipped.
    Skipping docstrings is an enhancement that could be added.
    """

    LINE_COMMENT_DELIM = "#"

    def __init__(self):
        """
        Init method.
        """
        super(PythonLinter, self).__init__()
        self._skip_python_dirs = SKIP_DIRS + ('tests', 'test/acceptance')

    def process_file(self, directory, file_name):
        """
        Process file to determine if it is a Python file and
        if it is safe.

        Arguments:
            directory (string): The directory of the file to be checked
            file_name (string): A filename for a potential Python file

        Returns:
            The file results containing any violations.

        """
        file_full_path = os.path.normpath(directory + '/' + file_name)
        results = FileResults(file_full_path)

        if not results.is_file:
            return results

        if file_name.lower().endswith('.py') is False:
            return results

        # skip tests.py files
        # TODO: Add configuration for files and paths
        if file_name.lower().endswith('tests.py'):
            return results

        # skip this linter code (i.e. xss_linter.py)
        if file_name == os.path.basename(__file__):
            return results

        if not self._is_valid_directory(self._skip_python_dirs, directory):
            return results

        return self._load_and_check_file_is_safe(file_full_path, self.check_python_file_is_safe, results)

    def check_python_file_is_safe(self, file_contents, results):
        """
        Checks for violations in a Python file.

        Arguments:
            file_contents: The contents of the Python file.
            results: A file results objects to which violations will be added.

        """
        root_node = self.parse_python_code(file_contents, results)
        self.check_python_code_is_safe(file_contents, root_node, results)
        # Check rules specific to .py files only
        # Note that in template files, the scope is different, so you can make
        # different assumptions.
        if root_node is not None:
            # check format() rules that can be run on outer-most format() calls
            visitor = OuterFormatVisitor(file_contents, results)
            visitor.visit(root_node)
        results.prepare_results(file_contents, line_comment_delim=self.LINE_COMMENT_DELIM)

    def check_python_code_is_safe(self, python_code, root_node, results):
        """
        Checks for violations in Python code snippet. This can also be used for
        Python that appears in files other than .py files, like in templates.

        Arguments:
            python_code: The contents of the Python code.
            root_node: The root node of the Python code parsed by AST.
            results: A file results objects to which violations will be added.

        """
        if root_node is not None:
            # check illegal concatenation and interpolation
            visitor = AllNodeVisitor(python_code, results)
            visitor.visit(root_node)
        # check rules parse with regex
        self._check_custom_escape(python_code, results)

    def parse_python_code(self, python_code, results):
        """
        Parses Python code.

        Arguments:
            python_code: The Python code to be parsed.

        Returns:
            The root node that was parsed, or None for SyntaxError.

        """
        python_code = self._strip_file_encoding(python_code)
        try:
            return ast.parse(python_code)

        except SyntaxError as e:
            if e.offset is None:
                expression = Expression(0)
            else:
                lines = StringLines(python_code)
                line_start_index = lines.line_number_to_start_index(e.lineno)
                expression = Expression(line_start_index + e.offset)
            results.violations.append(ExpressionRuleViolation(
                Rules.python_parse_error, expression
            ))
            return None

    def _strip_file_encoding(self, file_contents):
        """
        Removes file encoding from file_contents because the file was already
        read into Unicode, and the AST parser complains.

        Arguments:
            file_contents: The Python file contents.

        Returns:
            The Python file contents with the encoding stripped.
        """
        # PEP-263 Provides Regex for Declaring Encoding
        # Example: -*- coding: <encoding name> -*-
        # This is only allowed on the first two lines, and it must be stripped
        # before parsing, because we have already read into Unicode and the
        # AST parser complains.
        encoding_regex = re.compile(r"^[ \t\v]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)")
        encoding_match = encoding_regex.search(file_contents)
        # If encoding comment not found on first line, search second line.
        if encoding_match is None:
            lines = StringLines(file_contents)
            if lines.line_count() >= 2:
                encoding_match = encoding_regex.search(lines.line_number_to_line(2))
        # If encoding was found, strip it
        if encoding_match is not None:
            file_contents = file_contents.replace(encoding_match.group(), '#', 1)
        return file_contents

    def _check_custom_escape(self, file_contents, results):
        """
        Checks for custom escaping calls, rather than using a standard escaping
        method.

        Arguments:
            file_contents: The contents of the Python file
            results: A list of results into which violations will be added.

        """
        for match in re.finditer("(<.*&lt;|&lt;.*<)", file_contents):
            expression = Expression(match.start(), match.end())
            results.violations.append(ExpressionRuleViolation(
                Rules.python_custom_escape, expression
            ))


class MakoTemplateLinter(BaseLinter):
    """
    The linter for Mako template files.
    """
    LINE_COMMENT_DELIM = "##"

    def __init__(self):
        """
        Init method.
        """
        super(MakoTemplateLinter, self).__init__()
        self.javascript_linter = JavaScriptLinter()
        self.python_linter = PythonLinter()

    def process_file(self, directory, file_name):
        """
        Process file to determine if it is a Mako template file and
        if it is safe.

        Arguments:
            directory (string): The directory of the file to be checked
            file_name (string): A filename for a potential Mako file

        Returns:
            The file results containing any violations.

        """
        mako_file_full_path = os.path.normpath(directory + '/' + file_name)
        results = FileResults(mako_file_full_path)

        if not results.is_file:
            return results

        if not self._is_valid_directory(directory):
            return results

        # TODO: When safe-by-default is turned on at the platform level, will we:
        # 1. Turn it on for .html only, or
        # 2. Turn it on for all files, and have different rulesets that have
        #    different rules of .xml, .html, .js, .txt Mako templates (e.g. use
        #    the n filter to turn off h for some of these)?
        # For now, we only check .html and .xml files
        if not (file_name.lower().endswith('.html') or file_name.lower().endswith('.xml')):
            return results

        return self._load_and_check_file_is_safe(mako_file_full_path, self._check_mako_file_is_safe, results)

    def _is_valid_directory(self, directory):
        """
        Determines if the provided directory is a directory that could contain
        Mako template files that need to be linted.

        Arguments:
            directory: The directory to be linted.

        Returns:
            True if this directory should be linted for Mako template violations
            and False otherwise.
        """
        if is_skip_dir(SKIP_DIRS, directory):
            return False

        # TODO: This is an imperfect guess concerning the Mako template
        # directories. This needs to be reviewed before turning on safe by
        # default at the platform level.
        if ('/templates/' in directory) or directory.endswith('/templates'):
            return True

        return False

    def _check_mako_file_is_safe(self, mako_template, results):
        """
        Checks for violations in a Mako template.

        Arguments:
            mako_template: The contents of the Mako template.
            results: A file results objects to which violations will be added.

        """
        if self._is_django_template(mako_template):
            return
        has_page_default = self._has_page_default(mako_template, results)
        self._check_mako_expressions(mako_template, has_page_default, results)
        self._check_mako_python_blocks(mako_template, has_page_default, results)
        results.prepare_results(mako_template, line_comment_delim=self.LINE_COMMENT_DELIM)

    def _is_django_template(self, mako_template):
        """
            Determines if the template is actually a Django template.

        Arguments:
            mako_template: The template code.

        Returns:
            True if this is really a Django template, and False otherwise.

        """
        if re.search('({%.*%})|({{.*}})|({#.*#})', mako_template) is not None:
            return True
        return False

    def _get_page_tag_count(self, mako_template):
        """
        Determines the number of page expressions in the Mako template. Ignores
        page expressions that are commented out.

        Arguments:
            mako_template: The contents of the Mako template.

        Returns:
            The number of page expressions
        """
        count = len(re.findall('<%page ', mako_template, re.IGNORECASE))
        count_commented = len(re.findall(r'##\s+<%page ', mako_template, re.IGNORECASE))
        return max(0, count - count_commented)

    def _has_page_default(self, mako_template, results):
        """
        Checks if the Mako template contains the page expression marking it as
        safe by default.

        Arguments:
            mako_template: The contents of the Mako template.
            results: A list of results into which violations will be added.

        Side effect:
            Adds violations regarding page default if necessary

        Returns:
            True if the template has the page default, and False otherwise.

        """
        page_tag_count = self._get_page_tag_count(mako_template)
        # check if there are too many page expressions
        if 2 <= page_tag_count:
            results.violations.append(RuleViolation(Rules.mako_multiple_page_tags))
            return False
        # make sure there is exactly 1 page expression, excluding commented out
        # page expressions, before proceeding
        elif page_tag_count != 1:
            results.violations.append(RuleViolation(Rules.mako_missing_default))
            return False
        # check that safe by default (h filter) is turned on
        page_h_filter_regex = re.compile('<%page[^>]*expression_filter=(?:"h"|\'h\')[^>]*/>')
        page_match = page_h_filter_regex.search(mako_template)
        if not page_match:
            results.violations.append(RuleViolation(Rules.mako_missing_default))
        return page_match

    def _check_mako_expressions(self, mako_template, has_page_default, results):
        """
        Searches for Mako expressions and then checks if they contain
        violations, including checking JavaScript contexts for JavaScript
        violations.

        Arguments:
            mako_template: The contents of the Mako template.
            has_page_default: True if the page is marked as default, False
                otherwise.
            results: A list of results into which violations will be added.

        """
        expressions = self._find_mako_expressions(mako_template)
        contexts = self._get_contexts(mako_template)
        self._check_javascript_contexts(mako_template, contexts, results)
        for expression in expressions:
            if expression.end_index is None:
                results.violations.append(ExpressionRuleViolation(
                    Rules.mako_unparseable_expression, expression
                ))
                continue

            context = self._get_context(contexts, expression.start_index)
            self._check_expression_and_filters(mako_template, expression, context, has_page_default, results)

    def _check_javascript_contexts(self, mako_template, contexts, results):
        """
        Lint the JavaScript contexts for JavaScript violations inside a Mako
        template.

        Arguments:
            mako_template: The contents of the Mako template.
            contexts: A list of context dicts with 'type' and 'index'.
            results: A list of results into which violations will be added.

        Side effect:
            Adds JavaScript violations to results.
        """
        javascript_start_index = None
        for context in contexts:
            if context['type'] == 'javascript':
                if javascript_start_index < 0:
                    javascript_start_index = context['index']
            else:
                if javascript_start_index is not None:
                    javascript_end_index = context['index']
                    javascript_code = mako_template[javascript_start_index:javascript_end_index]
                    self._check_javascript_context(javascript_code, javascript_start_index, results)
                    javascript_start_index = None
        if javascript_start_index is not None:
            javascript_code = mako_template[javascript_start_index:]
            self._check_javascript_context(javascript_code, javascript_start_index, results)

    def _check_javascript_context(self, javascript_code, start_offset, results):
        """
        Lint a single JavaScript context for JavaScript violations inside a Mako
        template.

        Arguments:
            javascript_code: The template contents of the JavaScript context.
            start_offset: The offset of the JavaScript context inside the
                original Mako template.
            results: A list of results into which violations will be added.

        Side effect:
            Adds JavaScript violations to results.

        """
        javascript_results = FileResults("")
        self.javascript_linter.check_javascript_file_is_safe(javascript_code, javascript_results)
        self._shift_and_add_violations(javascript_results, start_offset, results)

    def _check_mako_python_blocks(self, mako_template, has_page_default, results):
        """
        Searches for Mako python blocks and checks if they contain
        violations.

        Arguments:
            mako_template: The contents of the Mako template.
            has_page_default: True if the page is marked as default, False
                otherwise.
            results: A list of results into which violations will be added.

        """
        # Finds Python blocks such as <% ... %>, skipping other Mako start tags
        # such as <%def> and <%page>.
        python_block_regex = re.compile(r'<%\s(?P<code>.*?)%>', re.DOTALL)

        for python_block_match in python_block_regex.finditer(mako_template):
            self._check_expression_python(
                python_code=python_block_match.group('code'),
                start_offset=(python_block_match.start() + len('<% ')),
                has_page_default=has_page_default,
                results=results
            )

    def _check_expression_python(self, python_code, start_offset, has_page_default, results):
        """
        Lint the Python inside a single Python expression in a Mako template.

        Arguments:
            python_code: The Python contents of an expression.
            start_offset: The offset of the Python content inside the original
                Mako template.
            has_page_default: True if the page is marked as default, False
                otherwise.
            results: A list of results into which violations will be added.

        Side effect:
            Adds Python violations to results.

        """
        python_results = FileResults("")

        # Dedent expression internals so it is parseable.
        # Note that the final columns reported could be off somewhat.
        adjusted_python_code = textwrap.dedent(python_code)
        first_letter_match = re.search('\w', python_code)
        adjusted_first_letter_match = re.search('\w', adjusted_python_code)
        if first_letter_match is not None and adjusted_first_letter_match is not None:
            start_offset += (first_letter_match.start() - adjusted_first_letter_match.start())
        python_code = adjusted_python_code

        root_node = self.python_linter.parse_python_code(python_code, python_results)
        self.python_linter.check_python_code_is_safe(python_code, root_node, python_results)
        # Check mako expression specific Python rules.
        if root_node is not None:
            visitor = HtmlStringVisitor(python_code, python_results, True)
            visitor.visit(root_node)
            for unsafe_html_string_node in visitor.unsafe_html_string_nodes:
                python_results.violations.append(ExpressionRuleViolation(
                    Rules.python_wrap_html, visitor.node_to_expression(unsafe_html_string_node)
                ))
            if has_page_default:
                for over_escaped_entity_string_node in visitor.over_escaped_entity_string_nodes:
                    python_results.violations.append(ExpressionRuleViolation(
                        Rules.mako_html_entities, visitor.node_to_expression(over_escaped_entity_string_node)
                    ))
        python_results.prepare_results(python_code, line_comment_delim=self.LINE_COMMENT_DELIM)
        self._shift_and_add_violations(python_results, start_offset, results)

    def _shift_and_add_violations(self, other_linter_results, start_offset, results):
        """
        Adds results from a different linter to the Mako results, after shifting
        the offset into the original Mako template.

        Arguments:
            other_linter_results: Results from another linter.
            start_offset: The offset of the linted code, a part of the template,
                inside the original Mako template.
            results: A list of results into which violations will be added.

        Side effect:
            Adds violations to results.

        """
        # translate the violations into the proper location within the original
        # Mako template
        for violation in other_linter_results.violations:
            expression = violation.expression
            expression.start_index += start_offset
            if expression.end_index is not None:
                expression.end_index += start_offset
            results.violations.append(ExpressionRuleViolation(violation.rule, expression))

    def _check_expression_and_filters(self, mako_template, expression, context, has_page_default, results):
        """
        Checks that the filters used in the given Mako expression are valid
        for the given context. Adds violation to results if there is a problem.

        Arguments:
            mako_template: The contents of the Mako template.
            expression: A Mako Expression.
            context: The context of the page in which the expression was found
                (e.g. javascript, html).
            has_page_default: True if the page is marked as default, False
                otherwise.
            results: A list of results into which violations will be added.

        """
        if context == 'unknown':
            results.violations.append(ExpressionRuleViolation(
                Rules.mako_unknown_context, expression
            ))
            return

        # Example: finds "| n, h}" when given "${x | n, h}"
        filters_regex = re.compile(r'\|([.,\w\s]*)\}')
        filters_match = filters_regex.search(expression.expression)

        # Check Python code inside expression.
        if filters_match is None:
            python_code = expression.expression[2:-1]
        else:
            python_code = expression.expression[2:filters_match.start()]
        self._check_expression_python(python_code, expression.start_index + 2, has_page_default, results)

        # Check filters.
        if filters_match is None:
            if context == 'javascript':
                results.violations.append(ExpressionRuleViolation(
                    Rules.mako_invalid_js_filter, expression
                ))
            return
        filters = filters_match.group(1).replace(" ", "").split(",")
        if filters == ['n', 'decode.utf8']:
            # {x | n, decode.utf8} is valid in any context
            pass
        elif context == 'html':
            if filters == ['h']:
                if has_page_default:
                    # suppress this violation if the page default hasn't been set,
                    # otherwise the template might get less safe
                    results.violations.append(ExpressionRuleViolation(
                        Rules.mako_unwanted_html_filter, expression
                    ))
            elif filters == ['n', 'strip_all_tags_but_br']:
                # {x | n,  strip_all_tags_but_br} is valid in html context
                pass
            else:
                results.violations.append(ExpressionRuleViolation(
                    Rules.mako_invalid_html_filter, expression
                ))
        elif context == 'javascript':
            self._check_js_expression_not_with_html(mako_template, expression, results)
            if filters == ['n', 'dump_js_escaped_json']:
                # {x | n, dump_js_escaped_json} is valid
                pass
            elif filters == ['n', 'js_escaped_string']:
                # {x | n, js_escaped_string} is valid, if surrounded by quotes
                self._check_js_string_expression_in_quotes(mako_template, expression, results)
            else:
                results.violations.append(ExpressionRuleViolation(
                    Rules.mako_invalid_js_filter, expression
                ))

    def _check_js_string_expression_in_quotes(self, mako_template, expression, results):
        """
        Checks that a Mako expression using js_escaped_string is surrounded by
        quotes.

        Arguments:
            mako_template: The contents of the Mako template.
            expression: A Mako Expression.
            results: A list of results into which violations will be added.
        """
        parse_string = self._find_string_wrapping_expression(mako_template, expression)
        if parse_string is None:
            results.violations.append(ExpressionRuleViolation(
                Rules.mako_js_missing_quotes, expression
            ))

    def _check_js_expression_not_with_html(self, mako_template, expression, results):
        """
        Checks that a Mako expression in a JavaScript context does not appear in
        a string that also contains HTML.

        Arguments:
            mako_template: The contents of the Mako template.
            expression: A Mako Expression.
            results: A list of results into which violations will be added.
        """
        parse_string = self._find_string_wrapping_expression(mako_template, expression)
        if parse_string is not None and re.search('[<>]', parse_string.string) is not None:
            results.violations.append(ExpressionRuleViolation(
                Rules.mako_js_html_string, expression
            ))

    def _find_string_wrapping_expression(self, mako_template, expression):
        """
        Finds the string wrapping the Mako expression if there is one.

        Arguments:
            mako_template: The contents of the Mako template.
            expression: A Mako Expression.

        Returns:
            ParseString representing a scrubbed version of the wrapped string,
            where the Mako expression was replaced with "${...}", if a wrapped
            string was found.  Otherwise, returns None if none found.
        """
        lines = StringLines(mako_template)
        start_index = lines.index_to_line_start_index(expression.start_index)
        if expression.end_index is not None:
            end_index = lines.index_to_line_end_index(expression.end_index)
        else:
            return None
        # scrub out the actual expression so any code inside the expression
        # doesn't interfere with rules applied to the surrounding code (i.e.
        # checking JavaScript).
        scrubbed_lines = "".join((
            mako_template[start_index:expression.start_index],
            "${...}",
            mako_template[expression.end_index:end_index]
        ))
        adjusted_start_index = expression.start_index - start_index
        start_index = 0
        while True:
            parse_string = ParseString(scrubbed_lines, start_index, len(scrubbed_lines))
            # check for validly parsed string
            if 0 <= parse_string.start_index < parse_string.end_index:
                # check if expression is contained in the given string
                if parse_string.start_index < adjusted_start_index < parse_string.end_index:
                    return parse_string
                else:
                    # move to check next string
                    start_index = parse_string.end_index
            else:
                break
        return None

    def _get_contexts(self, mako_template):
        """
        Returns a data structure that represents the indices at which the
        template changes from HTML context to JavaScript and back.

        Return:
            A list of dicts where each dict contains:
                - index: the index of the context.
                - type: the context type (e.g. 'html' or 'javascript').
        """
        contexts_re = re.compile(
            r"""
                <script.*?> |  # script tag start
                </script> |  # script tag end
                <%static:require_module(_async)?.*?> |  # require js script tag start (optionally the _async version)
                </%static:require_module(_async)?> | # require js script tag end (optionally the _async version)
                <%static:invoke_page_bundle.*?> |  # require js script tag start
                </%static:invoke_page_bundle> |  # require js script tag end
                <%static:webpack.*?> |  # webpack script tag start
                </%static:webpack> | # webpack script tag end
                <%static:studiofrontend.*?> | # studiofrontend script tag start
                </%static:studiofrontend> | # studiofrontend script tag end
                <%block[ ]*name=['"]requirejs['"]\w*> |  # require js tag start
                </%block>  # require js tag end
            """,
            re.VERBOSE | re.IGNORECASE
        )
        media_type_re = re.compile(r"""type=['"].*?['"]""", re.IGNORECASE)

        contexts = [{'index': 0, 'type': 'html'}]
        javascript_types = [
            'text/javascript', 'text/ecmascript', 'application/ecmascript', 'application/javascript',
            'text/x-mathjax-config', 'json/xblock-args', 'application/json',
        ]
        html_types = ['text/template']
        for context in contexts_re.finditer(mako_template):
            match_string = context.group().lower()
            if match_string.startswith("<script"):
                match_type = media_type_re.search(match_string)
                context_type = 'javascript'
                if match_type is not None:
                    # get media type (e.g. get text/javascript from
                    # type="text/javascript")
                    match_type = match_type.group()[6:-1].lower()
                    if match_type in html_types:
                        context_type = 'html'
                    elif match_type not in javascript_types:
                        context_type = 'unknown'
                contexts.append({'index': context.end(), 'type': context_type})
            elif match_string.startswith("</"):
                contexts.append({'index': context.start(), 'type': 'html'})
            else:
                contexts.append({'index': context.end(), 'type': 'javascript'})

        return contexts

    def _get_context(self, contexts, index):
        """
        Gets the context (e.g. javascript, html) of the template at the given
        index.

        Arguments:
            contexts: A list of dicts where each dict contains the 'index' of the context
                and the context 'type' (e.g. 'html' or 'javascript').
            index: The index for which we want the context.

        Returns:
             The context (e.g. javascript or html) for the given index.
        """
        current_context = contexts[0]['type']
        for context in contexts:
            if context['index'] <= index:
                current_context = context['type']
            else:
                break
        return current_context

    def _find_mako_expressions(self, mako_template):
        """
        Finds all the Mako expressions in a Mako template and creates a list
        of dicts for each expression.

        Arguments:
            mako_template: The content of the Mako template.

        Returns:
            A list of Expressions.

        """
        start_delim = '${'
        start_index = 0
        expressions = []

        while True:
            start_index = mako_template.find(start_delim, start_index)
            if start_index < 0:
                break

            # If start of mako expression is commented out, skip it.
            uncommented_start_index = self._uncommented_start_index(mako_template, start_index)
            if uncommented_start_index != start_index:
                start_index = uncommented_start_index
                continue

            result = self._find_closing_char_index(
                start_delim, '{', '}', mako_template, start_index=start_index + len(start_delim)
            )
            if result is None:
                expression = Expression(start_index)
                # for parsing error, restart search right after the start of the
                # current expression
                start_index = start_index + len(start_delim)
            else:
                close_char_index = result['close_char_index']
                expression = mako_template[start_index:close_char_index + 1]
                expression = Expression(
                    start_index,
                    end_index=close_char_index + 1,
                    template=mako_template,
                    start_delim=start_delim,
                    end_delim='}',
                    strings=result['strings'],
                )
                # restart search after the current expression
                start_index = expression.end_index
            expressions.append(expression)
        return expressions


def _process_file(full_path, template_linters, options, summary_results, out):
    """
    For each linter, lints the provided file.  This means finding and printing
    violations.

    Arguments:
        full_path: The full path of the file to lint.
        template_linters: A list of linting objects.
        options: A list of the options.
        summary_results: A SummaryResults with a summary of the violations.
        out: output file

    """
    num_violations = 0
    directory = os.path.dirname(full_path)
    file_name = os.path.basename(full_path)
    for template_linter in template_linters:
        results = template_linter.process_file(directory, file_name)
        results.print_results(options, summary_results, out)


def _process_os_dir(directory, files, template_linters, options, summary_results, out):
    """
    Calls out to lint each file in the passed list of files.

    Arguments:
        directory: Directory being linted.
        files: All files in the directory to be linted.
        template_linters: A list of linting objects.
        options: A list of the options.
        summary_results: A SummaryResults with a summary of the violations.
        out: output file

    """
    for current_file in sorted(files, key=lambda s: s.lower()):
        full_path = os.path.join(directory, current_file)
        _process_file(full_path, template_linters, options, summary_results, out)


def _process_os_dirs(starting_dir, template_linters, options, summary_results, out):
    """
    For each linter, lints all the directories in the starting directory.

    Arguments:
        starting_dir: The initial directory to begin the walk.
        template_linters: A list of linting objects.
        options: A list of the options.
        summary_results: A SummaryResults with a summary of the violations.
        out: output file

    """
    for root, dirs, files in os.walk(starting_dir):
        if is_skip_dir(SKIP_DIRS, root):
            del dirs
            continue
        dirs.sort(key=lambda s: s.lower())
        _process_os_dir(root, files, template_linters, options, summary_results, out)


def _lint(file_or_dir, template_linters, options, summary_results, out):
    """
    For each linter, lints the provided file or directory.

    Arguments:
        file_or_dir: The file or initial directory to lint.
        template_linters: A list of linting objects.
        options: A list of the options.
        summary_results: A SummaryResults with a summary of the violations.
        out: output file

    """

    if file_or_dir is not None and os.path.isfile(file_or_dir):
        _process_file(file_or_dir, template_linters, options, summary_results, out)
    else:
        directory = "."
        if file_or_dir is not None:
            if os.path.exists(file_or_dir):
                directory = file_or_dir
            else:
                raise ValueError("Path [{}] is not a valid file or directory.".format(file_or_dir))
        _process_os_dirs(directory, template_linters, options, summary_results, out)

    summary_results.print_results(options, out)


def main():
    """
    Used to execute the linter. Use --help option for help.

    Prints all violations.
    """
    epilog = "For more help using the xss linter, including details on how to\n"
    epilog += "understand and fix any violations, read the docs here:\n"
    epilog += "\n"
    # pylint: disable=line-too-long
    epilog += "  http://edx.readthedocs.org/projects/edx-developer-guide/en/latest/conventions/preventing_xss.html#xss-linter\n"

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Checks that templates are safe.',
        epilog=epilog,
    )
    parser.add_argument(
        '--list-files', dest='list_files', action='store_true',
        help='Only display the filenames that contain violations.'
    )
    parser.add_argument(
        '--rule-totals', dest='rule_totals', action='store_true',
        help='Display the totals for each rule.'
    )
    parser.add_argument(
        '--verbose', dest='verbose', action='store_true',
        help='Print multiple lines where possible for additional context of violations.'
    )
    parser.add_argument('path', nargs="?", default=None, help='A file to lint or directory to recursively lint.')

    args = parser.parse_args()

    options = {
        'list_files': args.list_files,
        'rule_totals': args.rule_totals,
        'verbose': args.verbose,
    }
    template_linters = [MakoTemplateLinter(), UnderscoreTemplateLinter(), JavaScriptLinter(), PythonLinter()]
    summary_results = SummaryResults()

    _lint(args.path, template_linters, options, summary_results, out=sys.stdout)


if __name__ == "__main__":
    main()
