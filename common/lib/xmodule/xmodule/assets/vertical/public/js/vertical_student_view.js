/* JavaScript for Vertical Student View. */
window.VerticalStudentView = function(runtime, element) {
    'use strict';
    RequireJS.require(['js/bookmarks/views/bookmark_button'], function(BookmarkButton) {
        var $element = $(element);
        var $bookmarkButtonElement = $element.find('.bookmark-button');

        return new BookmarkButton({
            el: $bookmarkButtonElement,
            bookmarkId: $bookmarkButtonElement.data('bookmarkId'),
            usageId: $element.data('usageId'),
            bookmarked: $element.parent('#seq_content').data('bookmarked'),
            apiUrl: $('.courseware-bookmarks-button').data('bookmarksApiUrl')
        });
    });

    for (var key in usageKeysToFragments) {
        fragment = usageKeysToFragments[key];
        var destinationDiv = $(document.getElementById("vert__" + fragment['id']));
        XBlock.renderXBlockFragment(fragment, destinationDiv);
    }
};
