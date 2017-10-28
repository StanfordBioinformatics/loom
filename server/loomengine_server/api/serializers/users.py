from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import IntegrityError

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'is_staff', 'password')

    password = serializers.CharField(write_only=True, required=True)
    username = serializers.CharField(required=True)
    is_staff = serializers.BooleanField(required=False)
    id = serializers.IntegerField(read_only=True)

    def create(self, validated_data):
        password = validated_data.get('password')
        username = validated_data.get('username')
        is_staff = validated_data.get('is_staff', False)

        try:
            u = User.objects.create_user(username,'',password)
        except IntegrityError:
            raise serializers.ValidationError(
                'The username "%s" is not available.' % username)
        if is_staff:
            u.is_staff = True
            u.save()
        return u

    def update(self, instance, validated_data):
        if validated_data.get('is_staff'):
            instance.is_staff = validated_data.get('is_staff')

        if validated_data.get('password'):
            instance.set_password(validated_data.get('password'))

        return instance
