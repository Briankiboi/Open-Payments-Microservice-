import logging
from typing import Any, Dict

logger = logging.getLogger("arq.worker")


async def process_payment_async(ctx: Dict[Any, Any], transaction_id: str) -> None:
    """
    Background task to process a payment asynchronously.
    In a real scenario, this allows FastAPI to return immediately
    while the worker handles the slow network request to the payment gateway.
    """
    # Import locally to avoid circular dependencies and only hit DB in worker context
    from app.core.database import async_session
    from app.gateways.mpesa_gateway import MpesaGateway
    from app.services.payment_service import PaymentService

    logger.info(f"Starting async processing for transaction {transaction_id}")

    async with async_session() as db:
        gateway = MpesaGateway()
        service = PaymentService(db, gateway)
        try:
            # We initiate the payment here instead of blocking the main thread
            await service.initiate_payment(transaction_id)
            logger.info(f"Successfully initiated payment for {transaction_id}")
        except Exception as e:
            logger.error(f"Failed to process async payment {transaction_id}: {str(e)}")
            # ARQ will retry automatically based on worker settings if this throws an unhandled exception
            raise e
