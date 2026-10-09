import asyncio
import logging

from aio_pika import DeliveryMode, IncomingMessage, Message

from app.config import NOTIFICATION_MAX_RETRIES
from app.infrastructure.rabbitmq.client import get_connection
from app.infrastructure.rabbitmq.serializer import dumps, loads
from app.infrastructure.rabbitmq.topology import (
    TICKET_ASSIGNED_RETRY_ROUTING_KEY,
    declare_topology,
    get_retry_exchange,
)
from app.schemas.schemas import TicketAssignedEvent
from app.workers.notifications.handlers import handle_ticket_assigned

logger = logging.getLogger(__name__)


async def _republish_for_retry(message: IncomingMessage, event: TicketAssignedEvent) -> None:
    retries = int((message.headers or {}).get("x-retry", 0)) + 1
    connection = await get_connection()
    channel = await connection.channel()
    retry_exchange = await get_retry_exchange(channel)
    await retry_exchange.publish(
        Message(
            body=dumps(event),
            content_type="application/json",
            delivery_mode=DeliveryMode.PERSISTENT,
            message_id=event.message_id,
            headers={"x-retry": retries},
        ),
        routing_key=TICKET_ASSIGNED_RETRY_ROUTING_KEY,
    )


async def _on_message(message: IncomingMessage) -> None:
    async with message.process(requeue=False):
        event = loads(message.body, TicketAssignedEvent)
        try:
            handle_ticket_assigned(event)
        except Exception:
            retries = int((message.headers or {}).get("x-retry", 0))
            if retries < NOTIFICATION_MAX_RETRIES:
                logger.exception(
                    "Retrying ticket.assigned notification ticket_id=%s attempt=%s",
                    event.ticket_id,
                    retries + 1,
                )
                await _republish_for_retry(message, event)
                return
            logger.exception(
                "Moving ticket.assigned notification to DLQ ticket_id=%s",
                event.ticket_id,
            )
            raise


async def consume_ticket_notifications() -> None:
    connection = await get_connection()
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)
    queue = await declare_topology(channel)
    await queue.consume(_on_message)
    logger.info("Listening for ticket.assigned notification events")
    await asyncio.Future()
