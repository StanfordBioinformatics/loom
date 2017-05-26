from rest_framework import serializers
from api.models.process import *


class ProcessSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Process
        """
        fields = ('uuid', 'url', 'datetime_created', 'datetime_finished',
                  'status_is_finished', 'status_is_failed', 'status_is_waiting',
                  'status_is_killed', 'status_is_running', 'status_is_cleaned_up',
                  'status',)
        """
