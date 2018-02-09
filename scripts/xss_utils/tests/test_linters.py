# -*- coding: utf-8 -*-
"""
Tests for linters.py
"""
from __future__ import print_function

import textwrap
from unittest import TestCase

from ddt import data, ddt

from scripts.xss_utils.reporting import FileResults
from scripts.xss_utils.linters import UnderscoreTemplateLinter
from scripts.xss_utils.rules import Rules


class TestLinter(TestCase):
    """
    Test Linter base class
    """
    def _validate_data_rules(self, data, results):
        """
        Validates that the appropriate rule violations were triggered.

        Arguments:
            data: A dict containing the 'rule' (or rules) to be tests.
            results: The results, containing violations to be validated.

        """
        rules = []
        if isinstance(data['rule'], list):
            rules = data['rule']
        elif data['rule'] is not None:
            rules.append(data['rule'])
        results.violations.sort(key=lambda violation: violation.sort_key())

        # Print violations if the lengths are different.
        if len(results.violations) != len(rules):
            for violation in results.violations:
                print("Found violation: {}".format(violation.rule))

        self.assertEqual(len(results.violations), len(rules))
        for violation, rule in zip(results.violations, rules):
            self.assertEqual(violation.rule, rule)


@ddt
class TestUnderscoreTemplateLinter(TestLinter):
    """
    Test UnderscoreTemplateLinter
    """

    def test_check_underscore_file_is_safe(self):
        """
        Test check_underscore_file_is_safe with safe template
        """
        linter = UnderscoreTemplateLinter()
        results = FileResults('')

        template = textwrap.dedent("""
            <%- gettext('Single Line') %>

            <%-
                gettext('Multiple Lines')
            %>
        """)

        linter.check_underscore_file_is_safe(template, results)

        self.assertEqual(len(results.violations), 0)

    def test_check_underscore_file_is_not_safe(self):
        """
        Test check_underscore_file_is_safe with unsafe template
        """
        linter = UnderscoreTemplateLinter()
        results = FileResults('')

        template = textwrap.dedent("""
            <%= gettext('Single Line') %>

            <%=
                gettext('Multiple Lines')
            %>
        """)

        linter.check_underscore_file_is_safe(template, results)

        self.assertEqual(len(results.violations), 2)
        self.assertEqual(results.violations[0].rule, Rules.underscore_not_escaped)
        self.assertEqual(results.violations[1].rule, Rules.underscore_not_escaped)

    @data(
        {
            'template':
                '<% // xss-lint:   disable=underscore-not-escaped   %>\n'
                '<%= message %>',
            'is_disabled': [True],
        },
        {
            'template':
                '<% // xss-lint: disable=another-rule,underscore-not-escaped %>\n'
                '<%= message %>',
            'is_disabled': [True],
        },
        {
            'template':
                '<% // xss-lint: disable=another-rule %>\n'
                '<%= message %>',
            'is_disabled': [False],
        },
        {
            'template':
                '<% // xss-lint: disable=underscore-not-escaped %>\n'
                '<%= message %>\n'
                '<%= message %>',
            'is_disabled': [True, False],
        },
        {
            'template':
                '// This test does not use proper Underscore.js Template syntax\n'
                '// But, it is just testing that a maximum of 5 non-whitespace\n'
                '// are used to designate start of line for disabling the next line.\n'
                ' 1 2 3 4 5 xss-lint: disable=underscore-not-escaped %>\n'
                '<%= message %>\n'
                ' 1 2 3 4 5 6 xss-lint: disable=underscore-not-escaped %>\n'
                '<%= message %>',
            'is_disabled': [True, False],
        },
        {
            'template':
                '<%= message %><% // xss-lint: disable=underscore-not-escaped %>\n'
                '<%= message %>',
            'is_disabled': [True, False],
        },
        {
            'template':
                '<%= message %>\n'
                '<% // xss-lint: disable=underscore-not-escaped %>',
            'is_disabled': [False],
        },
    )
    def test_check_underscore_file_disable_rule(self, data):
        """
        Test check_underscore_file_is_safe with various disabled pragmas
        """
        linter = UnderscoreTemplateLinter()
        results = FileResults('')

        linter.check_underscore_file_is_safe(data['template'], results)

        violation_count = len(data['is_disabled'])
        self.assertEqual(len(results.violations), violation_count)
        for index in range(0, violation_count - 1):
            self.assertEqual(results.violations[index].is_disabled, data['is_disabled'][index])

    def test_check_underscore_file_disables_one_violation(self):
        """
        Test check_underscore_file_is_safe with disabled before a line only
        disables for the violation following
        """
        linter = UnderscoreTemplateLinter()
        results = FileResults('')

        template = textwrap.dedent("""
            <% // xss-lint: disable=underscore-not-escaped %>
            <%= message %>
            <%= message %>
        """)

        linter.check_underscore_file_is_safe(template, results)

        self.assertEqual(len(results.violations), 2)
        self.assertEqual(results.violations[0].is_disabled, True)
        self.assertEqual(results.violations[1].is_disabled, False)

    @data(
        {'template': '<%= HtmlUtils.ensureHtml(message) %>'},
        {'template': '<%= _.escape(message) %>'},
    )
    def test_check_underscore_no_escape_allowed(self, data):
        """
        Test check_underscore_file_is_safe with expressions that are allowed
        without escaping because the internal calls properly escape.
        """
        linter = UnderscoreTemplateLinter()
        results = FileResults('')

        linter.check_underscore_file_is_safe(data['template'], results)

        self.assertEqual(len(results.violations), 0)
