import copy
from rest_framework import serializers
import re

from .base import SuperclassModelSerializer, CreateWithParentModelSerializer, NoUpdateModelSerializer
from api.models.channels import IndexedDataObject
from api.models.run_requests import *
from api.models.workflows import AbstractWorkflow
from api.serializers.workflows import AbstractWorkflowIdSerializer
from api.serializers.workflow_runs import AbstractWorkflowRunSerializer


class RunRequestInputSerializer(CreateWithParentModelSerializer):

    value = serializers.CharField() #converted from IndexedDataObjects

    class Meta:
        model = RunRequestInput
        fields = ('channel', 'value',)

    def create(self, validated_data):
        data = copy.deepcopy(validated_data)

        # Convert 'value' into its corresponding data object
        value = data.pop('value')
        data_object = DataObject.get_by_value(
            value,
            self.context['data_type'])

        run_request_input = super(RunRequestInputSerializer, self).create(data)

        # TODO: for each (index, data_object)
        IndexedDataObject.objects.create(
            data_object=data_object,
            input_output_node = run_request_input)

        return run_request_input

    '''
    def parse_string_to_nested_lists(self, value):
        """e.g., convert "[[a,b,c],[d,e],[f,g]]" 
        into [["a","b","c"],["d","e"],["f","g"]]
        """
        if not re.match('\[.*\]', value.strip()):
            if '[' in value or ']' in value or ',' in value:
                raise Exception('Missing outer brace')
            elif len(value.strip()) == 0:
                raise Exception('Missing value')
            else:
                terms = value.split(',')
                if len(terms) == 1:
                    return terms[0]
                else:
                    return terms
                
        # remove outer braces
        value = value[1:-1]

        terms = []
        depth = 0
        leftmost = 0
        first_open_brace = None
        break_on_commas = False
        for i in range(len(value)):
            if value[i] == ',' and depth == 0:
                terms.append(
                    self.parse_string_to_nested_lists(value[leftmost:i]))
                leftmost = i+1
            if value[i] == '[':
                if first_open_brace is None:
                    first_open_brace = i
                depth += 1
            if value[i] == ']':
                depth -= 1
                if depth < 0:
                    raise Exception('Unbalanced close brace')
            i += i
        if depth > 0:
            raise Exception('Expected "]"')
        terms.append(
            self.parse_string_to_nested_lists(value[leftmost:len(value)]))
        return terms

    def create_data_objects(data_object_values, index_list):
        index_list = copy.deepcopy(index_list)
        if not isinstance(data_object_values, list):
            self.create_data_object(data_object_values, index_list)
        for i in len(data_object_values):
            index_list_i = copy.deepcopy(index_list)
            index_list_i.append(i)
            self.create_data_objects(data_object_values[i],index_list_i)

    def create_data_object(data_object_value, index_list):
        # TODO
        pass
    '''

class CancelRequestSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = CancelRequest


class RestartRequestSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = RestartRequest


class FailureNoticeSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = FailureNotice


class RunRequestSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    name = serializers.CharField(required=False, read_only=True)
    inputs = RunRequestInputSerializer(many=True, required=False)
    template = AbstractWorkflowIdSerializer()
    run = AbstractWorkflowRunSerializer(required=False)

    class Meta:
        model = RunRequest
        fields = ('id',
                  'name',
                  'template',
                  'inputs',
                  'datetime_created',
                  'run',)

    def create(self, validated_data):
        data = copy.deepcopy(validated_data)
        
        inputs = self.initial_data.get('inputs', None)
        data.pop('inputs', None)

        # convert 'template' name@id into its corresponding object
        s = AbstractWorkflowIdSerializer(data=data.pop('template'))
        s.is_valid()
        workflow = s.save()
        data['template'] = workflow

        #run_serializer = AbstractWorkflowRunSerializer(
        #    data=self.initial_data.get('run', None))
        #run_serializer.is_valid()
        #data['run'] = run_serializer.save()

        run_request = RunRequest.objects.create(**data)

        if inputs is not None:
            for input_data in inputs:
                # We need to know the data type to find or create the
                # data object from the value given. Get that from the
                # corresponding workflow input.
                data_type = workflow.get_input(input_data['channel']).type
                s = RunRequestInputSerializer(
                    data=input_data,
                    context={'parent_field': 'run_request',
                             'parent_instance': run_request,
                             'data_type': data_type,
                    })
                s.is_valid(raise_exception=True)
                s.save()

        run_request.post_create()

        return run_request
