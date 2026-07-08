from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.merchant import Merchant

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_password(password: str) -> str:
    """Hash a plain-text password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


async def get_current_merchant(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Merchant:
    """FastAPI dependency — extract current merchant from JWT token."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    merchant_id = payload.get("sub")
    if not merchant_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise HTTPException(status_code=401, detail="Merchant not found")

    return merchant


async def get_merchant_by_api_key(
    api_key: str,
    db: AsyncSession,
) -> Merchant:
    """Look up a merchant by their API key."""
    result = await db.execute(select(Merchant).where(Merchant.api_key == api_key))
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return merchant


async def get_current_merchant_flexible(
    api_key: str | None = Depends(api_key_header),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Merchant:
    """
    FastAPI dependency — supports auth via X-API-Key, Authorization: Bearer <api_key>, or Authorization: Bearer <jwt>.
    """
    if api_key:
        return await get_merchant_by_api_key(api_key, db)

    if credentials and credentials.credentials:
        token = credentials.credentials
        if token.startswith("pk_"):
            return await get_merchant_by_api_key(token, db)
        else:
            try:
                payload = decode_token(token)
                merchant_id = payload.get("sub")
                if not merchant_id:
                    raise HTTPException(status_code=401, detail="Invalid token payload")

                result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
                merchant = result.scalar_one_or_none()
                if not merchant:
                    raise HTTPException(status_code=401, detail="Merchant not found")
                return merchant
            except HTTPException:
                raise
            except Exception:
                raise HTTPException(status_code=401, detail="Invalid authorization token")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid credentials",
    )

