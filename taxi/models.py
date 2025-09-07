from django.db import models
from accounts.models import CustomUser

class Taxi(models.Model):
    driver = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='taxi')
    license_plate = models.CharField(max_length=15)
    location_lat = models.FloatField(default=0.0)
    location_lng = models.FloatField(default=0.0)
    available = models.BooleanField(default=True)

    def __str__(self):
        return f"Taxi {self.license_plate} - Driver {self.driver.username}"
    
class TaxiRating(models.Model):
    taxi = models.ForeignKey(Taxi, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="taxi_ratings")
    score = models.IntegerField(default=0)  # 1 → 5
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("taxi", "user")  # user ما يقيّمش نفس التاكسي كان مرة وحدة

    def __str__(self):
        return f"{self.user.username} rated {self.taxi.license_plate} {self.score}/5"


class Ride(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('in_ride', 'In Ride'),
        ('shared', 'Shared'),
    ]
    passenger = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='rides')
    taxi = models.ForeignKey(Taxi, on_delete=models.SET_NULL, null=True, blank=True, related_name="taxi_rides")
    start_lat = models.FloatField()
    start_lng = models.FloatField()
    end_lat = models.FloatField()
    end_lng = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    price = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    # جديد: shared passenger
    shared_passenger = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='shared_rides'
    )
    pending_requests = models.ManyToManyField(
        CustomUser, related_name='pending_rides', blank=True
    )

    def __str__(self):
        return f"Ride {self.id} - {self.status}"
