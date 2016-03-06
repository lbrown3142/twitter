from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.db.models import Count

from . import follower_descriptions_search, tasks
import twitter
import celery
from celery.task.control import inspect

from . import models

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

from twitter import settings

@login_required
def search_following(request):

    try:
        twitter_handle = request.POST["twitter_handle"]

        tasks.log('search_following ' + twitter_handle + '...')
        try:
            university = models.University.objects.get(uni_handle = twitter_handle)
        except models.University.DoesNotExist:
            university = models.University(uni_handle = twitter_handle)
            university.save()

        tasks.task_get_follower_ids.delay(twitter_handle)

        tasks.log('search_following ' + twitter_handle + '...done')
    except Exception as e:
        pass

    # Retrieve tasks
    # Reference: http://docs.celeryproject.org/en/latest/reference/celery.events.state.html
    #query = celery.events.state.tasks_by_type('debug_task')

    # Kill tasks
    # Reference: http://docs.celeryproject.org/en/latest/userguide/workers.html#revoking-tasks
    #for uuid, task in query:
    #    celery.control.revoke(uuid, terminate=True)

    # Get the universities, with a count of how many graduates are following them
    followers = models.University.objects.annotate(num_followers=Count('graduate'))

    context = { 'organisations': followers }
    return render(request, 'follower_descriptions/search_following.html', context)

@login_required
def search_followers(request):

    search_term = ''
    response = {}
    cursor = 0
    cursor_end = 0
    page_size = 10
    count = 0
    next_disabled = ""
    previous_disabled = ""

    try:
        search_term = request.POST["search_term"]

        # Get the cursor value
        cursor = int(request.POST["cursor"])
        if "search" in request.POST:
            cursor = 0

        if "next" in request.POST:
            cursor += page_size

        if "previous" in request.POST:
            cursor -= page_size

        # See http://elasticsearch-dsl.readthedocs.org/en/latest/search_dsl.html
        client = Elasticsearch('localhost')

        #s = Search(using=client, index="my_index") \
        #    .query("match", user_description=search_term)

        s = Search(using=client, index="my_index") \
            .query("multi_match", query=search_term, fields=['user_description','screen_name'])

        if (cursor < 0):
            cursor = 0

        cursor_end = cursor + page_size
        s = s[cursor:cursor_end]

        response = s.execute(ignore_cache=True)

        count = response.hits.total

        if cursor_end > count:
            cursor_end = count

        if cursor == 0:
            previous_disabled = "disabled"

        if cursor_end == count:
            next_disabled = "disabled"

    except Exception as e:
        pass

    context = { 'search_term':search_term,
                'followers':response,
                'page_size':page_size,
                'cursor':cursor,
                'cursor_end':cursor_end,
                'count': count,
                'previous_disabled':previous_disabled,
                'next_disabled':next_disabled,}

    return render(request, 'follower_descriptions/search_followers.html', context)

def CeleryStats(request):

    i = inspect()
    active = i.active()
    scheduled = i.scheduled()
    reserved = i.reserved()

    # These are tasks running now
    active_count = 0
    if active:
        for queue in active:
            active_count += len(active[queue])

    # These are tasks which have failed at least once and have been rescheduled to run again
    scheduled_count = 0
    if scheduled:
        for queue in scheduled:
            scheduled_count += len(scheduled[queue])

    # These are tasks that have been received but not yet had a chance to run
    reserved_count = 0
    if reserved:
        for queue in reserved:
            reserved_count += len(reserved[queue])

    context = { 'active_count':active_count,
                'scheduled_count':scheduled_count,
                'reserved_count':reserved_count}

    return render(request, 'follower_descriptions/stats.html', context)

def test(request):
    tasks.log('Launching task_test...')
    tasks.task_test.delay()
    tasks.log('Launching task_test...done')
    context = {'test_count':''}

    return render(request, 'follower_descriptions/tests.html', context)
