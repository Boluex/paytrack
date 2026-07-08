from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.merchant import Merchant
from app.services.auth import get_current_merchant

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


class WebhookConfig(BaseModel):
    """Schema for webhook configuration."""
    webhook_url: str


class WebhookResponse(BaseModel):
    """Schema for webhook config response."""
    webhook_url: str | None
    message: str


@router.get("", response_model=WebhookResponse)
async def get_webhook(merchant: Merchant = Depends(get_current_merchant)):
    """Get current webhook configuration."""
    return WebhookResponse(
        webhook_url=merchant.webhook_url,
        message="Webhook URL retrieved",
    )


@router.put("", response_model=WebhookResponse)
async def update_webhook(
    config: WebhookConfig,
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Set or update the webhook URL for transaction notifications."""
    merchant.webhook_url = config.webhook_url
    db.add(merchant)
    await db.flush()

    return WebhookResponse(
        webhook_url=merchant.webhook_url,
        message="Webhook URL updated successfully",
    )


@router.delete("", response_model=WebhookResponse)
async def delete_webhook(
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Remove the webhook URL."""
    merchant.webhook_url = None
    db.add(merchant)
    await db.flush()

    return WebhookResponse(
        webhook_url=None,
        message="Webhook URL removed",
    )
