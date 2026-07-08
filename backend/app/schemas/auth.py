from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    """Schema for merchant registration."""
    email: str
    password: str
    business_name: str


class LoginRequest(BaseModel):
    """Schema for merchant login."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class MerchantResponse(BaseModel):
    """Schema for merchant profile response."""
    id: str
    email: str
    business_name: str
    api_key: str
    webhook_url: str | None
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True
