from django.conf import settings
from django.conf.urls import patterns, url
from lms.djangoapps.motivationalfee import views

urlpatterns = patterns(
    url(r'^facebook/$', views.FacebookMotivationalFeeView.as_view(), name='motivational_post'),
)