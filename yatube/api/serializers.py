from rest_framework import serializers
from posts.models import Group


class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = ('title', 'description')


class GroupDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = '__all__'