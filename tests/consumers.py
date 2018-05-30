from channels.generic.websocket import AsyncJsonWebsocketConsumer

from drf_channels.mixins import AsyncConsumerActionMixin
from .models import SampleModel


class SampleModelConsumer(AsyncConsumerActionMixin, AsyncJsonWebsocketConsumer):
    model = SampleModel

    async def testmodel_broadcast(self, event):
        await self.send_json(event)
