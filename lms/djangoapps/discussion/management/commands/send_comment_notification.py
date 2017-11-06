from django.core.management.base import BaseCommand
from lms.djangoapps.discussions.signals.handlers import send_message
import lms.lib.comment_client as cc

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            'comment-id',
            help='The comment id to send a notification about',
        )

    def handle(self, *args, **options):
        comment_id = options['comment-id']

        send_message(cc.Comment(id=comment_id).retrieve())