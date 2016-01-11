from __future__ import absolute_import
import sys
from datetime import datetime, timedelta
from twitter import celery_app as app
from . import models
from django.utils import timezone
import random
import urllib.request
import pprint

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
                task_get_followers_data.delay(data, uni_handle)

            university.last_refresh = timezone.now()

        university.save()

    except urllib.error.HTTPError as e:
            print("task_get_follower_ids failed. Exception: {0}".format(e.msg))

            # 429 means Too Many Requests
            if e.code == 429:
                self.retry(exc=e,
                           countdown=int(60 * (2 ** self.request.retries) ))


@app.task(bind=True)
def task_get_followers_data(self, id_list, uni_handle):

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

                data['followed_uni_handle'] = uni_handle
                data['category'] = ''

                task_upload_to_kibana.delay(data)

    except urllib.error.HTTPError as e:
        print("task_get_followers_data failed. Exception: {0}".format(e.msg))

        # 429 means Too Many Requests
        if e.code == 429:
            self.retry(exc=e,
                       countdown=int(60 * (2 ** self.request.retries) ))


@app.task(bind=True)
def task_upload_to_kibana(self, data):

    try:


        # http://52.31.43.191:5601
        payload = '{"index": {"_id" : "' + str(data['id'])  + '"}}\n'
        payload += '{"category": "' + data['category'] + '", "screen_name":"' + data['screen_name'] + '",'
        payload += '"url":"' + data['url'] + '", "user_description":"' + data['description'] + '",'
        payload += '"followed_uni_handle":"' + data['followed_uni_handle'] + '"}\n'


        req = urllib.request.Request(url='http://52.31.43.191:9200/my_index/twitter/_bulk',
                                     data=payload.encode('utf-8'),
                                     method='PUT')

        with urllib.request.urlopen(req) as f:
            pass

    except urllib.error.HTTPError as e:
        print("task_upload_to_kibana failed. Exception: {0}".format(e.msg))

        # 429 means Too Many Requests
        if e.code == 429:
            self.retry(exc=e,
                       countdown=int(60 * (2 ** self.request.retries) ))

    except Exception as e:
        print('EXCEPTION: ' + str(e))
        pprint.pprint(data)
