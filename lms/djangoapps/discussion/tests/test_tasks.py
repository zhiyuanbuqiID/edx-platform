from django.test import TestCase
from lms.djangoapps.discussion.tasks import send_ace_message
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from django_comment_common.models import (
    CourseDiscussionSettings,
    ForumsConfig,
    FORUM_ROLE_STUDENT,
)
from xmodule.modulestore.tests.factories import CourseFactory


class BlaTestCase(TestCase):
    def setUp(self):
        self.course = CourseFactory.create()
        self.thread_user = UserFactory(
            username='thread_user',
            password='password',
            email='email'
        )
        self.comment_user = UserFactory(
            username='comment_user',
            password='password',
            email='email'
        )

        CourseEnrollmentFactory(
            user=self.thread_user,
            course_id=self.course.id
        )
        CourseEnrollmentFactory(
            user=self.comment_user,
            course_id=self.course
        )

        config = ForumsConfig.current()
        config.enabled = True
        config.save()

    def test_send_message(self):
        send_ace_message(
            'thread_id',
            'thread_user_id',
            'comment_user_id',
            'course_id'
        )
