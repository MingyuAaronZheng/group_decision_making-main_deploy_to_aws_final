from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    # Regex version
    re_path(
        r'^ws/chat/(?P<room_name>[^/]+)/$',
        consumers.ChatConsumer.as_asgi()
    ),

    # Or, simpler with path()
    path(
        'ws/chat/<str:room_name>/',
        consumers.ChatConsumer.as_asgi()
    ),
]