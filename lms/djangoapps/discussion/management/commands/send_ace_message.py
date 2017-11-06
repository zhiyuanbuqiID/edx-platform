from openedx.core.djangoapps.schedules.management.commands import SendEmailBaseCommand
from lms.djangoapps.discussion.tasks import send_ace_message


class Command(SendEmailBaseCommand):
    async_send_task = send_ace_message
    log_prefix = 'Sent Forum Comment Email Notification'
    offsets = (-2,-1)
