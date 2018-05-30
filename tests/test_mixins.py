import pytest

from django.test.utils import override_settings

from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator

from .bindings import (
    SampleModelSerializer,
    SampleModelResourceBinding,
)
from .models import SampleModel


class SimpleWebsocketApp(SampleModelResourceBinding.consumer):
    """
    Barebones WebSocket ASGI app for testing.
    """
    async def connect(self):
        assert self.scope['path'] == '/testws/'
        await self.accept()


@pytest.mark.asyncio
async def setup_communicator():
    communicator = WebsocketCommunicator(SimpleWebsocketApp, '/testws/')
    connected, subprotocol = await communicator.connect()
    assert connected
    return communicator


@database_sync_to_async
def create_test_model():
    return SampleModel.objects.create(name='wew')


@database_sync_to_async
def update_test_model(instance):
    instance.name = 'newname'
    instance.save()
    return instance


@database_sync_to_async
def delete_test_model(instance):
    instance.delete()


def get_serialized_data(instance):
    return SampleModelSerializer(instance).data


@pytest.mark.asyncio
async def test_action_subscribe():
    """
    Verifies that a message is sent to channel when the model is created
    """
    communicator = await setup_communicator()

    payload = {
        'action': 'subscribe',
        'data': {
            'action': 'create',
        },
    }
    await communicator.send_json_to(payload)
    event = await communicator.receive_json_from()
    assert event['action'] == 'subscribe'
    await communicator.disconnect()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_create_binding():
    """
    Verifies that a message is sent to channel when the model is created
    """
    communicator = await setup_communicator()

    payload = {
        'action': 'subscribe',
        'data': {
            'action': 'create',
        },
    }
    await communicator.send_json_to(payload)
    event = await communicator.receive_json_from()

    instance = await create_test_model()
    event = await communicator.receive_json_from()
    assert event['type'] == 'testmodel_broadcast'
    assert event['message']['action'] == 'create'
    assert event['message']['data'] == get_serialized_data(instance)
    await communicator.disconnect()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_update_binding():
    """
    Verifies that a message is sent to channel when the model is updated
    """
    instance = await create_test_model()

    communicator = await setup_communicator()

    payload = {
        'action': 'subscribe',
        'data': {
            'action': 'update',
        },
    }
    await communicator.send_json_to(payload)
    event = await communicator.receive_json_from()

    updated_instance = await update_test_model(instance)
    updated_instance_data = get_serialized_data(updated_instance)
    assert updated_instance_data['name'] == 'newname'

    event = await communicator.receive_json_from()
    assert event['type'] == 'testmodel_broadcast'
    assert event['message']['action'] == 'update'
    assert event['message']['data'] == updated_instance_data
    await communicator.disconnect()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_delete_binding():
    """
    Verifies that a message is sent to channel when the model is deleted
    """
    instance = await create_test_model()
    instance_data = get_serialized_data(instance)

    communicator = await setup_communicator()

    payload = {
        'action': 'subscribe',
        'data': {
            'action': 'delete',
        },
    }
    await communicator.send_json_to(payload)
    event = await communicator.receive_json_from()

    await delete_test_model(instance)
    event = await communicator.receive_json_from()

    assert event['type'] == 'testmodel_broadcast'
    assert event['message']['action'] == 'delete'
    assert event['message']['data'] == instance_data
    await communicator.disconnect()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_update_with_id_binding():
    """
    Verifies that message is only sent to the correct
    subscriber with `id`
    """
    instance = await create_test_model()
    instance2 = await create_test_model()

    communicator = await setup_communicator()
    communicator2 = await setup_communicator()

    payload = {
        'action': 'subscribe',
        'data': {
            'action': 'update',
            'id': instance.id,
        },
    }

    payload2 = {
        'action': 'subscribe',
        'data': {
            'action': 'update',
            'id': instance2.id,
        },
    }

    await communicator.send_json_to(payload)
    await communicator.receive_json_from()

    await communicator2.send_json_to(payload2)
    await communicator2.receive_json_from()

    await update_test_model(instance)

    event = await communicator.receive_json_from()
    assert event['message']['action'] == 'update'
    # communicator2 shoud not receive a message
    with pytest.raises(Exception):
        await communicator2.receive_json_from()

    await communicator.disconnect()
    await communicator2.disconnect()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_delete_with_id_binding():
    """
    Verifies that message is only sent to the correct
    subscriber with `id`
    """
    instance = await create_test_model()
    instance2 = await create_test_model()

    communicator = await setup_communicator()
    communicator2 = await setup_communicator()

    payload = {
        'action': 'subscribe',
        'data': {
            'action': 'delete',
            'id': instance.id,
        },
    }

    payload2 = {
        'action': 'subscribe',
        'data': {
            'action': 'delete',
            'id': instance2.id,
        },
    }

    await communicator.send_json_to(payload)
    await communicator.receive_json_from()

    await communicator2.send_json_to(payload2)
    await communicator2.receive_json_from()

    await delete_test_model(instance)

    event = await communicator.receive_json_from()
    assert event['message']['action'] == 'delete'
    # communicator2 shoud not receive a message
    with pytest.raises(Exception):
        await communicator2.receive_json_from()

    await communicator.disconnect()
    await communicator2.disconnect()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_multiple_actions_binding():
    """
    Verifies that multiple subscribe actions work
    """
    communicator = await setup_communicator()

    payload = {
        'action': 'subscribe',
        'data': {
            'action': ['create', 'update', 'delete'],
        },
    }

    await communicator.send_json_to(payload)
    await communicator.receive_json_from()

    instance = await create_test_model()
    event = await communicator.receive_json_from()
    assert event['message']['action'] == 'create'

    await update_test_model(instance)
    event = await communicator.receive_json_from()
    assert event['message']['action'] == 'update'

    await delete_test_model(instance)
    event = await communicator.receive_json_from()
    assert event['message']['action'] == 'delete'

    await communicator.disconnect()
