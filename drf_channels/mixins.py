from urllib.parse import parse_qsl

from rest_framework.exceptions import ValidationError

from .utils import get_group_name


class AsyncConsumerActionMixin(object):
    """
    Mixin class for channels Consumer that adds groups
    based on action and model
    """
    ACTION_SUBSCRIBE = 'subscribe'
    model = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.model is None:
            raise ValidationError('model is required')

        self.model_label = '%s.%s' % (
            self.model._meta.app_label.lower(),
            self.model._meta.object_name.lower(),
        )

    async def connect(self):
        query = dict(parse_qsl(self.scope['query_string'].decode('utf-8')))
        if 'subscribe' in query:
            await self.set_groups(
                query['subscribe'].split(','),
                query.get('id')
            )

        await self.accept()

    async def set_groups(self, actions, id):
        for action in actions:
            await self.channel_layer.group_add(
                get_group_name(self.model_label, action, id),
                self.channel_name
            )


class SerializerMixin(object):
    """
    Mixin class that handles the loading of the serializer class,
    context and object.
    """
    serializer_class = None

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self):
        assert self.serializer_class is not None, (
            "'%s' should either include a `serializer_class` attribute, "
            "or override the `get_serializer_class()` method."
            % self.__class__.__name__
        )
        return self.serializer_class

    def get_serializer_context(self):
        return {}

    def serialize_data(self, instance):
        return self.get_serializer(instance).data
