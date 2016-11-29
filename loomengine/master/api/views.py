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


logger = logging.getLogger(__name__)


class DataObjectViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = serializers.DataObjectSerializer

    def get_queryset(self):
        queryset = models.DataObject.objects.all()
        queryset = queryset.select_related('stringdataobject')\
                           .select_related('filedataobject')\
                           .select_related('filedataobject__file_resource')\
                           .select_related('booleandataobject')\
                           .select_related('integerdataobject')\
                           .select_related('floatdataobject')\
                           .select_related('dataobjectarray')\
                           .prefetch_related(
                               'dataobjectarray__prefetch_members__stringdataobject')\
                           .prefetch_related(
                               'dataobjectarray__prefetch_members__booleandataobject')\
                           .prefetch_related(
                               'dataobjectarray__prefetch_members__integerdataobject')\
                           .prefetch_related(
                               'dataobjectarray__prefetch_members__floatdataobject')\
                           .prefetch_related(
                               'dataobjectarray__prefetch_members__filedataobject__file_resource')
        return queryset


class DataTreeViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.DataNodeSerializer

    def get_queryset(self):
        queryset = models.DataNode.objects.filter(parent__isnull=True)
        queryset = queryset.select_related('data_object')\
                .prefetch_related('descendants__data_object')
        return queryset

        
class TaskViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = serializers.TaskSerializer

    def get_queryset(self):
        queryset = models.tasks.Task.objects.all()
        queryset = queryset.select_related('resources')\
                           .select_related('accepted_task_attempt')\
                           .prefetch_related('task_attempts')\
                           .prefetch_related('inputs__data_object')\
                           .prefetch_related('outputs__data_object')\
                           .prefetch_related('outputs__source')
        return queryset


class TaskAttemptViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = serializers.TaskAttemptSerializer

    def get_queryset(self):
        queryset = models.tasks.TaskAttempt.objects.all()
        queryset = queryset.select_related('task')\
                           .select_related('task__step_run')\
                           .prefetch_related('task__resources')\
                           .prefetch_related('task__environment')\
                           .prefetch_related('task__inputs__data_object')\
                           .prefetch_related('outputs__data_object')\
                           .prefetch_related('outputs__task_output__source')\
                           .prefetch_related('log_files__file')\
                           .prefetch_related('errors')
        return queryset


class TemplateViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = serializers.TemplateSerializer

    def get_queryset(self):
        queryset = models.Template.objects.all()
        queryset = queryset\
            .prefetch_related(
                'workflow__fixed_inputs__data_root')\
            .prefetch_related(
                'step__fixed_inputs__data_root')
        return queryset

class RunViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = serializers.RunSerializer

    def get_queryset(self):
        queryset = models.Run.objects.all()
        queryset = queryset.select_related('template__template_import')\
                           .prefetch_related('workflowrun__inputs__data_root')\
                           .prefetch_related(
                               'workflowrun__fixed_inputs__data_root')\
                           .prefetch_related('workflowrun__outputs__data_root')\
                           .prefetch_related('workflowrun__steps')\
                           .prefetch_related('steprun__inputs__data_root')\
                           .prefetch_related(
                               'steprun__fixed_inputs__data_root')\
                           .prefetch_related('steprun__outputs__data_root')\
                           .prefetch_related('steprun__outputs__source')\
                           .prefetch_related('steprun__tasks')
        return queryset

class RunRequestViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = serializers.RunRequestSerializer

    def get_queryset(self):
        queryset = models.RunRequest.objects.all()
        queryset = queryset.select_related('run')\
                           .select_related('template')\
                           .prefetch_related('inputs__data_root')\
                           .prefetch_related('outputs__data_root')
        return queryset.order_by('-datetime_created')


"""
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

class TaskAttemptErrorViewSet(viewsets.ModelViewSet):
    queryset = models.tasks.TaskAttemptError.objects.all()
    serializer_class = serializers.TaskAttemptErrorSerializer

class TaskAttemptOutputViewSet(viewsets.ModelViewSet):
    queryset = models.tasks.TaskAttemptOutput.objects.all()
    serializer_class = serializers.TaskAttemptOutputSerializer

class AbstractWorkflowRunViewSet(viewsets.ModelViewSet):
    queryset = models.AbstractWorkflowRun.objects.all()
    serializer_class = serializers.AbstractWorkflowRunSerializer

"""

@require_http_methods(["GET"])
def status(request):
    return JsonResponse({"message": "server is up"}, status=200)

@require_http_methods(["GET"])
def worker_settings(request, id):
    try:
        task_attempt = models.TaskAttempt.objects.get(id=id)
        return JsonResponse({
            'WORKING_DIR': task_attempt.get_working_dir(),
            'STDOUT_LOG_FILE': task_attempt.get_stdout_log_file(),
            'STDERR_LOG_FILE': task_attempt.get_stderr_log_file(),
        }, status=200)
    except ObjectDoesNotExist:
        return JsonResponse({"message": "Not Found"}, status=404)
    except Exception as e:
        return JsonResponse({"message": e.message}, status=500)

@require_http_methods(["GET"])
def filemanager_settings(request):
    return JsonResponse({
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
def create_task_attempt_log_file(request, id):
    data_json = request.body
    data = json.loads(data_json)
    try:
        task_attempt = models.TaskAttempt.objects.get(id=id)
    except ObjectDoesNotExist:
        return JsonResponse({"message": "Not Found"}, status=404)
    s = serializers.TaskAttemptLogFileSerializer(
        data=data,
        context={
            'parent_field': 'task_attempt',
            'parent_instance': task_attempt
        })
    s.is_valid(raise_exception=True)
    model = s.save()
    return JsonResponse(s.data, status=201)

@csrf_exempt
@require_http_methods(["POST"])
def create_task_attempt_error(request, id):
    data_json = request.body
    data = json.loads(data_json)
    try:
        task_attempt = models.TaskAttempt.objects.get(id=id)
    except ObjectDoesNotExist:
        return JsonResponse({"message": "Not Found"}, status=404)
    s = serializers.TaskAttemptErrorSerializer(
        data=data,
        context={
            'parent_field': 'task_attempt',
            'parent_instance': task_attempt
        })
    s.is_valid(raise_exception=True)
    model = s.save()
    return JsonResponse(s.data, status=201)

