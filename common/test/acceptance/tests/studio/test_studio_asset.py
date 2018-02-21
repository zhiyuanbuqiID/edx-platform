"""
Acceptance tests for Studio related to the asset index page.
"""

from common.test.acceptance.fixtures.base import StudioApiLoginError
from common.test.acceptance.fixtures.config import ConfigModelFixture
from common.test.acceptance.pages.studio.asset_index import AssetIndexPage, AssetIndexPageStudioFrontend
from common.test.acceptance.tests.helpers import skip_if_browser
from common.test.acceptance.tests.studio.base_studio_test import StudioCourseTest


class AssetIndexTest(StudioCourseTest):

    """
    Tests for the Asset index page.
    """
    def setUp(self, is_staff=False):
        super(AssetIndexTest, self).setUp()
        self.asset_page = AssetIndexPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

    def populate_course_fixture(self, course_fixture):
        """
        Populate the children of the test course fixture.
        """
        self.course_fixture.add_asset(['image.jpg', 'textbook.pdf'])

    @skip_if_browser('chrome')  # TODO Need to fix test_page_existance for this for chrome browser
    def test_type_filter_exists(self):
        """
        Make sure type filter is on the page.
        """
        self.asset_page.visit()
        assert self.asset_page.type_filter_on_page() is True

    @skip_if_browser('chrome')  # TODO Need to fix test_page_existance for this for chrome browser
    def test_filter_results(self):
        """
        Make sure type filter actually filters the results.
        """
        self.asset_page.visit()
        all_results = len(self.asset_page.return_results_set())
        if self.asset_page.select_type_filter(1):
            filtered_results = len(self.asset_page.return_results_set())
            assert self.asset_page.type_filter_header_label_visible()
            assert all_results > filtered_results
        else:
            msg = "Could not open select Type filter"
            raise StudioApiLoginError(msg)

class AssetIndexTestStudioFrontend(StudioCourseTest):

    """
    Tests for the Asset index page.
    """
    def setUp(self, is_staff=False):
        super(AssetIndexTestStudioFrontend, self).setUp()
        self.asset_page = AssetIndexPageStudioFrontend(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

    def populate_course_fixture(self, course_fixture):
        """
        Populate the children of the test course fixture.
        """
        ConfigModelFixture('/config/assets', {'enabled_for_all_courses': True, 'enabled': True}, 'cms').install()
        self.course_fixture.add_asset(['image.jpg', 'textbook.pdf'])

    def test_type_filter_exists(self):
        """
        Make sure type filter is on the page.
        """
        self.asset_page.visit()
        assert self.asset_page.filter_element_on_page() is True

    # def test_correct_filters_exist(self):
    #     """
    #     Make sure type filter is on the page.
    #     """
    #     self.asset_page.visit()
    #     assert self.asset_page.correct_filters__in_filter_element() is True
    #
    # def test_correct_filters_exist(self):
    #     """
    #     Make sure type filter is on the page.
    #     """
    #     self.asset_page.visit()
    #     assert self.asset_page.correct_filters__in_filter_element() is True

    def test_clicking_filter_with_results(self):
        """
        Make sure clicking a type filter that has results performs the filtering
        correctly.
        """
        self.asset_page.visit()
        all_results = len(self.asset_page.return_results_set())
        # select Images
        if self.asset_page.select_type_filter(3):
            filtered_results = len(self.asset_page.return_results_set())
            assert all_results > filtered_results
        else:
            msg = "Could not select filter"
            raise StudioApiL

    def test_clicking_filter_without_results(self):
        """
        Make sure clicking a type filter that has no results performs the filtering
        correctly, updates the page view to display the no_results view, hides the pagination
        element, and hides the table.
        """
        self.asset_page.visit()
        all_results = len(self.asset_page.return_results_set())
        # select Audio
        if self.asset_page.select_type_filter(0):
            filtered_results = len(self.asset_page.return_results_set())
            # assert self.asset_page.type_filter_header_label_visible()
            assert all_results > filtered_results
            assert filtered_results == 0
            assert not self.asset_page.sortable_element_on_page()
            assert not self.asset_page.table_element_on_page()
            # TODO check for h3, h4, clear filter button
            # import pudb; pudb.set_trace()
        else:
            msg = "Could not select filter"
            raise StudioApiL


    # def test_clicking_filter_without_results(self):


    def test_upload_element_exists(self):
        """
        Make sure upload dropzone is on the page.
        """
        self.asset_page.visit()
        assert self.asset_page.is_upload_element_on_page() is True

    def test_sortable_table_element_exists(self):
        """
        Make sure sortable table headings are on the page.
        """
        self.asset_page.visit()
        assert self.asset_page.sortable_element_on_page() is True

    def test_status_element_exists(self):
        """
        Make sure status alert is on the page but not visible.
        """
        self.asset_page.visit()
        assert self.asset_page.status_alert_element_on_page() is True

    def test_pagination_element_exists(self):
        """
        Make sure pagination element is on the page.
        """
        self.asset_page.visit()
        assert self.asset_page.pagination_element_on_page() is True

    def test_lock(self):
        """
        Make sure clicking the lock button toggles correctly.
        """
        self.asset_page.visit()
        # Verify that a file can be locked
        self.asset_page.set_asset_lock()
        # Get the list of locked assets, there should be one
        locked_assets = self.asset_page.asset_lock_buttons(locked_only=True)
        self.assertEqual(len(locked_assets), 1)

        # Confirm that there are 2 assets, with the first
        # locked and the second unlocked.
        all_assets = self.asset_page.asset_lock_buttons(locked_only=False)
        self.assertEqual(len(all_assets), 2)
        self.assertTrue('fa-lock' in all_assets[0].get_attribute('class'))
        self.assertTrue('fa-unlock' in all_assets[1].get_attribute('class'))

    def test_delete_and_upload(self):
        """
        Upload specific files to page.
        Start by deleting all files, to ensure starting on a blank slate.
        """
        self.asset_page.visit()
        self.asset_page.delete_all_assets()
        file_names = [u'file-0.png', u'file-13.pdf', u'file-26.js', u'file-39.txt']
        # Upload the files
        self.asset_page.upload_new_file(file_names)
        # Assert that the files have been uploaded.
        all_assets = self.asset_page.asset_files_count
        self.assertEqual(all_assets, 4)
        self.assertEqual(file_names[::-1], self.asset_page.asset_files_names)
