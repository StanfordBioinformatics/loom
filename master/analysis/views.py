import logging
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from analysis.models import File, RunRequest, StepRun, StepResult

logger = logging.getLogger('loom')

class Helper:

    @classmethod
    def create(cls, request, model_class):
        data_json = request.body
        try:
            model = model_class.create(data_json)
            return JsonResponse({"message": "created %s" % model_class.get_name(), "_id": str(model._id)}, status=201)
        except Exception as e:
            return JsonResponse({"message": e.message}, status=400)

    @classmethod
    def index(cls, request, model_class):
        model_list = []
        for model in model_class.objects.all():
            model_list.append(model.downcast().to_serializable_obj())
        return JsonResponse({model_class.get_name(plural=True): model_list}, status=200)

    @classmethod
    def show(cls, request, id, model_class):
        model = model_class.get_by_id(id)
        return JsonResponse(model.to_serializable_obj(), status=200)

    @classmethod
    def update(cls, request, id, model_class):
        model = model_class.get_by_id(id)
        data_json = request.body
        try:
            model.update(data_json)
            return JsonResponse({"message": "updated %s _id=%s" % (model_class.get_name(), model._id)}, status=201)
        except Exception as e:
            return JsonResponse({"message": e.message}, status=400)

@require_http_methods(["GET"])
def status(request):
    return JsonResponse({"message": "server is up"}, status=200)

@require_http_methods(["GET"])
def workerinfo(request):
    workerinfo = {
        'FILE_SERVER_FOR_WORKER': settings.FILE_SERVER_FOR_WORKER,
        'FILE_ROOT_FOR_WORKER': settings.FILE_ROOT_FOR_WORKER,
        'WORKER_LOGFILE': settings.WORKER_LOGFILE,
        'LOG_LEVEL': settings.LOG_LEVEL,
        }
    return JsonResponse({'workerinfo': workerinfo})

@require_http_methods(["GET"])
def filehandlerinfo(request):
    filehandlerinfo = {
        'FILE_SERVER_TYPE': settings.FILE_SERVER_TYPE,
        'FILE_ROOT': settings.FILE_ROOT,
        'IMPORT_DIR': settings.IMPORT_DIR,
        'STEP_RUNS_DIR': settings.STEP_RUNS_DIR,
        'BUCKET_ID': settings.BUCKET_ID,
        }
    return JsonResponse({'filehandlerinfo': filehandlerinfo})

@csrf_exempt
@require_http_methods(["POST"])
def submitrequest(request):
    data_json = request.body
    try:
        run_request = RunRequest.create(data_json)
        logger.info('Created run request %s' % run_request._id)
        return JsonResponse({"message": "created %s" % run_request.get_name(), "_id": str(run_request._id)}, status=201)
    except Exception as e:
        logger.error('Failed to create run request with data "%s". %s' % (data_json, e.message))
        return JsonResponse({"message": e.message}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def submitresult(request):
    data_json = request.body
    try:
        result = StepRun.submit_result(data_json)
        return JsonResponse({"message": "created new %s" % result.get_name(), "_id": str(result._id)}, status=201)
    except Exception as e:
        return JsonResponse({"message": e.message}, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def create_or_index(request, model_class):
    if request.method == "POST":
        return Helper.create(request, model_class)
    else:
        return Helper.index(request, model_class)
   
@csrf_exempt
@require_http_methods(["GET", "POST"])
def show_or_update(request, id, model_class):
    if request.method == "POST":
        return Helper.update(request, id, model_class)
    else:
        return Helper.show(request, id, model_class)

@csrf_exempt
@require_http_methods(["GET"])
def show_input_port_bundles(request, id):
    step_run = StepRun.get_by_id(id)
    input_port_bundles = step_run.get_input_bundles()
    return JsonResponse({"input_port_bundles": input_port_bundles}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
def dashboard(request):
    # Display all active RunRequests plus the last n closed RunRequests

    def _get_count(request):
        DEFAULT_COUNT_STR = '10'
        count_str = request.GET.get('count', DEFAULT_COUNT_STR)
        try:
            count = int(count_str)
        except ValueError as e:
            count = int(DEFAULT_COUNT_STR)
        if count < 0:
            count = int(DEFAULT_COUNT_STR)
        return count

    def _get_step_info(s):
        return {
            'id': s.get_field_as_serializable('_id'),
            'name': s.name,
            'are_results_complete': s.are_results_complete,
            'command': s.command,
            }

    def _get_workflow_info(w):
        return {
            'id': w.get_field_as_serializable('_id'),
            'name': w.name,
            'are_results_complete': w.are_results_complete,
            'steps': [
                _get_step_info(s) for s in w.steps.order_by('datetime_created').reverse().all()
                ]
            }

    def _get_run_request_info(r):
        return {
            'created_at': r.datetime_created,
            'are_results_complete': r.are_results_complete,
            'id': r.get_field_as_serializable('_id'),
            'workflows': [ 
                _get_workflow_info(w) for w in r.workflows.order_by('datetime_created').reverse().all()
                ]
            }

    count = _get_count(request)
    run_requests = RunRequest.get_sorted(count=count)
    if len(run_requests) == 0:
        run_requests_info = []
    run_requests_info = [_get_run_request_info(r) for r in run_requests]

    return JsonResponse({'run_requests': run_requests_info}, status=200)
