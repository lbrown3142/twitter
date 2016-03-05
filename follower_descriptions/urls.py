from django.conf.urls import url
from django.views.generic import TemplateView, RedirectView

import follower_descriptions
from . import views

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='followers/'), ),
    url(r'^following$', follower_descriptions.views.search_following),
    url(r'^followers$', follower_descriptions.views.search_followers),

    url(r'^test$', follower_descriptions.views.test),
]