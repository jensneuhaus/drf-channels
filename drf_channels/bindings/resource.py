import six

from channels.layers import get_channel_layer

from ..mixins import SerializerMixin
from ..utils import get_group_name
from .base import (
    ACTION_CREATE,
    ACTION_DELETE,
    ACTION_UPDATE,
    Binding,
)


class ResourceBinding(SerializerMixin, Binding):
    # the kwargs the triggering signal (e.g. post_save) was emitted with
    signal_kwargs = None

    # mark as abstract
    model = None
    serializer_class = None

    @classmethod
    def pre_change_receiver(cls, instance, action):
        """
        Entry point for triggering the binding from save signals.
        """
        if action == ACTION_CREATE:
            group_names = set()
        else:
            group_names = set(cls.group_names(instance, action))

        if not hasattr(instance, '_binding_group_names'):
            instance._binding_group_names = {}
        instance._binding_group_names[cls] = group_names

    @classmethod
    def post_change_receiver(cls, instance, action, **kwargs):
        """
        Triggers the binding to possibly send to its group.
        """
        channel_layer = get_channel_layer()

        old_group_names = instance._binding_group_names[cls]
        if action == ACTION_DELETE:
            new_group_names = set()
        else:
            new_group_names = set(cls.group_names(instance, action))

        # if post delete, new_group_names should be []
        self = cls()
        self.instance = instance

        # Django DDP had used the ordering of ACTION_DELETE, ACTION_UPDATE then ACTION_CREATE for good reasons.
        self.send_messages(channel_layer, instance, old_group_names - new_group_names, ACTION_DELETE, **kwargs)
        self.send_messages(channel_layer, instance, old_group_names & new_group_names, ACTION_UPDATE, **kwargs)
        self.send_messages(channel_layer, instance, new_group_names - old_group_names, ACTION_CREATE, **kwargs)

    @classmethod
    def group_names(cls, instance, action):
        self = cls()
        groups = [get_group_name(self.model_label, action)]
        if instance.pk:
            groups.append(get_group_name(self.model_label, action, id=instance.pk))
        return groups

    def _format_errors(self, errors):
        if isinstance(errors, list):
            return errors
        elif isinstance(errors, six.string_types):
            return [errors]
        elif isinstance(errors, dict):
            return [errors]

    def serialize(self, instance, action):
        payload = {
            'action': action,
            'pk': instance.pk,
            'data': self.serialize_data(instance),
            'model': self.model_label,
        }
        return payload
