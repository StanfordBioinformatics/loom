from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
import os

from analysis import get_setting
from analysis.models import RunRequest, TaskRun, FileDataObject, TaskRunAttempt
from loom.common import version

logger = logging.getLogger('loom')

class Helper:

    @classmethod
    def create(cls, request, model_class):
        data_json = request.body
        try:
            model = model_class.create(data_json)
            return JsonResponse({"message": "created %s" % model_class.get_class_name(), "_id": str(model._id), "object": model.to_struct()}, status=201)
        except Exception as e:
            logger.error('Failed to create %s with data "%s". %s' % (model_class, data_json, e.message))
            return JsonResponse({"message": e.message}, status=500)

    @classmethod
    def index(cls, request, model_class):
        query_string = request.GET.get('q')
        if query_string is None:
            model_list = model_class.objects.all()
        else:
            model_list = model_class.get_by_name_or_id(query_string)
        return JsonResponse(
            {
                model_class.get_class_name(plural=True):
                [model.to_struct() for model in model_list]
            },
            status=200)

    @classmethod
    def show(cls, request, id, model_class):
        try:
            model = model_class.get_by_id(id)
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Not Found"}, status=404)
        return JsonResponse(model.to_struct(), status=200)

    @classmethod
    def update(cls, request, id, model_class):
        data_json = request.body
        model = model_class.get_by_id(id)
        try:
            model.downcast().update(data_json)
            return JsonResponse({"message": "updated %s" % model_class.get_class_name(), "_id": str(model._id), "object": model.to_struct()}, status=201)
        except Exception as e:
            logger.error('Failed to update %s with data "%s". %s' % (model_class, data_json, e.message))
            return JsonResponse({"message": e.message}, status=500)

@require_http_methods(["GET"])
def status(request):
    return JsonResponse({"message": "server is up"}, status=200)

@require_http_methods(["GET"])
def worker_settings(request, id):
    try:
        WORKING_DIR = TaskRunAttempt.get_working_dir(id)
        LOG_DIR = TaskRunAttempt.get_log_dir(id)
        return JsonResponse({
            'worker_settings': {
                'LOG_LEVEL': get_setting('LOG_LEVEL'),
                'WORKING_DIR': WORKING_DIR,
                'WORKER_LOG_FILE': os.path.join(LOG_DIR, 'worker.log'),
                'STDOUT_LOG_FILE': os.path.join(LOG_DIR, 'stdout.log'),
                'STDERR_LOG_FILE': os.path.join(LOG_DIR, 'stderr.log'),
            }})
    except Exception as e:
        return JsonResponse({"message": e.message}, status=500)

@require_http_methods(["GET"])
def filehandler_settings(request):
    filehandler_settings = {
        'HASH_FUNCTION': get_setting('HASH_FUNCTION'),
        'PROJECT_ID': get_setting('PROJECT_ID'),
        }
    return JsonResponse({'filehandler_settings': filehandler_settings})

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

@require_http_methods(["GET"])
def locations_by_file(request, id):
    try:
        file = FileDataObject.get_by_id(id)
    except ObjectDoesNotExist:
        return JsonResponse({"message": "Not Found"}, status=404)
    return JsonResponse({"file_locations": [o.to_struct() for o in file.file_content.unnamed_file_content.file_locations.all()]}, status=200)

@require_http_methods(["GET"])
def file_data_source_runs(request, id):
    try:
        file = FileDataObject.get_by_id(id)
    except ObjectDoesNotExist:
        return JsonResponse({"message": "Not Found"}, status=404)
    runs = []
    for task_run_output in file.taskrunoutput_set.all():
        runs.append({'step_run': {'_id': task_run_output.task_run.steprun._id.hex,
                                  'step_name': task_run_output.task_run.steprun.step.step_name},
                     'workflow_run': {'_id': task_run_output.task_run.steprun.workflow_run._id.hex,
                                      'workflow_name': task_run_output.task_run.steprun.workflow_run.workflow.workflow_name}})
    return JsonResponse({"runs": runs}, status=200)

@require_http_methods(["GET"])
def file_imports_by_file(request, id):
    try:
        file = FileDataObject.get_by_id(id)
    except ObjectDoesNotExist:
        return JsonResponse({"message": "Not Found"}, status=404)
    return JsonResponse({"file_imports": [o.to_struct() for o in file.file_imports.all()]}, status=200)

@csrf_exempt
@require_http_methods(["POST"])
def refresh(request):
    RunRequest.refresh_status_for_all()
    return JsonResponse({"status": "ok"}, status=200)

@require_http_methods(["GET"])
def info(request):
    data = {
        'version': version.version()
    }
    return JsonResponse(data, status=200)

@csrf_exempt
@require_http_methods(["POST"])
def create_task_run_attempt_log_file(request, id):
    data_json = request.body
    data = json.loads(data_json)
    try:
        task_run_attempt = TaskRunAttempt.get_by_id(id)
    except ObjectDoesNotExist:
        return JsonResponse({"message": "Not Found"}, status=404)
    model = task_run_attempt.create_log_file(data)
    return JsonResponse({"message": "created %s" % model.get_class_name(), "_id": model.get_id(), "object": model.to_struct()}, status=201)

@require_http_methods(["GET"])
def imported_file_data_objects(request):
    return JsonResponse(
            {
                'file_data_objects':
                [model.to_struct() for model in FileDataObject.objects.filter(file_import__fileimport__isnull=False).distinct()]
            },
            status=200)

@require_http_methods(["GET"])
def result_file_data_objects(request):
    return JsonResponse(
            {
                'file_data_objects':
                [model.to_struct() for model in FileDataObject.objects.filter(file_import__taskrunattemptoutputfileimport__isnull=False).distinct()]
            },
            status=200)
