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

aws = "54.194.146.38"

twitter_ids = 0;
twitter_data = 0;
kibana_uploads = 0;

@app.task(bind=True)
def task_get_follower_ids(self, uni_handle, cursor=-1):
    try:
        try:
            university = models.University.objects.get(uni_handle=uni_handle)
        except models.University.DoesNotExist:
            university = models.University(uni_handle=uni_handle)

        if cursor == -1 and ( university.last_refresh == None or university.last_refresh < timezone.now() - timedelta(days=1)):
            if cursor == -1:
                university.last_refresh = timezone.now()
                university.save()

        results, cursor = follower_descriptions_search.get_follower_ids(uni_handle, cursor)


        if cursor != 0:
            task_get_follower_ids.delay(uni_handle, cursor)

        # Process the id's, 100 at a time, by spawning child tasks to get their descriptions.
        for start in range(0, len(results), 100):
            finish = start + 100
            if finish < len(results):
                data = results[start:finish]
            else:
                data = results[start:]

            # Spawn a task to fetch up to 100 followers
            task_get_followers_data.delay(data, uni_handle)





    except urllib.error.HTTPError as e:
        print("task_get_follower_ids failed. Exception: {0}".format(e.msg))

        # 429 means Too Many Requests
        if e.code == 429:
            self.retry(exc=e, countdown=int(1000))

@app.task(bind=True)
def task_get_followers_data(self, id_list, uni_handle):
    try:
        results = follower_descriptions_search.get_followers_data(id_list)

        for data in results:
            try:
                graduate = models.Graduate.objects.get(id=data['id'])
            except models.Graduate.DoesNotExist:
                graduate = models.Graduate(id=data['id'])



            if len(data['description']) > 6:
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
                       countdown=int(60 * (2 ** self.request.retries)))


@app.task(bind=True)
def task_upload_to_kibana(self, data):
    try:

        payload = '{"index": {"_id" : "' + str(data['id']) + '"}}\n'
        payload += '{"category": "' + data['category'] + '", "screen_name":"' + data['screen_name'] + '",'
        payload += '"url":"' + data['url'] + '", "user_description":"' + data['description'] + '",'
        payload += '"followed_uni_handle":"' + data['followed_uni_handle'] + '"}\n'

        req = urllib.request.Request(url='http://' + aws + ':9200/my_index/twitter/_bulk',
                                     data=payload.encode('utf-8'),
                                     method='PUT')

        with urllib.request.urlopen(req) as f:
            pass

    except urllib.error.HTTPError as e:
        print("task_upload_to_kibana failed. Exception: {0}".format(e.msg))

        # 429 means Too Many Requests
        if e.code == 429:
            self.retry(exc=e,
                       countdown=int(60 * (2 ** self.request.retries)))

    except Exception as e:
       # print('EXCEPTION: ' + str(e))
        pprint.pprint(data)
