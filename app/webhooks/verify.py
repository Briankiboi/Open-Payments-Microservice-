import hashlib
import hmac
import logging
import os

logger = logging.getLogger(__name__)

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "super_secret_webhook_key").encode()


def verify_webhook_signature(payload: bytes, signature_header: str) -> bool:
    """
    Verifies the HMAC-SHA256 signature of an incoming webhook payload.
    This ensures that the webhook truly originated from the payment gateway.
    """
    if not signature_header:
        logger.warning("Missing signature header in webhook")
        return False

    try:
        # Calculate expected signature
        expected_signature = hmac.new(WEBHOOK_SECRET, payload, hashlib.sha256).hexdigest()

        # Use hmac.compare_digest to prevent timing attacks
        if hmac.compare_digest(
            f"sha256={expected_signature}", signature_header
        ) or hmac.compare_digest(expected_signature, signature_header):
            return True

        logger.warning(
            f"Invalid webhook signature. Expected: {expected_signature}, Got: {signature_header}"
        )
        return False

    except Exception as e:
        logger.error(f"Error validating webhook signature: {str(e)}")
        return False
