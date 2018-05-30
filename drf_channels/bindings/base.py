import six

from django.apps import apps
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save

from asgiref.sync import async_to_sync

ACTION_CREATE = 'create'
ACTION_UPDATE = 'update'
ACTION_DELETE = 'delete'


class BindingMetaclass(type):
    """
    Metaclass that tracks instantiations of its type.
    """
    register_immediately = False
    binding_classes = []

    def __new__(cls, name, bases, body):
        klass = type.__new__(cls, name, bases, body)
        if bases != (object, ):
            cls.binding_classes.append(klass)
            if cls.register_immediately:
                klass.register()
        return klass

    @classmethod
    def register_all(cls):
        for binding_class in cls.binding_classes:
            binding_class.register()
        cls.register_immediately = True


@six.add_metaclass(BindingMetaclass)
class Binding(object):
    model = None

    # the kwargs the triggering signal (e.g. post_save) was emitted with
    signal_kwargs = None

    @classmethod
    def register(cls):
        """
        Resolves models.
        """
        # Connect signals
        for model in cls.get_registered_models():
            pre_save.connect(cls.pre_save_receiver, sender=model)
            post_save.connect(cls.post_save_receiver, sender=model)
            pre_delete.connect(cls.pre_delete_receiver, sender=model)
            post_delete.connect(cls.post_delete_receiver, sender=model)

    @classmethod
    def get_registered_models(cls):
        """
        Resolves the class model attribute if it's a string and returns it.
        """
        # If model is None directly on the class, assume it's abstract.
        if cls.model is None:
            if 'model' in cls.__dict__:
                return []
            else:
                raise ValueError('You must set the model attribute on Binding %r!' % cls)
        # Optionally resolve model strings
        if isinstance(cls.model, six.string_types):
            cls.model = apps.get_model(cls.model)
        cls.model_label = '%s.%s' % (
            cls.model._meta.app_label.lower(),
            cls.model._meta.object_name.lower(),
        )
        return [cls.model]

    @classmethod
    def pre_save_receiver(cls, instance, **kwargs):
        creating = instance._state.adding
        cls.pre_change_receiver(instance, ACTION_CREATE if creating else ACTION_UPDATE)

    @classmethod
    def post_save_receiver(cls, instance, created, **kwargs):
        cls.post_change_receiver(instance, ACTION_CREATE if created else ACTION_UPDATE, **kwargs)

    @classmethod
    def pre_delete_receiver(cls, instance, **kwargs):
        cls.pre_change_receiver(instance, ACTION_DELETE)

    @classmethod
    def post_delete_receiver(cls, instance, **kwargs):
        cls.post_change_receiver(instance, ACTION_DELETE, **kwargs)

    def get_stream_type(self):
        """
        Returns the type of stream from consumer
        """
        return '{}_broadcast'.format(self.model._meta.object_name.lower())

    def send_messages(self, channel_layer, instance, group_names, action, **kwargs):
        """
        Serializes the instance and sends it to all provided group names.
        """
        if not group_names:
            return  # no need to serialize, bail.
        self.signal_kwargs = kwargs

        payload = self.serialize(instance, action)
        if payload == {}:
            return  # nothing to send, bail.

        for group_name in group_names:
            async_to_sync(channel_layer.group_send)(group_name, {
                'type': self.get_stream_type(),
                'message': payload,
            })
