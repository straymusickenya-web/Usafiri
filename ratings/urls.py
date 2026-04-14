from django.urls import path
from . import views

app_name = "ratings"

urlpatterns = [
    path("<int:driver_id>/", views.rate_driver, name="rate_driver"),
]