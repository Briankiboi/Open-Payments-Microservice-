import logging
import uuid
from typing import Any, Optional

import redis.asyncio as redis
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.gateways.base_gateway import PaymentGateway
from app.models.payment import Payment, PaymentLog, PaymentStatus
from app.schemas.payment_schema import PaymentCreate

logger = logging.getLogger(__name__)
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


class PaymentService:
    def __init__(self, db: AsyncSession, gateway: PaymentGateway):
        self.db = db
        self.gateway = gateway

    async def create_payment(
        self, payment_data: PaymentCreate, idempotency_key: Optional[str] = None
    ) -> Payment:
        # Check idempotency
        if idempotency_key:
            cached_payment_id = await redis_client.get(f"idempotency:{idempotency_key}")
            if cached_payment_id:
                logger.info(f"Idempotency hit for key: {idempotency_key}")
                stmt = select(Payment).where(Payment.id == uuid.UUID(cached_payment_id))
                result = await self.db.execute(stmt)
                payment = result.scalar_one_or_none()
                if payment:
                    return payment

        transaction_id = str(uuid.uuid4())

        new_payment = Payment(
            transaction_id=transaction_id,
            amount=payment_data.amount,
            currency=payment_data.currency,
            customer_phone=payment_data.customer_phone,
            status=PaymentStatus.PENDING,
        )
        self.db.add(new_payment)
        await self.db.commit()
        await self.db.refresh(new_payment)

        # Save idempotency key for 24 hours
        if idempotency_key:
            await redis_client.setex(f"idempotency:{idempotency_key}", 86400, str(new_payment.id))

        return new_payment

    async def get_payment_by_transaction_id(self, transaction_id: str) -> Payment:
        stmt = select(Payment).where(Payment.transaction_id == transaction_id)
        result = await self.db.execute(stmt)
        payment = result.scalar_one_or_none()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        return payment

    async def initiate_payment(self, transaction_id: str) -> Payment:
        payment = await self.get_payment_by_transaction_id(transaction_id)

        if payment.status != PaymentStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Payment cannot be initiated. Current status: {payment.status.value}",
            )

        try:
            gateway_response = await self.gateway.initiate_payment(
                transaction_id=payment.transaction_id,
                amount=float(payment.amount),
                currency=payment.currency,
                phone=payment.customer_phone,
            )

            log = PaymentLog(
                payment_id=payment.id,
                gateway_response={"action": "initiate", "response": gateway_response},
            )
            self.db.add(log)
            await self.db.commit()

            return payment

        except Exception as e:
            logger.error(f"Error initiating payment: {str(e)}")
            raise HTTPException(status_code=502, detail="Payment gateway error") from e

    async def process_webhook(self, payload: dict[str, Any]) -> Payment:
        """
        Processes an incoming webhook from the payment provider.
        Assumes payload contains the transaction_id for mapping.
        """
        transaction_id = payload.get("transaction_id")
        if not transaction_id:
            raise HTTPException(status_code=400, detail="Missing transaction_id in webhook payload")

        payment = await self.get_payment_by_transaction_id(transaction_id)

        parsed_response = await self.gateway.handle_callback(payload)

        log = PaymentLog(
            payment_id=payment.id,
            gateway_response={"action": "webhook", "payload": payload, "parsed": parsed_response},
        )
        self.db.add(log)

        status_update = parsed_response.get("status")
        if status_update == "success":
            payment.status = PaymentStatus.SUCCESS
        elif status_update == "failed":
            payment.status = PaymentStatus.FAILED

        await self.db.commit()
        await self.db.refresh(payment)

        return payment
