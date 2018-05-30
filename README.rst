DRF Channels
------------

.. image:: https://travis-ci.org/iamriel/drf-channels.svg?branch=master
    :target: https://travis-ci.org/iamriel/drf-channels

DRF Channels provides a simple django-channels bindings and consumer
mixin that can be used to automatically listen and send to groups
everytime a Resource is created/updated/deleted.

It requires Python >= 3.5, Channels >= 2.0, Django >=1.11, and Django Rest Framework 3.x

This is like a port of Channels 1.x's `Data_Binding <https://channels.readthedocs.io/en/1.x/binding.html>`__
and `Channels API <https://github.com/linuxlewis/channels-api/blob/master/README.rst>`__
with few differences.

The data sent to the clients are based on the Serializer class
provided.


How does it work?
-----------------

The API exposes a ``ResourceBinding`` class that holds your Model, Serializer class, and Consumer class.
Your Consumer class needs to be a subclass of ``AsyncJsonWebsocketConsumer`` from channels and
have a ``AsyncConsumerActionMixin`` mixin.

The ``ResourceBinding`` class binds ``pre_save``, ``pre_delete``, ``post_save``, and ``post_delete`` signals
to your model.  These signals will then send to the corresponding Consumer groups that listens to your stream.

The first thing you need to do is connect to your consumer and pass the actions you want to subscribe to
via url parameters.

For example, you want to subscribe to the create and update actions ``Job`` Resource (Model),
and the channels route is `/jobs/`, You will connect to the websocket like below,
if you are using `Channels Websocket Wrapper <https://channels.readthedocs.io/en/latest/javascript.html>`__:

.. code:: javascript

   const webSocketBridge = new channels.WebSocketBridge()
   webSocketBridge.connect('/jobs/?subscribe=create,update')


You then need to add a listener on your webSocketBridge to receive the messages sent by the Consumer
via signals.

.. code:: javascript

   webSocketBridge.socket.addEventListener('message', function(event) {
       
   })
