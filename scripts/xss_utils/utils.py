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
