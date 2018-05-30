from rest_framework import serializers

from drf_channels.bindings import ResourceBinding
from .consumers import SampleModelConsumer
from .models import SampleModel


class SampleModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SampleModel
        fields = ('id', 'name', )


class SampleModelResourceBinding(ResourceBinding):
    model = SampleModel
    serializer_class = SampleModelSerializer
    consumer = SampleModelConsumer
