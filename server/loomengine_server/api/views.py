from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
import django.core.exceptions
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
import os
import rest_framework.response
import rest_framework.viewsets
import rest_framework.status
from rest_framework.decorators import detail_route
from rest_framework.generics import RetrieveAPIView
from rest_framework.views import APIView
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.authtoken.models import Token

from api import get_setting
from api import models
from api import serializers
from api import async
from loomengine_utils import version

logger = logging.getLogger(__name__)


class QuietBasicAuthentication(authentication.BasicAuthentication):
    # disclaimer: once the user is logged in, this should NOT be used as a
    # substitute for SessionAuthentication, which uses the django session cookie,
    # rather it can check credentials before a session cookie has been granted.
    def authenticate_header(self, request):
        return 'xBasic realm="%s"' % self.www_authenticate_realm


class AuthView(APIView):
    authentication_classes = (QuietBasicAuthentication,)
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        login(request, request.user)
        return JsonResponse({'username': request.user.username})

    def delete(self, request, *args, **kwargs):
        logout(request)
        return JsonResponse({})


class TokenView(APIView):
    authentication_classes = (QuietBasicAuthentication,)
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        # DRF allows only 1 token per user, so we only create one if none exists
        try:
            token = Token.objects.get(user=request.user)
        except Token.DoesNotExist:
            token = Token.objects.create(user=request.user)
        return JsonResponse({'token': token.key})


class UserViewSet(rest_framework.viewsets.ModelViewSet):

    serializer_class = serializers.UserSerializer
    permission_classes = (permissions.IsAdminUser,)

    def get_queryset(self):
        query_string = self.request.query_params.get('q', '')
        if query_string:
            queryset = User.objects.filter(username=query_string)
        else:
            queryset = User.objects.all()
        return queryset.exclude(username='loom-system')


class ExpandableViewSet(rest_framework.viewsets.ModelViewSet):
    """Some models contain nested data that cannot be rendered in an index
    view in a finite number of queries, making it very slow to render all nested
    data as the number of model instances grows.

    For these models, we include three distinct serializers:
    - default (collapsed): Includes all data either rendered or through links
    - expanded: Includes all data fully rendered
    - summary: Include a subset of data useful for display. This is
    useful for efficiently rendering a skeleton version of nested data.
    - url: Show only the model's id and url

    Because the number of database queries with the number of objects for
    summary and expanded views, these are disabled in the index view.

    URL serializers are not useful when accessed directly from the viewset, 
    since they only container information that was implicit in the URL from 
    which they were retrieved. But collapsed serializers use url serializers 
    to minimally represent nested data, and a ?url option is include with the
    viewsets for testing purposes.

    Write behavior for all serializers types is the same. Only the representation
    differs.
    """

    def get_serializer_class(self):
        if 'expand' in self.request.query_params:
            return self.EXPANDED_SERIALIZER
        elif 'summary' in self.request.query_params:
            return self.SUMMARY_SERIALIZER
        elif 'url' in self.request.query_params:
            return self.URL_SERIALIZER
        else:
            return self.DEFAULT_SERIALIZER

    def list(self, request):
        if 'expand' in self.request.query_params:
            return rest_framework.response.Response(
                {"non_field_errors":
                 "'expand' mode is not allowed in a list view."},
                status=rest_framework.status.HTTP_400_BAD_REQUEST)
        elif 'summary' in self.request.query_params:
            return rest_framework.response.Response(
                {"non_field_errors":
                 "'summary' mode is not allowed in a list view."},
                status=rest_framework.status.HTTP_400_BAD_REQUEST)
        return super(ExpandableViewSet, self).list(self, request)

    def get_queryset(self):
        Serializer = self.get_serializer_class()
        queryset = Serializer.Meta.model.objects.all()
        queryset = Serializer.apply_prefetch(queryset)
        return queryset #.order_by('-datetime_created')


class DataObjectViewSet(rest_framework.viewsets.ModelViewSet):
    """Each DataObject represents a value of type file, string, boolean, 
    integer, or float.
    """

    lookup_field = 'uuid'

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return serializers.DataObjectUpdateSerializer
        else:
            return serializers.DataObjectSerializer

    def get_queryset(self):
        query_string = self.request.query_params.get('q', '')
        type = self.request.query_params.get('type', '')
        source_type = self.request.query_params.get('source_type', '')
        labels = self.request.query_params.get('labels', '')
        if query_string:
            queryset = models.DataObject.filter_by_name_or_id_or_tag_or_hash(
                query_string)
        else:
            queryset = models.DataObject.objects.all()
        if source_type and source_type != 'all':
            queryset = queryset.filter(file_resource__source_type=source_type)
        if type:
            queryset = queryset.filter(type=type)
        if labels:
            for label in labels.split(','):
                queryset = queryset.filter(labels__label=label)
        queryset = self.get_serializer_class().apply_prefetch(queryset)
        return queryset.order_by('-datetime_created')
    
    @detail_route(methods=['post'], url_path='add-tag',
                  serializer_class=serializers.DataTagSerializer)
    def add_tag(self, request, uuid=None):
        data_json = request.body
        data = json.loads(data_json)
        try:
            data_object = models.DataObject.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise rest_framework.exceptions.NotFound()
        s = serializers.DataTagSerializer(
            data=data, context={'data_object': data_object})
        s.is_valid(raise_exception=True)
        s.save()
        return JsonResponse(s.data, status=201)

    @detail_route(methods=['post'], url_path='remove-tag',
                  serializer_class=serializers.DataTagSerializer)
    def remove_tag(self, request, uuid=None):
        data_json = request.body
        data = json.loads(data_json)
        tag = data.get('tag')
        try:
            data_object = models.DataObject.objects.get(uuid=uuid)
            tag_instance = data_object.tags.get(tag=tag)
        except ObjectDoesNotExist:
            raise rest_framework.exceptions.NotFound()
        tag_instance.delete()
        return JsonResponse({
            'tag': tag,
            'message': 'Tag %s was removed from DataObject @%s' % (
                tag, data_object.uuid)},
                            status=200)

    @detail_route(methods=['get'], url_path='tags')
    def list_tags(self, request, uuid=None):
        try:
            data_object = models.DataObject.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise rest_framework.exceptions.NotFound()
        tags = []
        for tag in data_object.tags.all():
            tags.append(tag.tag)

        return JsonResponse({'tags': tags}, status=200)

    @detail_route(methods=['post'], url_path='add-label',
                  serializer_class=serializers.DataLabelSerializer)
    def add_label(self, request, uuid=None):
        data_json = request.body
        data = json.loads(data_json)
        try:
            data_object = models.DataObject.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise rest_framework.exceptions.NotFound()
        s = serializers.DataLabelSerializer(
            data=data, context={'data_object': data_object})
        s.is_valid(raise_exception=True)
        s.save()
        return JsonResponse(s.data, status=201)

    @detail_route(methods=['post'], url_path='remove-label',
                  serializer_class=serializers.DataLabelSerializer)
    def remove_label(self, request, uuid=None):
        data_json = request.body
        data = json.loads(data_json)
        label = data.get('label')
        try:
            data_object = models.DataObject.objects.get(uuid=uuid)
            label_instance = data_object.labels.get(label=label)
        except ObjectDoesNotExist:
            raise rest_framework.exceptions.NotFound()
        label_instance.delete()
        return JsonResponse({
            'label': label,
            'message': 'Label %s was removed from DataObject @%s' % (
                label, data_object.uuid)},
                            status=200)

    @detail_route(methods=['get'], url_path='labels',
                  serializer_class=serializers.DataLabelSerializer)
    def list_labels(self, request, uuid=None):
        try:
            data_object = models.DataObject.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise rest_framework.exceptions.NotFound()
        labels = []
        for label in data_object.labels.all():
            labels.append(label.label)
        return JsonResponse({'labels': labels}, status=200)


class DataNodeViewSet(ExpandableViewSet):
    """DataNodes are used to organize DataObjects into arrays or trees to facilitate parallel runs. All nodes in a tree must have the same type. The 'contents' field is a JSON containing a single DataObject, a list of DataObjects, or nested lists. For write actions, each DataObject can be represented in full for as a dict, or as a string, where the string represents a given value (e.g. '3' for type integer), or a reference id (e.g. myfile.txt@22588117-425d-44f9-8a61-0cfd4d241d5e). PARAMS: ?expand or ?summary will show data contents (not allowed in index view). ?url will show only the url and uuid fields (for testing only).
    """
    lookup_field = 'uuid'

    DEFAULT_SERIALIZER = serializers.DataNodeSerializer
    EXPANDED_SERIALIZER = serializers.ExpandedDataNodeSerializer
    SUMMARY_SERIALIZER = serializers.ExpandedDataNodeSerializer
    URL_SERIALIZER = serializers.DataNodeSerializer

class TaskViewSet(ExpandableViewSet):
    """A Task represents a specific combination of runtime environment, command, and inputs that describe a reproducible unit of analysis. PARAMS: ?expand will show expanded version of linked objects (not allowed in index view). ?summary will show a summary version (not allowed in index view). ?url will show only the url and uuid fields (for testing only).
    """
    lookup_field = 'uuid'

    DEFAULT_SERIALIZER = serializers.TaskSerializer
    EXPANDED_SERIALIZER = serializers.ExpandedTaskSerializer
    SUMMARY_SERIALIZER = serializers.SummaryTaskSerializer
    URL_SERIALIZER = serializers.URLTaskSerializer


class TaskAttemptViewSet(ExpandableViewSet):
    """A TaskAttempt represents a single attempt at executing a Task. A Task may have multiple TaskAttempts due to retries. PARAMS: ?expand will show expanded version of linked objects (not allowed in index view). ?summary will show a summary version (not allowed in index view). ?url will show only the url and uuid fields (for testing only). DETAIL_ROUTES: "fail" will set a run to failed status. "finish" will set a run to finished status. "log-files" can be used to POST a new LogFile. "events" can be used to POST a new event. "settings" can be used to get settings for loom-task-monitor.
    """
    lookup_field = 'uuid'

    DEFAULT_SERIALIZER = serializers.TaskAttemptSerializer
    EXPANDED_SERIALIZER = serializers.TaskAttemptSerializer
    SUMMARY_SERIALIZER = serializers.URLTaskAttemptSerializer
    URL_SERIALIZER = serializers.URLTaskAttemptSerializer

    def _get_task_attempt(self, request, uuid):
        try:
            return models.TaskAttempt.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise rest_framework.exceptions.NotFound()

    @detail_route(methods=['post'], url_path='log-files',
                  serializer_class=serializers.TaskAttemptLogFileSerializer)
    def create_log_file(self, request, uuid=None):
        data_json = request.body
        data = json.loads(data_json)
        task_attempt = self._get_task_attempt(request, uuid)
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

    @detail_route(methods=['post'], url_path='system-error',
                  # Use base serializer since request has no data. Used by API doc.
                  serializer_class=rest_framework.serializers.Serializer)
    def system_error(self, request, uuid):
        task_attempt = self._get_task_attempt(request, uuid)
        task_attempt.system_error()
        return JsonResponse({}, status=201)

    @detail_route(methods=['post'], url_path='analysis-error',
                  # Use base serializer since request has no data. Used by API doc.
                  serializer_class=rest_framework.serializers.Serializer)
    def analysis_error(self, request, uuid):
        task_attempt = self._get_task_attempt(request, uuid)
        task_attempt.analysis_error()
        return JsonResponse({}, status=201)

    @detail_route(methods=['post'], url_path='finish',
                  serializer_class=rest_framework.serializers.Serializer)
    def finish(self, request, uuid=None):
        task_attempt = self._get_task_attempt(request, uuid)
        async.finish_task_attempt(task_attempt.uuid)
        return JsonResponse({}, status=201)

    @detail_route(methods=['post'], url_path='events',
                  serializer_class=serializers.TaskAttemptEventSerializer)
    def create_event(self, request, uuid=None):
        data_json = request.body
        data = json.loads(data_json)
        task_attempt = self._get_task_attempt(request, uuid)
        s = serializers.TaskAttemptEventSerializer(
            data=data,
            context={
                'parent_field': 'task_attempt',
                'parent_instance': task_attempt,
                'request': request
            })
        s.is_valid(raise_exception=True)
        model = s.save()

        return JsonResponse(s.data, status=201)

    @detail_route(methods=['get'], url_path='settings')
    def get_task_monitor_settings(self, request, uuid=None):
        task_attempt = self._get_task_attempt(request, uuid)
        return JsonResponse({
            'SERVER_NAME': get_setting('SERVER_NAME'),
            'DEBUG': get_setting('DEBUG'),
            'WORKING_DIR': task_attempt.get_working_dir(),
            'STDOUT_LOG_FILE': task_attempt.get_stdout_log_file(),
            'STDERR_LOG_FILE': task_attempt.get_stderr_log_file(),
            'DEFAULT_DOCKER_REGISTRY': get_setting('DEFAULT_DOCKER_REGISTRY'),
            'PRESERVE_ALL': get_setting('PRESERVE_ON_FAILURE'),
            'PRESERVE_ON_FAILURE': get_setting('PRESERVE_ON_FAILURE'),
            'HEARTBEAT_INTERVAL_SECONDS':
            get_setting('TASKRUNNER_HEARTBEAT_INTERVAL_SECONDS'),
        }, status=200)


class TemplateViewSet(ExpandableViewSet):
    """A Template is a pattern for analysis to be performed, but without assigned inputs. Templates can be nested under the 'steps' field. Only leaf nodes contain command, interpreter, resources, and environment. PARAMS: ?expand will show expanded version of linked objects to the full nested depth (not allowed in index view). ?summary will show a summary version to full nested depth (not allowed in index view). ?url will show only the url and uuid fields (for testing only).
    """
    lookup_field = 'uuid'

    DEFAULT_SERIALIZER = serializers.TemplateSerializer
    EXPANDED_SERIALIZER = serializers.TemplateSerializer
    SUMMARY_SERIALIZER = serializers.SummaryTemplateSerializer
    URL_SERIALIZER = serializers.URLTemplateSerializer

    def get_queryset(self):
        query_string = self.request.query_params.get('q', '')
        imported = 'imported' in self.request.query_params
        labels = self.request.query_params.get('labels', '')
        Serializer = self.get_serializer_class()
        if query_string:
            queryset = models.Template.filter_by_name_or_id_or_tag_or_hash(query_string)
        else:
            queryset = models.Template.objects.all()
        if imported:
            queryset = queryset.exclude(imported=False)
        if labels:
            for label in labels.split(','):
                queryset = queryset.filter(labels__label=label)
        queryset = Serializer.apply_prefetch(queryset)
        return queryset.order_by('-datetime_created')

    @detail_route(methods=['post'], url_path='add-tag',
                  serializer_class=serializers.TemplateTagSerializer)
    def add_tag(self, request, uuid=None):
        data_json = request.body
        data = json.loads(data_json)
        try:
            template = models.Template.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise rest_framework.exceptions.NotFound()
        s = serializers.TemplateTagSerializer(
            data=data, context={'template': template})
        s.is_valid(raise_exception=True)
        s.save()
        return JsonResponse(s.data, status=201)

    @detail_route(methods=['post'], url_path='remove-tag',
                  serializer_class=serializers.DataTagSerializer)
    def remove_tag(self, request, uuid=None):
        data_json = request.body
        data = json.loads(data_json)
        tag = data.get('tag')
        try:
            template = models.Template.objects.get(uuid=uuid)
            tag_instance = template.tags.get(tag=tag)
        except ObjectDoesNotExist:
            raise rest_framework.exceptions.NotFound()
        tag_instance.delete()
        return JsonResponse({
            'tag': tag,
            'message': 'Tag %s was removed from Template @%s' % (
                tag, template.uuid)},
                            status=200)

    @detail_route(methods=['get'], url_path='tags')
    def list_tags(self, request, uuid=None):
        try:
            template = models.Template.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise rest_framework.exceptions.NotFound()
        tags = []
        for tag in template.tags.all():
            tags.append(tag.tag)

        return JsonResponse({'tags': tags}, status=200)

    @detail_route(methods=['post'], url_path='add-label',
                  serializer_class=serializers.TemplateLabelSerializer)
    def add_label(self, request, uuid=None):
        data_json = request.body
        data = json.loads(data_json)
        try:
            template = models.Template.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise rest_framework.exceptions.NotFound()
        s = serializers.TemplateLabelSerializer(
            data=data, context={'template': template})
        s.is_valid(raise_exception=True)
        s.save()
        return JsonResponse(s.data, status=201)

    @detail_route(methods=['post'], url_path='remove-label',
                  serializer_class=serializers.DataLabelSerializer)
    def remove_label(self, request, uuid=None):
        data_json = request.body
        data = json.loads(data_json)
        label = data.get('label')
        try:
            template = models.Template.objects.get(uuid=uuid)
            label_instance = template.labels.get(label=label)
        except ObjectDoesNotExist:
            raise rest_framework.exceptions.NotFound()
        label_instance.delete()
        return JsonResponse({
            'label': label,
            'message': 'Label %s was removed from Template @%s' % (
                label, template.uuid)},
                            status=200)

    @detail_route(methods=['get'], url_path='labels')
    def list_labels(self, request, uuid=None):
        try:
            template = models.Template.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise rest_framework.exceptions.NotFound()
        labels = []
        for label in template.labels.all():
            labels.append(label.label)
        return JsonResponse({'labels': labels}, status=200)


class RunViewSet(ExpandableViewSet):
    """A Run represents the execution of a Template on a specific set of inputs. Runs can be nested under the 'steps' field. Only leaf nodes contain command, interpreter, resources, environment, and tasks. PARAMS: ?expand will show expanded version of linked objects to the full nested depth (not allowed in index view). ?summary will show a summary version to full nested depth (not allowed in index view). ?url will show only the url and uuid fields (for testing only).
    """

    lookup_field = 'uuid'

    DEFAULT_SERIALIZER = serializers.RunSerializer
    EXPANDED_SERIALIZER = serializers.ExpandedRunSerializer
    SUMMARY_SERIALIZER = serializers.SummaryRunSerializer
    URL_SERIALIZER = serializers.URLRunSerializer

    def get_queryset(self):
        query_string = self.request.query_params.get('q', '')
        parent_only = 'parent_only' in self.request.query_params
        labels = self.request.query_params.get('labels', '')
        Serializer = self.get_serializer_class()
        if query_string:
            queryset = models.Run.filter_by_name_or_id_or_tag(query_string)
        else:
            queryset = models.Run.objects.all()
        if parent_only:
            queryset = queryset.filter(parent__isnull=True)
        if labels:
            for label in labels.split(','):
                queryset = queryset.filter(labels__label=label)
        queryset = Serializer.apply_prefetch(queryset)
        return queryset.order_by('-datetime_created')

    @detail_route(methods=['post'], url_path='add-tag',
                  serializer_class=serializers.RunTagSerializer)
    def add_tag(self, request, uuid=None):
        data_json = request.body
        data = json.loads(data_json)
        try:
            run = models.Run.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise rest_framework.exceptions.NotFound()
        s = serializers.RunTagSerializer(
            data=data, context={'run': run})
        s.is_valid(raise_exception=True)
        s.save()
        return JsonResponse(s.data, status=201)

    @detail_route(methods=['post'], url_path='remove-tag',
                  serializer_class=serializers.DataTagSerializer)
    def remove_tag(self, request, uuid=None):
        data_json = request.body
        data = json.loads(data_json)
        tag = data.get('tag')
        try:
            run = models.Run.objects.get(uuid=uuid)
            tag_instance = run.tags.get(tag=tag)
        except ObjectDoesNotExist:
            raise rest_framework.exceptions.NotFound()
        tag_instance.delete()
        return JsonResponse({
            'tag': tag,
            'message': 'Tag %s was removed from DataObject @%s' % (
                tag, run.uuid)},
                            status=200)

    @detail_route(methods=['get'], url_path='tags')
    def list_tags(self, request, uuid=None):
        try:
            run = models.Run.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise rest_framework.exceptions.NotFound()
        tags = []
        for tag in run.tags.all():
            tags.append(tag.tag)

        return JsonResponse({'tags': tags}, status=200)

    @detail_route(methods=['post'], url_path='add-label',
                  serializer_class=serializers.RunLabelSerializer)
    def add_label(self, request, uuid=None):
        data_json = request.body
        data = json.loads(data_json)
        try:
            run = models.Run.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise rest_framework.exceptions.NotFound()
        s = serializers.RunLabelSerializer(
            data=data, context={'run': run})
        s.is_valid(raise_exception=True)
        s.save()
        return JsonResponse(s.data, status=201)

    @detail_route(methods=['post'], url_path='remove-label',
                  serializer_class=serializers.DataLabelSerializer)
    def remove_label(self, request, uuid=None):
        data_json = request.body
        data = json.loads(data_json)
        label = data.get('label')
        try:
            run = models.Run.objects.get(uuid=uuid)
            label_instance = run.labels.get(label=label)
        except ObjectDoesNotExist:
            raise rest_framework.exceptions.NotFound()
        label_instance.delete()
        return JsonResponse({
            'label': label,
            'message': 'Label %s was removed from DataObject @%s' % (
                label, run.uuid)},
                            status=200)

    @detail_route(methods=['get'], url_path='labels')
    def list_labels(self, request, uuid=None):
        try:
            run = models.Run.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise rest_framework.exceptions.NotFound()
        labels = []
        for label in run.labels.all():
            labels.append(label.label)
        return JsonResponse({'labels': labels}, status=200)


class TaskAttemptLogFileViewSet(rest_framework.viewsets.ModelViewSet):
    """LogFiles represent the logs for TaskAttempts. The same data is available in the TaskAttempt endpoint. This endpoint is to allow updating a LogFile without updating the full TaskAttempt. DETAIL_ROUTES: "data-object" allows you to post the file DataObject for the LogFile.
    """

    lookup_field = 'uuid'
    serializer_class = serializers.TaskAttemptLogFileSerializer

    def get_queryset(self):
        queryset = models.TaskAttemptLogFile.objects.all()
        queryset = queryset.select_related('data_object')\
                   .select_related('data_object__file_resource')
        return queryset.order_by('-datetime_created')

    @detail_route(methods=['post'], url_path='data-object',
                  # Use base serializer since request has no data. Used by API doc.
                  serializer_class=rest_framework.serializers.Serializer)
    def create_data_object(self, request, uuid=None):
        try:
            task_attempt_log_file = models\
                                    .TaskAttemptLogFile\
                                    .objects\
                                    .select_related('task_attempt')\
                                    .select_related('data_object')\
                                    .get(uuid=uuid)
        except ObjectDoesNotExist:
            raise rest_framework.exceptions.NotFound()
        if task_attempt_log_file.data_object:
            return JsonResponse({'message': 'Object already exists.'}, status=400)
        data_json = request.body
        data = json.loads(data_json)
        s = serializers.DataObjectSerializer(
            task_attempt_log_file.data_object, data=data, context={
                'request': request,
                'task_attempt_log_file': task_attempt_log_file,
                'task_attempt': task_attempt_log_file.task_attempt,
            })
        s.is_valid(raise_exception=True)
        data_object = s.save()
        return JsonResponse(s.data, status=201)


class TaskAttemptOutputViewSet(rest_framework.viewsets.ModelViewSet):
    """Outputs represent the outputs for TaskAttempts. The same data is available in the TaskAttempt endpoint. This endpoint is to allow updating an Output without updating the full TaskAttempt.
    """
    
    lookup_field = 'uuid'

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return serializers.TaskAttemptOutputUpdateSerializer
        else:
            return serializers.TaskAttemptOutputSerializer

    def get_queryset(self):
        return models.TaskAttemptOutput.objects.all()

class DataTagViewSet(rest_framework.viewsets.ReadOnlyModelViewSet):

    serializer_class = serializers.DataTagSerializer
    lookup_field = 'id'
    queryset = models.DataTag.objects.all()


class DataLabelViewSet(rest_framework.viewsets.ReadOnlyModelViewSet):

    serializer_class = serializers.DataLabelSerializer
    lookup_field = 'id'
    queryset = models.DataLabel.objects.all()

class TemplateTagViewSet(rest_framework.viewsets.ReadOnlyModelViewSet):

    serializer_class = serializers.TemplateTagSerializer
    lookup_field = 'id'
    queryset = models.TemplateTag.objects.all()


class TemplateLabelViewSet(rest_framework.viewsets.ReadOnlyModelViewSet):

    serializer_class = serializers.TemplateLabelSerializer
    lookup_field = 'id'
    queryset = models.TemplateLabel.objects.all()

class RunTagViewSet(rest_framework.viewsets.ReadOnlyModelViewSet):

    serializer_class = serializers.RunTagSerializer
    lookup_field = 'id'
    queryset = models.RunTag.objects.all()


class RunLabelViewSet(rest_framework.viewsets.ReadOnlyModelViewSet):

    serializer_class = serializers.RunLabelSerializer
    lookup_field = 'id'
    queryset = models.RunLabel.objects.all()

@require_http_methods(["GET"])
def status(request):
    return JsonResponse({"message": "server is up"}, status=200)



class FileManagerSettingsView(RetrieveAPIView):

    def retrieve(self, request):
        return JsonResponse({
            'GCE_PROJECT': get_setting('GCE_PROJECT'),
        })

@require_http_methods(["GET"])
def info(request):
    if request.user.is_authenticated():
        username = request.user.username
    else:
        username = None
    data = {
        'version': version.version(),
        'username': username,
        'login_required': get_setting('LOGIN_REQUIRED'),
    }
    return JsonResponse(data, status=200)

@require_http_methods(["GET"])
def auth_status(request):
    if get_setting('LOGIN_REQUIRED')==False:
        return JsonResponse({'message': 'Authentication not required'})
    elif request.user.is_authenticated():
        return JsonResponse({
            'message': 'User is authenticated as %s' % request.user.username})
    else:
        return JsonResponse({'message': 'User is not authenticated'}, status=401)

@require_http_methods(["GET"])
def raise_server_error(request):
    logger.error('Server error intentionally logged for debugging.')
    raise Exception('Server error intentionally raised for debugging')
