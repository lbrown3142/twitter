from __future__ import absolute_import
from celery import Celery
import time
from datetime import datetime, timedelta
from twitter import celery_app as app
from . import models
from django.utils import timezone


from . import follower_descriptions_search
'''
from celery.task.control import inspect

# Inspect all nodes.
>>> i = inspect()

>>> i.scheduled()
or:
>>> i.active()
'''

@app.task(bind=True)
def task_get_follower_ids(self, uni_handle):

    try:
        university = models.University.objects.get(uni_handle = uni_handle)
    except models.University.DoesNotExist:
        university = models.University(uni_handle = uni_handle)

    if university.last_refresh == None or university.last_refresh < timezone.now() - timedelta(days = 1):

        results = follower_descriptions_search.get_follower_ids(uni_handle)
        for id in results:
            task_get_followers_data.delay(id)

        university.last_refresh = datetime.now()

    university.save()

@app.task(bind=True)
def task_get_followers_data(self, graduate_id):
    data = follower_descriptions_search.get_followers_data(graduate_id)

    # Save results and queue GetDescriptionTasks
    try:
        graduate = models.Graduate.objects.get(id = graduate_id)
    except models.Graduate.DoesNotExist:
        graduate = models.Graduate(id = graduate_id)

    if graduate.last_refresh == None or graduate.last_refresh < timezone.now() - timedelta(days = 1):

        graduate.name = data[0]['name']
        graduate.description = data[0]['description']
        graduate.last_refresh = datetime.now()
        graduate.save()
