from abc import ABC, abstractmethod
from app.services.bank.schemas import TransferRequest, TransferResponse, BalanceResponse


class BankServiceInterface(ABC):
    @abstractmethod
    def initiate_transfer(self, request: TransferRequest) -> TransferResponse:
        pass

    @abstractmethod
    def get_transfer_status(self, reference_id: str) -> TransferResponse:
        pass

    @abstractmethod
    def get_balance(self, account_id: str) -> BalanceResponse:
        pass

    @abstractmethod
    def initiate_ach(self, request: TransferRequest) -> TransferResponse:
        pass

    @abstractmethod
    def send_rfp(self, request: TransferRequest) -> TransferResponse:
        pass
