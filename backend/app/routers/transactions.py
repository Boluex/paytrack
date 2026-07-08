import math
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from sqlalchemy import select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.merchant import Merchant
from app.models.transaction import Transaction, TransactionStatus
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionListResponse,
    TransactionStats,
)
from app.services.auth import get_current_merchant, get_merchant_by_api_key, get_current_merchant_flexible
from app.services.fraud import calculate_fraud_score
from app.services.webhook import enqueue_webhook
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/transactions", tags=["Transactions"])


def format_transaction(txn: Transaction) -> TransactionResponse:
    """Convert a Transaction model to a response schema."""
    return TransactionResponse(
        id=txn.id,
        merchant_id=txn.merchant_id,
        amount=float(txn.amount),
        currency=txn.currency,
        status=txn.status,
        customer_email=txn.customer_email,
        description=txn.description,
        fraud_score=txn.fraud_score,
        fraud_reasons=txn.fraud_reasons,
        created_at=txn.created_at.isoformat(),
    )


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    request: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant_flexible),
):
    """
    Log a new payment transaction.
    Automatically runs fraud detection and triggers webhooks.
    """
    # Run fraud detection
    fraud_score, fraud_reasons = await calculate_fraud_score(
        db=db,
        merchant_id=merchant.id,
        amount=request.amount,
        customer_email=request.customer_email,
    )

    # Determine status — auto-flag if fraud score exceeds threshold
    status_value = request.status
    if fraud_score >= settings.FRAUD_SCORE_THRESHOLD:
        status_value = TransactionStatus.FLAGGED

    # Create transaction
    transaction = Transaction(
        merchant_id=merchant.id,
        amount=request.amount,
        currency=request.currency,
        status=status_value,
        customer_email=request.customer_email,
        description=request.description,
        fraud_score=fraud_score,
        fraud_reasons="; ".join(fraud_reasons) if fraud_reasons else None,
    )
    db.add(transaction)
    await db.flush()

    # Enqueue webhook if merchant has a webhook URL configured
    if merchant.webhook_url:
        await enqueue_webhook(
            merchant_id=merchant.id,
            webhook_url=merchant.webhook_url,
            payload={
                "event": "transaction.created",
                "transaction_id": transaction.id,
                "amount": float(transaction.amount),
                "currency": transaction.currency,
                "status": transaction.status,
                "fraud_score": transaction.fraud_score,
            },
        )

    return format_transaction(transaction)


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant_flexible),
):
    """List transactions with pagination and optional filters."""
    query = select(Transaction).where(Transaction.merchant_id == merchant.id)
    count_query = select(func.count(Transaction.id)).where(Transaction.merchant_id == merchant.id)

    # Apply filters
    if status_filter:
        query = query.where(Transaction.status == status_filter)
        count_query = count_query.where(Transaction.status == status_filter)
    if search:
        query = query.where(Transaction.customer_email.ilike(f"%{search}%"))
        count_query = count_query.where(Transaction.customer_email.ilike(f"%{search}%"))

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    # Get paginated results
    offset = (page - 1) * page_size
    query = query.order_by(Transaction.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    transactions = result.scalars().all()

    return TransactionListResponse(
        transactions=[format_transaction(t) for t in transactions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/stats", response_model=TransactionStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant_flexible),
):
    """Get transaction statistics for the dashboard."""
    merchant_filter = Transaction.merchant_id == merchant.id

    # Total transactions
    total_result = await db.execute(
        select(func.count(Transaction.id)).where(merchant_filter)
    )
    total_transactions = total_result.scalar() or 0

    # Total volume
    volume_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(merchant_filter)
    )
    total_volume = float(volume_result.scalar() or 0)

    # Count by status
    status_counts = {}
    for s in ["completed", "pending", "failed", "flagged"]:
        count_result = await db.execute(
            select(func.count(Transaction.id)).where(
                merchant_filter, Transaction.status == s
            )
        )
        status_counts[s] = count_result.scalar() or 0

    # Success rate
    success_rate = 0.0
    if total_transactions > 0:
        success_rate = round((status_counts["completed"] / total_transactions) * 100, 1)

    # Daily volume (last 7 days)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    daily_result = await db.execute(
        select(
            cast(Transaction.created_at, Date).label("date"),
            func.count(Transaction.id).label("count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("volume"),
        )
        .where(merchant_filter, Transaction.created_at >= seven_days_ago)
        .group_by(cast(Transaction.created_at, Date))
        .order_by(cast(Transaction.created_at, Date))
    )
    daily_volume = [
        {"date": str(row.date), "count": row.count, "volume": float(row.volume)}
        for row in daily_result.all()
    ]

    return TransactionStats(
        total_transactions=total_transactions,
        total_volume=total_volume,
        completed_count=status_counts["completed"],
        pending_count=status_counts["pending"],
        failed_count=status_counts["failed"],
        flagged_count=status_counts["flagged"],
        success_rate=success_rate,
        daily_volume=daily_volume,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant_flexible),
):
    """Get a single transaction by ID."""
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.merchant_id == merchant.id,
        )
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return format_transaction(transaction)
