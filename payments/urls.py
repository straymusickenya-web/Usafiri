# payments/urls.py
from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("mpesa/webhook/", views.mpesa_webhook, name="mpesa_webhook"),
]
