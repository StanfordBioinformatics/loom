from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
import os

from analysis import get_setting
from analysis.models import DataObject, AbstractWorkflow, FileDataObject
from analysis.serializers import TaskRunAttemptLogFileSerializer
# from analysis.models import RunRequest, TaskRun, FileDataObject
from loomengine.utils import version

logger = logging.getLogger('loom')

from analysis import models
from analysis import serializers
from rest_framework import viewsets


class QueryViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        query_string = self.request.query_params.get('q', '')
        Model = self.Model
        if query_string:
            return Model.query(query_string)
        else:
            return Model.objects.all()

class DataObjectViewSet(QueryViewSet):
    Model = DataObject
    serializer_class = serializers.DataObjectSerializer

class AbstractWorkflowViewSet(QueryViewSet):
    Model = AbstractWorkflow
    serializer_class = serializers.AbstractWorkflowSerializer

class ImportedWorkflowViewSet(viewsets.ModelViewSet):
    queryset = models.AbstractWorkflow.objects.filter(workflow_import__isnull=False)
    serializer_class = serializers.AbstractWorkflowSerializer
    
class DataObjectContentViewSet(viewsets.ModelViewSet):
    queryset = models.DataObjectContent.objects.all()
    serializer_class = serializers.DataObjectContentSerializer

class UnnamedFileContentViewSet(viewsets.ModelViewSet):
    queryset = models.UnnamedFileContent.objects.all()
    serializer_class = serializers.UnnamedFileContentSerializer

class FileContentViewSet(viewsets.ModelViewSet):
    queryset = models.FileContent.objects.all()
    serializer_class = serializers.FileContentSerializer

class FileLocationViewSet(viewsets.ModelViewSet):
    queryset = models.FileLocation.objects.all()
    serializer_class = serializers.FileLocationSerializer

class FileImportViewSet(viewsets.ModelViewSet):
    queryset = models.FileImport.objects.all()
    serializer_class = serializers.FileImportSerializer

class FileDataObjectViewSet(QueryViewSet):
    Model=FileDataObject
    serializer_class = serializers.FileDataObjectSerializer

class FileProvenanceViewSet(QueryViewSet):
    Model=FileDataObject
    serializer_class = serializers.FileProvenanceSerializer

class ImportedFileDataObjectViewSet(viewsets.ModelViewSet):
    queryset = models.FileDataObject.objects.filter(source_type='imported')
    serializer_class = serializers.FileDataObjectSerializer

class ResultFileDataObjectViewSet(viewsets.ModelViewSet):
    queryset = models.FileDataObject.objects.filter(source_type='result')
    serializer_class = serializers.FileDataObjectSerializer

class LogFileDataObjectViewSet(viewsets.ModelViewSet):
    queryset = models.FileDataObject.objects.filter(source_type='log')
    serializer_class = serializers.FileDataObjectSerializer

class StringContentViewSet(viewsets.ModelViewSet):
    queryset = models.StringContent.objects.all()
    serializer_class = serializers.StringContentSerializer

class StringDataObjectViewSet(viewsets.ModelViewSet):
    queryset = models.StringDataObject.objects.all()
    serializer_class = serializers.StringDataObjectSerializer

class BooleanContentViewSet(viewsets.ModelViewSet):
    queryset = models.BooleanContent.objects.all()
    serializer_class = serializers.BooleanContentSerializer

class BooleanDataObjectViewSet(viewsets.ModelViewSet):
    queryset = models.BooleanDataObject.objects.all()
    serializer_class = serializers.BooleanDataObjectSerializer

class IntegerContentViewSet(viewsets.ModelViewSet):
    queryset = models.IntegerContent.objects.all()
    serializer_class = serializers.IntegerContentSerializer

class IntegerDataObjectViewSet(viewsets.ModelViewSet):
    queryset = models.IntegerDataObject.objects.all()
    serializer_class = serializers.IntegerDataObjectSerializer

class RunRequestViewSet(viewsets.ModelViewSet):
    queryset = models.RunRequest.objects.all()
    serializer_class = serializers.RunRequestSerializer

class TaskRunAttemptViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.TaskRunAttempt.objects.all()
    serializer_class = serializers.TaskRunAttemptSerializer

class TaskRunViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.TaskRun.objects.all()
    serializer_class = serializers.TaskRunSerializer

class TaskRunAttemptOutputViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.TaskRunAttemptOutput.objects.all()
    serializer_class = serializers.TaskRunAttemptOutputSerializer

class AbstractWorkflowRunViewSet(viewsets.ModelViewSet):
    queryset = models.AbstractWorkflowRun.objects.all()
    serializer_class = serializers.AbstractWorkflowRunSerializer

class WorkflowRunViewSet(viewsets.ModelViewSet):
    queryset = models.WorkflowRun.objects.all()
    serializer_class = serializers.WorkflowRunSerializer

class StepRunViewSet(viewsets.ModelViewSet):
    queryset = models.StepRun.objects.all()
    serializer_class = serializers.StepRunSerializer


"""
class TaskDefinitionViewSet(viewsets.ModelViewSet):
    queryset = models.TaskDefinition.objects.all()
    serializer_class = serializers.TaskDefinitionSerializer

class InputOutputNodeViewSet(viewsets.ModelViewSet):
    queryset = models.InputOutputNode.objects.all()
    serializer_class = serializers.InputOutputNodeSerializer

class WorkflowViewSet(AbstractWorkflowViewSet):
    queryset = models.Workflow.objects.all()
    serializer_class = serializers.WorkflowSerializer

class StepViewSet(AbstractWorkflowViewSet):
    queryset = models.Step.objects.all()
    serializer_class = serializers.StepSerializer

class TaskRunAttemptOutputFileImportViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.TaskRunAttemptOutputFileImport.objects.all()
    serializer_class = serializers.TaskRunAttemptOutputFileImportSerializer

class TaskRunAttemptLogFileImportViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.TaskRunAttemptLogFileImport.objects.all()
    serializer_class = serializers.TaskRunAttemptLogFileImportSerializer

class TaskRunAttemptLogFileViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.TaskRunAttemptLogFile.objects.all()
    serializer_class = serializers.TaskRunAttemptLogFileSerializer

"""

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
def filehandler_settings(request):
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
    s = TaskRunAttemptLogFileSerializer(
        data=data,
        context={
            'parent_field': 'task_run_attempt',
            'parent_instance': task_run_attempt
        })
    s.is_valid(raise_exception=True)
    model = s.save()
    return JsonResponse(s.data, status=201)


"""
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
"""
