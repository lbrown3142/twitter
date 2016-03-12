from __future__ import absolute_import
import sys
from datetime import datetime, timedelta

from celery.schedules import crontab
from celery.task import periodic_task

from twitter import celery_app as app
from . import models
from django.utils import timezone
import random
import urllib.request
import pprint
from . import follower_descriptions_search
from twitter import settings

'''
from celery.task.control import inspect

# Inspect all nodes.
>>> i = inspect()

>>> i.scheduled()
or:
>>> i.active()
'''

aws = "localhost"

twitter_ids = 0;
twitter_data = 0;
kibana_uploads = 0;

def log(message):
    print(message)
    try:
        if settings.CAPGEMINI_LOG == True:
            with open('/var/log/capgemini/tasks.log', 'a') as the_file:
                the_file.write(message + '\n')
    except Exception as e:
        pass


@app.task(bind=True)
def task_periodic_refresh_all_follower_ids(self):
    # Check all universities for new followers
    universities = models.University.objects.all()
    for uni in universities:
        task_get_follower_ids.delay(uni.uni_handle)


@app.task(bind=True)
def task_get_follower_ids(self, uni_handle, cursor=-1):
    log('task_get_follower_ids ' + uni_handle + "...")
    try:
        try:
            university = models.University.objects.get(uni_handle=uni_handle)
        except models.University.DoesNotExist:
            university = models.University(uni_handle=uni_handle)

        if cursor == -1:
            # First call into the recursion
            if university.last_refresh == None or university.last_refresh < timezone.now() - timedelta(days=7):
                # Get the university name (more descriptive than its handle)
                uni_data = follower_descriptions_search.get_users_by_screen_name([uni_handle])
                name = uni_data[0]['name']
                university.name = name
                university.last_refresh = timezone.now()
                university.save()
            else:
                # Nothing to do
                return

        results, cursor = follower_descriptions_search.get_follower_ids(uni_handle, cursor)

        if cursor != 0:
            # Recursive call passing in the cursor
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

        log('task_get_follower_ids ' + uni_handle + "...done")

    except urllib.error.HTTPError as e:

        # 429 means Too Many Requests
        if e.code == 429:
            self.retry(exc=e, countdown=int(1000))
        else:
            log('task_get_follower_ids ' + uni_handle + "... exception: " + e.msg)

@app.task(bind=True)
def task_get_followers_data(self, id_list, uni_handle):
    try:
        university = models.University.objects.get(uni_handle=uni_handle)

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
                graduate.save() # Need to save before adding relationship
                graduate.following.add(university)
                graduate.save()

                data['followed_uni_handle'] = uni_handle
                data['category'] = ''

                task_upload_to_kibana.delay(data)

        print("task_get_followers_data succeeded: " + uni_handle)

    except urllib.error.HTTPError as e:
        print("task_get_followers_data failed. Exception: {0}".format(e.msg))

        # 429 means Too Many Requests
        if e.code == 429:
            self.retry(exc=e,
                       countdown=int(60 * (2 ** self.request.retries)))


@app.task(bind=True)
def task_upload_to_kibana(self, data):

    retry = 2
    while retry > 0:

        try:

            description = data['description']

            #description = 'SteveBrown3141\nBrownQuote"Quote'

            # We need to escape newlines because they have special meaning for the elasticsearch API
            description = description.replace('\n', '\\n')

            # and quotes " escaped as \\"
            #description = description.replace('"', '\\"')

            payload = '{"index": {"_id" : "' + str(data['id']) + '"}}\n'
            payload += '{"category": "' + data['category'] + '", "screen_name":"' + data['screen_name'] + '",'
            payload += '"url":"' + str(data['url']) + '", "user_description":"' + description + '",'
            payload += '"followed_uni_handle":"' + data['followed_uni_handle'] + '"}\n'

            req = urllib.request.Request(url='http://' + aws + ':9200/my_index/twitter/_bulk',
                                         data=payload.encode('utf-8'),
                                         method='PUT')

            with urllib.request.urlopen(req) as f:
                pass

            print("task_upload_to_kibana succeeded: " + data['screen_name'])
            retry = 0
        except urllib.error.HTTPError as e:
            print("task_upload_to_kibana failed. Exception: {0}".format(e.msg))

            # 429 means Too Many Requests
            if e.code == 429:
                self.retry(exc=e,
                           countdown=int(60 * (2 ** self.request.retries)))

            retry -= 1
        except Exception as e:
           # print('EXCEPTION: ' + str(e))
            pprint.pprint(data)
            retry -= 1

# See here for more crontab options:
# http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html

@periodic_task(run_every=(crontab(minute='*'))) # Every minute
def minute_updates():
    log('TASK: minute_updates')

@periodic_task(run_every=(crontab(minute='*/15'))) # Every 15 minutes
def quarter_hour_updates():
    log('TASK: quarter_hour_updates')


@periodic_task(run_every=(crontab(minute=0))) # Every hour
def hourly_updates():
    log('TASK: hourly_updates')

@periodic_task(run_every=(crontab(minute=0, hour=0))) # Daily at midnight
def daily_updates():
    log('TASK: daily_updates')

    # Refresh university followers
    task_periodic_refresh_all_follower_ids.delay()


@periodic_task(run_every=(crontab(minute=0, hour=0, day_of_week='sunday')))
def weekly_updates():
    log('TASK: weekly_updates')

