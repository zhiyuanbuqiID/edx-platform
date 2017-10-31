import logging
from urlparse import urlparse

from celery import task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.utils.http import urlquote

from celery_utils.logged_task import LoggedTask
from edx_ace import ace
from edx_ace.channel import ChannelType
from edx_ace.message import Message, MessageType
from edx_ace.recipient import Recipient
from edx_ace.utils.date import deserialize
from edxmako.shortcuts import marketing_link
from opaque_keys.edx.keys import CourseKey
from lms.lib.comment_client.user import User as CommentClientUser

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


DEFAULT_LANGUAGE = 'en'
ROUTING_KEY = getattr(settings, 'ACE_ROUTING_KEY', None)


class ResponseNotification(MessageType):
    def __init__(self, *args, **kwargs):
        super(ResponseNotification, self).__init__(*args, **kwargs)
        self.name = 'response_notification'


@task(base=LoggedTask, routing_key=ROUTING_KEY)
def send_ace_message(thread_id, thread_user_id, comment_user_id, course_id):
    thread_user = CommentClientUser.from_django_user(User.objects.get(id=thread_user_id))

    if thread_user.is_user_subscribed_to_thread(thread_id):
        commenting_user = User.objects.get(id=comment_user_id)
        context = _get_base_template_context(Site.objects.get_current())
        message = ResponseNotification().personalize(
            Recipient(commenting_user.username, commenting_user.email),
            _get_course_language(course_id),
            context
        )
        # ace.send(message)


def _get_course_language(course_id):
    try:
        course_key = CourseKey.from_string(course_id)
        course_overview = CourseOverview.objects.get(id=course_key)
        language = course_overview.language or DEFAULT_LANGUAGE
    except:
        language = DEFAULT_LANGUAGE
    return language


def _get_base_template_context(site):
    """Dict with entries needed for all templates that use the base template"""
    return {
        # Platform information
        'homepage_url': _encode_url(marketing_link('ROOT')),
        'dashboard_url': _absolute_url(site, reverse('dashboard')),
        'template_revision': settings.EDX_PLATFORM_REVISION,
        'platform_name': settings.PLATFORM_NAME,
        'contact_mailing_address': settings.CONTACT_MAILING_ADDRESS,
        'social_media_urls': _encode_urls_in_dict(getattr(settings, 'SOCIAL_MEDIA_FOOTER_URLS', {})),
        'mobile_store_urls': _encode_urls_in_dict(getattr(settings, 'MOBILE_STORE_URLS', {})),
    }


def _encode_url(url):
    # Sailthru has a bug where URLs that contain "+" characters in their path components are misinterpreted
    # when GA instrumentation is enabled. We need to percent-encode the path segments of all URLs that are
    # injected into our templates to work around this issue.
    parsed_url = urlparse(url)
    modified_url = parsed_url._replace(path=urlquote(parsed_url.path))
    return modified_url.geturl()


def _absolute_url(site, relative_path):
    root = site.domain.rstrip('/')
    relative_path = relative_path.lstrip('/')
    return _encode_url(u'https://{root}/{path}'.format(root=root, path=relative_path))


def _encode_urls_in_dict(mapping):
    urls = {}
    for key, value in mapping.iteritems():
        urls[key] = _encode_url(value)
    return urls
