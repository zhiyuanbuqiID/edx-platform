from django.conf import settings
from django.conf.urls import patterns, url
from lms.djangoapps.motivationalfee import views

urlpatterns = (
    # url(r'', views.FacebookMotivationalFeeView.as_view(), name='motivational_post'),
    url(r'facebook/', views.FacebookMotivationalFeeView.as_view(), name='motivational_post'),
)