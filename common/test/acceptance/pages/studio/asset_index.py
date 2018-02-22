"""
The Files and Uploads page for a course in Studio
"""

import os
from path import Path
import urllib

from bok_choy.javascript import wait_for_js
from bok_choy.promise import EmptyPromise
from opaque_keys.edx.locator import CourseLocator

from common.test.acceptance.pages.common.utils import click_css, sync_on_notification
from common.test.acceptance.pages.studio import BASE_URL
from common.test.acceptance.pages.studio.course_page import CoursePage


class AssetIndexPage(CoursePage):

    """
    The Files and Uploads page for a course in Studio
    """

    url_path = "assets"
    type_filter_element = '#js-asset-type-col'

    @property
    def url(self):
        """
        Construct a URL to the page within the course.
        """
        # TODO - is there a better way to make this agnostic to the underlying default module store?
        default_store = os.environ.get('DEFAULT_STORE', 'draft')
        course_key = CourseLocator(
            self.course_info['course_org'],
            self.course_info['course_num'],
            self.course_info['course_run'],
            deprecated=(default_store == 'draft')
        )
        url = "/".join([BASE_URL, self.url_path, urllib.quote_plus(unicode(course_key))])
        return url if url[-1] is '/' else url + '/'

    @wait_for_js
    def is_browser_on_page(self):
        return all([
            self.q(css='body.view-uploads').present,
            self.q(css='.page-header').present,
            not self.q(css='div.ui-loading').visible,
        ])

    @wait_for_js
    def type_filter_on_page(self):
        """
        Checks that type filter is in table header.
        """
        return self.q(css=self.type_filter_element).present

    @wait_for_js
    def type_filter_header_label_visible(self):
        """
        Checks type filter label is added and visible in the pagination header.
        """
        return self.q(css='span.filter-column').visible

    @wait_for_js
    def click_type_filter(self):
        """
        Clicks type filter menu.
        """
        self.q(css=".filterable-column .nav-item").click()

    @wait_for_js
    def select_type_filter(self, filter_number):
        """
        Selects Type filter from dropdown which filters the results.
        Returns False if no filter.
        """
        self.wait_for_ajax()
        if self.q(css=".filterable-column .nav-item").is_present():
            if not self.q(css=self.type_filter_element + " .wrapper-nav-sub").visible:
                self.q(css=".filterable-column > .nav-item").first.click()
            self.wait_for_element_visibility(
                self.type_filter_element + " .wrapper-nav-sub", "Type Filter promise satisfied.")
            self.q(css=self.type_filter_element + " .column-filter-link").nth(filter_number).click()
            self.wait_for_ajax()
            return True
        return False

    def return_results_set(self):
        """
        Returns the asset set from the page
        """
        return self.q(css="#asset-table-body tr").results

class AssetIndexPageStudioFrontend(CoursePage):

    """
    The Files and Uploads page for a course in Studio
    """

    pagination_page_element = ".pagination li"
    pagination_disabled_element = ".pagination .disabled .page-link"
    table_sort_buttons = 'th.sortable button.btn-header'
    type_filter_element = ".filter-set .form-group"
    url_path = "assets"


    @property
    def url(self):
        """
        Construct a URL to the page within the course.
        """
        # TODO - is there a better way to make this agnostic to the underlying default module store?
        default_store = os.environ.get('DEFAULT_STORE', 'draft')
        course_key = CourseLocator(
            self.course_info['course_org'],
            self.course_info['course_num'],
            self.course_info['course_run'],
            deprecated=(default_store == 'draft')
        )
        url = "/".join([BASE_URL, self.url_path, urllib.quote_plus(unicode(course_key))])
        return url if url[-1] is '/' else url + '/'

    @property
    def asset_files_names(self):
        """
        Get the names of uploaded files.
        Returns:
            list: Uploaded files.
        """
        return self.q(css='span[data-identifier="asset-file-name"]').text

    @property
    def asset_files_count(self):
        """
        Returns the count of files on the current page.
        """
        return len(self.q(css='span[data-identifier="asset-file-name"]').execute())

    @property
    def asset_delete_buttons(self):
        """Return a list of WebElements for deleting the assets"""
        css = 'button[data-identifier="asset-delete-button"]'
        return self.q(css=css).execute()

    def asset_lock_buttons(self, locked_only=True):
        """
        Return a list of WebElements of the lock buttons for assets
        or an empty list if there are none.
        """
        if locked_only:
            css = 'button[data-identifier="asset-lock-button"].fa-lock'
        else:
            css = 'button[data-identifier="asset-lock-button"]'
        return self.q(css=css).execute()

    @wait_for_js
    def is_browser_on_page(self):
        return all([
            self.q(css='body.view-uploads').present,
            self.q(css='.page-header').present,
            self.q(css='#root').present,
            not self.q(css='div.ui-loading').visible,
        ])

    @wait_for_js
    def is_sfe_container_on_page(self):
        """
        Checks that the studio-frontend container has been loaded.
        """
        return self.q(css='.SFE__container').present

    @wait_for_js
    def is_upload_element_on_page(self):
        """
        Checks that the dropzone area is on the page.
        """
        return self.q(css='.drop-zone').present

    # @wait_for_js
    # def get_filter_element_on_page(self):
    #     return self.q(css='.filter-set .form-group').execute()

    #
    # Should we add an id value to the div surrounding the assets filters?
    # self.q(css='div[@role = group]').present
    #
    @wait_for_js
    def is_filter_element_on_page(self):
        """
        Checks that type filter heading and checkboxes are on the page.
        """
        return all([
            self.q(css='.filter-heading').is_present,
            self.q(css=self.type_filter_element).present,
        ])

    @property
    def number_of_filters(self):
        return len(self.q(css='.form-check').execute())

    @wait_for_js
    def correct_filters_in_filter_element(self):
        """
        """
        correct_filters = [u'Audio', u'Code', u'Document', u'Image', u'Other']
        filters = self.q(css='.form-check').execute()
        return all([filter.text in correct_filters for filter in filters])

    #
    # next two items validate clicking the dropdown and selecting from the dropdown
    #
    # @wait_for_js
    # def click_type_filter(self):
    #     """
    #     Clicks type filter Images checkbox.
    #     """
    #     self.q(css=".asInput__form-check-input #Images").click()

    @wait_for_js
    def select_type_filter(self, filter_number):
        """
        Selects Images Type filter checkbox which filters the results.
        Returns False if no filter.
        """
        self.wait_for_ajax()
        if self.is_filter_element_on_page():
            self.q(css=self.type_filter_element + ' .form-check .form-check-input').nth(filter_number).click()
            self.wait_for_ajax()
            return True
        return False

    @wait_for_js
    def click_clear_filters_button(self):
        """
        Clicks 'Clear filters=' button.
        Returns False if no 'Clear filter' button.
        """
        self.wait_for_ajax()
        if self.is_no_results_clear_filter_button_on_page():
            self.q(css='.SFE-wrapper button.btn').filter(
                lambda el: el.text == 'Clear filter'
            ).click()
            self.wait_for_ajax()
            return True
        return False

    # @wait_for_js
    # def are_sortable_elements_on_page(self):
    #     """
    #     Checks that the table headings are sortable.
    #     how to check for all 3? should we?
    #     """
    #     return self.q(css='th.sortable').is_present()

    @property
    @wait_for_js
    def number_of_sortable_buttons_in_table_heading(self):
        return len(self.q(css=self.table_sort_buttons).execute())

    # @wait_for_js
    # def are_sortable_elements_on_page(self):
    #     return self.q(css='th.sortable').execute()

    @wait_for_js
    def is_status_alert_element_on_page(self):
        """
        Checks that status alert is hidden on page.
        """
        return all([
            self.q(css='.alert').present,
            not self.q(css='.alert').visible,
        ])

    @wait_for_js
    def is_pagination_element_on_page(self):
        """
        Checks that pagination is on the page.
        """
        return self.q(css='.pagination').present

    @wait_for_js
    def is_table_element_on_page(self):
        """
        Checks that table is on the page.
        """
        return self.q(css='table.table-responsive').present

    @wait_for_js
    def are_no_results_headings_on_page(self):
        """
        Checks that no results page text is on page.
        """
        return all([
            self.q(css='.SFE-wrapper h3').filter(
                lambda el: el.text == '0 files'
            ).present,
            self.q(css='.SFE-wrapper h4').filter(
                lambda el: el.text == 'No files were found for this filter.'
            ).present,
        ])

    @wait_for_js
    def is_no_results_clear_filter_button_on_page(self):
        """
        Checks that no results clear filter button is on page.
        """
        return self.q(css='.SFE-wrapper button.btn').filter(
            lambda el: el.text == 'Clear filter'
        ).present

    def set_asset_lock(self, index=0):
        """
        Set the state of the asset in the row specified by index
         to locked or unlocked by clicking the button.
        Note: this will raise an IndexError if the row does not exist
        """
        lock_button = self.q(css=".table-responsive tbody tr td:nth-child(7) button").execute()[index]
        lock_button.click()
        # Click initiates an ajax call, waiting for it to complete
        self.wait_for_ajax()
        sync_on_notification(self)

    def confirm_asset_deletion(self):
        """ Click to confirm deletion and sync on the notification"""
        confirmation_title_selector = '.modal'
        self.q(css='.modal button[data-identifier="asset-confirm-delete-button"]').click()
        # Click initiates an ajax call, waiting for it to complete
        self.wait_for_ajax()
        sync_on_notification(self)

    def delete_first_asset(self):
        """ Deletes file then clicks delete on confirmation """
        self.q(css='.fa-trash').first.click()
        self.confirm_asset_deletion()

    def delete_asset_named(self, name):
        """ Delete the asset with the specified name. """
        names = self.asset_files_names
        if name not in names:
            raise LookupError('Asset with filename {} not found.'.format(name))
        delete_buttons = self.asset_delete_buttons
        assets = dict(zip(names, asset_delete_buttons))
        # Now click the link in that row
        assets.get(name).click()
        self.confirm_asset_deletion()

    def delete_all_assets(self):
        """ Delete all uploaded assets """
        while self.asset_files_count:
            self.delete_first_asset()

            # add promise?

    def upload_new_file(self, file_names):
        """
        Upload file(s).

        Arguments:
            page (PageObject): Page to upload file to.
            file_names (list): file name(s) we want to upload.
        """
        # file path found from CourseFixture logic
        UPLOAD_FILE_DIR = Path(__file__).abspath().dirname().dirname().dirname().dirname() + '/data/uploads/studio-uploads/'
        # Make file input field visible.
        file_input_css = 'input[type="file"]'

        for file_name in file_names:
            self.q(css=file_input_css).results[0].clear()
            self.q(css=file_input_css).results[0].send_keys(
                UPLOAD_FILE_DIR + file_name)

        self.wait_for_element_visibility(
            '.alert', 'Upload status alert is visible.')
    #
    # def upload_all_studio_uploads_files(self):
    #     """
    #     Upload all file(s) under /data/uploads/studio-uploads and wait for them to upload.
    #     """
    #     # file path found from CourseFixture logic
    #     UPLOAD_FILE_DIR = Path(__file__).abspath().dirname().dirname().dirname().dirname() + '/data/uploads/studio-uploads/'
    #     # Make file input field visible.
    #     file_input_css = 'input[type="file"]'
    #
    #     for file_name in os.listdir(UPLOAD_FILE_DIR):
    #         self.q(css=file_input_css).results[0].clear()
    #         self.q(css=file_input_css).results[0].send_keys(
    #             UPLOAD_FILE_DIR + file_name)
    #     # import pudb; pudb.set_trace()
    #     ready_promise = EmptyPromise(
    #         lambda: self.asset_files_count == 50 and self.number_of_pagination_page_buttons == 2,
    #         "Files finished uploading"
    #         ).fulfill()

    def return_results_set(self):
        """
        Return the asset set from the page
        """
        return self.q(css=".table-responsive tr").results

    def is_previous_button_disabled(self):
        # return self.q(css=self.pagination_disabled_element).first.present
        return 'disabled' in self.q(css='.pagination li').first.attrs('class')[0];

    def is_next_button_disabled(self):
        # return self.q(css=self.pagination_disabled_element).nth(1).present
        return 'disabled' in self.q(css='.pagination li').nth(self.number_of_pagination_buttons-1).attrs('class')[0];


    def click_pagination_page_button(self, index):
        """
        Click pagination previous button.
        Return False if no pagination page button at specified index.
        """
        self.wait_for_ajax()
        if index < self.number_of_pagination_page_buttons:
            self.q(css=self.pagination_page_element + '.page-item').nth(index).click()
            self.wait_for_ajax()
            return True
        return False

    def click_pagination_next_button(self):
        """
        Click pagination next button.
        Return False if next button disabled.
        """
        self.wait_for_ajax()
        if not self.is_next_button_disabled():
            self.q(css=self.pagination_page_element).nth(self.number_of_pagination_buttons-1).click()
            self.wait_for_ajax()
            return True
        return False

    def click_pagination_previous_button(self):
        """
        Click pagination previous button.
        Return False if previous button disabled.
        """
        self.wait_for_ajax()
        # import pudb; pudb.set_trace()
        if not self.is_previous_button_disabled():
            self.q(css=self.pagination_page_element).first.click()
            self.wait_for_ajax()
            return True
        return False

    @property
    def number_of_pagination_page_buttons(self):
        """
        Return the number of pagination pages.
        """
        return len(self.q(css=self.pagination_page_element + '.page-item'))

    @property
    def number_of_pagination_buttons(self):
        """
        Return the number of total pagination page buttons, including previous, pages, and next buttons.
        """
        import pudb; pudb.set_trace()
        return len(self.q(css=self.pagination_page_element))

    def is_selected_page(self, index):
        """
        Return true if the pagination page at the current index is selected.
        Return false if the pagination page at the current index does not exist
        or is not selected.

        Note: this does not include the 'previous' and 'next' buttons
        Note: 0-indexed
        """
        if index < self.number_of_pagination_page_buttons:
            return 'active' in self.q(css=self.pagination_page_element + '.page-item').nth(index).attrs('class')[0]
        return False

    def click_sort_button(self, button_text):
        """
        """
        # import pudb; pudb.set_trace()
        self.wait_for_ajax()
        sort_button = self.q(css=self.table_sort_buttons).filter(
            lambda el: button_text in el.text
        )

        if sort_button:
            sort_button.click()
            return True
        return False
