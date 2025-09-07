from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/ride/(?P<passenger_id>\d+)/$', consumers.RideConsumer.as_asgi()),
]
