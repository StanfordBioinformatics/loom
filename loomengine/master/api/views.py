from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
import os
from rest_framework import viewsets
from rest_framework.decorators import detail_route

from api import get_setting
from api import models
from api import serializers
from loomengine.utils import version


logger = logging.getLogger(__name__)

DATA_CLASSES = {'file': models.FileDataObject,
                'string': models.StringDataObject,
                'boolean': models.BooleanDataObject,
                'float': models.FloatDataObject,
                'integer': models.IntegerDataObject}

class ExpandableViewSet(viewsets.ModelViewSet):

    def get_serializer_context(self):
        return {'request': self.request,
                'expand': 'expand' in self.request.query_params}


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
                               'dataobjectarray__prefetch_members__filedataobject__'\
                               'file_resource')
        return queryset.order_by('-datetime_created')


class FileDataObjectViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = serializers.FileDataObjectSerializer

    def get_queryset(self):
        query_string = self.request.query_params.get('q', '')
        source_type = self.request.query_params.get('source_type', '')
        if query_string:
            queryset = models.FileDataObject.filter_by_name_or_id_or_hash(query_string)
        else:
            queryset = models.FileDataObject.objects.all()
        if source_type and source_type != 'all':
            queryset = queryset.filter(source_type=source_type)
        queryset = queryset.select_related('file_resource')
        return queryset.order_by('-datetime_created')


class DataTreeViewSet(ExpandableViewSet):
    lookup_field = 'uuid'
    serializer_class = serializers.DataNodeSerializer

    def get_queryset(self):
        queryset = models.DataNode.objects.filter(parent__isnull=True)
        queryset = queryset\
                   .select_related('data_object')\
                   .prefetch_related('descendants__data_object')\
                   .prefetch_related('descendants__data_object__stringdataobject')\
                   .prefetch_related('descendants__data_object__filedataobject')\
                   .prefetch_related(
                       'descendants__data_object__filedataobject__file_resource')\
                   .prefetch_related('descendants__data_object__booleandataobject')\
                   .prefetch_related('descendants__data_object__integerdataobject')\
                   .prefetch_related('descendants__data_object__floatdataobject')
        return queryset


class FileResourceViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = serializers.FileResourceSerializer

    def get_queryset(self):
        return models.FileResource.objects.all().order_by('-datetime_created')

        
class TaskViewSet(ExpandableViewSet):
    lookup_field = 'uuid'
    serializer_class = serializers.TaskSerializer

    def get_queryset(self):
        queryset = models.Task.objects.all()
        queryset = queryset\
                   .select_related('selected_task_attempt')\
                   .prefetch_related('task_attempts')\
                   .prefetch_related('inputs')\
                   .prefetch_related('inputs__data_object')\
                   .prefetch_related('inputs__data_object__stringdataobject')\
                   .prefetch_related('inputs__data_object__filedataobject')\
                   .prefetch_related('inputs__data_object__filedataobject__'\
                                     'file_resource')\
                   .prefetch_related('inputs__data_object__booleandataobject')\
                   .prefetch_related('inputs__data_object__integerdataobject')\
                   .prefetch_related('inputs__data_object__floatdataobject')\
                   .prefetch_related('inputs__data_object__dataobjectarray')\
                   .prefetch_related(
                       'inputs__data_object__dataobjectarray__'\
                       'prefetch_members__stringdataobject')\
                   .prefetch_related(
                       'inputs__data_object__dataobjectarray__'\
                       'prefetch_members__booleandataobject')\
                   .prefetch_related(
                       'inputs__data_object__dataobjectarray__'\
                       'prefetch_members__integerdataobject')\
                   .prefetch_related(
                       'inputs__data_object__dataobjectarray__'\
                       'prefetch_members__floatdataobject')\
                   .prefetch_related(
                       'inputs__data_object__dataobjectarray__'\
                       'prefetch_members__filedataobject__'\
                       'file_resource')\
                   .prefetch_related('outputs')\
                   .prefetch_related('outputs__data_object')\
                   .prefetch_related('outputs__data_object__stringdataobject')\
                   .prefetch_related('outputs__data_object__filedataobject')\
                   .prefetch_related('outputs__data_object__filedataobject__'\
                                     'file_resource')\
                   .prefetch_related('outputs__data_object__booleandataobject')\
                   .prefetch_related('outputs__data_object__integerdataobject')\
                   .prefetch_related('outputs__data_object__floatdataobject')\
                   .prefetch_related('outputs__data_object__dataobjectarray')\
                   .prefetch_related(
                       'outputs__data_object__dataobjectarray__'\
                       'prefetch_members__stringdataobject')\
                   .prefetch_related(
                       'outputs__data_object__dataobjectarray__'\
                       'prefetch_members__booleandataobject')\
                   .prefetch_related(
                       'outputs__data_object__dataobjectarray__'\
                       'prefetch_members__integerdataobject')\
                   .prefetch_related(
                       'outputs__data_object__dataobjectarray__'\
                       'prefetch_members__floatdataobject')\
                   .prefetch_related(
                       'outputs__data_object__dataobjectarray__'\
                       'prefetch_members__filedataobject__'\
                       'file_resource')\
                   .prefetch_related('timepoints')
        return queryset.order_by('-datetime_created')


class TaskAttemptViewSet(ExpandableViewSet):
    lookup_field = 'uuid'
    serializer_class = serializers.TaskAttemptSerializer

    def get_queryset(self):
        queryset = models.TaskAttempt.objects.all()
        queryset = queryset.select_related('task')\
                           .prefetch_related('inputs')\
                           .prefetch_related('inputs__data_object')\
                           .prefetch_related('inputs__data_object__stringdataobject')\
                           .prefetch_related('inputs__data_object__filedataobject')\
                           .prefetch_related('inputs__data_object__filedataobject__'\
                                             'file_resource')\
                           .prefetch_related('inputs__data_object__booleandataobject')\
                           .prefetch_related('inputs__data_object__integerdataobject')\
                           .prefetch_related('inputs__data_object__floatdataobject')\
                           .prefetch_related('inputs__data_object__dataobjectarray')\
                           .prefetch_related(
                               'inputs__data_object__dataobjectarray__'\
                               'prefetch_members__stringdataobject')\
                           .prefetch_related(
                               'inputs__data_object__dataobjectarray__'\
                               'prefetch_members__booleandataobject')\
                           .prefetch_related(
                               'inputs__data_object__dataobjectarray__'\
                               'prefetch_members__integerdataobject')\
                           .prefetch_related(
                               'inputs__data_object__dataobjectarray__'\
                               'prefetch_members__floatdataobject')\
                           .prefetch_related(
                               'inputs__data_object__dataobjectarray__'\
                               'prefetch_members__filedataobject__'\
                               'file_resource')\
                           .prefetch_related('outputs')\
                           .prefetch_related('outputs__'\
                                             'data_object')\
                           .prefetch_related('outputs__'\
                                             'data_object__stringdataobject')\
                           .prefetch_related('outputs__'\
                                             'data_object__filedataobject')\
                           .prefetch_related('outputs__'\
                                             'data_object__filedataobject__'\
                                             'file_resource')\
                           .prefetch_related('outputs__'\
                                             'data_object__booleandataobject')\
                           .prefetch_related('outputs__'\
                                             'data_object__integerdataobject')\
                           .prefetch_related('outputs__'\
                                             'data_object__floatdataobject')\
                           .prefetch_related('outputs__'\
                                             'data_object__dataobjectarray')\
                           .prefetch_related(
                               'outputs__data_object__'\
                               'dataobjectarray__prefetch_members__stringdataobject')\
                           .prefetch_related(
                               'outputs__data_object__'\
                               'dataobjectarray__prefetch_members__booleandataobject')\
                           .prefetch_related(
                               'outputs__data_object__'\
                               'dataobjectarray__prefetch_members__integerdataobject')\
                           .prefetch_related(
                               'outputs__data_object__'\
                               'dataobjectarray__prefetch_members__floatdataobject')\
                           .prefetch_related(
                               'outputs__data_object__'\
                               'dataobjectarray__prefetch_members__filedataobject__'\
                               'file_resource')\
                           .prefetch_related('log_files__file')\
                           .prefetch_related('log_files__file__'\
                                             'filedataobject__file_resource')\
                           .prefetch_related('timepoints')
        return queryset.order_by('-datetime_created')

    @detail_route(methods=['post'], url_path='create-log-file')
    def create_log_file(self, request, uuid=None):
        data_json = request.body
        data = json.loads(data_json)
        try:
            task_attempt = models.TaskAttempt.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Not Found"}, status=404)
        s = serializers.TaskAttemptLogFileSerializer(
            data=data,
            context={
                'parent_field': 'task_attempt',
                'parent_instance': task_attempt,
                'request': request,
            })
        s.is_valid(raise_exception=True)
        model = s.save()
        return JsonResponse(s.data, status=201)

    @detail_route(methods=['post'], url_path='fail')
    def fail(self, request, uuid=None):
        try:
            task_attempt = models.TaskAttempt.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Not Found"}, status=404)
        task_attempt.fail()
        return JsonResponse({}, status=201)

    @detail_route(methods=['post'], url_path='finish')
    def finish(self, request, uuid=None):
        try:
            task_attempt = models.TaskAttempt.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Not Found"}, status=404)
        task_attempt.finish()
        return JsonResponse({}, status=201)
    
    @detail_route(methods=['post'], url_path='create-timepoint')
    def create_timepoint(self, request, uuid=None):
        data_json = request.body
        data = json.loads(data_json)
        try:
            task_attempt = models.TaskAttempt.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Not Found"}, status=404)
        s = serializers.TaskAttemptTimepointSerializer(
            data=data,
            context={
                'parent_field': 'task_attempt',
                'parent_instance': task_attempt,
                'request': request
            })
        s.is_valid(raise_exception=True)
        model = s.save()

        return JsonResponse(s.data, status=201)

    @detail_route(methods=['get'], url_path='worker-settings')
    def get_worker_settings(self, request, uuid=None):
        try:
            task_attempt = models.TaskAttempt.objects.get(uuid=uuid)
            return JsonResponse({
                'WORKING_DIR': task_attempt.get_working_dir(),
                'STDOUT_LOG_FILE': task_attempt.get_stdout_log_file(),
                'STDERR_LOG_FILE': task_attempt.get_stderr_log_file(),
                'HEARTBEAT_INTERVAL_SECONDS':
                get_setting('TASKRUNNER_HEARTBEAT_INTERVAL_SECONDS'),
            }, status=200)
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Not Found"}, status=404)
        except Exception as e:
            return JsonResponse({"message": e.message}, status=500)


class TemplateViewSet(ExpandableViewSet):
    lookup_field = 'uuid'
    serializer_class = serializers.TemplateSerializer

    def get_queryset(self):
        query_string = self.request.query_params.get('q', '')
        imported = 'imported' in self.request.query_params
        if query_string:
            queryset = models.Template.filter_by_name_or_id(query_string)
        else:
            queryset = models.Template.objects.all()
        if imported:
            queryset = queryset.filter(template_import__isnull=False)
        queryset = queryset\
                   .prefetch_related('workflow__steps')\
                   .prefetch_related(
                       'workflow__fixed_inputs__data_root')\
                   .prefetch_related(
                       'step__fixed_inputs__data_root')
        return queryset.order_by('-datetime_created')

class RunViewSet(ExpandableViewSet):
    lookup_field = 'uuid'
    serializer_class = serializers.RunSerializer

    def get_queryset(self):
        query_string = self.request.query_params.get('q', '')
        parent_only = 'parent_only' in self.request.query_params
        if query_string:
            queryset = models.Run.filter_by_name_or_id(query_string)
        else:
            queryset = models.Run.objects.all()
        if parent_only:
            queryset = queryset.filter(parent__isnull=True)
        queryset = queryset.select_related('workflowrun__template')\
                           .prefetch_related('workflowrun__inputs')\
                           .prefetch_related(
                               'workflowrun__inputs__data_root')\
                           .prefetch_related('workflowrun__outputs')\
                           .prefetch_related(
                               'workflowrun__outputs__data_root')\
                           .prefetch_related('workflowrun__steps')\
                           .select_related(
                               'workflowrun__run_request')\
                           .prefetch_related('workflowrun__timepoints')\
                           .select_related('steprun__template')\
                           .prefetch_related('steprun__inputs')\
                           .prefetch_related('steprun__inputs__data_root')\
                           .prefetch_related('steprun__outputs')\
                           .prefetch_related('steprun__outputs__data_root')\
                           .prefetch_related('steprun__tasks')\
                           .select_related(
                               'steprun__run_request')\
                           .prefetch_related('steprun__timepoints')
        return queryset.order_by('-datetime_created')

class RunRequestViewSet(ExpandableViewSet):
    lookup_field = 'uuid'
    serializer_class = serializers.RunRequestSerializer

    def get_queryset(self):
        queryset = models.RunRequest.objects.all()
        queryset = queryset.select_related('run')\
                           .select_related('template')\
                           .prefetch_related('inputs__data_root')
        return queryset.order_by('-datetime_created')

class TaskAttemptLogFileViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.TaskAttemptLogFileSerializer

    def get_queryset(self):
        queryset = models.TaskAttemptLogFile.objects.all()
        queryset = queryset.select_related('file')\
                   .select_related('file__filedataobject__file_resource')
        return queryset.order_by('-datetime_created')

class TaskAttemptOutputViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.TaskAttemptOutputSerializer

    def get_queryset(self):
        queryset = models.TaskAttemptOutput.objects.all()
        queryset = queryset.select_related('data_object__stringdataobject')\
                           .select_related('data_object__filedataobject')\
                           .select_related(
                               'data_object__filedataobject__file_resource')\
                           .select_related('data_object__booleandataobject')\
                           .select_related('data_object__integerdataobject')\
                           .select_related('data_object__floatdataobject')\
                           .select_related('data_object__dataobjectarray')\
                           .prefetch_related(
                               'data_object__dataobjectarray__'\
                               'prefetch_members__stringdataobject')\
                           .prefetch_related(
                               'data_object__dataobjectarray__'\
                               'prefetch_members__booleandataobject')\
                           .prefetch_related(
                               'data_object__dataobjectarray__'\
                               'prefetch_members__integerdataobject')\
                           .prefetch_related(
                               'data_object__dataobjectarray__'\
                               'prefetch_members__floatdataobject')\
                           .prefetch_related(
                               'data_object__dataobjectarray__'\
                               'prefetch_members__filedataobject__'\
                               'file_resource')
        return queryset.order_by('-datetime_created')


"""
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

class AbstractWorkflowRunViewSet(viewsets.ModelViewSet):
    queryset = models.AbstractWorkflowRun.objects.all()
    serializer_class = serializers.AbstractWorkflowRunSerializer

"""

@require_http_methods(["GET"])
def status(request):
    return JsonResponse({"message": "server is up"}, status=200)

@require_http_methods(["GET"])
def filemanager_settings(request):
    return JsonResponse({
        'GCE_PROJECT': get_setting('GCE_PROJECT'),
    })

@require_http_methods(["GET"])
def info(request):
    data = {
        'version': version.version()
    }
    return JsonResponse(data, status=200)
