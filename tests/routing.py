from django.conf.urls import url
from channels.routing import URLRouter

from .bindings import SampleModelResourceBinding

application = URLRouter([
    url(r'testmodels/$', SampleModelResourceBinding.consumer),
])
