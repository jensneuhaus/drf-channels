from django.db import models


class SampleModel(models.Model):
    """ Simple model to test with. """

    name = models.CharField(max_length=255)
