from django.conf.urls import url
from django.views.generic import TemplateView

import follower_descriptions
from . import views

urlpatterns = [

    url(r'^$', TemplateView.as_view(template_name='follower_descriptions/search_form.html')),
    url(r'search$', follower_descriptions.views.search)

]