from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
import os

from analysis import get_setting
#from analysis.models import RunRequest, TaskRun, FileDataObject, TaskRunAttempt
from loom.common import version

logger = logging.getLogger('loom')

from analysis import models
from analysis import serializers
from rest_framework import viewsets


class QueryViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        query_string = self.request.query_params.get('q', '')
        Model = self.serializer_class.Meta.model
        if query_string:
            return Model.query_by_name_or_id(query_string)
        else:
            return Model.objects.all()

class DataObjectViewSet(QueryViewSet):
    serializer_class = serializers.DataObjectSerializer

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

class AbstractFileImportViewSet(viewsets.ModelViewSet):
    queryset = models.AbstractFileImport.objects.all()
    serializer_class = serializers.AbstractFileImportSerializer

class FileImportViewSet(viewsets.ModelViewSet):
    queryset = models.FileImport.objects.all()
    serializer_class = serializers.FileImportSerializer

class FileDataObjectViewSet(DataObjectViewSet):
    queryset = models.FileDataObject.objects.all()
    serializer_class = serializers.FileDataObjectSerializer

class StringContentViewSet(viewsets.ModelViewSet):
    queryset = models.StringContent.objects.all()
    serializer_class = serializers.StringContentSerializer

class StringDataObjectViewSet(DataObjectViewSet):
    queryset = models.StringDataObject.objects.all()
    serializer_class = serializers.StringDataObjectSerializer

class BooleanContentViewSet(viewsets.ModelViewSet):
    queryset = models.BooleanContent.objects.all()
    serializer_class = serializers.BooleanContentSerializer

class BooleanDataObjectViewSet(DataObjectViewSet):
    queryset = models.BooleanDataObject.objects.all()
    serializer_clsas = serializers.BooleanDataObjectSerializer

class IntegerContentViewSet(viewsets.ModelViewSet):
    queryset = models.IntegerContent.objects.all()
    serializer_class = serializers.IntegerContentSerializer

class IntegerDataObjectViewSet(DataObjectViewSet):
    queryset = models.IntegerDataObject.objects.all()
    serializer_class = serializers.IntegerDataObjectSerializer

class TaskDefinitionViewSet(viewsets.ModelViewSet):
    queryset = models.TaskDefinition.objects.all()
    serializer_class = serializers.TaskDefinitionSerializer

class TaskDefinitionInputViewSet(viewsets.ModelViewSet):
    queryset = models.TaskDefinitionInput.objects.all()
    serializer_class = serializers.TaskDefinitionInputSerializer

class TaskDefinitionOutputViewSet(viewsets.ModelViewSet):
    queryset = models.TaskDefinitionOutput.objects.all()
    serializer_class = serializers.TaskDefinitionOutputSerializer

class TaskDefinitionEnvironmentViewSet(viewsets.ModelViewSet):
    queryset = models.TaskDefinitionEnvironment.objects.all()
    serializer_class = serializers.TaskDefinitionEnvironmentSerializer

class TaskDefinitionDockerEnvironmentViewSet(viewsets.ModelViewSet):
    queryset = models.TaskDefinitionDockerEnvironment.objects.all()
    serializer_class = serializers.TaskDefinitionDockerEnvironmentSerializer

class InputOutputNodeViewSet(viewsets.ModelViewSet):
    queryset = models.InputOutputNode.objects.all()
    serializer_class = serializers.InputOutputNodeSerializer

class ChannelOutputViewSet(viewsets.ModelViewSet):
    queryset = models.ChannelOutput.objects.all()
    serializer_class = serializers.ChannelOutputSerializer

class ChannelViewSet(viewsets.ModelViewSet):
    queryset = models.Channel.objects.all()
    serializer_class = serializers.ChannelSerializer

class AbstractWorkflowViewSet(QueryViewSet):
    queryset = models.AbstractWorkflow.objects.all()
    serializer_class = serializers.AbstractWorkflowSerializer

class WorkflowViewSet(AbstractWorkflowViewSet):
    queryset = models.Workflow.objects.all()
    serializer_class = serializers.WorkflowSerializer

class StepViewSet(AbstractWorkflowViewSet):
    queryset = models.Step.objects.all()
    serializer_class = serializers.StepSerializer

class RequestedEnvironmentViewSet(viewsets.ModelViewSet):
    queryset = models.RequestedEnvironment.objects.all()
    serializer_class = serializers.RequestedEnvironmentSerializer

class RequestedDockerEnvironmentViewSet(viewsets.ModelViewSet):
    queryset = models.RequestedDockerEnvironment.objects.all()
    serializer_class = serializers.RequestedDockerEnvironmentSerializer

class RequestedResourceSetViewSet(viewsets.ModelViewSet):
    queryset = models.RequestedResourceSet.objects.all()
    serializer_class = serializers.RequestedResourceSetSerializer

class WorkflowInputViewSet(viewsets.ModelViewSet):
    queryset = models.WorkflowInput.objects.all()
    serializer_class = serializers.WorkflowInputSerializer

class StepInputViewSet(viewsets.ModelViewSet):
    queryset = models.StepInput.objects.all()
    serializer_class = serializers.StepInputSerializer

class FixedWorkflowInputViewSet(viewsets.ModelViewSet):
    queryset = models.FixedWorkflowInput.objects.all()
    serializer_class = serializers.FixedWorkflowInputSerializer

class FixedStepInputViewSet(viewsets.ModelViewSet):
    queryset = models.FixedStepInput.objects.all()
    serializer_class = serializers.FixedStepInputSerializer

class WorkflowOutputViewSet(viewsets.ModelViewSet):
    queryset = models.WorkflowOutput.objects.all()
    serializer_class = serializers.WorkflowOutputSerializer

class StepOutputViewSet(viewsets.ModelViewSet):
    queryset = models.StepOutput.objects.all()
    serializer_class = serializers.StepOutputSerializer

class TaskRunAttemptOutputFileImportViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.TaskRunAttemptOutputFileImport.objects.all()
    serializer_class = serializers.TaskRunAttemptOutputFileImportSerializer

class TaskRunAttemptLogFileImportViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.TaskRunAttemptLogFileImport.objects.all()
    serializer_class = serializers.TaskRunAttemptLogFileImportSerializer

class TaskRunAttemptOutputViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.TaskRunAttemptOutput.objects.all()
    serializer_class = serializers.TaskRunAttemptOutputSerializer

class TaskRunAttemptLogFileViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.TaskRunAttemptLogFile.objects.all()
    serializer_class = serializers.TaskRunAttemptLogFileSerializer

class TaskRunAttemptViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.TaskRunAttempt.objects.all()
    serializer_class = serializers.TaskRunAttemptSerializer

class MockTaskRunAttemptViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.MockTaskRunAttempt.objects.all()
    serializer_class = serializers.MockTaskRunAttemptSerializer

class LocalTaskRunAttemptViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.LocalTaskRunAttempt.objects.all()
    serializer_class = serializers.LocalTaskRunAttemptSerializer

class GoogleCloudTaskRunAttemptViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.GoogleCloudTaskRunAttempt.objects.all()
    serializer_class = serializers.GoogleCloudTaskRunAttemptSerializer

class TaskRunInputViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.TaskRunInput.objects.all()
    serializer_class = serializers.TaskRunInputSerializer

class TaskRunOutputViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.TaskRunOutput.objects.all()
    serializer_class = serializers.TaskRunOutputSerializer

class TaskRunViewSet(viewsets.ModelViewSet):
    queryset = models.task_runs.TaskRun.objects.all()
    serializer_class = serializers.TaskRunSerializer

class AbstractWorkflowRunViewSet(viewsets.ModelViewSet):
    queryset = models.AbstractWorkflowRun.objects.all()
    serializer_class = serializers.AbstractWorkflowRunSerializer

class WorkflowRunViewSet(viewsets.ModelViewSet):
    queryset = models.WorkflowRun.objects.all()
    serializer_class = serializers.WorkflowRunSerializer

class StepRunViewSet(viewsets.ModelViewSet):
    queryset = models.StepRun.objects.all()
    serializer_class = serializers.StepRunSerializer

class AbstractStepRunInputViewSet(viewsets.ModelViewSet):
    queryset = models.AbstractStepRunInput.objects.all()
    serializer_class = serializers.AbstractStepRunInputSerializer

class StepRunInputViewSet(viewsets.ModelViewSet):
    queryset = models.StepRunInput.objects.all()
    serializer_class = serializers.StepRunInputSerializer

class FixedStepRunInputViewSet(viewsets.ModelViewSet):
    queryset = models.FixedStepRunInput.objects.all()
    serializer_class = serializers.FixedStepRunInputSerializer

class StepRunOutputViewSet(viewsets.ModelViewSet):
    queryset = models.StepRunOutput.objects.all()
    serializer_class = serializers.StepRunOutputSerializer

class WorkflowRunInputViewSet(viewsets.ModelViewSet):
    queryset = models.WorkflowRunInput.objects.all()
    serializer_class = serializers.WorkflowRunInputSerializer
    
class FixedWorkflowRunInputViewSet(viewsets.ModelViewSet):
    queryset = models.FixedWorkflowRunInput.objects.all()
    serializer_class = serializers.FixedWorkflowRunInputSerializer

class WorkflowRunOutputViewSet(viewsets.ModelViewSet):
    queryset = models.WorkflowRunOutput.objects.all()
    serializer_class = serializers.WorkflowRunOutputSerializer

class RunRequestViewSet(viewsets.ModelViewSet):
    queryset = models.RunRequest.objects.all()
    serializer_class = serializers.RunRequestSerializer

class RunRequestInputViewSet(viewsets.ModelViewSet):
    queryset = models.RunRequestInput.objects.all()
    serializer_class = serializers.RunRequestInputSerializer
    
class RunRequestOutputViewSet(viewsets.ModelViewSet):
    queryset = models.RunRequestOutput.objects.all()
    serializer_class = serializers.RunRequestOutputSerializer

class CancelRequestViewSet(viewsets.ModelViewSet):
    queryset = models.CancelRequest.objects.all()
    serializer_class = serializers.CancelRequestSerializer

class RestartRequestViewSet(viewsets.ModelViewSet):
    queryset = models.RestartRequest.objects.all()
    serializer_class = serializers.RestartRequestSerializer

class FailureNoticeViewSet(viewsets.ModelViewSet):
    queryset = models.FailureNotice.objects.all()
    serializer_class = serializers.FailureNoticeSerializer

@require_http_methods(["GET"])
def status(request):
    return JsonResponse({"message": "server is up"}, status=200)

@require_http_methods(["GET"])
def worker_settings(request, id):
    try:
        WORKING_DIR = TaskRunAttempt.get_working_dir(id)
        LOG_DIR = TaskRunAttempt.get_log_dir(id)
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
"""
