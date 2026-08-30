from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import PaymentStatus


class PaymentCreate(BaseModel):
    amount: Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)] = Field(
        ..., json_schema_extra={"example": 1500}
    )
    currency: str = Field(default="KES", max_length=3, json_schema_extra={"example": "KES"})
    customer_phone: str = Field(..., max_length=20, json_schema_extra={"example": "254700000000"})


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    transaction_id: str
    amount: Annotated[Decimal, Field(max_digits=10, decimal_places=2)]
    currency: str
    customer_phone: str
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime


class PaymentStatusUpdate(BaseModel):
    status: PaymentStatus
    gateway_response: Optional[dict[str, Any]] = None
