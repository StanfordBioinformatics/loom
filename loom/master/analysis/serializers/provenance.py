from rest_framework import serializers

from analysis.models.data_objects import *
from .data_objects import FileDataObjectSerializer
from .task_runs import TaskRunAttemptSerializer

class FileProvenanceSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)

    class Meta:
        model = FileDataObject

    def to_representation(self, obj):
        fileset, taskset, edgeset = obj.get_provenance_data()
        
        files = []
        tasks = []
        edges = list(edgeset)
        
        for model in fileset:
            s = FileDataObjectSerializer(model)
            files.append(s.data)

        for model in taskset:
            s = TaskRunAttemptSerializer(model)
            tasks.append(s.data)

        return {
            'provenance': {
                'files': files,
                'tasks': tasks,
                'edges': edges
            }
        }
