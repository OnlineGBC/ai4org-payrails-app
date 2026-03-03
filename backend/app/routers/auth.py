from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.merchant import Merchant
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, UserUpdate, TokenResponse,
    MerchantRegisterPayload, PasswordResetRequest, PasswordResetConfirm,
    PasswordResetRequestResponse,
)
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_reset_token,
    decode_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    # Create a linked merchant record for the consumer so they can manage bank accounts
    local_part = payload.email.split("@")[0]
    merchant = Merchant(
        name=local_part,
        contact_email=payload.email,
        onboarding_status="active",
        kyb_status="not_required",
    )
    db.add(merchant)
    db.flush()  # get merchant.id before commit
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        merchant_id=merchant.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/register/merchant", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_merchant(payload: MerchantRegisterPayload, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    if db.query(Merchant).filter(Merchant.ein == payload.ein).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="EIN already registered"
        )
    merchant = Merchant(
        name=payload.business_name,
        ein=payload.ein,
        contact_email=payload.contact_email,
        onboarding_status="active",
        kyb_status="not_submitted",
    )
    db.add(merchant)
    db.flush()
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role="merchant_admin",
        merchant_id=merchant.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    token_data = {"sub": user.id, "email": user.email, "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(refresh_token: str, db: Session = Depends(get_db)):
    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    token_data = {"sub": user.id, "email": user.email, "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/password-reset/request", response_model=PasswordResetRequestResponse)
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        # Don't reveal whether the email exists
        return PasswordResetRequestResponse(
            message="If that email is registered, a reset code has been sent."
        )
    token = create_reset_token(payload.email)
    return PasswordResetRequestResponse(
        message="Reset code generated. In production this would be emailed.",
        reset_token=token,
    )


@router.post("/password-reset/confirm")
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    decoded = decode_token(payload.token)
    if decoded is None or decoded.get("type") != "reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    email = decoded.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if len(payload.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password reset successfully"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.email is not None:
        new_email = payload.email.strip().lower()
        if new_email and new_email != current_user.email:
            taken = db.query(User).filter(User.email == new_email, User.id != current_user.id).first()
            if taken:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
            current_user.email = new_email
    if payload.phone is not None:
        current_user.phone = payload.phone.strip() or None
    if payload.first_name is not None:
        current_user.first_name = payload.first_name.strip() or None
    if payload.last_name is not None:
        current_user.last_name = payload.last_name.strip() or None
    db.commit()
    db.refresh(current_user)
    return current_user
