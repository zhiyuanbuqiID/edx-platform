from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from openedx.core.djangoapps.course_groups.models import CourseUserGroup
from openedx.core.djangoapps.verified_track_content.models import VerifiedTrackCohortedCourse

from xmodule.modulestore.django import modulestore
from xmodule.partitions.partitions import ENROLLMENT_TRACK_PARTITION_ID



class Command(BaseCommand):
    """
    Be sure to run with --settings=devstack
    """
    help = ''

    def add_arguments(self, parser):
        parser.add_argument('course_id')

    def handle(self, *args, **options):
        """
        """
        module_store = modulestore()

        # TODO ensure old feature for course is disabled
        # TODO ensure verified track has been created

        try:
            course_key = CourseKey.from_string(options['course_id'])
        except InvalidKeyError:
            try:
                course_key = SlashSeparatedCourseKey.from_string(options['course_id'])
            except InvalidKeyError:
                raise CommandError("Invalid course_key: '%s'." % options['course_id'])
        items = module_store.get_items(course_key)
        if not items:
            raise CommandError("Course with %s key not found." % options['course_id'])

        # TODO get course modes

        verified_track = VerifiedTrackCohortedCourse(course_key=course_key)
        course_user_group = CourseUserGroup(
            course_id=course_key,
            group_type=CourseUserGroup.COHORT,
            name=verified_track.verified_cohort_name
        )
        course_mode = None
        if verified_track and verified_track.enabled:
            for item in items:
                # TODO Find out how the block is decided if it is "published", look at item.py and try below
                # is_library_block = isinstance(xblock.location, LibraryUsageLocator)
                # published = modulestore().has_published_version(xblock) if not is_library_block else None

                # If the item has changes, republish, if it is not published, error and exit
                # if module_store.has_changes(item):
                #     module_store.publish(item.location, 5)
                #     print item
                if item.group_access != {}:
                    if item.group_access[course_user_group.id]:
                        audit_cohorts = []
                        verified_cohorts = []
                        for key, value in item.group_access.iteritems():
                            if key == course_user_group.id:
                                verified_cohorts += value
                            else:
                                audit_cohorts += value
                            print value
                            # TODO don't use partition id, try just using the track ids
                            item.group_access = [{ENROLLMENT_TRACK_PARTITION_ID: value}]
                            module_store.update_item(item, 5)  # update_item does not create a new entry
                            module_store.publish(item.location, 5)
