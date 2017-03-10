.. _middleware:

Middleware
==========

Middleware components provide a way to execute logic before the framework routes each request, after each request is routed but before the response. Middleware is registered by the settings.cfg file. You need to ensure you import your application then you can specify middleware classes to be loaded located in the application views.py

The middleware is executed within the order defined in the settings.cfg configuration.

There are two methods you can can define for middleware *'pre'* and *'post'*. *'pre'* being before the request is routed and *'post'* being after.

Middleware Example Component

.. code:: python

    class Login(object):
        def __init__(self, app):
            pass

        def pre(self, req, resp):
            pass

    class Counter(object):
        def __init__(self, app):
            pass

        def post(self, req, resp):
            pass

