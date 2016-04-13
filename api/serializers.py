from rest_framework import serializers
from api.models import *

class SampleCountField(serializers.RelatedField):
    def to_representation(self, value):
        return value.samplecount

class QuerySerializer(serializers.ModelSerializer):

    user = serializers.SlugRelatedField(
       read_only=True,
       slug_field='username'
    )
    
    project = serializers.SlugRelatedField(
       read_only=True,
       slug_field='name'
    )

    samplecount = SampleCountField() 

    class Meta:
        model = Query
        fields = ('user', 'project', 'name', 'description', 'samplecount', 'share')
