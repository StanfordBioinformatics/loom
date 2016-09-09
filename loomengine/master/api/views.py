from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
import os
from rest_framework import viewsets

from api import get_setting
from api import models
from api import serializers
from loomengine.utils import version


logger = logging.getLogger('loom')

class AbstractWorkflowViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.AbstractWorkflowSerializer

    def get_queryset(self):
        query_string = self.request.query_params.get('q', '')
        if query_string:
            queryset = models.AbstractWorkflow.query(query_string)
        else:
            queryset = models.AbstractWorkflow.objects.all()
        return queryset

class ImportedWorkflowViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.AbstractWorkflowSerializer

    def get_queryset(self):
        query_string = self.request.query_params.get('q', '')
        if query_string:
            queryset = models.AbstractWorkflow.query(query_string)
        else:
            queryset = models.AbstractWorkflow.objects.all()
        return queryset.filter(workflow_import__isnull=False).order_by('-datetime_created')
    
class FileLocationViewSet(viewsets.ModelViewSet):
    queryset = models.FileLocation.objects.all()
    serializer_class = serializers.FileLocationSerializer

class FileImportViewSet(viewsets.ModelViewSet):
    queryset = models.FileImport.objects.all()
    serializer_class = serializers.FileImportSerializer

class FileDataObjectViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.FileDataObjectSerializer

    def get_queryset(self):
        query_string = self.request.query_params.get('q', '')
        if query_string:
            queryset = models.FileDataObject.query(query_string)
        else:
            queryset = models.FileDataObject.objects.all()
        return queryset

class FileProvenanceViewSet(viewsets.ModelViewSet):
    queryset = models.FileDataObject.objects.all()
    serializer_class = serializers.FileProvenanceSerializer

class ImportedFileDataObjectViewSet(viewsets.ModelViewSet):
    queryset = models.FileDataObject.objects.filter(source_type='imported').order_by('-datetime_created')
    serializer_class = serializers.FileDataObjectSerializer

class ResultFileDataObjectViewSet(viewsets.ModelViewSet):
    queryset = models.FileDataObject.objects.filter(source_type='result').order_by('-datetime_created')
    serializer_class = serializers.FileDataObjectSerializer

class LogFileDataObjectViewSet(viewsets.ModelViewSet):
    queryset = models.FileDataObject.objects.filter(source_type='log').order_by('-datetime_created')
    serializer_class = serializers.FileDataObjectSerializer

class RunRequestViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.RunRequestSerializer

    def get_queryset(self):
        query_string = self.request.query_params.get('q', '')
        if query_string:
            queryset = models.RunRequest.query(query_string)
        else:
            queryset = models.RunRequest.objects.all()
        return queryset.order_by('-datetime_created')

class TaskRunViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.TaskRun.objects.all()
    serializer_class = serializers.TaskRunSerializer

class TaskRunAttemptOutputViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.TaskRunAttemptOutput.objects.all()
    serializer_class = serializers.TaskRunAttemptOutputSerializer

class AbstractWorkflowRunViewSet(viewsets.ModelViewSet):
    queryset = models.AbstractWorkflowRun.objects.all()
    serializer_class = serializers.AbstractWorkflowRunSerializer

class TaskRunAttemptViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.TaskRunAttempt.objects.all()
    serializer_class = serializers.TaskRunAttemptSerializer

class WorkerProcessViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.WorkerProcess.objects.all()
    serializer_class = serializers.WorkerProcessSerializer

@require_http_methods(["GET"])
def status(request):
    return JsonResponse({"message": "server is up"}, status=200)

@require_http_methods(["GET"])
def worker_settings(request, id):
    try:
        WORKING_DIR = models.TaskRunAttempt.get_working_dir(id)
        LOG_DIR = models.TaskRunAttempt.get_log_dir(id)
        return JsonResponse({
            'LOG_LEVEL': get_setting('LOG_LEVEL'),
            'WORKING_DIR': WORKING_DIR,
            'WORKER_LOG_FILE': os.path.join(LOG_DIR, 'worker.log'),
            'STDOUT_LOG_FILE': os.path.join(LOG_DIR, 'stdout.log'),
            'STDERR_LOG_FILE': os.path.join(LOG_DIR, 'stderr.log'),
        })
    except Exception as e:
        return JsonResponse({"message": e.message}, status=500)

@require_http_methods(["GET"])
def filemanager_settings(request):
    return JsonResponse({
        'HASH_FUNCTION': get_setting('HASH_FUNCTION'),
        'PROJECT_ID': get_setting('PROJECT_ID'),
    })

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
        task_run_attempt = models.TaskRunAttempt.objects.get(id=id)
    except ObjectDoesNotExist:
        return JsonResponse({"message": "Not Found"}, status=404)
    s = serializers.TaskRunAttemptLogFileSerializer(
        data=data,
        context={
            'parent_field': 'task_run_attempt',
            'parent_instance': task_run_attempt
        })
    s.is_valid(raise_exception=True)
    model = s.save()
    return JsonResponse(s.data, status=201)
