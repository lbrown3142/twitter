import urllib

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count

from follower_descriptions.word_cloud import GenerateWordCloud
from twitter.settings import AWS
from . import tasks
import twitter
import celery
from celery.task.control import inspect

from . import models

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

from twitter import settings

from datetime import timedelta
from django.utils import timezone

@login_required
def search_following(request):

    GenerateWordCloud()

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

    context = { 'organisations': followers, 'base_dir': twitter.settings.BASE_DIR }
    return render(request, 'follower_descriptions/organisations_admin.html', context)

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
            .query("multi_match", query=search_term, fields=['user_description','screen_name', 'followed_uni_handle'])

        if (cursor < 0):
            cursor = 0

        cursor_end = cursor + page_size
        s = s[cursor:cursor_end]

        response = s.execute(ignore_cache=True)

        for result in response:
            screen_name = result['screen_name']

            # We should be able to find just the one graduate. But filter syntax returns a list of one.
            graduates = models.Graduate.objects.filter(twitter_handle = screen_name)
            if len(graduates) > 0:
                graduate = graduates[0]
                if graduate.contacted:
                    result['contacted'] = 'yes'
                else:
                    result['contacted'] = ''

            pass

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

    # Get TaskStats
    task_stats = models.TaskStats.objects.all()

    i = inspect()
    active = i.active()
    scheduled = i.scheduled()
    reserved = i.reserved()

    # These are tasks running now
    active_queues = []
    if active:
        for queue in active:
            active_queues += active[queue]

    # These are tasks which have failed at least once and have been rescheduled to run again
    scheduled_queues = []
    if scheduled:
        for queue in scheduled:
            scheduled_queues += scheduled[queue]

    # These are tasks that have been received but not yet had a chance to run
    reserved_queues = []
    if reserved:
        for queue in reserved:
            reserved_queues += reserved[queue]

    context = { 'task_stats': task_stats,
                'active_count':len(active_queues),
                'scheduled_count':len(scheduled_queues),
                'reserved_count':len(reserved_queues),
                'active':active_queues,
                'scheduled':scheduled_queues,
                'reserved':reserved_queues}

    return render(request, 'follower_descriptions/stats.html', context)


def user_detail(request, twitter_handle):

    graduate = models.Graduate.objects.get(twitter_handle=twitter_handle)

    contacted = graduate.contacted
    contacted_on = graduate.contacted_on

    if (request.method == 'POST'):
        description = request.POST['description']

        # Check for a newly contacted post
        posted_contacted = request.POST.get('contacted', '')
        if not contacted and posted_contacted == 'on':
            contacted = True
            contacted_on = timezone.now()

            # Mark the graduate contacted
            graduate.contacted = contacted
            graduate.contacted_on = contacted_on
            graduate.save()

            # Add a "Has been contacted" comment
            comment = models.Comment(user=request.user,
                                     graduate=graduate,
                                     description='Contacted on ' + contacted_on.strftime("%Y-%m-%d %H:%M"))
            comment.save()

        # Save a non-empty comment
        if description:
            comment = models.Comment(user = request.user,
                                 graduate = graduate,
                                 description = description)
            comment.save()


    # See http://elasticsearch-dsl.readthedocs.org/en/latest/search_dsl.html
    client = Elasticsearch(AWS)

    # s = Search(using=client, index="my_index") \
    #    .query("match", user_description=search_term)

    s = Search(using=client, index="my_index") \
        .query("multi_match", query=twitter_handle, fields=['screen_name'])

    response = s.execute(ignore_cache=True)

    # Resolve the uni handle to something more user-facing
    followed_uni_handle = response[0].followed_uni_handle
    university = models.University.objects.get(uni_handle=followed_uni_handle)

    # Get comments
    comment_list = []
    comments = models.Comment.objects.filter(graduate = graduate)
    for comment in comments:
        comment_list.append(comment)

    # Get profile banner info
    #profile_banner_info = follower_descriptions_search.get_profile_banner_info(twitter_handle, graduate.id)



    context = { 'screen_name': twitter_handle,
                'name': graduate.name,
                'detail': response[0],
                'uni_name': university.name,
                'comments': comment_list,
                'contacted': contacted,
                'contacted_on' : contacted_on}

    return render(request, 'follower_descriptions/user_detail.html', context)

def settings(request):
    context = {}
    if (request.method == 'POST'):
        clear = request.POST['clear']
        if clear == 'clear':

            # Purge all celery tasks (not sure if we need all 3 calls)
            number_discarded1 = celery.task.control.discard_all()
            number_discarded2 = celery.current_app.control.purge()
            number_discarded3 = twitter.celery_app.control.purge()

            # The scheduled queue doesn't get purged by discard_all/purge.
            # It seems we have to revoke the tasks explicitly. Even then, they
            # still remain in the queue, but are ignored when they are eventually
            # scheduled to run.
            scheduled_queues = []
            scheduled = celery.task.control.inspect().scheduled()
            if scheduled:
                for queue in scheduled:
                    scheduled_queues += scheduled[queue]

            for task in scheduled_queues:
                id = task['request']['id']
                celery.task.control.revoke(id)


            # Purge ElasticSearch
            req = urllib.request.Request(url='http://' + AWS + ':9200/_all', method='DELETE')
            with urllib.request.urlopen(req) as f:
                pass

            # Purge the local database
            models.University.objects.all().delete()
            models.Graduate.objects.all().delete()
            models.Comment.objects.all().delete()
            models.TaskStats.objects.all().delete()
            models.CeleryTasksRetrying.objects.all().delete()

            # We don't delete users (otherwise we would delete admin users)
            # We don't delete feedback

            context['database_cleared'] = True

    return render(request, 'follower_descriptions/settings.html', context)


def about(request):
    return render(request, 'follower_descriptions/about.html', {})

def contact(request):
     context = {}

     if (request.method == 'POST'):
        description = request.POST['description']

        feedback = models.Feedback(user = request.user,
                                 description = description)
        feedback.save()
        context = {'success': True}



     return render(request, 'follower_descriptions/contact.html', context)

def test(request):
    x = timezone.now()
    last_refresh  = x - timedelta(minutes=1)

    if last_refresh < x :
        pass

    return render(request, 'follower_descriptions/contact.html', {})
    #if university.last_refresh == None or university.last_refresh < (timezone.now() - timedelta(days=7)):

