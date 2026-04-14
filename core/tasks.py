from celery import shared_task
from django.contrib.auth import get_user_model

from drivers.models import DriverProfile
from payments.models import Payment
from .emails import (
    send_client_welcome_email,
    send_driver_welcome_email,
    send_payment_success_email,
    send_driver_activation_success_email,
)

User = get_user_model()


@shared_task
def send_client_welcome_email_task(user_id):
    user = User.objects.get(id=user_id)
    if user.email:
        send_client_welcome_email(user)


@shared_task
def send_driver_welcome_email_task(user_id, profile_id):
    user = User.objects.get(id=user_id)
    profile = DriverProfile.objects.get(id=profile_id)
    if user.email:
        send_driver_welcome_email(user, profile)


@shared_task
def send_payment_success_email_task(payment_id):
    payment = Payment.objects.select_related("client", "driver").get(id=payment_id)
    if payment.client and payment.client.email:
        send_payment_success_email(payment)


@shared_task
def send_driver_activation_success_email_task(payment_id):
    payment = Payment.objects.select_related("driver__user").get(id=payment_id)
    driver_user = payment.driver.user

    if driver_user and driver_user.email:
        send_driver_activation_success_email(payment)