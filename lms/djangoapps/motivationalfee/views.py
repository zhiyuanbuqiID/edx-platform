# -*- coding: utf-8 -*-

from django.conf import settings
from django.views.generic import View
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
import requests
from six.moves.urllib.parse import urlencode
from lms.djangoapps.motivationalfee.models import FacebookMotivationalPostConfig
from django.shortcuts import redirect
from django.core.urlresolvers import reverse

from edxmako.shortcuts import render_to_response


class FacebookMotivationalFeeView(View):
    """
    The motivational post view for our demo.
    """

    def get(self, request):
        """
        The track selection page can be modified to redirect here, and this can render a template with the fb login logic.
        """
        context = {
            'course_run_id': request.GET.get('course_run_id'),
            'fb_app_id': '1925614871011240'
        }
        render_to_response('motivational_costs/facebook_auth.html', context)

    def post(self, request):
        """
        Takes fb authentication/authorization data and retrieves a long lived token to store for future motivational
        posting when the course ends.
        """
        course_run_id = request.POST.get('course_run_id')
        fb_access_token = request.POST.get('fb_access_token')
        fb_user_id = request.POST.get('fb_user_id')

        fb_app_id = configuration_helpers.get_value('HACKATHON_FB_APP_ID', settings.HACKATHON_FB_APP_ID)
        fb_app_secret = configuration_helpers.get_value('HACKATHON_FB_APP_SECRET', settings.HACKATHON_FB_APP_SECRET)

        response = requests.get(
            '{fb_url}?{params}'.format(
                fb_url='http://graph.facebook.com/oauth/access_token',
                params=urlencode((
                    ('grant_type', 'fb_exchange_token'),
                    ('client_id', fb_app_id),
                    ('client_secret', fb_app_secret),
                    ('fb_exchange_token', fb_access_token)
                ))
            )
        )

        # store the token from the response in the model and redirect to dashboard
        response_body = response.json()
        FacebookMotivationalPostConfig.objects.update_or_create(
            user_id=request.user.id,
            course_run_id=course_run_id,
            fb_user_id=fb_user_id,
            fb_access_token=response_body['access_token'],
        )

        return redirect(reverse('dashboard'))
