# import json
# from channels.generic.websocket import AsyncWebsocketConsumer

# class RideConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         # room name = passenger_id
#         self.room_name = self.scope['url_route']['kwargs']['passenger_id']
#         self.room_group_name = f'ride_{self.room_name}'

#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )
#         await self.accept()

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_name
#         )

#     # Receive message from group
#     async def ride_notification(self, event):
#         await self.send(text_data=json.dumps(event["message"]))



# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

# ---------------- NotificationsConsumer ----------------
class NotificationsConsumer(AsyncWebsocketConsumer):
    """
    اتصال عام لكل user يربط على مجموعة خاصة به:
    group name: user_<user_id>
    السيرفر ينجم يبعث إشعارات خاصة بكل user بواسطة group_send.
    """
    async def connect(self):
        user = self.scope.get("user")
        if user and user.is_authenticated:
            self.user_id = str(user.id)
            self.group_name = f"user_{self.user_id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            # رفض الاتصال لو مش متوثق
            await self.close(code=4001)

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # نجم تستخدمه لو حبيت client يبعت أحداث للnotifications channel
        # لكن عادة السيرفر هو اللي يبعث
        pass

    async def notification_message(self, event):
        # Event shape: {"type":"notification_message","message":{...}}
        await self.send(text_data=json.dumps(event["message"]))


# ---------------- RideConsumer ----------------
class RideConsumer(AsyncWebsocketConsumer):
    """
    Room per ride: /ws/ride/<ride_id>/
    Group name: ride_<ride_id>
    يستعمل للتراكينغ، شات، و status updates داخل الرحلة
    """
    async def connect(self):
        self.ride_id = self.scope["url_route"]["kwargs"].get("ride_id")
        if not self.ride_id:
            await self.close()
            return
        self.group_name = f"ride_{self.ride_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """
        Messages from client -> عادة يحتوي على {action: 'location'|'chat'|'status', data: {...}}
        نبعثو للـ group باش الكل يسمع (client + driver)
        """
        try:
            payload = json.loads(text_data)
        except Exception:
            return

        action = payload.get("action")
        data = payload.get("data", {})

        # broadcast to group so both driver and passenger get it
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "ride_event",
                "message": {
                    "action": action,
                    "data": data
                }
            }
        )

    async def ride_event(self, event):
        await self.send(text_data=json.dumps(event["message"]))


# ---------------- DriverConsumer ----------------
class DriverConsumer(AsyncWebsocketConsumer):
    """
    /ws/driver/<driver_id>/
    Group name: driver_<driver_id>
    يستخدم لعرض موقع التاكسيات للكل (أو لكل client محدد لو حبّ).
    """
    async def connect(self):
        self.driver_id = self.scope["url_route"]["kwargs"].get("driver_id")
        if not self.driver_id:
            await self.close()
            return
        self.group_name = f"driver_{self.driver_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # لو السائق يبعث موقعه عبر الـ websocket (بدل POST)، نستلمو ونعمل broadcast
        try:
            payload = json.loads(text_data)
        except Exception:
            return

        # نتوقع payload = {"action":"location","data":{"lat":..,"lng":..}}
        action = payload.get("action")
        data = payload.get("data", {})

        if action == "location":
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "driver_location",
                    "message": {
                        "driver_id": self.driver_id,
                        "lat": data.get("lat"),
                        "lng": data.get("lng"),
                        "ts": payload.get("ts")  # optional timestamp
                    }
                }
            )

    async def driver_location(self, event):
        await self.send(text_data=json.dumps(event["message"]))
