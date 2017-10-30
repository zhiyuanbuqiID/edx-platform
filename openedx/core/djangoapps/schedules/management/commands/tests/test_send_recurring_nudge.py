from unittest import skipUnless

import ddt
from django.conf import settings
from mock import patch

from edx_ace.utils.date import serialize
from openedx.core.djangoapps.schedules import resolvers, tasks
from openedx.core.djangoapps.schedules.management.commands import send_recurring_nudge as nudge
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
class TestSendRecurringNudge(ScheduleUpsellTestMixin, ScheduleSendEmailTestBase):
    __test__ = True

    # pylint: disable=protected-access
    resolver = resolvers.RecurringNudgeResolver
    task = tasks.ScheduleRecurringNudge
    deliver_task = tasks._recurring_nudge_schedule_send
    command = nudge.Command
    deliver_config = 'deliver_recurring_nudge'
    enqueue_config = 'enqueue_recurring_nudge'
    expected_offsets = (-3, -10)

    consolidates_emails_for_learner = True

    @ddt.data(
        ExperienceTest(experience=ScheduleExperience.DEFAULT, offset=-3, email_sent=True),
        ExperienceTest(experience=ScheduleExperience.DEFAULT, offset=-10, email_sent=True),
        ExperienceTest(experience=ScheduleExperience.COURSE_UPDATES, offset=-3, email_sent=True),
        ExperienceTest(experience=ScheduleExperience.COURSE_UPDATES, offset=-10, email_sent=False),
    )
    @patch.object(tasks, 'ace')
    def test_nudge_experience(self, test_config, mock_ace):
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

    @ddt.data(*expected_offsets)
    @patch.object(tasks, 'ace')
    def test_nudge_without_experience(self, offset, mock_ace):
        current_day, offset, target_day, _ = self._get_dates(offset=offset)

        schedule = self._schedule_factory(
            offset=offset,
            experience=None,
        )

        self.task.apply(kwargs=dict(
            site_id=self.site_config.site.id, target_day_str=serialize(target_day), day_offset=offset,
            bin_num=self._calculate_bin_for_user(schedule.enrollment.user),
        ))

        self.assertTrue(mock_ace.send.called)
