 # accounts/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_driver = models.BooleanField(default=False)
    is_client = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=32, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Ensure role flags consistent
        if self.is_driver:
            self.is_client = False
        super().save(*args, **kwargs)
