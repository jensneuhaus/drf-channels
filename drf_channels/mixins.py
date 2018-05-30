import six

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

    async def group_names(self, data):
        groups = []
        actions = data['action']
        if isinstance(actions, six.string_types):
            actions = [actions]

        instance_id = data.get('id')
        for action in actions:
            if instance_id is not None:
                group_name = get_group_name(self.model_label, action, instance_id)
            else:
                group_name = get_group_name(self.model_label, action)

            if group_name not in groups:
                groups.append(group_name)

        return groups

    async def receive_json(self, content):
        if 'action' not in content:
            raise ValidationError('action required')

        request_type = content['action']
        if request_type == self.ACTION_SUBSCRIBE:
            await self.subscribe(content)

    async def subscribe(self, content):
        data = content['data']
        if 'action' not in data:
            raise ValidationError('action required')

        for group_name in await self.group_names(data):
            await self.add_group(group_name)

        content.update({
            'response_status': 200,
            'errors': [],
        })
        await self.send_json(content)

    async def add_group(self, group_name):
        await self.channel_layer.group_add(
            group_name,
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
