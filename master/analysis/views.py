import logging
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from analysis.models import File, RequestSubmission, WorkInProgress, StepRun, StepResult

logger = logging.getLogger('xppf')

@require_http_methods(["GET"])
def status(request):
    return JsonResponse({"message": "server is up"}, status=200)

@require_http_methods(["GET"])
def workerinfo(request):
    workerinfo = {
        'FILE_SERVER': settings.FILE_SERVER,
        'FILE_ROOT': settings.FILE_ROOT,
        'WORKER_LOGFILE': settings.WORKER_LOGFILE,
        'LOG_LEVEL': settings.LOG_LEVEL,
        }
    return JsonResponse({'workerinfo': workerinfo})

@csrf_exempt
@require_http_methods(["POST"])
def submitrequest(request):
    data_json = request.body
    try:
        request_submission = RequestSubmission.create(data_json)
        logger.info('Created request submission %s' % request_submission._id)
    except Exception as e:
        logger.error('Failed to create request submission with data "%s". %s' % (data_json, e.message))
        return JsonResponse({"message": e.message}, status=400)
    try:
        WorkInProgress.submit_new_request(request_submission.to_obj())
        return JsonResponse({"message": "created new %s" % request_submission.get_name(), "_id": str(request_submission._id)}, status=201)
    except Exception as e:
        return JsonResponse({"message": e.message}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def submitresult(request):
    data_json = request.body
    try:
        result = WorkInProgress.submit_result(data_json)
        return JsonResponse({"message": "created new %s" % result.get_name(), "_id": str(result._id)}, status=201)
    except Exception as e:
        return JsonResponse({"message": e.message}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def closerun(request):
    data_json = request.body
    try:
        WorkInProgress.close_run(data_json)
        return JsonResponse({"message": "closed run", "_id": data_json.get('_id')})
    except Exception as e:
        return JsonResponse({"message": e.message}, status=500)
    run_id = data_json.get('_id')

def create(request, cls):
    data_json = request.body
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
    return JsonResponse(model.to_obj(), status=200)

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

@csrf_exempt
@require_http_methods(["GET"])
def show_input_port_bundles(request, id):
    step_run = StepRun.get_by_id(id)
    input_port_bundles = step_run.get_input_port_bundles()
    return JsonResponse({"input_port_bundles": input_port_bundles}, status=200)