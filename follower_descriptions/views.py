from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.db.models import Count

from . import follower_descriptions_search, tasks
import twitter
import celery
from . import models

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q


# Create your views here.
@login_required
def search(request):

    try:
        twitter_handle = request.POST["twitter_handle"]

        try:
            university = models.University.objects.get(uni_handle = twitter_handle)
        except models.University.DoesNotExist:
            university = models.University(uni_handle = twitter_handle)
            university.save()

        tasks.task_get_follower_ids.delay(twitter_handle)
    except Exception as e:
        pass

    # Retrieve tasks
    # Reference: http://docs.celeryproject.org/en/latest/reference/celery.events.state.html
    #query = celery.events.state.tasks_by_type('debug_task')

    # Kill tasks
    # Reference: http://docs.celeryproject.org/en/latest/userguide/workers.html#revoking-tasks
    #for uuid, task in query:
    #    celery.control.revoke(uuid, terminate=True)



    # http://52.31.43.191:5601

    '''
    search_terms = []
    search_terms.append(request.POST["Search_1"])
    twitter_handle = request.POST["twitter_handle"]

    results = follower_descriptions_search.DoSearch(twitter_handle, search_terms)

    #return JsonResponse(results, safe=False)
    context = { "results": results[0] }
    '''

    # Get the universities, with a count of how many graduates are following them
    followers = models.University.objects.annotate(num_followers=Count('graduate'))

    context = { 'organisations': followers }
    return render(request, 'follower_descriptions/search_form.html', context)

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

        s = Search(using=client, index="my_index") \
            .query("match", user_description=search_term)

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

def test(request):

    client = Elasticsearch('localhost')

    s = Search(using=client, index="my_index") \
        .query("match", user_description="maths") #   \
        #.query(~Q("match", description="Professor"))

    #.filter("term", category="user_description") \

    #s.aggs.bucket('per_tag', 'terms', field='tags') \
    #    .metric('max_lines', 'max', field='lines')

    response = s.execute(ignore_cache=True)

    for hit in s.scan():
        print(hit)

    #for tag in response.aggregations.per_tag.buckets:
    #    print(tag.key, tag.max_lines.value)