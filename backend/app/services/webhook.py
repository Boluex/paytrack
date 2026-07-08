import json
import asyncio
import logging

import httpx
import redis.asyncio as redis

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Redis client for webhook queue
redis_client: redis.Redis | None = None

WEBHOOK_QUEUE = "paytrack:webhooks"
MAX_RETRIES = 3


async def get_redis() -> redis.Redis:
    """Get or create Redis connection."""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return redis_client


async def enqueue_webhook(merchant_id: str, webhook_url: str, payload: dict):
    """Add a webhook delivery job to the Redis queue."""
    r = await get_redis()
    job = json.dumps({
        "merchant_id": merchant_id,
        "webhook_url": webhook_url,
        "payload": payload,
        "retries": 0,
    })
    await r.lpush(WEBHOOK_QUEUE, job)
    logger.info(f"Webhook enqueued for merchant {merchant_id}")


async def process_webhooks():
    """Background worker: process webhook delivery queue."""
    r = await get_redis()
    logger.info("Webhook worker started")

    while True:
        try:
            # Blocking pop from queue
            result = await r.brpop(WEBHOOK_QUEUE, timeout=5)
            if result is None:
                continue

            _, job_data = result
            job = json.loads(job_data)

            success = await deliver_webhook(
                job["webhook_url"],
                job["payload"],
            )

            if not success and job["retries"] < MAX_RETRIES:
                # Re-enqueue with incremented retry count
                job["retries"] += 1
                await r.lpush(WEBHOOK_QUEUE, json.dumps(job))
                # Exponential backoff
                await asyncio.sleep(2 ** job["retries"])
            elif not success:
                logger.error(
                    f"Webhook delivery failed after {MAX_RETRIES} retries "
                    f"for merchant {job['merchant_id']}"
                )

        except Exception as e:
            logger.error(f"Webhook worker error: {e}")
            await asyncio.sleep(1)


async def deliver_webhook(url: str, payload: dict) -> bool:
    """Send HTTP POST to merchant's webhook URL."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json", "User-Agent": "PayTrack/1.0"},
            )
            if response.status_code < 300:
                logger.info(f"Webhook delivered to {url} (status: {response.status_code})")
                return True
            else:
                logger.warning(f"Webhook to {url} returned {response.status_code}")
                return False
    except Exception as e:
        logger.warning(f"Webhook delivery to {url} failed: {e}")
        return False
