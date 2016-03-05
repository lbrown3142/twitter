from django.conf.urls import url
from django.views.generic import TemplateView

import follower_descriptions
from . import views

urlpatterns = [

    url(r'^$', follower_descriptions.views.search),
    url(r'^search_followers', follower_descriptions.views.search_followers),

    url(r'^test$', follower_descriptions.views.test),
]