from abc import ABC, abstractmethod
from typing import Dict, Any

from app.config import settings

class PaymentGatewayProvider(ABC):
    """Abstract base class for payment gateways to ensure future swap compatibility."""
    
    @abstractmethod
    async def create_order(self, amount: float,  currency: str, receipt_id: str, notes: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a payment order and return gateway-specific session tokens/IDs."""
        pass

    @abstractmethod
    async def verify_payment(self, payload: Dict[str, Any]) -> bool:
        """Verify the payment signature/webhook from the provider."""
        pass


class CashfreeProvider(PaymentGatewayProvider):
    async def create_order(self, amount: float, currency: str, receipt_id: str, notes: Dict[str, Any] = None) -> Dict[str, Any]:
        # TODO: Implement Cashfree SDK call using settings.CASHFREE_APP_ID
        return {"provider": "cashfree", "status": "stub", "order_id": f"cf_{receipt_id}"}
        
    async def verify_payment(self, payload: Dict[str, Any]) -> bool:
        # TODO: Implement Cashfree signature verification
        return True


class RazorpayProvider(PaymentGatewayProvider):
    async def create_order(self, amount: float, currency: str, receipt_id: str, notes: Dict[str, Any] = None) -> Dict[str, Any]:
        # TODO: Implement Razorpay SDK call using settings.RAZORPAY_KEY_ID
        return {"provider": "razorpay", "status": "stub", "order_id": f"rzp_{receipt_id}"}
        
    async def verify_payment(self, payload: Dict[str, Any]) -> bool:
        # TODO: Implement Razorpay signature verification
        return True


def get_payment_provider() -> PaymentGatewayProvider:
    """Factory to return the active payment provider based on configuration."""
    if settings.ACTIVE_PAYMENT_GATEWAY.lower() == "razorpay":
        return RazorpayProvider()
    return CashfreeProvider()
