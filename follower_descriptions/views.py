from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView

from . import follower_descriptions_search

# Create your views here.
def search(request):

    # http://52.31.43.191:5601

    search_terms = []
    search_terms.append(request.POST["Search_1"])
    twitter_handle = request.POST["twitter_handle"]

    results = follower_descriptions_search.DoSearch(twitter_handle, search_terms)

    #return JsonResponse(results, safe=False)
    context = { "results": results[0] }
    return render(request, 'follower_descriptions/search_form.html', context)