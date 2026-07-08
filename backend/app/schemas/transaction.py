from pydantic import BaseModel
from datetime import datetime


class TransactionCreate(BaseModel):
    """Schema for creating a new transaction."""
    amount: float
    currency: str = "USD"
    status: str = "pending"
    customer_email: str | None = None
    description: str | None = None


class TransactionResponse(BaseModel):
    """Schema for transaction response."""
    id: str
    merchant_id: str
    amount: float
    currency: str
    status: str
    customer_email: str | None
    description: str | None
    fraud_score: int
    fraud_reasons: str | None
    created_at: str

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list."""
    transactions: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TransactionStats(BaseModel):
    """Schema for transaction statistics."""
    total_transactions: int
    total_volume: float
    completed_count: int
    pending_count: int
    failed_count: int
    flagged_count: int
    success_rate: float
    daily_volume: list[dict]
