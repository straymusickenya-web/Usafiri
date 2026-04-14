from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "Usafiri <info@usafiri.co.ke>")


def send_templated_email(
    *,
    subject: str,
    to_email: str,
    template_base: str,
    context: dict,
    from_email: str | None = None,
):
    """
    Sends multipart email using:
    - templates/emails/<template_base>.txt
    - templates/emails/<template_base>.html
    """
    from_email = from_email or FROM_EMAIL

    text_body = render_to_string(f"emails/{template_base}.txt", context)
    html_body = render_to_string(f"emails/{template_base}.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=[to_email],
    )
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)


def send_client_welcome_email(user):
    send_templated_email(
        subject="Welcome to Usafiri",
        to_email=user.email,
        template_base="welcome_client",
        context={
            "user": user,
            "app_name": "Usafiri",
            "login_url": getattr(settings, "APP_LOGIN_URL", "/accounts/login/"),
            "drivers_url": getattr(settings, "APP_DRIVERS_URL", "/drivers/"),
        },
    )


def send_driver_welcome_email(user, profile):
    send_templated_email(
        subject="Welcome to Usafiri Driver Network",
        to_email=user.email,
        template_base="welcome_driver",
        context={
            "user": user,
            "profile": profile,
            "app_name": "Usafiri",
            "dashboard_url": getattr(settings, "APP_DRIVER_DASHBOARD_URL", "/drivers/dashboard/driver/"),
            "edit_profile_url": getattr(settings, "APP_EDIT_PROFILE_URL", "/drivers/profile/edit/"),
        },
    )


def send_payment_success_email(payment):
    send_templated_email(
        subject="Payment received successfully",
        to_email=payment.client.email,
        template_base="payment_success",
        context={
            "payment": payment,
            "client": payment.client,
            "driver": payment.driver,
            "app_name": "Usafiri",
            "driver_url": f"/drivers/{payment.driver.id}/",
            "dashboard_url": getattr(settings, "APP_CLIENT_DASHBOARD_URL", "/accounts/dashboard/client/"),
        },
    )

from celery import shared_task
from django.contrib.auth import get_user_model

from drivers.models import DriverProfile
from payments.models import Payment
from .emails import (
    send_client_welcome_email,
    send_driver_welcome_email,
    send_payment_success_email,
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
    if payment.client.email:
        send_payment_success_email(payment)

def send_driver_activation_success_email(payment):
    driver_user = payment.driver.user

    send_templated_email(
        subject="Your Usafiri driver account is now active",
        to_email=driver_user.email,
        template_base="driver_activation_success",
        context={
            "payment": payment,
            "user": driver_user,
            "driver": payment.driver,
            "app_name": "Usafiri",
            "dashboard_url": getattr(
                settings,
                "APP_DRIVER_DASHBOARD_URL",
                "https://usafiri.co.ke/drivers/dashboard/driver/",
            ),
        },
    )