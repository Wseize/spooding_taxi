from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    username_field = models.CharField(max_length=255, null=True, blank=True)
    is_driver = models.BooleanField(default=False)


    def __str__(self):
        return self.username