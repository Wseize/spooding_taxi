# from django.urls import re_path
# from . import consumers

# websocket_urlpatterns = [
#     re_path(r'ws/ride/(?P<passenger_id>\d+)/$', consumers.RideConsumer.as_asgi()),
# ]


# routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/notifications/$', consumers.NotificationsConsumer.as_asgi()),
    re_path(r'ws/ride/(?P<ride_id>\d+)/$', consumers.RideConsumer.as_asgi()),
    re_path(r'ws/driver/(?P<driver_id>\d+)/$', consumers.DriverConsumer.as_asgi()),
]
