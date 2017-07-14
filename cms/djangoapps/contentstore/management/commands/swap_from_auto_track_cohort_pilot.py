from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from xmodule.modulestore.django import modulestore


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
        for item in items:
            # TODO check that group_access is set to "enrollment cohort content groups" and change
            # TODO their variable to enrollment track user partition
            if item.group_access != {}:
                for key, value in item.group_access.iteritems():
                    print value

