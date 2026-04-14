# Drivers/models.py

from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField
from django.utils import timezone

VEHICLE_CHOICES = [
    ("car","Car"),("van","Van"),("matatu","Matatu"),("motorbike","Motorbike")
]

class DriverProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    id_number = models.CharField(max_length=64)
    id_photo = CloudinaryField(resource_type='image', folder='drivers/id_photos')
    id_verified = models.BooleanField(default=False)
    vehicle_type = models.CharField(max_length=32, choices=VEHICLE_CHOICES)
    vehicle_seats = models.PositiveIntegerField(default=4)
    location = models.CharField(max_length=255, help_text="Driver base city/neighborhood")
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    phone_number = models.CharField(max_length=32)
    is_active_searchable = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def first_name(self):
        return self.full_name.split()[0] if self.full_name else self.user.first_name or ""
    
    def approx_location(self):
        return self.location

    def avg_rating(self):
        from ratings.models import Rating
        qs = Rating.objects.filter(driver=self)
        if not qs.exists():
            return None
        return qs.aggregate(models.Avg('score'))['score__avg']
    
    def active_destinations(self):
        return self.destinations.filter(is_active=True).order_by("name")
    
    def sync_destinations(self, names):
        cleaned = []
        seen = set()

        for raw in names:
            name = (raw or "").strip()
            if not name:
                continue
            key = name.lower()
            if key not in seen:
                seen.add(key)
                cleaned.append(name)

        existing = {d.name.lower(): d for d in self.destinations.all()}

        for key, dest in existing.items():
            should_be_active = key in seen
            if dest.is_active != should_be_active:
                dest.is_active = should_be_active
                dest.save(update_fields=["is_active"])

        for name in cleaned:
            key = name.lower()
            if key not in existing:
                DriverDestination.objects.create(
                    driver=self,
                    name=name,
                    is_active=True,
                )
    
    def __str__(self):
        return f"{self.full_name} ({self.vehicle_type})"
    
class DriverDestination(models.Model):
    driver = models.ForeignKey(
        DriverProfile,
        on_delete=models.CASCADE,
        related_name="destinations",
    )
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("driver", "name")

    def __str__(self):
        return f"{self.driver.full_name} → {self.name}"
    
class DriverVehicle(models.Model):
    driver = models.ForeignKey(
        DriverProfile,
        on_delete=models.CASCADE,
        related_name="vehicles",
    )
    registration = models.CharField(max_length=20, unique=True)
    make = models.CharField(max_length=64)        # e.g. Toyota
    model = models.CharField(max_length=64)       # e.g. Hiace
    color = models.CharField(max_length=32)       # e.g. White
    is_primary = models.BooleanField(default=True)  # active/default vehicle
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "-created_at"]

    def __str__(self):
        return f"{self.registration} — {self.make} {self.model} ({self.driver.full_name})"
