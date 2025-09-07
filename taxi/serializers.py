from rest_framework import serializers

from accounts.models import CustomUser
from .models import Taxi, Ride, TaxiRating
from accounts.serializers import CustomUserSerializer

class TaxiSerializer(serializers.ModelSerializer):
    driver = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(is_driver=True).exclude(taxi__isnull=False),
        required=False,
        allow_null=True
    )
    average_rating = serializers.SerializerMethodField()
    ratings_count = serializers.SerializerMethodField()
    completed_rides_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Taxi
        fields = ['id', 'driver', 'license_plate', 'location_lat', 'location_lng', 'available', 'average_rating', 'ratings_count', 'completed_rides_count',]

    def get_average_rating(self, obj):
        ratings = obj.ratings.all()
        if not ratings.exists():
            return None
        return round(sum(r.score for r in ratings) / ratings.count(), 2)

    def get_ratings_count(self, obj):
        return obj.ratings.count()

    def get_completed_rides_count(self, obj):
        """compter rides completed mtaa taxi"""
        return obj.taxi_rides.filter(status="completed").count()

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.driver:
            rep['driver'] = instance.driver.id
        return rep

    def update(self, instance, validated_data):
        if instance.driver:
            validated_data.pop('driver', None)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Rendre driver readonly si déjà défini"""
        rep = super().to_representation(instance)
        if instance.driver:
            rep['driver'] = instance.driver.id  # just the ID
        return rep

    def update(self, instance, validated_data):
        # Si driver existe déjà, on ne l'autorise pas à changer
        if instance.driver:
            validated_data.pop('driver', None)
        return super().update(instance, validated_data)
    

class TaxiRatingSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.id")

    class Meta:
        model = TaxiRating
        fields = ["id", "taxi", "user", "score", "created_at"]



class RideSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ride
        fields = "__all__"