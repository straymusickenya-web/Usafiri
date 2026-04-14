# payments/tasks.py

import logging
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .models import Payment, DriverAccessGrant
from core.tasks import send_payment_success_email_task, send_driver_activation_success_email_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 5},
)
def process_mpesa_webhook_async(self, payload: dict):
    """
    Process M-Pesa STK Push callback payload.
    This task is idempotent and safe to retry.
    """

    try:
        stk_callback = payload["Body"]["stkCallback"]
    except KeyError:
        logger.error("Invalid M-Pesa payload structure", extra={"payload": payload})
        return

    checkout_request_id = stk_callback.get("CheckoutRequestID")
    result_code = stk_callback.get("ResultCode")

    if not checkout_request_id:
        logger.error("Missing CheckoutRequestID", extra={"payload": payload})
        return

    with transaction.atomic():
        try:
            payment = Payment.objects.select_for_update().get(
                checkout_request_id=checkout_request_id
            )
        except Payment.DoesNotExist:
            logger.error(
                "Payment not found for CheckoutRequestID",
                extra={"checkout_request_id": checkout_request_id},
            )
            return

        # Idempotency: do nothing if already processed
        if payment.status in (Payment.Status.SUCCESS, Payment.Status.FAILED):
            logger.info(
                "Duplicate webhook ignored",
                extra={"payment_id": str(payment.id), "status": payment.status},
            )
            return

        payment.metadata["callback"] = payload

        if result_code == 0:
            payment.status = Payment.Status.SUCCESS
            # Keep idempotency_key on success to permanently block re-processing

            payment_type = payment.metadata.get("payment_type")

            if payment_type == "driver_activation":
                driver_profile = payment.driver
                driver_profile.is_active_searchable = True
                driver_profile.save(update_fields=["is_active_searchable"])
                logger.info(
                    "Driver account activated",
                    extra={
                        "driver_id": driver_profile.id,
                        "driver_name": driver_profile.full_name
                    }
                )
            else:
                DriverAccessGrant.objects.get_or_create(
                    payment=payment,
                    defaults={
                        "client": payment.client,
                        "driver": payment.driver,
                        "expires_at": timezone.now() + timedelta(days=7),
                    },
                )

        else:
            payment.status = Payment.Status.FAILED
            # Clear idempotency_key on failure so the user can retry
            payment.idempotency_key = None
            logger.warning(
                "Payment failed",
                extra={"payment_id": str(payment.id), "result_code": result_code}
            )

        payment.save(update_fields=["status", "metadata", "idempotency_key"])

        # Queue email only after DB commit succeeds
        if payment.status == Payment.Status.SUCCESS:
            payment_type = payment.metadata.get("payment_type")

            if payment_type == "driver_activation":
                if payment.driver and payment.driver.user.email:
                    transaction.on_commit(
                        lambda payment_id=payment.id: send_driver_activation_success_email_task.delay(payment_id)
                    )
            else:
                if payment.client and payment.client.email:
                    transaction.on_commit(
                        lambda payment_id=payment.id: send_payment_success_email_task.delay(payment_id)
                    )

        logger.info(
            "Payment processed",
            extra={"payment_id": str(payment.id), "status": payment.status}
        )