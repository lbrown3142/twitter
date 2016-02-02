from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView

from . import follower_descriptions_search, tasks
import twitter
import celery
from . import models


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

    context = { 'organisations': models.University.objects.all() }



    return render(request, 'follower_descriptions/search_form.html', context)

def test(request):

    data = {}
    data['id'] = 999
    data['category'] = 'physics'
    data['screen_name'] = 'Lewis Brown'
    data['url'] = 'lewis.brown@example.com'
    data['user_description'] = "test data"
    data['followed_uni_handle'] = 'sheffielduni'

    tasks.task_upload_to_kibana(data)