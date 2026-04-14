# accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "accounts"

urlpatterns = [
    # --- Signup flows ---
    path("signup/", views.signup_choice, name="signup_choice"),
    path("signup/client/", views.signup_client, name="signup_client"),
    path("signup/driver/", views.signup_driver, name="signup_driver"),

    # --- Auth ---
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page='core:home'), name="logout"),

    # --- Dashboard redirect ---
    path("dashboard/", views.dashboard_redirect, name="dashboard_redirect"),
    path("dashboard/client/", views.client_dashboard, name="client_dashboard"),

]
