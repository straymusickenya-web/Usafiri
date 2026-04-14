from django.db import models
from django.conf import settings
from drivers.models import DriverProfile
from django.utils import timezone
import uuid

class Rating(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE)
    score = models.IntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def can_edit(self):
        from django.utils import timezone
        window_hours = 24
        return (timezone.now() - self.created_at).total_seconds() < window_hours*3600
    
    class Meta:
        unique_together = ("client", "driver")
