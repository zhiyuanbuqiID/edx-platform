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

from xss_utils.linters import BaseLinter
from xss_utils.reporting import ExpressionRuleViolation, FileResults, RuleViolation, SummaryResults
from xss_utils.rules import Rules
from xss_utils.utils import Expression, ParseString, StringLines, is_skip_dir, SKIP_DIRS


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


class JavaScriptLinter(BaseLinter):
    """
    The linter for JavaScript and CoffeeScript files.
    """

    LINE_COMMENT_DELIM = "//"

    def __init__(self):
        """
        Init method.
        """
        super(JavaScriptLinter, self).__init__()
        self._skip_javascript_dirs = SKIP_DIRS + ('i18n', 'static/coffee')
        self._skip_coffeescript_dirs = SKIP_DIRS
        self.underscore_linter = UnderscoreTemplateLinter()

    def process_file(self, directory, file_name):
        """
        Process file to determine if it is a JavaScript file and
        if it is safe.

        Arguments:
            directory (string): The directory of the file to be checked
            file_name (string): A filename for a potential JavaScript file

        Returns:
            The file results containing any violations.

        """
        file_full_path = os.path.normpath(directory + '/' + file_name)
        results = FileResults(file_full_path)

        if not results.is_file:
            return results

        if file_name.lower().endswith('.js') and not file_name.lower().endswith('.min.js'):
            skip_dirs = self._skip_javascript_dirs
        elif file_name.lower().endswith('.coffee'):
            skip_dirs = self._skip_coffeescript_dirs
        else:
            return results

        if not self._is_valid_directory(skip_dirs, directory):
            return results

        return self._load_and_check_file_is_safe(file_full_path, self.check_javascript_file_is_safe, results)

    def check_javascript_file_is_safe(self, file_contents, results):
        """
        Checks for violations in a JavaScript file.

        Arguments:
            file_contents: The contents of the JavaScript file.
            results: A file results objects to which violations will be added.

        """
        no_caller_check = None
        no_argument_check = None
        self._check_jquery_function(
            file_contents, "append", Rules.javascript_jquery_append, no_caller_check,
            self._is_jquery_argument_safe, results
        )
        self._check_jquery_function(
            file_contents, "prepend", Rules.javascript_jquery_prepend, no_caller_check,
            self._is_jquery_argument_safe, results
        )
        self._check_jquery_function(
            file_contents, "unwrap|wrap|wrapAll|wrapInner|after|before|replaceAll|replaceWith",
            Rules.javascript_jquery_insertion, no_caller_check, self._is_jquery_argument_safe, results
        )
        self._check_jquery_function(
            file_contents, "appendTo|prependTo|insertAfter|insertBefore",
            Rules.javascript_jquery_insert_into_target, self._is_jquery_insert_caller_safe, no_argument_check, results
        )
        self._check_jquery_function(
            file_contents, "html", Rules.javascript_jquery_html, no_caller_check,
            self._is_jquery_html_argument_safe, results
        )
        self._check_javascript_interpolate(file_contents, results)
        self._check_javascript_escape(file_contents, results)
        self._check_concat_with_html(file_contents, Rules.javascript_concat_html, results)
        self.underscore_linter.check_underscore_file_is_safe(file_contents, results)
        results.prepare_results(file_contents, line_comment_delim=self.LINE_COMMENT_DELIM)

    def _get_expression_for_function(self, file_contents, function_start_match):
        """
        Returns an expression that matches the function call opened with
        function_start_match.

        Arguments:
            file_contents: The contents of the JavaScript file.
            function_start_match: A regex match representing the start of the function
                call (e.g. ".escape(").

        Returns:
            An Expression that best matches the function.

        """
        start_index = function_start_match.start()
        inner_start_index = function_start_match.end()
        result = self._find_closing_char_index(
            None, "(", ")", file_contents, start_index=inner_start_index
        )
        if result is not None:
            end_index = result['close_char_index'] + 1
            expression = Expression(
                start_index, end_index, template=file_contents, start_delim=function_start_match.group(), end_delim=")"
            )
        else:
            expression = Expression(start_index)
        return expression

    def _check_javascript_interpolate(self, file_contents, results):
        """
        Checks that interpolate() calls are safe.

        Only use of StringUtils.interpolate() or HtmlUtils.interpolateText()
        are safe.

        Arguments:
            file_contents: The contents of the JavaScript file.
            results: A file results objects to which violations will be added.

        """
        # Ignores calls starting with "StringUtils.", because those are safe
        regex = re.compile(r"(?<!StringUtils).interpolate\(")
        for function_match in regex.finditer(file_contents):
            expression = self._get_expression_for_function(file_contents, function_match)
            results.violations.append(ExpressionRuleViolation(Rules.javascript_interpolate, expression))

    def _check_javascript_escape(self, file_contents, results):
        """
        Checks that only necessary escape() are used.

        Allows for _.escape(), although this shouldn't be the recommendation.

        Arguments:
            file_contents: The contents of the JavaScript file.
            results: A file results objects to which violations will be added.

        """
        # Ignores calls starting with "_.", because those are safe
        regex = regex = re.compile(r"(?<!_).escape\(")
        for function_match in regex.finditer(file_contents):
            expression = self._get_expression_for_function(file_contents, function_match)
            results.violations.append(ExpressionRuleViolation(Rules.javascript_escape, expression))

    def _check_jquery_function(self, file_contents, function_names, rule, is_caller_safe, is_argument_safe, results):
        """
        Checks that the JQuery function_names (e.g. append(), prepend()) calls
        are safe.

        Arguments:
            file_contents: The contents of the JavaScript file.
            function_names: A pipe delimited list of names of the functions
                (e.g. "wrap|after|before").
            rule: The name of the rule to use for validation errors (e.g.
                Rules.javascript_jquery_append).
            is_caller_safe: A function to test if caller of the JQuery function
                is safe.
            is_argument_safe: A function to test if the argument passed to the
                JQuery function is safe.
            results: A file results objects to which violations will be added.

        """
        # Ignores calls starting with "HtmlUtils.", because those are safe
        regex = re.compile(r"(?<!HtmlUtils).(?:{})\(".format(function_names))
        for function_match in regex.finditer(file_contents):
            is_violation = True
            expression = self._get_expression_for_function(file_contents, function_match)
            if expression.end_index is not None:
                start_index = expression.start_index
                inner_start_index = function_match.end()
                close_paren_index = expression.end_index - 1
                function_argument = file_contents[inner_start_index:close_paren_index].strip()
                if is_argument_safe is not None and is_caller_safe is None:
                    is_violation = is_argument_safe(function_argument) is False
                elif is_caller_safe is not None and is_argument_safe is None:
                    line_start_index = StringLines(file_contents).index_to_line_start_index(start_index)
                    caller_line_start = file_contents[line_start_index:start_index]
                    is_violation = is_caller_safe(caller_line_start) is False
                else:
                    raise ValueError("Must supply either is_argument_safe, or is_caller_safe, but not both.")
            if is_violation:
                results.violations.append(ExpressionRuleViolation(rule, expression))

    def _is_jquery_argument_safe_html_utils_call(self, argument):
        """
        Checks that the argument sent to a jQuery DOM insertion function is a
        safe call to HtmlUtils.

        A safe argument is of the form:
        - HtmlUtils.xxx(anything).toString()
        - edx.HtmlUtils.xxx(anything).toString()

        Arguments:
            argument: The argument sent to the jQuery function (e.g.
            append(argument)).

        Returns:
            True if the argument is safe, and False otherwise.

        """
        # match on HtmlUtils.xxx().toString() or edx.HtmlUtils
        match = re.search(r"(?:edx\.)?HtmlUtils\.[a-zA-Z0-9]+\(.*\)\.toString\(\)", argument)
        return match is not None and match.group() == argument

    def _is_jquery_argument_safe(self, argument):
        """
        Check the argument sent to a jQuery DOM insertion function (e.g.
        append()) to check if it is safe.

        Safe arguments include:
        - the argument can end with ".el", ".$el" (with no concatenation)
        - the argument can be a single variable ending in "El" or starting with
            "$". For example, "testEl" or "$test".
        - the argument can be a single string literal with no HTML tags
        - the argument can be a call to $() with the first argument a string
            literal with a single HTML tag.  For example, ".append($('<br/>'))"
            or ".append($('<br/>'))".
        - the argument can be a call to HtmlUtils.xxx(html).toString()

        Arguments:
            argument: The argument sent to the jQuery function (e.g.
            append(argument)).

        Returns:
            True if the argument is safe, and False otherwise.

        """
        match_variable_name = re.search("[_$a-zA-Z]+[_$a-zA-Z0-9]*", argument)
        if match_variable_name is not None and match_variable_name.group() == argument:
            if argument.endswith('El') or argument.startswith('$'):
                return True
        elif argument.startswith('"') or argument.startswith("'"):
            # a single literal string with no HTML is ok
            # 1. it gets rid of false negatives for non-jquery calls (e.g. graph.append("g"))
            # 2. JQuery will treat this as a plain text string and will escape any & if needed.
            string = ParseString(argument, 0, len(argument))
            if string.string == argument and "<" not in argument:
                return True
        elif argument.startswith('$('):
            # match on JQuery calls with single string and single HTML tag
            # Examples:
            #    $("<span>")
            #    $("<div/>")
            #    $("<div/>", {...})
            match = re.search(r"""\$\(\s*['"]<[a-zA-Z0-9]+\s*[/]?>['"]\s*[,)]""", argument)
            if match is not None:
                return True
        elif self._is_jquery_argument_safe_html_utils_call(argument):
            return True
        # check rules that shouldn't use concatenation
        elif "+" not in argument:
            if argument.endswith('.el') or argument.endswith('.$el'):
                return True
        return False

    def _is_jquery_html_argument_safe(self, argument):
        """
        Check the argument sent to the jQuery html() function to check if it is
        safe.

        Safe arguments to html():
        - no argument (i.e. getter rather than setter)
        - empty string is safe
        - the argument can be a call to HtmlUtils.xxx(html).toString()

        Arguments:
            argument: The argument sent to html() in code (i.e. html(argument)).

        Returns:
            True if the argument is safe, and False otherwise.

        """
        if argument == "" or argument == "''" or argument == '""':
            return True
        elif self._is_jquery_argument_safe_html_utils_call(argument):
            return True
        return False

    def _is_jquery_insert_caller_safe(self, caller_line_start):
        """
        Check that the caller of a jQuery DOM insertion function that takes a
        target is safe (e.g. thisEl.appendTo(target)).

        If original line was::

            draggableObj.iconEl.appendTo(draggableObj.containerEl);

        Parameter caller_line_start would be:

            draggableObj.iconEl

        Safe callers include:
        - the caller can be ".el", ".$el"
        - the caller can be a single variable ending in "El" or starting with
            "$". For example, "testEl" or "$test".

        Arguments:
            caller_line_start: The line leading up to the jQuery function call.

        Returns:
            True if the caller is safe, and False otherwise.

        """
        # matches end of line for caller, which can't itself be a function
        caller_match = re.search(r"(?:\s*|[.])([_$a-zA-Z]+[_$a-zA-Z0-9])*$", caller_line_start)
        if caller_match is None:
            return False
        caller = caller_match.group(1)
        if caller is None:
            return False
        elif caller.endswith('El') or caller.startswith('$'):
            return True
        elif caller == 'el' or caller == 'parentNode':
            return True
        return False

    def _check_concat_with_html(self, file_contents, rule, results):
        """
        Checks that strings with HTML are not concatenated

        Arguments:
            file_contents: The contents of the JavaScript file.
            rule: The rule that was violated if this fails.
            results: A file results objects to which violations will be added.

        """
        lines = StringLines(file_contents)
        last_expression = None
        # Match quoted strings that starts with '<' or ends with '>'.
        regex_string_with_html = r"""
            {quote}                             # Opening quote.
                (
                   \s*<                         # Starts with '<' (ignoring spaces)
                   ([^{quote}]|[\\]{quote})*    # followed by anything but a closing quote.
                |                               # Or,
                   ([^{quote}]|[\\]{quote})*    # Anything but a closing quote
                   >\s*                         # ending with '>' (ignoring spaces)
                )
            {quote}                             # Closing quote.
        """
        # Match single or double quote.
        regex_string_with_html = "({}|{})".format(
            regex_string_with_html.format(quote="'"),
            regex_string_with_html.format(quote='"'),
        )
        # Match quoted HTML strings next to a '+'.
        regex_concat_with_html = re.compile(
            r"(\+\s*{string_with_html}|{string_with_html}\s*\+)".format(
                string_with_html=regex_string_with_html,
            ),
            re.VERBOSE
        )
        for match in regex_concat_with_html.finditer(file_contents):
            found_new_violation = False
            if last_expression is not None:
                last_line = lines.index_to_line_number(last_expression.start_index)
                # check if violation should be expanded to more of the same line
                if last_line == lines.index_to_line_number(match.start()):
                    last_expression = Expression(
                        last_expression.start_index, match.end(), template=file_contents
                    )
                else:
                    results.violations.append(ExpressionRuleViolation(
                        rule, last_expression
                    ))
                    found_new_violation = True
            else:
                found_new_violation = True
            if found_new_violation:
                last_expression = Expression(
                    match.start(), match.end(), template=file_contents
                )

        # add final expression
        if last_expression is not None:
            results.violations.append(ExpressionRuleViolation(
                rule, last_expression
            ))


class BaseVisitor(ast.NodeVisitor):
    """
    Base class for AST NodeVisitor used for Python xss linting.

    Important: This base visitor skips all __repr__ function definitions.
    """
    def __init__(self, file_contents, results):
        """
        Init method.

        Arguments:
            file_contents: The contents of the Python file.
            results: A file results objects to which violations will be added.

        """
        super(BaseVisitor, self).__init__()
        self.file_contents = file_contents
        self.lines = StringLines(self.file_contents)
        self.results = results

    def node_to_expression(self, node):
        """
        Takes a node and translates it to an expression to be used with
        violations.

        Arguments:
            node: An AST node.

        """
        line_start_index = self.lines.line_number_to_start_index(node.lineno)
        start_index = line_start_index + node.col_offset
        if isinstance(node, ast.Str):
            # Triple quotes give col_offset of -1 on the last line of the string.
            if node.col_offset == -1:
                triple_quote_regex = re.compile("""['"]{3}""")
                end_triple_quote_match = triple_quote_regex.search(self.file_contents, line_start_index)
                open_quote_index = self.file_contents.rfind(end_triple_quote_match.group(), 0, end_triple_quote_match.start())
                if open_quote_index > 0:
                    start_index = open_quote_index
                else:
                    # If we can't find a starting quote, let's assume that what
                    # we considered the end quote is really the start quote.
                    start_index = end_triple_quote_match.start()
            string = ParseString(self.file_contents, start_index, len(self.file_contents))
            return Expression(string.start_index, string.end_index)
        else:
            return Expression(start_index)

    def visit_FunctionDef(self, node):
        """
        Skips processing of __repr__ functions, since these sometimes use '<'
        for non-HTML purposes.

        Arguments:
            node: An AST node.
        """
        if node.name != '__repr__':
            self.generic_visit(node)


class HtmlStringVisitor(BaseVisitor):
    """
    Checks for strings that contain HTML. Assumes any string with < or > is
    considered potential HTML.

    To be used only with strings in context of format or concat.

    """
    def __init__(self, file_contents, results, skip_wrapped_html=False):
        """
        Init function.

        Arguments:
            file_contents: The contents of the Python file.
            results: A file results objects to which violations will be added.
            skip_wrapped_html: True if visitor should skip strings wrapped with
                HTML() or Text(), and False otherwise.
        """
        super(HtmlStringVisitor, self).__init__(file_contents, results)
        self.skip_wrapped_html = skip_wrapped_html
        self.unsafe_html_string_nodes = []
        self.over_escaped_entity_string_nodes = []
        self.has_text_or_html_call = False

    def visit_Str(self, node):
        """
        When strings are visited, checks if it contains HTML.

        Arguments:
            node: An AST node.
        """
        # Skips '<' (and '>') in regex named groups. For example, "(?P<group>)".
        if re.search('[(][?]P<', node.s) is None and re.search('<', node.s) is not None:
            self.unsafe_html_string_nodes.append(node)
        if re.search(r"&[#]?[a-zA-Z0-9]+;", node.s):
            self.over_escaped_entity_string_nodes.append(node)

    def visit_Call(self, node):
        """
        Skips processing of string contained inside HTML() and Text() calls when
        skip_wrapped_html is True.

        Arguments:
            node: An AST node.

        """
        is_html_or_text_call = isinstance(node.func, ast.Name) and node.func.id in ['HTML', 'Text']
        if self.skip_wrapped_html and is_html_or_text_call:
            self.has_text_or_html_call = True
        else:
            self.generic_visit(node)


class ContainsFormatVisitor(BaseVisitor):
    """
    Checks if there are any nested format() calls.

    This visitor is meant to be called on HTML() and Text() ast.Call nodes to
    search for any illegal nested format() calls.

    """
    def __init__(self, file_contents, results):
        """
        Init function.

        Arguments:
            file_contents: The contents of the Python file.
            results: A file results objects to which violations will be added.

        """
        super(ContainsFormatVisitor, self).__init__(file_contents, results)
        self.contains_format_call = False

    def visit_Attribute(self, node):
        """
        Simple check for format calls (attribute).

        Arguments:
            node: An AST node.

        """
        # Attribute(expr value, identifier attr, expr_context ctx)
        if node.attr == 'format':
            self.contains_format_call = True
        else:
            self.generic_visit(node)


class FormatInterpolateVisitor(BaseVisitor):
    """
    Checks if format() interpolates any HTML() or Text() calls. In other words,
    are Text() or HTML() calls nested inside the call to format().

    This visitor is meant to be called on a format() attribute node.

    """
    def __init__(self, file_contents, results):
        """
        Init function.

        Arguments:
            file_contents: The contents of the Python file.
            results: A file results objects to which violations will be added.

        """
        super(FormatInterpolateVisitor, self).__init__(file_contents, results)
        self.interpolates_text_or_html = False
        self.format_caller_node = None

    def visit_Call(self, node):
        """
        Checks all calls. Remembers the caller of the initial format() call, or
        in other words, the left-hand side of the call. Also tracks if HTML()
        or Text() calls were seen.

        Arguments:
            node: The AST root node.

        """
        if isinstance(node.func, ast.Attribute) and node.func.attr is 'format':
            if self.format_caller_node is None:
                # Store the caller, or left-hand-side node of the initial
                # format() call.
                self.format_caller_node = node.func.value
        elif isinstance(node.func, ast.Name) and node.func.id in ['HTML', 'Text']:
            # found Text() or HTML() call in arguments passed to format()
            self.interpolates_text_or_html = True
        self.generic_visit(node)

    def generic_visit(self, node):
        """
        Determines whether or not to continue to visit nodes according to the
        following rules:
        - Once a Text() or HTML() call has been found, stop visiting more nodes.
        - Skip the caller of the outer-most format() call, or in other words,
        the left-hand side of the call.

        Arguments:
            node: The AST root node.

        """
        if self.interpolates_text_or_html is False:
            if self.format_caller_node is not node:
                super(FormatInterpolateVisitor, self).generic_visit(node)


class OuterFormatVisitor(BaseVisitor):
    """
    Only visits outer most Python format() calls. These checks are not repeated
    for any nested format() calls.

    This visitor is meant to be used once from the root.

    """
    def visit_Call(self, node):
        """
        Checks that format() calls which contain HTML() or Text() use HTML() or
        Text() as the caller. In other words, Text() or HTML() must be used
        before format() for any arguments to format() that contain HTML() or
        Text().

        Arguments:
             node: An AST node.
        """
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'format':
            visitor = HtmlStringVisitor(self.file_contents, self.results, True)
            visitor.visit(node)
            for unsafe_html_string_node in visitor.unsafe_html_string_nodes:
                self.results.violations.append(ExpressionRuleViolation(
                    Rules.python_wrap_html, self.node_to_expression(unsafe_html_string_node)
                ))
            # Do not continue processing child nodes of this format() node.
        else:
            self.generic_visit(node)


class AllNodeVisitor(BaseVisitor):
    """
    Visits all nodes and does not interfere with calls to generic_visit(). This
    is used in conjunction with other visitors to check for a variety of
    violations.

    This visitor is meant to be used once from the root.

    """

    def visit_Attribute(self, node):
        """
        Checks for uses of deprecated `display_name_with_default_escaped`.

        Arguments:
             node: An AST node.
        """
        if node.attr == 'display_name_with_default_escaped':
            self.results.violations.append(ExpressionRuleViolation(
                Rules.python_deprecated_display_name, self.node_to_expression(node)
            ))
        self.generic_visit(node)

    def visit_Call(self, node):
        """
        Checks for a variety of violations:
        - Checks that format() calls with nested HTML() or Text() calls use
        HTML() or Text() on the left-hand side.
        - For each HTML() and Text() call, calls into separate visitor to check
        for inner format() calls.

        Arguments:
             node: An AST node.

        """
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'format':
            visitor = FormatInterpolateVisitor(self.file_contents, self.results)
            visitor.visit(node)
            if visitor.interpolates_text_or_html:
                format_caller = node.func.value
                is_caller_html_or_text = isinstance(format_caller, ast.Call) and \
                    isinstance(format_caller.func, ast.Name) and \
                    format_caller.func.id in ['Text', 'HTML']
                # If format call has nested Text() or HTML(), then the caller,
                # or left-hand-side of the format() call, must be a call to
                # Text() or HTML().
                if is_caller_html_or_text is False:
                    self.results.violations.append(ExpressionRuleViolation(
                        Rules.python_requires_html_or_text, self.node_to_expression(node.func)
                    ))
        elif isinstance(node.func, ast.Name) and node.func.id in ['HTML', 'Text']:
            visitor = ContainsFormatVisitor(self.file_contents, self.results)
            visitor.visit(node)
            if visitor.contains_format_call:
                self.results.violations.append(ExpressionRuleViolation(
                    Rules.python_close_before_format, self.node_to_expression(node.func)
                ))

        self.generic_visit(node)

    def visit_BinOp(self, node):
        """
        Checks for concat using '+' and interpolation using '%' with strings
        containing HTML.

        """
        rule = None
        if isinstance(node.op, ast.Mod):
            rule = Rules.python_interpolate_html
        elif isinstance(node.op, ast.Add):
            rule = Rules.python_concat_html
        if rule is not None:
            visitor = HtmlStringVisitor(self.file_contents, self.results)
            visitor.visit(node.left)
            has_illegal_html_string = len(visitor.unsafe_html_string_nodes) > 0
            # Create new visitor to clear state.
            visitor = HtmlStringVisitor(self.file_contents, self.results)
            visitor.visit(node.right)
            has_illegal_html_string = has_illegal_html_string or len(visitor.unsafe_html_string_nodes) > 0
            if has_illegal_html_string:
                self.results.violations.append(ExpressionRuleViolation(
                    rule, self.node_to_expression(node)
                ))
        self.generic_visit(node)


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
