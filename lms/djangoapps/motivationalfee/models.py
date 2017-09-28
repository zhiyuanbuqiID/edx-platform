# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals
from django.db import models
from model_utils.models import TimeStampedModel
from django.contrib.auth.models import User

# TODO: Create a model that stores facebook authentication info (userID and access token), edX user id, and course key
#       To be used by the script that will create and publish facebook posts at the end of the course
#       for users that have not completed it


class FacebookMotivationalPostConfig(TimeStampedModel):
    """
    Model that keeps track of information needed for the "motivational" facebook post.

    More specifically, this stores facebook authentication info (userID and access token), edX user id, and course key
    To be used by the script that will create and publish facebook posts at the end of the course
    for users that have not completed it.
    """

    user_id = models.PositiveIntegerField(null=False, blank=False)
    course_run_id = models.CharField(max_length=255, null=False, blank=False)
    target_end_date = models.DateTimeField(null=False, blank=False)
    fb_user_id = models.CharField(max_length=255, null=False, blank=False)
    fb_access_token = models.CharField(max_length=255, null=False, blank=False)


    class Meta(object):
        app_label = 'motivationalfee'
        unique_together = (("course_run_id", "user_id"),)

    @property
    def user(self):
        """
        Return User associated with this instance.
        """
        try:
            return User.objects.get(pk=self.user_id)
        except User.DoesNotExist:
            return None

    @property
    def user_email(self):
        """
        Return linked user email.
        """
        if self.user is not None:
            return self.user.email
        return None

    @property
    def username(self):
        """
        Return linked user's username.
        """
        if self.user is not None:
            return self.user.username
        return None
