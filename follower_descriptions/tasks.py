from __future__ import absolute_import
import sys
from datetime import datetime, timedelta
from celery.schedules import crontab
from celery.task import periodic_task

from twitter import celery_app as app
from twitter.settings import AWS
from . import models
from django.utils import timezone
import random
import urllib.request
import pprint
import datetime
from . import follower_descriptions_search
from twitter import settings

twitter_ids = 0;
twitter_data = 0;
kibana_uploads = 0;

def log(message):
    message = datetime.datetime.utcnow().isoformat() + " " + message

    print(message)
    try:
        if settings.CAPGEMINI_LOG == True:
            with open('/var/log/capgemini/tasks.log', 'a') as the_file:
                the_file.write(message + '\n')
    except Exception as e:
        pass

@app.task(bind=True)
def task_test(self):
    update_task_stats('task_test')
    self.retry(countdown=int(60))

@app.task(bind=True)
def task_periodic_refresh_all_follower_ids(self):
    update_task_stats('task_periodic_refresh_all_follower_ids')

    # Check all universities for new followers
    universities = models.University.objects.all()
    for uni in universities:
        task_get_follower_ids.delay(uni.uni_handle)

def StartTrackingTask(uni_handle, task_id, task_name):
    try:
        task_tracker = models.CeleryTasksRetrying.objects.get(task_id=task_id)
    except models.CeleryTasksRetrying.DoesNotExist:
        task_tracker = models.CeleryTasksRetrying(task_id=task_id)
        task_tracker.uni_handle = uni_handle
        task_tracker.task_name = task_name

        # task_tracker.created defaults to now
        task_tracker.save()
    return task_tracker


@app.task(bind=True)
def task_get_follower_ids(self, uni_handle, cursor=-1):
    log('task_get_follower_ids ' + uni_handle + "...")
    update_task_stats('task_get_follower_ids')

    # Create a tracking record for this task. It will automatically be timestamped on creation
    task_id = task_get_follower_ids.request.id
    task_tracker = StartTrackingTask(uni_handle, task_id, 'task_get_follower_ids')


    try:
        try:
            university = models.University.objects.get(uni_handle=uni_handle)
        except models.University.DoesNotExist:
            university = models.University(uni_handle=uni_handle)

        if cursor == -1:
            # First call into the recursion
            if university.last_refresh == None or university.last_refresh < (timezone.now() - timedelta(days=7)):
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
        else:
            log('task_get_follower_ids ' + uni_handle + "...done all. Cursor == 0")

        # Process the id's, 100 at a time, by spawning child tasks to get their descriptions.
        for start in range(0, len(results), 100):
            finish = start + 100
            if finish < len(results):
                data = results[start:finish]
            else:
                data = results[start:]

            # Spawn a task to fetch up to 100 followers
            task_get_followers_data.delay(data, uni_handle)

        log('task_get_follower_ids ' + uni_handle + "...done batch")

        # If we get to here, the task is done and we can remove the tracker record
        task_tracker.delete()


    #except urllib.error.HTTPError as e:

        # 429 means Too Many Requests
    #    if e.code == 429:
    #        self.retry(exc=e, countdown=int(1000))
    #    else:
    #        log('task_get_follower_ids ' + uni_handle + "... exception: " + str(e))

    except Exception as e:
        # 2^12 minutes is about 2.8 days. So task will retry for about 5.6 days
        if self.request.retries < 12:
            self.retry(exc=e, countdown=int(60 * (2 ** self.request.retries)))
            log('task_get_follower_ids failed: ' + uni_handle +  ' retry ' + str(self.request.retries) + ' Exception ' + str(e))
        else:
            log('task_get_follower_ids failed: ' + uni_handle +  ' too many retries. Exception ' + str(e))


@app.task(bind=True)
def task_get_followers_data(self, id_list, uni_handle):

    # Create a tracking record for this task. It will automatically be timestamped on creation
    task_id = task_get_followers_data.request.id
    task_tracker = StartTrackingTask(uni_handle, task_id, 'task_get_followers_data')

    update_task_stats('task_get_followers_data')

    try:
        university = models.University.objects.get(uni_handle=uni_handle)

        results = follower_descriptions_search.get_followers_data(id_list)

        #start new stuff

        #how to get/pass in list of buzz words (query arg) from MySQL?
        #need for wordcloud too
        #added new fields in results so model.py needs to be updated
        #filtered_results = follower_descriptions_search.search_distribute(results, uni_handle, query)



        #for data in filtered_results:
        for data in results:

            #finish new stuff
            try:
                graduate = models.Graduate.objects.get(id=data['id'])
            except models.Graduate.DoesNotExist:
                graduate = models.Graduate(id=data['id'])

            if len(data['description']) > 6:
                graduate.name = data['name']
                graduate.description = data['description']
                #need to add graduate location, contacted? etc
                graduate.last_refresh = timezone.now()
                graduate.twitter_handle = data['screen_name']
                graduate.save() # Need to save before adding relationship
                graduate.following.add(university)
                graduate.save()

                data['followed_uni_handle'] = uni_handle
                data['category'] = ''

                task_upload_to_elasticsearch.delay(data)

        log("task_get_followers_data succeeded: " + uni_handle)

        # If we get to here, the task is done and we can remove the tracker record
        task_tracker.delete()

    #except urllib.error.HTTPError as e:

        # 429 means Too Many Requests
    #    if e.code == 429:
    #        self.retry(exc=e, countdown=int(60 * (2 ** self.request.retries)))

    except Exception as e:
        # 2^12 minutes is about 2.8 days
        if self.request.retries < 12:
            self.retry(exc=e, countdown=int(60 * (2 ** self.request.retries)))
            log('task_get_followers_data failed: ' + uni_handle + ' retry ' + str(self.request.retries) + ' Exception ' + str(e))
        else:
            log('task_get_followers_data failed: ' + uni_handle + ' too many retries. Exception ' + str(e))



@app.task(bind=True)
def task_upload_to_elasticsearch(self, data):

    update_task_stats('task_upload_to_elasticsearch')
    screen_name = ''

    try:
        screen_name = data['screen_name']
        description = data['description']

        # We need to escape newlines because they have special meaning for the elasticsearch API
        description = description.replace('\n', '\\n')

        # and quotes " escaped as \\"
        description = description.replace('"', '\\"')

        payload = '{"index": {"_id" : "' + str(data['id']) + '"}}\n'
        payload += '{"category": "' + data['category'] + '", "screen_name":"' + data['screen_name'] + '",'
        payload += '"url":"' + str(data['url']) + '", "user_description":"' + description + '",'
        payload += '"followed_uni_handle":"' + data['followed_uni_handle'] + '"}\n'

        req = urllib.request.Request(url='http://' + AWS + ':9200/my_index/twitter/_bulk',
                                     data=payload.encode('utf-8'),
                                     method='PUT')

        with urllib.request.urlopen(req) as f:
            pass

            log("task_upload_to_elasticsearch succeeded: " + data['screen_name'])

    #except urllib.error.HTTPError as e:

        # 429 means Too Many Requests
        #    if e.code == 429:
        #        self.retry(exc=e, countdown=int(60 * (2 ** self.request.retries)))

        # log("task_upload_to_elasticsearch failed. Exception: {0}".format(str(e)))

    except Exception as e:
        # 2^12 minutes is about 2.8 days
        if self.request.retries < 12:
            self.retry(exc=e, countdown=int(60 * (2 ** self.request.retries)))
            log('task_upload_to_elasticsearch failed: ' + screen_name + ' retry ' + str(self.request.retries) + ' Exception ' + str(e))
        else:
            log('task_upload_to_elasticsearch failed: ' + screen_name + ' too many retries. Exception ' + str(e))



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
    update_task_stats('daily_updates')

    # Refresh university followers
    task_periodic_refresh_all_follower_ids.delay()


@periodic_task(run_every=(crontab(minute=0, hour=0, day_of_week='sunday')))
def weekly_updates():
    log('TASK: weekly_updates')
    update_task_stats('weekly_updates')

def update_task_stats(task_name):
    try:
        task = models.TaskStats.objects.get(task_name=task_name)
    except models.TaskStats.DoesNotExist:
        task = models.TaskStats(task_name=task_name)

    task.count = task.count + 1
    task.last_run = timezone.now()
    task.save()