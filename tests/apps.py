from django.apps import AppConfig


class TestsConfig(AppConfig):

    name = 'tests'
    verbose_name = 'tests'

    def ready(self):
        from .bindings import SampleModelResourceBinding
        SampleModelResourceBinding.register_all()
