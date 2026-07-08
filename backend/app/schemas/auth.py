from pydantic import BaseModel, Field, field_validator
import re


class RegisterRequest(BaseModel):
    """Schema for merchant registration."""
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)
    business_name: str = Field(..., min_length=1)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Invalid email format")
        return v

    @field_validator("business_name")
    @classmethod
    def validate_business_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) == 0:
            raise ValueError("Business name cannot be empty")
        return v



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
