import asyncio
import logging
from typing import Any, Dict

from app.gateways.base_gateway import PaymentGateway

logger = logging.getLogger(__name__)


class MpesaGateway(PaymentGateway):
    """
    Example implemention of the PaymentGateway for M-PESA.
    In a real-world scenario, this would integrate with Daraja API.
    """

    async def initiate_payment(
        self, transaction_id: str, amount: float, currency: str, phone: str
    ) -> Dict[str, Any]:
        # Simulate network delay to external provider
        await asyncio.sleep(1)

        logger.info(f"Initiating M-Pesa STK push for {phone}, Amount: {amount} {currency}")

        # M-Pesa typically returns a MerchantRequestID and CheckoutRequestID
        return {
            "gateway_status": "Success",
            "message": "Payment initiation successful",
            "merchant_request_id": f"REQ_{transaction_id[:8]}",
        }

    async def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        await asyncio.sleep(0.5)
        # Simulate a successful payment status check
        return {"status": "success", "receipt_number": "R_" + transaction_id[:8].upper()}

    async def handle_callback(self, payload: dict[str, Any]) -> dict[str, Any]:
        # In M-Pesa, this unwraps the Body.stkCallback
        body = payload.get("Body", {}).get("stkCallback", {})
        result_code = body.get("ResultCode", -1)

        if result_code == 0:
            return {
                "status": "success",
                "message": body.get("ResultDesc", "Payment successful"),
                "raw_payload": payload,
            }

        return {
            "status": "failed",
            "message": body.get("ResultDesc", "Payment failed"),
            "raw_payload": payload,
        }
