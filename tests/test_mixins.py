from urllib.parse import urlencode

import pytest

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
    pass


@pytest.mark.asyncio
async def setup_communicator(payload):
    communicator = WebsocketCommunicator(
        SimpleWebsocketApp,
        '/samplemodels/?{}'.format(urlencode(payload))
    )
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


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_create_binding():
    """
    Verifies that a message is sent to channel when the model is created
    """
    payload = {
        'subscribe': 'create',
    }
    communicator = await setup_communicator(payload)

    instance = await create_test_model()
    event = await communicator.receive_json_from()
    assert event['type'] == 'samplemodel_broadcast'
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

    payload = {
        'subscribe': 'update',
    }
    communicator = await setup_communicator(payload)

    updated_instance = await update_test_model(instance)
    updated_instance_data = get_serialized_data(updated_instance)
    assert updated_instance_data['name'] == 'newname'

    event = await communicator.receive_json_from()
    assert event['type'] == 'samplemodel_broadcast'
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

    payload = {
        'subscribe': 'delete',
    }
    communicator = await setup_communicator(payload)

    await delete_test_model(instance)
    event = await communicator.receive_json_from()

    assert event['type'] == 'samplemodel_broadcast'
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

    payload = {
        'subscribe': 'update',
        'id': instance.id
    }
    communicator = await setup_communicator(payload)

    payload2 = {
        'subscribe': 'update',
        'id': instance2.id
    }
    communicator2 = await setup_communicator(payload2)

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

    payload = {
        'subscribe': 'delete',
        'id': instance.id
    }
    communicator = await setup_communicator(payload)

    payload2 = {
        'subscribe': 'delete',
        'id': instance2.id
    }
    communicator2 = await setup_communicator(payload2)

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
    payload = {
        'subscribe': 'create,update,delete'
    }
    communicator = await setup_communicator(payload)

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
