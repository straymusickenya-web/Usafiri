from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Rating
from drivers.models import DriverProfile
from payments.models import DriverAccessGrant

@login_required
def rate_driver(request, driver_id):
    """Allow clients to rate drivers they've unlocked"""
    if not request.user.is_client:
        messages.error(request, "Only clients can rate drivers.")
        return redirect("drivers:list")
    
    driver = get_object_or_404(DriverProfile, id=driver_id)
    
    # Check if client has access to this driver
    has_access = DriverAccessGrant.objects.filter(
        client=request.user,
        driver=driver
    ).exists()
    
    if not has_access:
        messages.error(request, "You must unlock the driver's contact before rating.")
        return redirect("drivers:detail_partial", driver_id=driver_id)
    
    # Check if already rated
    existing_rating = Rating.objects.filter(
        client=request.user,
        driver=driver
    ).first()
    
    if request.method == "POST":
        score = request.POST.get("score")
        comment = request.POST.get("comment", "").strip()
        
        try:
            score = int(score)
            if score < 1 or score > 5:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "Please select a rating between 1 and 5.")
            return redirect("ratings:rate_driver", driver_id=driver_id)
        
        if existing_rating:
            # Update existing rating
            existing_rating.score = score
            existing_rating.comment = comment
            existing_rating.save()
            messages.success(request, "Your rating has been updated!")
        else:
            # Create new rating
            Rating.objects.create(
                client=request.user,
                driver=driver,
                score=score,
                comment=comment
            )
            messages.success(request, "Thank you for rating this driver!")
        
        return redirect("drivers:detail_partial", driver_id=driver_id)
    
    return render(request, "ratings/rate_driver.html", {
        "driver": driver,
        "existing_rating": existing_rating
    })