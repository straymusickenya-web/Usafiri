from django.db import models
from django.conf import settings
from drivers.models import DriverProfile
from django.utils import timezone
import uuid


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    class Provider(models.TextChoices):
        MPESA = "mpesa", "M-Pesa"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    driver = models.ForeignKey(
        DriverProfile,
        on_delete=models.CASCADE,
        related_name="payments",
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    provider = models.CharField(
        max_length=32,
        choices=Provider.choices,
        default=Provider.MPESA,
    )

    # M-Pesa specific identifiers
    checkout_request_id = models.CharField(
        max_length=128, blank=True, null=True, db_index=True
    )
    merchant_request_id = models.CharField(
        max_length=128, blank=True, null=True, db_index=True
    )

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    metadata = models.JSONField(default=dict, blank=True)

    idempotency_key = models.CharField(max_length=64, unique=True, null=True, blank=True)


    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["client", "driver"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.client} → {self.driver} (KES {self.amount}) [{self.status}]"

class DriverAccessGrant(models.Model):
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="access_grants",
    )
    driver = models.ForeignKey(
        DriverProfile,
        on_delete=models.CASCADE,
        related_name="access_grants",
    )

    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name="access_grant",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("client", "driver")

    def is_valid(self):
        return not self.expires_at or timezone.now() < self.expires_at
