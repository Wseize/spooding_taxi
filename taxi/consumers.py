import json
from channels.generic.websocket import AsyncWebsocketConsumer

class RideConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # room name = passenger_id
        self.room_name = self.scope['url_route']['kwargs']['passenger_id']
        self.room_group_name = f'ride_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from group
    async def ride_notification(self, event):
        await self.send(text_data=json.dumps(event["message"]))
