# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand
from lms.djangoapps.certificates.models import CertificateStatuses, GeneratedCertificate
from lms.djangoapps.motivationalfee.models import FacebookMotivationalPostConfig
import requests


class Command(BaseCommand):
    """
    posts to FB on the behalf of users that have not completed a course by its end
    """

    MOTIVATIONAL_FB_POST = ''

    def add_arguments(self, parser):
        """
        Add required arguments to the parser.
        """
        parser.add_argument(
            '--course_run_id',
            dest='course_run_id',
            required=True,
            help='The course for which to post motivational'
        )
        super(Command, self).add_arguments(parser)

    def handle(self, *args, **options):
        """

        """
        course_run_id = options['course_run_id']

        fb_configs = FacebookMotivationalPostConfig.objects.filter({
            'course_run_id': course_run_id,
        })

        for fb_config in fb_configs:
            generated_certificate = GeneratedCertificate.objects.get({
                'course_id': course_run_id,
                'user__id': fb_config.user_id,
            })

            if (generated_certificate and generated_certificate.status in
                (CertificateStatuses.notpassing, CertificateStatuses.audit_notpassing)):
                self.post_to_facebook(fb_config)

    def post_to_facebook(self, fb_config):
        requests.post(
            'https://graph.facebook.com/me/feed',
            json={
                'message': self.MOTIVATIONAL_FB_POST.format(),
                'access_token': fb_config.access_token,
            }
        )
