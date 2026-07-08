from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.merchant import Merchant
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, MerchantResponse
from app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_merchant,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new merchant account."""
    # Check if email already exists
    result = await db.execute(select(Merchant).where(Merchant.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create merchant
    merchant = Merchant(
        email=request.email,
        hashed_password=hash_password(request.password),
        business_name=request.business_name,
    )
    db.add(merchant)
    await db.flush()

    # Generate JWT
    token = create_access_token({"sub": merchant.id})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate merchant and return JWT token."""
    result = await db.execute(select(Merchant).where(Merchant.email == request.email))
    merchant = result.scalar_one_or_none()

    if not merchant or not verify_password(request.password, merchant.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token({"sub": merchant.id})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=MerchantResponse)
async def get_me(merchant: Merchant = Depends(get_current_merchant)):
    """Get current merchant profile including API key."""
    return MerchantResponse(
        id=merchant.id,
        email=merchant.email,
        business_name=merchant.business_name,
        api_key=merchant.api_key,
        webhook_url=merchant.webhook_url,
        is_active=merchant.is_active,
        created_at=merchant.created_at.isoformat(),
    )


@router.post("/regenerate-api-key", response_model=MerchantResponse)
async def regenerate_api_key(
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Regenerate the merchant's API key."""
    import uuid
    merchant.api_key = f"pk_{uuid.uuid4().hex}"
    db.add(merchant)
    await db.flush()
    return MerchantResponse(
        id=merchant.id,
        email=merchant.email,
        business_name=merchant.business_name,
        api_key=merchant.api_key,
        webhook_url=merchant.webhook_url,
        is_active=merchant.is_active,
        created_at=merchant.created_at.isoformat(),
    )

