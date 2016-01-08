from __future__ import absolute_import
import sys
from datetime import datetime, timedelta
from twitter import celery_app as app
from . import models
from django.utils import timezone
import random
import urllib.request

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
        try:
            university = models.University.objects.get(uni_handle = uni_handle)
        except models.University.DoesNotExist:
            university = models.University(uni_handle = uni_handle)

        if university.last_refresh == None or university.last_refresh < timezone.now() - timedelta(days = 1):

            results = follower_descriptions_search.get_follower_ids(uni_handle)

            for start in range(0, len(results), 100):
                finish = start + 100
                if finish < len(results):
                    data = results[start:finish]
                else:
                    data = results[start:]

                # Spawn a task to fetch up to 100 followers
                task_get_followers_data.delay(data)

            university.last_refresh = timezone.now()

        university.save()

    except urllib.error.HTTPError as e:
            print("task_get_follower_ids failed. Exception: {0}".format(e.msg))

            # 429 means Too Many Requests
            if e.code == 429:
                self.retry(exc=e,
                           countdown=int(60 * (2 ** self.request.retries) ))


@app.task(bind=True)
def task_get_followers_data(self, id_list):

    try:
        results = follower_descriptions_search.get_followers_data(id_list)

        for data in results:
            try:
                graduate = models.Graduate.objects.get(id = data['id'])
            except models.Graduate.DoesNotExist:
                graduate = models.Graduate(id = data['id'])

            if graduate.last_refresh == None or graduate.last_refresh < timezone.now() - timedelta(days = 1):

                graduate.name = data['name']
                graduate.description = data['description']
                graduate.last_refresh = timezone.now()
                graduate.save()

                # http://52.31.43.191:5601
                #data += '{"index": {"_id" : "' + record['user_id']  + '"}}\n'
                #data += '{"category": "' + record['category'] + '", "screen_name":"' + record['screen_name'] + '",'
                #data += '"url":"' + record['url'] + '", "user_description": "' + record['user_description'] + '",'
                #data += '"followed_uni_handle":"' + record['followed_uni_handle'] + '"}\n'
                #response = requests.put('http://52.31.43.191:9200/my_index/twitter/_bulk', data=data.encode('utf-8'))

    except urllib.error.HTTPError as e:
        print("task_get_followers_data failed. Exception: {0}".format(e.msg))

        # 429 means Too Many Requests
        if e.code == 429:
            self.retry(exc=e,
                       countdown=int(60 * (2 ** self.request.retries) ))
