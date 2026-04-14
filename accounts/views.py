# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.db import transaction
from .forms import ClientSignupForm, DriverSignupForm
from drivers.forms import DriverProfileForm
from drivers.models import DriverProfile
from django.contrib.auth.decorators import login_required

from core.tasks import send_client_welcome_email_task, send_driver_welcome_email_task
def signup_choice(request):
    return render(request, "registration/signup_choice.html")

def signup_client(request):
    if request.method == "POST":
        form = ClientSignupForm(request.POST)
        # Backend enforcement — cannot be bypassed by JS or browser tricks
        if not request.POST.get("accept_terms"):
            form.add_error(None, "You must accept the Terms of Service and Privacy Policy to create an account.")
            return render(request, "registration/signup_client.html", {"form": form})
        if form.is_valid():
            user = form.save()
            if user.email:
                send_client_welcome_email_task.delay(user.id)
            messages.success(request, "Account created. Please log in.")
            return redirect("accounts:login")
    else:
        form = ClientSignupForm()
    return render(request, "registration/signup_client.html", {"form": form})

def signup_driver(request):
    """
    Two-step driver registration:
    Step 1: Create user account + upload ID and vehicle info
    Step 2: Payment to activate (handled in driver_dashboard)
    """
    if request.method == "POST":
        user_form = DriverSignupForm(request.POST)
        profile_form = DriverProfileForm(request.POST, request.FILES)
        
        # Backend enforcement — cannot be bypassed by JS or browser tricks
        if not request.POST.get("accept_terms"):
            profile_form.add_error(None, "You must accept the Terms of Service and Privacy Policy to create an account.")
            return render(request, "registration/signup_driver.html", {
                "user_form": user_form,
                "profile_form": profile_form
            })

        if user_form.is_valid() and profile_form.is_valid():
            try:
                # Use atomic transaction to ensure both are created together
                with transaction.atomic():
                    # Create and save user
                    user = user_form.save()
                    
                    # Create profile linked to user
                    profile = profile_form.save(commit=False)
                    profile.user = user
                    
                    # Set full_name from user's first and last name
                    profile.full_name = f"{user.first_name} {user.last_name}".strip()
                    
                    # Copy phone number from user to profile for consistency
                    profile.phone_number = user.phone_number or ""
                    
                    # Save profile
                    profile.save()

                    profile.sync_destinations(profile_form.cleaned_data["destinations"])

                    if user.email:
                        send_driver_welcome_email_task.delay(user.id, profile.id)
                        
                    # Log the user in automatically
                    login(request, user)
                    
                    messages.success(
                        request, 
                        "Driver profile created successfully! Please complete payment to activate your account."
                    )
                    return redirect("drivers:driver_dashboard")
                    
            except Exception as e:
                messages.error(request, f"Registration failed: {str(e)}. Please try again.")
        else:
            # Display form validation errors
            messages.error(request, "Please correct the errors below.")
    else:
        user_form = DriverSignupForm()
        profile_form = DriverProfileForm()
    
    return render(request, "registration/signup_driver.html", {
        "user_form": user_form, 
        "profile_form": profile_form
    })

@login_required
def dashboard_redirect(request):
    """Redirect users to appropriate dashboard based on their role."""
    if request.user.is_driver:
        return redirect("drivers:driver_dashboard")
    elif request.user.is_client:
        return redirect("accounts:client_dashboard")
    else:
        messages.warning(request, "Please complete your profile setup.")
        return redirect("core:home")
    
@login_required
def client_dashboard(request):
    """Dashboard for clients."""
    if not request.user.is_client:
        messages.error(request, "Access denied. Client account required.")
        return redirect("core:home")

    from payments.models import Payment

    payments = (
        Payment.objects.filter(client=request.user)
        .select_related("driver")
        .order_by("-created_at")
    )

    successful_payments = payments.filter(status=Payment.Status.SUCCESS)
    pending_payments = payments.filter(status=Payment.Status.PENDING)
    failed_payments = payments.filter(status=Payment.Status.FAILED)

    recent_payments = payments[:8]
    recent_unlocked = successful_payments[:6]

    context = {
        "payments": recent_payments,
        "recent_unlocked": recent_unlocked,
        "total_payments": payments.count(),
        "successful_count": successful_payments.count(),
        "pending_count": pending_payments.count(),
        "failed_count": failed_payments.count(),
    }
    return render(request, "clients/client_dashboard.html", context)