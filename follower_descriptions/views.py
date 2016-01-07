from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView

from . import follower_descriptions_search, tasks
import twitter
import celery

# Create your views here.
def search(request):

    t = tasks.task_get_follower_ids.delay(request.POST["twitter_handle"])


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

    context = {}
    return render(request, 'follower_descriptions/search_form.html', context)