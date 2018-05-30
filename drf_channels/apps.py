from django.apps import AppConfig

from .bindings import BindingMetaclass


class DrfChannelsConfig(AppConfig):
    name = 'drf_channels'

    def ready(self):
        BindingMetaclass.register_all()
