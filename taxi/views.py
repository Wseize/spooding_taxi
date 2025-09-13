from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from math import radians, sin, cos, sqrt, atan2
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import time

from .models import Taxi, Ride, TaxiRating
from .serializers import TaxiSerializer, RideSerializer, TaxiRatingSerializer
from taxi.permissions import TaxiPermission
from accounts.models import CustomUser  # assuming your user model

class TaxiViewSet(viewsets.ModelViewSet):
    serializer_class = TaxiSerializer
    permission_classes = [TaxiPermission]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Taxi.objects.all()
        return Taxi.objects.filter(driver=user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def rate(self, request, pk=None):
        taxi = self.get_object()
        score = request.data.get("score")

        if not score or int(score) < 1 or int(score) > 5:
            return Response({"error": "Score must be between 1 and 5"}, status=400)

        rating, created = TaxiRating.objects.update_or_create(
            taxi=taxi,
            user=request.user,
            defaults={"score": score}
        )

        serializer = TaxiRatingSerializer(rating)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def average_rating(self, request, pk=None):
        taxi = self.get_object()
        ratings = taxi.ratings.all()
        if not ratings.exists():
            return Response({"average": None, "count": 0})

        avg = sum(r.score for r in ratings) / ratings.count()
        return Response({"average": round(avg, 2), "count": ratings.count()})

    def get_object(self):
        taxi_id = self.kwargs.get('pk')
        try:
            return Taxi.objects.get(id=taxi_id)  # ناخذ التاكسي بالـ ID مباشرة
        except Taxi.DoesNotExist:
            raise NotFound("Taxi not found.")

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_location(self, request, pk=None):
        taxi = self.get_object()
        # تحقّق إنّ request.user هو السائق صاحب التاكسي
        if not hasattr(request.user, 'taxi') or request.user.taxi.id != taxi.id:
            return Response({"error": "Not allowed"}, status=403)

        try:
            lat = float(request.data.get('lat'))
            lng = float(request.data.get('lng'))
        except (TypeError, ValueError):
            return Response({"error": "lat and lng required"}, status=400)

        taxi.location_lat = lat
        taxi.location_lng = lng
        taxi.save()

        channel_layer = get_channel_layer()
        # broadcast للسائق نفسه
        async_to_sync(channel_layer.group_send)(
            f"driver_{taxi.driver.id}",
            {
                "type": "driver_location",
                "message": {
                    "driver_id": taxi.driver.id,
                    "lat": lat,
                    "lng": lng,
                    "ts": str(taxi.updated_at) if hasattr(taxi, "updated_at") else None
                }
            }
        )

        # لو التاكسي مرتبط برحلة شغّالة نبعث لتلك الرحلة زادة
        active_ride = taxi.taxi_rides.filter(status__in=['accepted', 'in_progress', 'in_ride']).first()
        if active_ride:
            async_to_sync(channel_layer.group_send)(
                f"ride_{active_ride.id}",
                {
                    "type": "ride_event",
                    "message": {
                        "action": "location",
                        "data": {"lat": lat, "lng": lng, "taxi_id": taxi.id}
                    }
                }
            )

        return Response({"status": "ok"})


    # def get_object(self):
    #     user_id = self.kwargs.get('pk')
    #     try:
    #         if self.request.user.is_superuser:
    #             return Taxi.objects.get(driver__id=user_id)
    #         return Taxi.objects.get(driver=self.request.user, driver__id=user_id)
    #     except Taxi.DoesNotExist:
    #         raise NotFound("No Taxi matches the given driver ID.")

    @action(detail=False, methods=['get'], url_path='nearby')
    def nearby_taxis(self, request):
        try:
            lat = float(request.query_params.get('lat'))
            lng = float(request.query_params.get('lng'))
        except (TypeError, ValueError):
            return Response({"error": "lat and lng query parameters are required"}, status=400)

        nearby = []
        for taxi in Taxi.objects.filter(available=True):
            distance = self.haversine(lat, lng, taxi.location_lat, taxi.location_lng)
            if distance <= 1:  # 1 km
                nearby.append(taxi)
        serializer = self.get_serializer(nearby, many=True)
        return Response(serializer.data)

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371.0
        lat1_rad, lon1_rad = radians(lat1), radians(lon1)
        lat2_rad, lon2_rad = radians(lat2), radians(lon2)
        dlat, dlon = lat2_rad - lat1_rad, lon2_rad - lon1_rad
        a = sin(dlat/2)**2 + cos(lat1_rad)*cos(lat2_rad)*sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c

# ------------------- RideViewSet -------------------
class RideViewSet(viewsets.ModelViewSet):
    queryset = Ride.objects.all()
    serializer_class = RideSerializer
    permission_classes = [IsAuthenticated]

    # --- Helpers ---
    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371000  # meters
        lat1_rad, lon1_rad = radians(lat1), radians(lon1)
        lat2_rad, lon2_rad = radians(lat2), radians(lon2)
        dlat, dlon = lat2_rad - lat1_rad, lon2_rad - lon1_rad
        a = sin(dlat/2)**2 + cos(lat1_rad)*cos(lat2_rad)*sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c

    # ---------------- Create ride ----------------
    def perform_create(self, serializer):
        user = self.request.user
        start_lat = self.request.data.get("start_lat")
        start_lng = self.request.data.get("start_lng")

        nearest_taxi = None
        min_distance = float("inf")

        if start_lat and start_lng:
            start_lat = float(start_lat)
            start_lng = float(start_lng)

            # نجيبو كان التاكسيات الـ available
            for taxi in Taxi.objects.filter(available=True):
                distance = self.haversine(start_lat, start_lng, taxi.location_lat, taxi.location_lng)
                if distance < min_distance:
                    min_distance = distance
                    nearest_taxi = taxi

        # نعمل save للـ ride مع أقرب taxi
        serializer.save(passenger=user, taxi=nearest_taxi)

    # --- Nearby rides for join ---
    @action(detail=False, methods=['get'], url_path='nearby')
    def nearby_rides(self, request):
        try:
            lat = float(request.query_params.get('lat'))
            lng = float(request.query_params.get('lng'))
            radius = float(request.query_params.get('radius', 500))
        except (TypeError, ValueError):
            return Response({"error": "lat, lng et radius sont requis"}, status=400)

        rides = []
        for ride in Ride.objects.filter(status='shared'):
            distance = self.haversine(lat, lng, ride.start_lat, ride.start_lng)
            if distance <= radius:
                rides.append(ride)
        serializer = self.get_serializer(rides, many=True)
        return Response(serializer.data)

    # --- Passenger requests to join ---
    @action(detail=True, methods=['post'])
    def request_join(self, request, pk=None):
        ride = self.get_object()
        user = request.user

        if user.is_driver:
            return Response({"error": "Drivers cannot join rides"}, status=403)
        if ride.shared_passenger is not None:
            return Response({"error": "Ride already accepted"}, status=400)

        # Save pending request
        ride.pending_requests.add(user)
        return Response({"status": "request_sent"})

    # --- Owner checks requests (polling) ---
    @action(detail=True, methods=['get'], url_path='share')
    def check_requests(self, request, pk=None):
        ride = self.get_object()
        pending = ride.pending_requests.all()
        data = [{"id": u.id, "username": u.username} for u in pending]
        return Response(data)

    # --- Owner responds ---
    @action(detail=True, methods=['post'])
    def respond_join(self, request, pk=None):
        ride = self.get_object()
        user = request.user
        if ride.passenger != user:
            return Response({"error": "Only owner can respond"}, status=403)

        action_type = request.data.get("action")  # 'accept' or 'refuse'
        requester_id = request.data.get("requester_id")

        try:
            requester = CustomUser.objects.get(id=requester_id)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        if action_type == 'accept':
            ride.shared_passenger = requester
            ride.status = 'waiting'
            ride.pending_requests.clear()  # clear list after accept
        elif action_type == 'refuse':
            ride.pending_requests.remove(requester)
        ride.save()

        return Response({"status": action_type})

    # --- Taxi accepts ride ---
    @action(detail=True, methods=['post'])
    def accept_by_taxi(self, request, pk=None):
        ride = self.get_object()
        user = request.user
        if not hasattr(user, 'taxi'):
            return Response({"error": "Only drivers can accept rides"}, status=403)

        ride.taxi = user.taxi
        ride.status = 'accepted'
        ride.save()

        # Notify passenger
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'ride_{ride.passenger.id}',
            {
                "type": "ride_notification",
                "message": {
                    "ride_id": ride.id,
                    "status": ride.status,
                    "taxi_id": ride.taxi.id,
                    "msg": "Taxi accepté!"
                }
            }
        )
        serializer = RideSerializer(ride)
        return Response(serializer.data)
