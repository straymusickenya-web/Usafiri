from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import EmailMessage
from django.core.mail import send_mail

from .forms import ContactForm

def home(request):
    return render(request, "core/home.html")

def about(request):
    return render(request, "core/about.html")

def terms(request):
    return render(request, "core/terms.html")

def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            message = form.cleaned_data["message"]

            subject = f"Usafiri Contact Form — {name}"
            body = (
                f"New message from the Usafiri contact form\n\n"
                f"Name: {name}\n"
                f"Email: {email}\n\n"
                f"Message:\n{message}\n"
            )

            email_message = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.CONTACT_EMAIL],
                reply_to=[email],
            )

            try:
                email_message.send(fail_silently=False)
                messages.success(
                    request,
                    "Thanks for reaching out. Your message has been sent successfully."
                )
                return redirect("core:contact")
            except Exception:
                messages.error(
                    request,
                    "We couldn't send your message right now. Please try again in a moment."
                )
    else:
        form = ContactForm()

    return render(request, "core/contact.html", {"form": form})

def privacy(request):
    return render(request, "core/privacy.html")