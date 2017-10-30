import ddt
from edx_ace.utils.date import serialize
from mock import patch
from unittest import skipUnless

from django.conf import settings

from openedx.core.djangoapps.schedules import resolvers, tasks
from openedx.core.djangoapps.schedules.management.commands import send_course_update as nudge
from openedx.core.djangoapps.schedules.management.commands.tests.send_email_base import ScheduleSendEmailTestBase, \
    ExperienceTest
from openedx.core.djangoapps.schedules.management.commands.tests.upsell_base import ScheduleUpsellTestMixin
from openedx.core.djangoapps.schedules.models import ScheduleExperience
from openedx.core.djangolib.testing.utils import skip_unless_lms


@ddt.ddt
@skip_unless_lms
@skipUnless(
    'openedx.core.djangoapps.schedules.apps.SchedulesConfig' in settings.INSTALLED_APPS,
    "Can't test schedules if the app isn't installed",
)
class TestSendCourseUpdate(ScheduleUpsellTestMixin, ScheduleSendEmailTestBase):
    __test__ = True

    # pylint: disable=protected-access
    resolver = resolvers.CourseUpdateResolver
    task = tasks.ScheduleCourseUpdate
    deliver_task = tasks._course_update_schedule_send
    command = nudge.Command
    deliver_config = 'deliver_course_update'
    enqueue_config = 'enqueue_course_update'
    expected_offsets = range(-7, -77, -7)
    experience_type = ScheduleExperience.COURSE_UPDATES

    queries_deadline_for_each_course = True

    def setUp(self):
        super(TestSendCourseUpdate, self).setUp()
        patcher = patch('openedx.core.djangoapps.schedules.resolvers.get_week_highlights')
        mock_highlights = patcher.start()
        mock_highlights.return_value = ['Highlight {}'.format(num + 1) for num in range(3)]
        self.addCleanup(patcher.stop)

    @ddt.data(
        ExperienceTest(experience=ScheduleExperience.DEFAULT, offset=expected_offsets[0], email_sent=False),
        ExperienceTest(experience=ScheduleExperience.COURSE_UPDATES, offset=expected_offsets[0], email_sent=True),
    )
    @patch.object(tasks, 'ace')
    def test_schedule_in_different_experience(self, test_config, mock_ace):
        current_day, offset, target_day, _ = self._get_dates(offset=test_config.offset)

        schedule = self._schedule_factory(
            offset=offset,
            experience__experience_type=test_config.experience,
        )

        self.task.apply(kwargs=dict(
            site_id=self.site_config.site.id, target_day_str=serialize(target_day), day_offset=offset,
            bin_num=self._calculate_bin_for_user(schedule.enrollment.user),
        ))

        self.assertEqual(mock_ace.send.called, test_config.email_sent)

    @patch.object(tasks, 'ace')
    def test_no_experience_specified(self, mock_ace):
        current_day, offset, target_day, _ = self._get_dates(offset=self.expected_offsets[0])

        schedule = self._schedule_factory(
            offset=offset,
            experience=None,
        )

        self.task.apply(kwargs=dict(
            site_id=self.site_config.site.id, target_day_str=serialize(target_day), day_offset=offset,
            bin_num=self._calculate_bin_for_user(schedule.enrollment.user),
        ))

        self.assertFalse(mock_ace.send.called)
