# drivers/views.py

from django.shortcuts import render, get_object_or_404, redirect
from .models import DriverProfile, DriverVehicle
from django.contrib import messages
from django.db.models import Q
from payments.mpesa import initiate_stk_push
from payments.models import Payment
from django_ratelimit.decorators import ratelimit
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from payments.utils import make_idempotency_key
from ratings.models import Rating
from .forms import parse_destinations

@ratelimit(key='ip', rate='10/m', block=True)
def driver_list(request):
    q_location = request.GET.get("location")
    q_destination = request.GET.get("destination")
    q_vehicle = request.GET.get("vehicle_type")
    q_seats = request.GET.get("seats")
    
    qs = DriverProfile.objects.filter(
        is_active_searchable=True
    ).prefetch_related("destinations")


    if q_location:
        qs = qs.filter(location__icontains=q_location)
    if q_destination:
        qs = qs.filter(
            destinations__name__icontains=q_destination,
            destinations__is_active=True,
        )
    if q_vehicle:
        qs = qs.filter(vehicle_type=q_vehicle)
    if q_seats:
        try:
            s = int(q_seats)
            qs = qs.filter(vehicle_seats__gte=s)
        except:
            pass

    qs = qs.distinct()
    
    # Check which drivers the user has access to
    unlocked_driver_ids = []
    if request.user.is_authenticated and request.user.is_client:
        from payments.models import DriverAccessGrant
        unlocked_driver_ids = list(
            DriverAccessGrant.objects.filter(
                client=request.user,
                driver__in=qs
            ).values_list('driver_id', flat=True)
        )

    pending_payment_id = request.session.get('pending_payment_id')
    pending_driver_id = request.session.get('pending_driver_id')
    
    return render(request, "drivers/list.html", {
        "drivers": qs,
        "unlocked_driver_ids": unlocked_driver_ids,
        "pending_payment_id": pending_payment_id,
        "pending_driver_id": pending_driver_id,
    })

# drivers/views.py

def driver_detail_partial(request, driver_id):
    driver = get_object_or_404(DriverProfile.objects.prefetch_related("destinations"), id=driver_id)
    
    # Check if user has access to this driver's contact
    has_access = False
    user_rating = None
    if request.user.is_authenticated and request.user.is_client:
        from payments.models import DriverAccessGrant
        has_access = DriverAccessGrant.objects.filter(
            client=request.user,
            driver=driver
        ).exists()

        user_rating = Rating.objects.filter(
            client=request.user,
            driver=driver
        ).first()

    ratings = Rating.objects.filter(driver=driver).order_by("-created_at")
    total_ratings = ratings.count()
    commented_ratings = ratings.exclude(comment__isnull=True).exclude(comment__exact="")

    # Pick up pending payment if user was sent back here after unlock
    pending_payment_id = None
    if (
        str(request.session.get('pending_driver_id', '')) == str(driver_id)
        and request.session.get('pending_next_url', '').startswith('/drivers/')
    ):
        pending_payment_id = request.session.get('pending_payment_id')
    
    return render(request, "drivers/detail_partial.html", {
        "driver": driver,
        "has_access": has_access,
        "user_rating": user_rating,
        "ratings": commented_ratings,
        "total_ratings": total_ratings,
        "destinations": driver.active_destinations(),
        "pending_payment_id": pending_payment_id,
    })

# def unlock_contact(request, driver_id):
#     """Start payment flow for client to unlock driver contact details via Daraja STK Push."""
#     if not request.user.is_authenticated or not request.user.is_client:
#         messages.error(request, "Log in as client to unlock contact.")
#         return redirect("accounts:login")
#     driver = get_object_or_404(DriverProfile, id=driver_id)
#     amount = 100  # registration fee / access fee, configurable
#     # create Payment object with pending status
#     payment = Payment.objects.create(
#         client=request.user,
#         driver=driver,
#         amount=amount,
#         status=Payment.Status.PENDING,
#         provider="mpesa",
#         metadata={"access_type":"contact_unlock"},
#     )
#     # initiate STK push (Daraja)
#     resp = initiate_stk_push(phone=request.user.phone_number, amount=amount, account_reference=str(payment.id))
#     if resp.get("error"):
#         messages.error(request, "Payment initiation failed: " + resp["error"])
#         return redirect("drivers:list")
#     messages.info(request, "Payment initiated. Complete the payment on your phone to unlock contact.")
#     return redirect("drivers:list")

# def unlock_contact(request, driver_id):
#     """Start payment flow for client to unlock driver contact details via Daraja STK Push."""
#     if not request.user.is_authenticated or not request.user.is_client:
#         messages.error(request, "Log in as client to unlock contact.")
#         return redirect("accounts:login")
    
#     driver = get_object_or_404(DriverProfile, id=driver_id)
    
#     # Check if already unlocked
#     from payments.models import DriverAccessGrant
#     if DriverAccessGrant.objects.filter(client=request.user, driver=driver).exists():
#         messages.info(request, "You already have access to this driver's contact.")
#         return redirect("drivers:detail_partial", driver_id=driver_id)
    
#     amount = 1  # registration fee / access fee, configurable
    
#     # Format phone number
#     phone = request.user.phone_number or ""
    
#     if not phone:
#         messages.error(request, "Please add a phone number to your profile.")
#         return redirect("drivers:list")
    
#     phone = str(phone)
#     if phone.startswith('0'):
#         phone = '254' + phone[1:]
#     elif phone.startswith('+'):
#         phone = phone[1:]
    
#     import uuid
#     temp_ref = str(uuid.uuid4())
    
#     resp = initiate_stk_push(
#         phone=phone, 
#         amount=amount, 
#         account_reference=f"UNLOCK-{temp_ref}"
#     )
    
#     if resp.get("error"):
#         messages.error(request, "Payment initiation failed: " + resp["error"])
#         return redirect("drivers:list")
    
#     if resp.get("ResponseCode") != "0":
#         error_msg = resp.get("errorMessage") or resp.get("CustomerMessage") or "Unknown error"
#         messages.error(request, f"Payment initiation failed: {error_msg}")
#         return redirect("drivers:list")
    
#     payment = Payment.objects.create(
#         client=request.user,
#         driver=driver,
#         amount=amount,
#         status=Payment.Status.PENDING,
#         provider="mpesa",
#         checkout_request_id=resp.get("CheckoutRequestID"),
#         merchant_request_id=resp.get("MerchantRequestID"),
#         metadata={"access_type": "contact_unlock"},
#     )
    
#     messages.success(request, "Payment initiated! Check your phone for the M-Pesa prompt.")
#     messages.info(request, "Contact details will be unlocked once payment is confirmed (usually within 30 seconds).")
    
#     # Store payment ID in session for status checking
#     request.session['pending_payment_id'] = str(payment.id)
#     request.session['pending_driver_id'] = driver_id
    
#     # Redirect to a payment pending page or back to list
#     return redirect("drivers:list")
def unlock_contact(request, driver_id):
    """Start payment flow for client to unlock driver contact details via Daraja STK Push."""
    if not request.user.is_authenticated or not request.user.is_client:
        messages.error(request, "Log in as client to unlock contact.")
        return redirect("accounts:login")

    driver = get_object_or_404(DriverProfile, id=driver_id)

    from payments.models import DriverAccessGrant, Payment
    from payments.utils import make_idempotency_key

    # Where to redirect after payment polling completes
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    # Restrict to safe internal paths only
    if not next_url.startswith("/"):
        next_url = ""

    # Already unlocked
    if DriverAccessGrant.objects.filter(client=request.user, driver=driver).exists():
        messages.info(request, "You already have access to this driver's contact.")
        return redirect(next_url or "drivers:detail_partial", driver_id=driver_id)

    idempotency_key = make_idempotency_key(
        user_id=request.user.id,
        driver_id=driver_id,
        payment_type="contact_unlock"
    )

    # Already a pending payment — don't fire another STK push
    existing = Payment.objects.filter(
        idempotency_key=idempotency_key,
        status=Payment.Status.PENDING
    ).first()

    if existing:
        messages.info(request, "Payment already initiated. Check your phone for the M-Pesa prompt.")
        request.session['pending_payment_id'] = str(existing.id)
        request.session['pending_driver_id'] = driver_id
        request.session['pending_next_url'] = next_url
        return redirect(next_url) if next_url else redirect("drivers:list")

    amount = 1

    phone = request.user.phone_number or ""
    if not phone:
        messages.error(request, "Please add a phone number to your profile.")
        return redirect(next_url) if next_url else redirect("drivers:list")

    phone = str(phone)
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif phone.startswith('+'):
        phone = phone[1:]

    resp = initiate_stk_push(
        phone=phone,
        amount=amount,
        account_reference=f"UNLOCK-{idempotency_key[:8]}"
    )

    if resp.get("error"):
        messages.error(request, "Payment initiation failed: " + resp["error"])
        return redirect(next_url) if next_url else redirect("drivers:list")

    if resp.get("ResponseCode") != "0":
        error_msg = resp.get("errorMessage") or resp.get("CustomerMessage") or "Unknown error"
        messages.error(request, f"Payment initiation failed: {error_msg}")
        return redirect(next_url) if next_url else redirect("drivers:list")

    payment = Payment.objects.create(
        client=request.user,
        driver=driver,
        amount=amount,
        status=Payment.Status.PENDING,
        provider="mpesa",
        checkout_request_id=resp.get("CheckoutRequestID"),
        merchant_request_id=resp.get("MerchantRequestID"),
        idempotency_key=idempotency_key,
        metadata={"access_type": "contact_unlock"},
    )

    messages.success(request, "Payment initiated! Check your phone for the M-Pesa prompt.")
    messages.info(request, "Contact details will be unlocked once payment is confirmed (usually within 30 seconds).")

    request.session['pending_payment_id'] = str(payment.id)
    request.session['pending_driver_id'] = driver_id
    request.session['pending_next_url'] = next_url

    return redirect(next_url) if next_url else redirect("drivers:list")

@login_required
def client_dashboard(request):
    """Dashboard for clients."""
    if not request.user.is_client:
        messages.error(request, "Access denied. Client account required.")
        return redirect("core:home")
    
    # Get client's booking history, payments, etc.
    payments = Payment.objects.filter(client=request.user).order_by('-created_at')[:10]
    
    context = {
        'payments': payments,
    }
    return render(request, "clients/client_dashboard.html", context)

# @login_required
# def activate_account(request):
#     """Handle driver account activation payment."""
#     if not request.user.is_driver:
#         messages.error(request, "Only drivers can activate accounts.")
#         return redirect("core:home")
    
#     try:
#         profile = request.user.driverprofile
#     except DriverProfile.DoesNotExist:
#         messages.error(request, "Please complete your driver profile first.")
#         return redirect("core:home")
    
#     # Check if already active
#     if profile.is_active_searchable:
#         messages.info(request, "Your account is already active.")
#         return redirect("drivers:driver_dashboard")
    
#     if request.method == "POST":
#         amount = 1  # Activation fee
        
#         # Initiate M-Pesa STK Push first
#         phone = request.user.phone_number or profile.phone_number
        
#         # Format phone number (ensure it starts with 254)
#         if phone.startswith('0'):
#             phone = '254' + phone[1:]
#         elif phone.startswith('+'):
#             phone = phone[1:]
        
#         # Create temporary payment reference
#         import uuid
#         temp_ref = str(uuid.uuid4())
        
#         resp = initiate_stk_push(
#             phone=phone, 
#             amount=amount, 
#             account_reference=f"ACTIVATE-{temp_ref}"
#         )
        
#         if resp.get("error"):
#             messages.error(request, f"Payment initiation failed: {resp['error']}")
#             return redirect("drivers:driver_dashboard")
        
#         # Check if STK push was successful
#         if resp.get("ResponseCode") != "0":
#             error_msg = resp.get("errorMessage") or resp.get("CustomerMessage") or "Unknown error"
#             messages.error(request, f"Payment initiation failed: {error_msg}")
#             return redirect("drivers:driver_dashboard")
        
#         # Create Payment object with the response IDs
#         payment = Payment.objects.create(
#             client=request.user,
#             driver=profile,
#             amount=amount,
#             status=Payment.Status.PENDING,
#             provider="mpesa",
#             checkout_request_id=resp.get("CheckoutRequestID"),
#             merchant_request_id=resp.get("MerchantRequestID"),
#             metadata={"payment_type": "driver_activation"},
#         )
        
#         messages.success(request, "Payment request sent! Check your phone for the M-Pesa prompt.")
#         messages.info(request, "Your account will be activated automatically once payment is confirmed.")
        
#         return redirect("drivers:driver_dashboard")
    
#     return redirect("drivers:driver_dashboard")
@login_required
def activate_account(request):
    """Handle driver account activation payment."""
    if not request.user.is_driver:
        messages.error(request, "Only drivers can activate accounts.")
        return redirect("core:home")

    try:
        profile = request.user.driverprofile
    except DriverProfile.DoesNotExist:
        messages.error(request, "Please complete your driver profile first.")
        return redirect("core:home")

    if profile.is_active_searchable:
        messages.info(request, "Your account is already active.")
        return redirect("drivers:driver_dashboard")

    if request.method == "POST":
        from payments.models import Payment
        from payments.utils import make_idempotency_key

        idempotency_key = make_idempotency_key(
            user_id=request.user.id,
            driver_id=profile.id,
            payment_type="driver_activation"
        )

        # Already a pending activation payment — don't fire another STK push
        existing = Payment.objects.filter(
            idempotency_key=idempotency_key,
            status=Payment.Status.PENDING
        ).first()

        if existing:
            messages.info(request, "Activation payment already initiated. Check your phone.")
            return redirect("drivers:driver_dashboard")

        amount = 1

        phone = request.user.phone_number or profile.phone_number
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('+'):
            phone = phone[1:]

        resp = initiate_stk_push(
            phone=phone,
            amount=amount,
            account_reference=f"ACTIVATE-{idempotency_key[:8]}"
        )

        if resp.get("error"):
            messages.error(request, f"Payment initiation failed: {resp['error']}")
            return redirect("drivers:driver_dashboard")

        if resp.get("ResponseCode") != "0":
            error_msg = resp.get("errorMessage") or resp.get("CustomerMessage") or "Unknown error"
            messages.error(request, f"Payment initiation failed: {error_msg}")
            return redirect("drivers:driver_dashboard")

        payment =  Payment.objects.create(
                client=request.user,
                driver=profile,
                amount=amount,
                status=Payment.Status.PENDING,
                provider="mpesa",
                checkout_request_id=resp.get("CheckoutRequestID"),
                merchant_request_id=resp.get("MerchantRequestID"),
                idempotency_key=idempotency_key,
                metadata={"payment_type": "driver_activation"},
            )

        messages.success(request, "Payment request sent! Check your phone for the M-Pesa prompt.")
        messages.info(request, "Your account will be activated automatically once payment is confirmed.")
        request.session['pending_activation_id'] = str(payment.id)

        return redirect("drivers:driver_dashboard")

    return redirect("drivers:driver_dashboard")

# @login_required
# def check_payment_status(request, payment_id):
#     """Check if a payment has been completed"""
#     from payments.models import Payment
    
#     try:
#         payment = Payment.objects.get(id=payment_id)
        
#         # Check if user is authorized to check this payment
#         if payment.client != request.user:
#             return JsonResponse({"error": "Unauthorized"}, status=403)
        
#         return JsonResponse({
#             "status": payment.status,
#             "is_complete": payment.status == Payment.Status.SUCCESS,
#             "redirect_url": None if payment.status == Payment.Status.PENDING else request.META.get('HTTP_REFERER', '/drivers/')
#         })
#     except Payment.DoesNotExist:
#         return JsonResponse({"error": "Payment not found"}, status=404)
@login_required
def check_payment_status(request, payment_id):
    from payments.models import Payment
    try:
        payment = Payment.objects.get(id=payment_id)
        if payment.client != request.user:
            return JsonResponse({"error": "Unauthorized"}, status=403)
        
        is_complete = payment.status == Payment.Status.SUCCESS
        is_failed = payment.status == Payment.Status.FAILED
        
        # Clear session once confirmed so banner doesn't show on future visits
        if is_complete or is_failed:
            request.session.pop('pending_payment_id', None)
            request.session.pop('pending_driver_id', None)
        
        return JsonResponse({
            "status": payment.status,
            "is_complete": is_complete,
            "is_failed": is_failed,
        })
    except Payment.DoesNotExist:
        return JsonResponse({"error": "Payment not found"}, status=404)

@login_required
def edit_driver_profile(request):
    if not request.user.is_driver:
        messages.error(request, "Only drivers can edit driver profiles.")
        return redirect("core:home")

    try:
        profile = request.user.driverprofile
    except DriverProfile.DoesNotExist:
        messages.error(request, "Driver profile not found.")
        return redirect("core:home")

    if request.method == "POST":
        profile.full_name = request.POST.get("full_name", profile.full_name).strip()
        profile.phone_number = request.POST.get("phone_number", profile.phone_number).strip()
        profile.location = request.POST.get("location", profile.location).strip()
        profile.vehicle_type = request.POST.get("vehicle_type", profile.vehicle_type)

        try:
            profile.vehicle_seats = int(request.POST.get("vehicle_seats", profile.vehicle_seats))
        except (TypeError, ValueError):
            messages.error(request, "Vehicle seats must be a valid number.")
            primary_vehicle = profile.vehicles.filter(is_primary=True).first()
            return render(request, "drivers/edit_profile.html", {"profile": profile, "vehicle": primary_vehicle})

        destinations = parse_destinations(request.POST.get("destinations", ""))

        if not destinations:
            messages.error(request, "Please add at least one destination.")
            primary_vehicle = profile.vehicles.filter(is_primary=True).first()
            return render(request, "drivers/edit_profile.html", {"profile": profile, "vehicle": primary_vehicle})

        if request.FILES.get("id_photo"):
            profile.id_photo = request.FILES["id_photo"]

        profile.save()
        profile.sync_destinations(destinations)

        registration = request.POST.get("registration", "").strip().upper()
        make = request.POST.get("vehicle_make", "").strip()
        model = request.POST.get("vehicle_model", "").strip()
        color = request.POST.get("vehicle_color", "").strip()

        if registration:
            DriverVehicle.objects.update_or_create(
                driver=profile,
                registration=registration,
                defaults={"make": make, "model": model, "color": color, "is_primary": True},
            )

        messages.success(request, "Profile updated successfully!")
        return redirect("drivers:driver_dashboard")
    
    primary_vehicle = profile.vehicles.filter(is_primary=True).first()

    return render(request, "drivers/edit_profile.html", {"profile": profile, "vehicle": primary_vehicle})

@login_required
def driver_dashboard(request):
    """Dashboard for drivers."""
    if not request.user.is_driver:
        messages.error(request, "Access denied. Driver account required.")
        return redirect("core:home")
    
    try:
        profile = request.user.driverprofile
    except DriverProfile.DoesNotExist:
        messages.error(request, "Please complete your driver profile first.")
        return redirect("core:home")
    
    from ratings.models import Rating
    payments = Payment.objects.filter(driver=profile).order_by("-created_at")[:10]
    ratings = Rating.objects.filter(driver=profile).select_related("client").order_by("-created_at")[:8]
    rating_count = Rating.objects.filter(driver=profile).count()

    # Only pass pending_payment_id if the payment is still actually pending
    pending_payment_id = request.session.get('pending_activation_id')
    if pending_payment_id:
        try:
            p = Payment.objects.get(id=pending_payment_id)
            if p.status != Payment.Status.PENDING:
                # Already resolved — clear session
                request.session.pop('pending_activation_id', None)
                pending_payment_id = None
        except Payment.DoesNotExist:
            request.session.pop('pending_activation_id', None)
            pending_payment_id = None
    
    context = {
        'profile': profile,
        'payments': payments,
        "ratings": ratings,
        "rating_count": rating_count,
        "destinations": profile.active_destinations(),
        "pending_activation_id": pending_payment_id,
    }
    return render(request, "drivers/driver_dashboard.html", context)

@login_required
def driver_card_fragment(request, driver_id):
    driver = get_object_or_404(
        DriverProfile.objects.prefetch_related("destinations", "vehicles"),
        id=driver_id
    )
    unlocked = False
    if request.user.is_authenticated and request.user.is_client:
        from payments.models import DriverAccessGrant
        unlocked = DriverAccessGrant.objects.filter(
            client=request.user, driver=driver
        ).exists()

    # Only allow AJAX requests to this endpoint
    if not request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return redirect("drivers:list")

    return render(request, "drivers/driver_card_fragment.html", {
        "d": driver,
        "unlocked_driver_ids": [driver.id] if unlocked else [],
    })