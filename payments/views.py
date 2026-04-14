# payments/views.py

import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from .models import Payment, DriverAccessGrant
from drivers.models import DriverProfile
from django.shortcuts import get_object_or_404
from .tasks import process_mpesa_webhook_async
from django.conf import settings

@csrf_exempt
def mpesa_webhook(request):
    # Daraja sends JSON to your callback URL. We enqueue processing to Celery to verify & avoid blocking.
    try:
        body = json.loads(request.body.decode())
    except:
        return JsonResponse({"error":"invalid json"}, status=400)
    # Basic ack — Daraja expects 200 quickly. Enqueue processing
    process_mpesa_webhook_async.delay(body)
    return HttpResponse("received", status=200)
