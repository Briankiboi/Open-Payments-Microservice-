import json
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limiter import limiter
from app.gateways.mpesa_gateway import MpesaGateway
from app.services.payment_service import PaymentService
from app.webhooks.verify import verify_webhook_signature

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def get_payment_service(db: AsyncSession = Depends(get_db)) -> PaymentService:
    gateway = MpesaGateway()
    return PaymentService(db, gateway)


@router.post("/payment")
@limiter.limit("60/minute")  # type: ignore[untyped-decorator]
async def payment_webhook(
    request: Request,
    signature: Optional[str] = Header(None, alias="X-Signature"),
    service: PaymentService = Depends(get_payment_service),
) -> dict[str, Any]:
    """
    Receives callbacks from payment gateways and updates payment status.
    """
    # 1. Read the raw body
    body_bytes = await request.body()

    if not body_bytes:
        raise HTTPException(status_code=400, detail="Request body is empty")

    # 2. Verify signature BEFORE parsing (security first)
    if signature is None or not verify_webhook_signature(body_bytes, signature):
        raise HTTPException(status_code=401, detail="Invalid Webhook Signature")

    # 3. Parse JSON safely
    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from None

    # 4. Process webhook
    await service.process_webhook(payload)

    return {"status": "received"}
