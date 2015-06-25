from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from analysis.models import File, Request, WorkInProgress

@require_http_methods(["GET"])
def status(request):
    return JsonResponse({"message": "server is up"}, status=200)

@csrf_exempt
@require_http_methods(["POST"])
def submitrequest(request):
    data_json = request.body
    try:
        request = Request.create(data_json)
    except Exception as e:
        return JsonResponse({"message": e.message}, status=400)

    try:
        WorkInProgress.add_open_request(request)
        return JsonResponse({"message": "created new %s" % request.get_name(), "_id": str(request._id)}, status=201)
    except Exception as e:
        return JsonResponse({"message": e.message}, status=500)

def create(request, cls):

    try:
        model = cls.create(data_json)
        return JsonResponse({"message": "created %s" % cls.get_name(), "_id": str(model._id)}, status=201)
    except Exception as e:
        return JsonResponse({"message": e.message}, status=400)

def index(request, cls):
    model_list = []
    for model in cls.objects.all():
        model_list.append(model.downcast().to_obj())
    return JsonResponse({cls.get_name(plural=True): model_list}, status=200)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def create_or_index(request, cls):
    if request.method == "POST":
        return create(request, cls)
    else:
        return index(request, cls)
   
def show(request, id, cls):
    model = cls.get_by_id(id)
    return JsonResponse({model.get_name(): model.to_obj()}, status=200)

def update(request, id, cls):
    model = cls.get_by_id(id)
    data_json = request.body
    try:
        model.update(data_json)
        return JsonResponse({"message": "updated %s _id=%s" % (cls.get_name(), model._id)}, status=201)
    except Exception as e:
        return JsonResponse({"message": e.message}, status=400)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def show_or_update(request, id, cls):
    if request.method == "POST":
        return update(request, id, cls)
    else:
        return show(request, id, cls)
