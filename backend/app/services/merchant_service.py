from typing import Optional
from sqlalchemy.orm import Session

from app.models.merchant import Merchant
from app.schemas.merchant import MerchantCreate, MerchantUpdate, MerchantResponse, KYBSubmit
from app.services.event_service import log_event


def create_merchant(db: Session, payload: MerchantCreate) -> MerchantResponse:
    merchant = Merchant(
        name=payload.name,
        ein=payload.ein,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        sponsor_bank_id=payload.sponsor_bank_id,
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    log_event(db, "merchant.created", "merchant_service", merchant.id)
    return MerchantResponse.model_validate(merchant)


def get_merchant(db: Session, merchant_id: str) -> Optional[MerchantResponse]:
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        return None
    return MerchantResponse.model_validate(merchant)


def update_merchant(db: Session, merchant_id: str, payload: MerchantUpdate) -> Optional[MerchantResponse]:
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(merchant, key, value)

    db.commit()
    db.refresh(merchant)
    log_event(db, "merchant.updated", "merchant_service", merchant.id)
    return MerchantResponse.model_validate(merchant)


def submit_kyb(db: Session, merchant_id: str, payload: KYBSubmit) -> MerchantResponse:
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise ValueError("Merchant not found")

    merchant.ein = payload.ein
    merchant.kyb_status = "approved"  # Mock: auto-approve
    merchant.onboarding_status = "active"
    db.commit()
    db.refresh(merchant)

    log_event(db, "merchant.kyb_approved", "merchant_service", merchant.id)
    return MerchantResponse.model_validate(merchant)
