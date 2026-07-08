from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.transaction import Transaction

settings = get_settings()


async def calculate_fraud_score(
    db: AsyncSession,
    merchant_id: str,
    amount: float,
    customer_email: str | None,
) -> tuple[int, list[str]]:
    """
    Calculate fraud score for a transaction.

    Rules:
    1. Velocity check — >10 transactions in 1 minute → +40 points
    2. Amount anomaly — amount > 3x merchant average → +35 points
    3. Duplicate check — same amount + customer in 2 minutes → +30 points

    Returns:
        (fraud_score, list_of_reasons)
    """
    score = 0
    reasons = []
    now = datetime.now(timezone.utc)

    # Rule 1: Velocity check
    one_minute_ago = now - timedelta(minutes=1)
    velocity_result = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.merchant_id == merchant_id,
            Transaction.created_at >= one_minute_ago,
        )
    )
    recent_count = velocity_result.scalar() or 0
    if recent_count >= settings.FRAUD_VELOCITY_LIMIT:
        score += 40
        reasons.append(f"Velocity: {recent_count} transactions in last minute (limit: {settings.FRAUD_VELOCITY_LIMIT})")

    # Rule 2: Amount anomaly
    avg_result = await db.execute(
        select(func.avg(Transaction.amount)).where(
            Transaction.merchant_id == merchant_id,
        )
    )
    avg_amount = avg_result.scalar()
    if avg_amount and float(avg_amount) > 0:
        if amount > float(avg_amount) * settings.FRAUD_AMOUNT_MULTIPLIER:
            score += 35
            reasons.append(
                f"Amount anomaly: ${amount:.2f} is >{settings.FRAUD_AMOUNT_MULTIPLIER}x "
                f"average (${float(avg_amount):.2f})"
            )

    # Rule 3: Duplicate check
    if customer_email:
        two_minutes_ago = now - timedelta(minutes=2)
        dup_result = await db.execute(
            select(func.count(Transaction.id)).where(
                Transaction.merchant_id == merchant_id,
                Transaction.amount == amount,
                Transaction.customer_email == customer_email,
                Transaction.created_at >= two_minutes_ago,
            )
        )
        dup_count = dup_result.scalar() or 0
        if dup_count > 0:
            score += 30
            reasons.append(
                f"Duplicate: same amount (${amount:.2f}) and customer ({customer_email}) "
                f"within 2 minutes"
            )

    return score, reasons
