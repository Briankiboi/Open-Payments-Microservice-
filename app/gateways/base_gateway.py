from abc import ABC, abstractmethod
from typing import Any, Dict, TypeVar

# Define a TypeVar for the payload and response types
# This allows subclasses to specify more concrete types if needed
PayloadType = TypeVar('PayloadType', bound=Dict[str, Any])
ResponseType = TypeVar('ResponseType', bound=Dict[str, Any])


class PaymentGateway(ABC):
    """
    Base interface for payment gateways.
    All implementing gateways must provide concrete implementations for these methods.
    """

    @abstractmethod
    async def initiate_payment(
        self, transaction_id: str, amount: float, currency: str, phone: str
    ) -> Dict[str, Any]:
        """
        Initiates a payment request to the external provider.
        """
        pass

    @abstractmethod
    async def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """
        Checks the status of a specific transaction asynchronously.
        """
        pass

    @abstractmethod
    async def handle_callback(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Parses the provider's webhook payload and returns normalized status / identifiers.
        """
        pass
