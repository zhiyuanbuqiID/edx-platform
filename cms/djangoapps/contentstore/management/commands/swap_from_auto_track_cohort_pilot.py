from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from xmodule.contentstore.django import contentstore
from xmodule.modulestore.django import modulestore


class Command(BaseCommand):
    """

    """
    help = ''

    def add_arguments(self, parser):
        parser.add_argument('course_id')

    def handle(self, *args, **options):
        """
        """
        module_store = modulestore()

        try:
            course_key = CourseKey.from_string(options['course_id'])
        except InvalidKeyError:
            try:
                course_key = SlashSeparatedCourseKey.from_string(options['course_id'])
            except InvalidKeyError:
                raise CommandError("Invalid course_key: '%s'." % options['course_id'])

        if not module_store.get_course(course_key):
            raise CommandError("Course with %s key not found." % options['course_id'])

