# payments/utils.py
import hashlib

def make_idempotency_key(user_id, driver_id, payment_type):
    """
    Deterministic key based on who is paying, for what, and what type.
    Same click scenario always produces the same key.
    """
    raw = f"{user_id}:{driver_id}:{payment_type}"
    return hashlib.sha256(raw.encode()).hexdigest()