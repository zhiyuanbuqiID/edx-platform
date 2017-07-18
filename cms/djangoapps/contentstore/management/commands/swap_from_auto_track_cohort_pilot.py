from course_modes.models import CourseMode
from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from openedx.core.djangoapps.course_groups.cohorts import CourseCohort
from openedx.core.djangoapps.course_groups.models import (CourseUserGroup, CourseUserGroupPartitionGroup)
from openedx.core.djangoapps.verified_track_content.models import VerifiedTrackCohortedCourse

from xmodule.modulestore.django import modulestore
from xmodule.partitions.partitions import ENROLLMENT_TRACK_PARTITION_ID


class Command(BaseCommand):
    """
    Be sure to run with --settings=devstack
    """
    help = ''

    def add_arguments(self, parser):
        pass
        # parser.add_argument('course_id')
        # parser.add_argument('audit_cohort_names')

    def handle(self, *args, **options):
        """
        """
        module_store = modulestore()

        course_id = 'course-v1:edX+DemoX+Demo_Course'
        audit_cohort_names = ['Audit Cohort', 'Third Cohort']

        # TODO ensure old feature for course is disabled
        # TODO ensure verified track has been created

        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            try:
                course_key = SlashSeparatedCourseKey.from_string(course_id)
            except InvalidKeyError:
                raise CommandError("Invalid course_key: '%s'." % course_id)
        items = module_store.get_items(course_key)
        if not items:
            raise CommandError("Course with %s key not found." % course_id)

        # Get the course user group IDs for the audit course names
        audit_course_user_group_ids = CourseUserGroup.objects.filter(
            name__in=audit_cohort_names,
            course_id=course_key,
            group_type=CourseUserGroup.COHORT,
        ).values_list('id', flat=True)

        # Get all of the audit course cohorts from the above IDs that are RANDOM
        random_audit_course_user_group_ids = CourseCohort.objects.filter(
            course_user_group_id__in=audit_course_user_group_ids,
            assignment_type=CourseCohort.RANDOM
        ).values_list('course_user_group_id', flat=True)

        # Get the CourseUserGroupPartitionGroup for the above IDs, these contain the partition IDs and group IDs
        # that are set for access in modulestore
        random_audit_course_user_group_partition_groups = list(CourseUserGroupPartitionGroup.objects.filter(
            course_user_group_id__in=random_audit_course_user_group_ids
        ))

        verified_track = VerifiedTrackCohortedCourse.objects.get(course_key=course_key)
        verified_course_user_group = CourseUserGroup.objects.get(
            course_id=course_key,
            group_type=CourseUserGroup.COHORT,
            name=verified_track.verified_cohort_name
        )
        verified_course_user_group_partition_group = CourseUserGroupPartitionGroup.objects.get(
            course_user_group_id=verified_course_user_group.id
        )

        audit_course_mode = CourseMode.objects.get(
            course_id=course_key,
            mode_slug=CourseMode.AUDIT
        )
        verified_course_mode = CourseMode.objects.get(
            course_id=course_key,
            mode_slug=CourseMode.VERIFIED
        )
        if verified_track:
            for item in items:
                # TODO Find out how the block is decided if it is "published", look at item.py and try below
                # is_library_block = isinstance(xblock.location, LibraryUsageLocator)
                # published = modulestore().has_published_version(xblock) if not is_library_block else None

                # TODO If the item has changes, republish, if it is not published, error and exit
                # if module_store.has_changes(item):
                #     module_store.publish(item.location, 5)
                #     print item
                if item.group_access != {}:
                    set_audit_enrollment_track = False
                    set_verified_enrollment_track = False
                    for audit_course_user_group_partition_group in random_audit_course_user_group_partition_groups:
                        audit_partition_group_access = item.group_access.get(
                            audit_course_user_group_partition_group.partition_id,
                            None
                        )
                        if (audit_partition_group_access
                                and audit_course_user_group_partition_group.group_id in audit_partition_group_access):
                            # TODO verify below call is not needed to remove the old setting
                            # audit_partition_group_access.remove(audit_course_user_group_partition_group.group_id)
                            set_audit_enrollment_track = True

                    verified_parition_group_access = item.group_access.get(
                        verified_course_user_group_partition_group.partition_id,
                        None
                    )
                    if (verified_parition_group_access
                            and verified_course_user_group_partition_group.group_id in verified_parition_group_access):
                        # TODO verify below call is not needed to remove the old setting
                        # verified_parition_group_access.remove(verified_course_user_group_partition_group.group_id)
                        set_verified_enrollment_track = True

                    enrollment_track_group_access = item.group_access.get(ENROLLMENT_TRACK_PARTITION_ID, [])
                    if set_audit_enrollment_track:
                        enrollment_track_group_access.append(audit_course_mode.id)
                    if set_verified_enrollment_track:
                        enrollment_track_group_access.append(verified_course_mode.id)

                    item.group_access = [{ENROLLMENT_TRACK_PARTITION_ID: enrollment_track_group_access}]
                    # TODO figure out what ID to use for update
                    module_store.update_item(item, 5)  # update_item does not create a new entry, 5 is staff locally
                    module_store.publish(item.location, 5)
