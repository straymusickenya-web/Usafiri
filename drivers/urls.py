# drivers/urls.py
from django.urls import path
from . import views

app_name = "drivers"

urlpatterns = [
    path("", views.driver_list, name="list"),
    path("<int:driver_id>/", views.driver_detail_partial, name="detail_partial"),
    path("<int:driver_id>/unlock/", views.unlock_contact, name="unlock_contact"),
    path("<int:driver_id>/card/", views.driver_card_fragment, name="driver_card_fragment"),

    # Dashboards
    path("dashboard/driver/", views.driver_dashboard, name="driver_dashboard"),

    path("activate/", views.activate_account, name="activate_account"),
    path("profile/edit/", views.edit_driver_profile, name="edit_driver_profile"),
    
    # Payment status
    path("payment/<uuid:payment_id>/status/", views.check_payment_status, name="check_payment_status"),
]
