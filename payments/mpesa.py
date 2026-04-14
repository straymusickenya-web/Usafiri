# payments/mpesa.py

import base64, requests, time, os
import logging

logger = logging.getLogger(__name__)

DARAJA_BASE = os.getenv("DARAJA_BASE")
DARAJA_CONSUMER_KEY = os.getenv("DARAJA_KEY")
DARAJA_CONSUMER_SECRET = os.getenv("DARAJA_SECRET")
DARAJA_PASSKEY = os.getenv("DARAJA_PASSKEY")
SHORTCODE = os.getenv("DARAJA_SHORTCODE")
TILL_NUMBER = os.getenv("TILL_NUMBER")
CALLBACK_URL = os.getenv("DARAJA_CALLBACK_URL")  # must be publicly reachable

def get_oauth_token():
    url = f"{DARAJA_BASE}/oauth/v1/generate?grant_type=client_credentials"
    # logger.log("URL: " + url)
    logger.error(f"[MPESA] Getting token from: {url}")
    logger.error(f"[MPESA] Using key: {DARAJA_CONSUMER_KEY[:6] if DARAJA_CONSUMER_KEY else 'MISSING'}...")
    r = requests.get(url, auth=(DARAJA_CONSUMER_KEY, DARAJA_CONSUMER_SECRET))
    logger.error(f"[MPESA] Token response {r.status_code}: {r.text}")
    r.raise_for_status()
    return r.json()["access_token"]

def stk_push(phone, amount, account_reference):
    token = get_oauth_token()
    timestamp = time.strftime("%Y%m%d%H%M%S")
    password = base64.b64encode((SHORTCODE + DARAJA_PASSKEY + timestamp).encode()).decode()
    payload = {
        "BusinessShortCode": SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerBuyGoodsOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": TILL_NUMBER,
        "PhoneNumber": phone,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": account_reference,
        "TransactionDesc": "Usafiri payment"
    }
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{DARAJA_BASE}/mpesa/stkpush/v1/processrequest", json=payload, headers=headers)

    logger.error(f"STK Push payload: {payload}")
    logger.error(f"STK Push response {resp.status_code}: {resp.text}")

    return resp.json()

def initiate_stk_push(*, phone, amount, account_reference):
    try:
        return stk_push(phone, amount, account_reference)
    except Exception as exc:
        return {"error": str(exc)}
    
def query_stk_status(checkout_request_id):
    token = get_oauth_token()
    timestamp = time.strftime("%Y%m%d%H%M%S")
    password = base64.b64encode((SHORTCODE + DARAJA_PASSKEY + timestamp).encode()).decode()
    payload = {
        "BusinessShortCode": SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_request_id
    }
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(
        f"{DARAJA_BASE}/mpesa/stkpushquery/v1/query",
        json=payload,
        headers=headers
    )
    return resp.json()