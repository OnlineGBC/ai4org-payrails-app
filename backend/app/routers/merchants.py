from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.bank_account import BankAccount
from app.schemas.merchant import MerchantCreate, MerchantUpdate, MerchantResponse, KYBSubmit
from app.schemas.bank_account import BankAccountCreate, BankAccountResponse, MicroDepositVerify
from app.services.merchant_service import create_merchant, get_merchant, update_merchant, submit_kyb
from app.services.account_verification import (
    validate_routing_number,
    validate_account_number,
    generate_micro_deposits,
    verify_micro_deposits,
    mock_plaid_verification,
)
from app.utils.encryption import encrypt_value, decrypt_value
from app.services.event_service import log_event

router = APIRouter(prefix="/merchants", tags=["merchants"])


@router.post("", response_model=MerchantResponse, status_code=status.HTTP_201_CREATED)
def create_merchant_endpoint(
    payload: MerchantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_merchant(db, payload)


@router.get("/{merchant_id}/status", response_model=MerchantResponse)
def get_merchant_status(
    merchant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_merchant(db, merchant_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")
    return result


@router.put("/{merchant_id}", response_model=MerchantResponse)
def update_merchant_endpoint(
    merchant_id: str,
    payload: MerchantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = update_merchant(db, merchant_id, payload)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")
    return result


@router.post("/{merchant_id}/kyb", response_model=MerchantResponse)
def submit_kyb_endpoint(
    merchant_id: str,
    payload: KYBSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return submit_kyb(db, merchant_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{merchant_id}/bank-accounts", response_model=BankAccountResponse, status_code=status.HTTP_201_CREATED)
def add_bank_account(
    merchant_id: str,
    payload: BankAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not validate_routing_number(payload.routing_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid routing number",
        )
    if not validate_account_number(payload.account_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid account number",
        )

    amount_1, amount_2 = generate_micro_deposits()

    account = BankAccount(
        merchant_id=merchant_id,
        bank_name=payload.bank_name,
        routing_number=payload.routing_number,
        encrypted_account_number=encrypt_value(payload.account_number),
        account_type=payload.account_type,
        verification_status="micro_deposit_sent",
        micro_deposit_amount_1=amount_1,
        micro_deposit_amount_2=amount_2,
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    log_event(db, "bank_account.created", "merchants_router", account.id)

    return BankAccountResponse(
        id=account.id,
        merchant_id=account.merchant_id,
        bank_name=account.bank_name,
        routing_number=account.routing_number,
        account_number_last4=payload.account_number[-4:],
        account_type=account.account_type,
        verification_status=account.verification_status,
        created_at=account.created_at,
    )


@router.get("/{merchant_id}/bank-accounts")
def list_bank_accounts(
    merchant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    accounts = db.query(BankAccount).filter(BankAccount.merchant_id == merchant_id).all()
    result = []
    for acc in accounts:
        try:
            decrypted = decrypt_value(acc.encrypted_account_number)
            last4 = decrypted[-4:] if decrypted else None
        except Exception:
            last4 = "****"
        result.append(BankAccountResponse(
            id=acc.id,
            merchant_id=acc.merchant_id,
            bank_name=acc.bank_name,
            routing_number=acc.routing_number,
            account_number_last4=last4,
            account_type=acc.account_type,
            verification_status=acc.verification_status,
            created_at=acc.created_at,
        ))
    return result


@router.post("/{merchant_id}/bank-accounts/{account_id}/verify-micro-deposits", response_model=BankAccountResponse)
def verify_micro_deposits_endpoint(
    merchant_id: str,
    account_id: str,
    payload: MicroDepositVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = (
        db.query(BankAccount)
        .filter(BankAccount.id == account_id, BankAccount.merchant_id == merchant_id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank account not found")

    if account.verification_status == "verified":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already verified")

    if verify_micro_deposits(
        account.micro_deposit_amount_1,
        account.micro_deposit_amount_2,
        payload.amount_1,
        payload.amount_2,
    ):
        account.verification_status = "verified"
        db.commit()
        db.refresh(account)
        log_event(db, "bank_account.verified", "merchants_router", account.id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Micro-deposit amounts do not match",
        )

    decrypted = decrypt_value(account.encrypted_account_number)
    return BankAccountResponse(
        id=account.id,
        merchant_id=account.merchant_id,
        bank_name=account.bank_name,
        routing_number=account.routing_number,
        account_number_last4=decrypted[-4:] if decrypted else None,
        account_type=account.account_type,
        verification_status=account.verification_status,
        created_at=account.created_at,
    )


@router.post("/{merchant_id}/bank-accounts/{account_id}/verify-instant", response_model=BankAccountResponse)
def verify_instant_endpoint(
    merchant_id: str,
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = (
        db.query(BankAccount)
        .filter(BankAccount.id == account_id, BankAccount.merchant_id == merchant_id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank account not found")

    decrypted = decrypt_value(account.encrypted_account_number)
    plaid_result = mock_plaid_verification(account.routing_number, decrypted)

    if plaid_result["status"] == "verified":
        account.verification_status = "verified"
        db.commit()
        db.refresh(account)
        log_event(db, "bank_account.instant_verified", "merchants_router", account.id)

    return BankAccountResponse(
        id=account.id,
        merchant_id=account.merchant_id,
        bank_name=account.bank_name,
        routing_number=account.routing_number,
        account_number_last4=decrypted[-4:] if decrypted else None,
        account_type=account.account_type,
        verification_status=account.verification_status,
        created_at=account.created_at,
    )
