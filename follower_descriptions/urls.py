from django.conf.urls import url
from django.views.generic import TemplateView, RedirectView

import follower_descriptions
from . import views

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='users'), ),
    url(r'^organisations$', follower_descriptions.views.search_following),
    url(r'^users$', follower_descriptions.views.search_followers),
    url(r'^user\/(.+)$', follower_descriptions.views.user_detail),

    url(r'^stats$', follower_descriptions.views.CeleryStats),
    url(r'^test$', follower_descriptions.views.test),

]