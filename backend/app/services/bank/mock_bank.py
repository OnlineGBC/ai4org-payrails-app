import uuid
import random
import time
from decimal import Decimal
from typing import Dict

from app.services.bank.interface import BankServiceInterface
from app.services.bank.schemas import TransferRequest, TransferResponse, BalanceResponse

RAIL_LIMITS = {
    "fednow": Decimal("500000"),
    "rtp": Decimal("1000000"),
    "ach": Decimal("10000000"),
    "card": Decimal("50000"),
}

ERROR_RATE = 0.05  # 5% error simulation


class MockBankService(BankServiceInterface):
    def __init__(self):
        self._transfers: Dict[str, TransferResponse] = {}
        self._idempotency_cache: Dict[str, TransferResponse] = {}

    def _simulate_delay(self, rail: str):
        delays = {"fednow": 0.1, "rtp": 0.1, "ach": 0.5, "card": 0.2}
        time.sleep(delays.get(rail, 0.1))

    def _simulate_error(self) -> bool:
        return random.random() < ERROR_RATE

    def _check_limit(self, rail: str, amount: Decimal) -> bool:
        limit = RAIL_LIMITS.get(rail)
        if limit is None:
            return False
        return amount <= limit

    def initiate_transfer(self, request: TransferRequest) -> TransferResponse:
        # Idempotency check
        if request.idempotency_key in self._idempotency_cache:
            return self._idempotency_cache[request.idempotency_key]

        # Limit check
        if not self._check_limit(request.rail, request.amount):
            response = TransferResponse(
                reference_id=str(uuid.uuid4()),
                status="failed",
                rail=request.rail,
                amount=request.amount,
                failure_reason=f"Amount exceeds {request.rail} limit of ${RAIL_LIMITS[request.rail]}",
            )
            self._idempotency_cache[request.idempotency_key] = response
            return response

        self._simulate_delay(request.rail)

        # Simulate random error
        if self._simulate_error():
            response = TransferResponse(
                reference_id=str(uuid.uuid4()),
                status="failed",
                rail=request.rail,
                amount=request.amount,
                failure_reason="Bank processing error (simulated)",
            )
        else:
            response = TransferResponse(
                reference_id=str(uuid.uuid4()),
                status="completed",
                rail=request.rail,
                amount=request.amount,
            )

        self._transfers[response.reference_id] = response
        self._idempotency_cache[request.idempotency_key] = response
        return response

    def get_transfer_status(self, reference_id: str) -> TransferResponse:
        if reference_id in self._transfers:
            return self._transfers[reference_id]
        return TransferResponse(
            reference_id=reference_id,
            status="not_found",
            rail="unknown",
            amount=Decimal("0"),
            failure_reason="Transfer not found",
        )

    def get_balance(self, account_id: str) -> BalanceResponse:
        return BalanceResponse(
            account_id=account_id,
            available_balance=Decimal("100000.00"),
        )

    def initiate_ach(self, request: TransferRequest) -> TransferResponse:
        request_copy = request.model_copy(update={"rail": "ach"})
        return self.initiate_transfer(request_copy)

    def send_rfp(self, request: TransferRequest) -> TransferResponse:
        return self.initiate_transfer(request)


# Singleton instance
mock_bank_service = MockBankService()
