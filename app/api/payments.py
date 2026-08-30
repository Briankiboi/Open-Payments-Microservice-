from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limiter import limiter
from app.core.security import verify_api_key
from app.gateways.mpesa_gateway import MpesaGateway
from app.schemas.payment_schema import PaymentCreate, PaymentResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


def get_payment_service(db: AsyncSession = Depends(get_db)) -> PaymentService:
    gateway = MpesaGateway()  # Usually injected via DI framework or app state
    return PaymentService(db, gateway)


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")  # type: ignore[untyped-decorator]
async def create_payment(
    request: Request,
    payment_in: PaymentCreate,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    service: PaymentService = Depends(get_payment_service),
    api_key: str = Depends(verify_api_key),
) -> Any:
    """
    Creates a new payment record and returns the transaction ID.
    Supports idempotency via the `Idempotency-Key` header.
    """
    payment = await service.create_payment(payment_in, idempotency_key)
    return payment


@router.get("/{transaction_id}", response_model=PaymentResponse)
@limiter.limit("20/minute")  # type: ignore[untyped-decorator]
async def get_payment(
    request: Request,
    transaction_id: str,
    service: PaymentService = Depends(get_payment_service),
    api_key: str = Depends(verify_api_key),
) -> Any:
    """
    Retrieves the status and details of a specific payment transaction.
    """
    payment = await service.get_payment_by_transaction_id(transaction_id)
    return payment


@router.post("/{transaction_id}/pay", response_model=PaymentResponse)
@limiter.limit("5/minute")  # type: ignore[untyped-decorator]
async def initiate_payment(
    request: Request,
    transaction_id: str,
    service: PaymentService = Depends(get_payment_service),
    api_key: str = Depends(verify_api_key),
) -> Any:
    """
    Triggers a payment request (e.g. STK Push) via the configured Gateway adapter.
    """
    payment = await service.initiate_payment(transaction_id)
    return payment
