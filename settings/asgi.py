# """
# ASGI config for settings project.

# It exposes the ASGI callable as a module-level variable named ``application``.

# For more information on this file, see
# https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
# """

# import os

# from django.core.asgi import get_asgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')

# application = get_asgi_application()


"""
ASGI config for settings project.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import taxi.routing  # routing des WebSockets pour taxi/rides

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')

# application ASGI pour HTTP + WebSocket
application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # les requêtes HTTP classiques
    "websocket": AuthMiddlewareStack(  # authentification pour WebSocket
        URLRouter(
            taxi.routing.websocket_urlpatterns  # tes routes websocket
        )
    ),
})
